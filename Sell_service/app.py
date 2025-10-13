import csv
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from models import db, Purchases,Sales
from datetime import datetime
import requests
import os
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

def generate_invoice_pdf(invoice_data, filename="invoice.pdf"):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "INVOICE")

    c.setFont("Helvetica", 12)
    y = height - 100
    for key, value in invoice_data.items():
        c.drawString(50, y, f"{key}: {value}")
        y -= 20

    c.drawString(50, y - 20, "Thank you for your purchase!")
    c.save()

load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "super-secret-key")

db.init_app(app)
jwt = JWTManager(app)

with app.app_context():
    db.create_all()
    print("Tables initialized!")

@app.route("/all_products", methods=["GET"])
@jwt_required()
def all_products():
    try:
        products = Purchases.query.all()
        product_list = []

        for product in products:
            product_list.append({
                "product_id": product.id,
                "product_name": product.product_name,
                "quantity": product.quantity,
                "price_per_unit": product.amount,
                
            })

        if not product_list:
            return jsonify({"message": "No products found in the database"}), 200

        return jsonify({"products": product_list}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/sell_product", methods=["POST"])
@jwt_required()
def sell_product():
    user_id = get_jwt_identity()
    data = request.get_json()
    product_name = data.get("product_name")
    quantity = int(data.get("quantity", 1))

    if not all([product_name, quantity]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        
        product = Purchases.query.filter_by(product_name=product_name).first()
        if not product:
            return jsonify({"error": f"Product '{product_name}' not found"}), 404

      
        total_bought = db.session.query(db.func.sum(Purchases.quantity))\
            .filter_by(product_name=product_name).scalar() or 0

        total_sold = db.session.query(db.func.sum(Sales.quantity))\
            .filter_by(product_name=product_name).scalar() or 0

        remaining_qty = total_bought - total_sold
        print(remaining_qty)
        if quantity > remaining_qty:
            return jsonify({"error": f"Only {remaining_qty} units available"}), 400

        price_per_unit = product.amount
        total_cost = quantity * price_per_unit
        sale_time = datetime.utcnow()

        
        payment_payload = {
            "amount": total_cost,
            "user_id": user_id,
            "product_name": product_name,
            "quantity": quantity,
            "price": price_per_unit
        }

        try:
            payment_response = requests.post("http://localhost:5002/payment", json=payment_payload, timeout=5)
            payment_data = payment_response.json()
        except Exception as e:
            return jsonify({"error": f"Payment service unavailable: {str(e)}"}), 503

        if payment_data.get("payment_status") != "success":
            return jsonify({"error": "Payment failed", "payment_data": payment_data}), 402

       
        new_sale = Sales(
            product_id=product.id,
            product_name=product_name,
            quantity=quantity,
            sold_by=user_id,
            sold_at=sale_time
        )
        db.session.add(new_sale)
        db.session.commit()

       
        csv_file = "sales_log.csv"
        file_exists = os.path.isfile(csv_file)

        with open(csv_file, mode="a", newline="") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow([
                    "Transaction ID", "User ID", "Product Name", "Quantity",
                    "Price per Unit", "Total Cost", "Payment Status", "Sale Time"
                ])
            writer.writerow([
                payment_data.get("transaction_id"),
                user_id,
                product_name,
                quantity,
                price_per_unit,
                total_cost,
                payment_data.get("payment_status"),
                sale_time
            ])
        invoice_data = {
    "Invoice ID": "INV-000123",
    "Transaction ID": "TXN-456789",
    "User ID": 101,
    "Product Name": "Wireless Mouse",
    "Quantity": 2,
    "Price per Unit": "₹500",
    "Total Cost": "₹1000",
    "Payment Status": "Success",
    "Sold At": datetime.utcnow().isoformat(),
    "Seller": "TechMart Pvt Ltd"
}
        generate_invoice_pdf(invoice_data)
        return jsonify({
            "message": "Sale recorded successfully",
            "user_id": user_id,
            "sale_id": new_sale.id,
            "product_name": product_name,
            "quantity": quantity,
            "price_per_unit": price_per_unit,
            "total_cost": total_cost,
            "sold_at": sale_time.isoformat(),
            "remaining_stock": remaining_qty - quantity
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to process sale: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(port=5003, debug=True)