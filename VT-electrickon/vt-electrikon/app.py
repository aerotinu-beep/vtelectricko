import os
import sqlite3
import json
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__, static_folder="statistcs")
app.secret_key = os.environ.get("SECRET_KEY", "fallback_secret")

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
UPI_ID = os.environ.get("UPI_ID", "vtelectrickon@upi")

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        brand TEXT,
        price REAL,
        stock INTEGER,
        image TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        address TEXT,
        items TEXT,
        total REAL,
        payment_method TEXT,
        payment_status TEXT DEFAULT 'pending',
        transaction_ref TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        delivery_status TEXT DEFAULT 'pending'
    )
    """)
    try:
        c.execute("ALTER TABLE orders ADD COLUMN delivery_status TEXT DEFAULT 'pending'")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE orders ADD COLUMN transaction_ref TEXT")
    except Exception:
        pass
    c.execute("SELECT COUNT(*) FROM products")
    count = c.fetchone()[0]
    if count == 0:
        c.execute("""
        INSERT INTO products (name,brand,price,stock,image)
        VALUES
        ('Multispan Digital Timer','Multispan',1200,5,'multispan_timer.jpg'),
        ('Sibass MCB','Sibass',850,2,'sibass_mcb.jpg')
        """)
    conn.commit()
    conn.close()

init_db()

# ---------------- HELPERS ----------------
def get_cart_products():
    cart_ids = session.get("cart", [])
    if not cart_ids:
        return [], 0
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    products = []
    for pid in cart_ids:
        c.execute("SELECT * FROM products WHERE id=?", (pid,))
        p = c.fetchone()
        if p:
            products.append(p)
    conn.close()
    total = sum(p[3] for p in products)
    return products, total

# ---------------- ADMIN AUTH ----------------
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))
        else:
            error = "Incorrect password."
    return render_template("admin_login.html", error=error)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("home"))

# ---------------- HOME ----------------
@app.route("/", methods=["GET", "HEAD"])
def home():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    conn.close()
    return render_template("index.html", products=products)

# ---------------- ADD TO CART ----------------
@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    cart = session.get("cart", [])
    cart.append(product_id)
    session["cart"] = cart
    return redirect(url_for("cart"))

# ---------------- CART PAGE ----------------
@app.route("/cart")
def cart():
    products, total = get_cart_products()
    return render_template("cart.html", products=products, total=total)

# ---------------- REMOVE FROM CART ----------------
@app.route("/remove_from_cart/<int:index>")
def remove_from_cart(index):
    cart = session.get("cart", [])
    if 0 <= index < len(cart):
        cart.pop(index)
        session["cart"] = cart
    return redirect(url_for("cart"))

# ---------------- BUY PRODUCT ----------------
@app.route("/buy/<int:product_id>")
def buy(product_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT stock FROM products WHERE id=?", (product_id,))
    stock = c.fetchone()
    if stock and stock[0] > 0:
        c.execute("UPDATE products SET stock = stock - 1 WHERE id=?", (product_id,))
        conn.commit()
    conn.close()
    return redirect(url_for("home"))

# ---------------- CHECKOUT ----------------
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    products, total = get_cart_products()
    if not products:
        return redirect(url_for("cart"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        method = request.form.get("payment_method", "cod")
        transaction_ref = request.form.get("transaction_ref", "").strip()
        items_json = json.dumps([{"name": p[1], "price": p[3]} for p in products])

        if method == "upi" and not transaction_ref:
            return render_template("checkout.html", products=products, total=total,
                                   upi_id=UPI_ID,
                                   error="Please enter your UPI transaction reference number after paying.")

        pay_status = "pending" if method == "upi" else "confirmed"
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("""INSERT INTO orders (name, phone, address, items, total, payment_method, payment_status, transaction_ref, delivery_status)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')""",
                  (name, phone, address, items_json, total, method, pay_status, transaction_ref or None))
        order_id = c.lastrowid
        conn.commit()
        conn.close()
        session["cart"] = []
        return render_template("order_confirmed.html", name=name, total=total,
                               method="UPI" if method == "upi" else "Cash on Delivery",
                               order_id=order_id)

    return render_template("checkout.html", products=products, total=total, upi_id=UPI_ID)

# ---------------- ORDER STATUS (for customers) ----------------
@app.route("/order/status/<int:order_id>")
def order_status(order_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, name, total, payment_method, delivery_status, created_at FROM orders WHERE id=?", (order_id,))
    order = c.fetchone()
    conn.close()
    return render_template("order_status.html", order=order, order_id=order_id)

# ---------------- ADMIN PANEL ----------------
@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        brand = request.form.get("brand", "").strip()
        price = request.form.get("price", "0").strip()
        stock = request.form.get("stock", "0").strip()
        image = request.form.get("image", "").strip()
        if name:
            try:
                price = float(price)
                stock = int(stock)
            except ValueError:
                price = 0.0
                stock = 0
            c.execute(
                "INSERT INTO products (name, brand, price, stock, image) VALUES (?, ?, ?, ?, ?)",
                (name, brand, price, stock, image)
            )
            conn.commit()
        conn.close()
        return redirect(url_for("admin"))
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    c.execute("""SELECT id, name, phone, address, total, payment_method, payment_status,
                        transaction_ref, delivery_status, created_at
                 FROM orders ORDER BY created_at DESC LIMIT 50""")
    orders = c.fetchall()
    conn.close()
    return render_template("admin.html", products=products, orders=orders)

# ---------------- MARK ORDER DONE ----------------
@app.route("/admin/order/<int:order_id>/done")
@admin_required
def order_done(order_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE orders SET delivery_status='done' WHERE id=?", (order_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

# ---------------- DELETE PRODUCT ----------------
@app.route("/admin/delete/<int:product_id>")
@admin_required
def delete_product(product_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

# ---------------- STARTUP ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
