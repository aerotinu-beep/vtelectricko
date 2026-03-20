# VT Electrikon

An electronics e-commerce store built with Flask and SQLite.

## Project Structure

```
vt-electrikon/
  app.py           - Main Flask application
  requirements.txt - Python dependencies (Flask, gunicorn)
  Procfile         - Process definition for deployment
  templates/       - Jinja2 HTML templates (index.html, cart.html, admin.html)
  statistcs/       - Static assets (CSS, JS)
```

## Tech Stack

- **Language:** Python 3.12
- **Framework:** Flask 2.3.2
- **Database:** SQLite (database.db, created at app startup)
- **Server:** Flask dev server (development), Gunicorn (production)

## Running the App

The app runs via the "Start application" workflow:
```
cd vt-electrikon && python app.py
```
Serves on `0.0.0.0:5000`.

## Key Features

- Product listing with stock management
- Shopping cart (session-based)
- Buy products (reduces stock)
- Admin panel (admin.html template)

## Database

SQLite database (`vt-electrikon/database.db`) is initialized automatically on startup via `init_db()`. Seeds two sample products if empty:
- Multispan Digital Timer (₹1200, stock: 5)
- Sibass MCB (₹850, stock: 2)

## Deployment

Configured for autoscale deployment using gunicorn:
```
cd vt-electrikon && gunicorn --bind=0.0.0.0:5000 --reuse-port app:app
```

## Notes

- Product images (multispan_timer.jpg, sibass_mcb.jpg) are referenced but not included in the repo — product cards will show broken image placeholders.
- The SECRET_KEY for sessions can be set via the `SECRET_KEY` environment variable.
