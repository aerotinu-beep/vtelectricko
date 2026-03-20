/* VTELECTRICKON - Checkout Payment Selection */

function selectMethod(method) {
    ['cod', 'upi', 'card'].forEach(function(m) {
        document.getElementById('label-' + m).classList.remove('selected');
    });
    document.getElementById('label-' + method).classList.add('selected');

    var upiBox = document.getElementById('upi-instructions');
    var txRef = document.getElementById('transaction_ref');

    if (method === 'upi') {
        upiBox.style.display = 'block';
        if (txRef) txRef.required = true;
    } else {
        upiBox.style.display = 'none';
        if (txRef) txRef.required = false;
    }
}

/* Auto-dismiss order toast after 5 seconds */
document.addEventListener('DOMContentLoaded', function() {
    var toast = document.getElementById('orderToast');
    if (toast) {
        setTimeout(function() { toast.remove(); }, 5000);
    }
});
