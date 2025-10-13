import os
from flask import Flask, request, jsonify
from datetime import datetime
import random
import string
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from flask_jwt_extended import JWTManager, jwt_required

app = Flask(__name__)


INVOICE_DIR = "invoices"
os.makedirs(INVOICE_DIR, exist_ok=True)


@app.route("/payment", methods=["POST"])

def payment():
    data = request.get_json()
    amount = data.get("amount")
    user_id = data.get("user_id")
    product_name = data.get("product_name")
    quantity=data.get("quantity")
    price=data.get("price_per_unit")
    

    if not all([amount, user_id, product_name]):
        return jsonify({"error": "Missing required fields"}), 400

    payment_status = "success" 
    transaction_id = "TXN_" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    invoice_filename = f"{transaction_id}.pdf"
    invoice_path = os.path.join(INVOICE_DIR, invoice_filename)

    c = canvas.Canvas(invoice_path, pagesize=A4)
    width, height = A4
    timestamp = datetime.utcnow().isoformat()

    c.setFont("Helvetica-Bold", 20)
    c.drawString(200, height - 50, "INVOICE")

  
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 100, f"Transaction ID: {transaction_id}")
    c.drawString(50, height - 120, f"User ID: {user_id}")
    c.drawString(50, height - 140, f"Product Name: {product_name}")
    c.drawString(50, height - 160, f"Quantity: {quantity}")
    c.drawString(50, height - 200, f"Total Amount: {amount:.2f}")
    c.drawString(50, height - 220, f"Payment Status: {payment_status}")
   
    c.drawString(50, height - 240, f"Date & Time: {timestamp}")

    c.showPage()
    c.save()


    response = {
        "transaction_id": transaction_id,
        "payment_status": payment_status,
        "amount": amount,
        "user_id": user_id,
        "product_name": product_name,
        "timestamp": timestamp
    }

    return jsonify(response), 200


if __name__ == "__main__":
    app.run(port=5002, debug=True)
