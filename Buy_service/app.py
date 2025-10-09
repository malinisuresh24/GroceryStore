from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, get_jwt_identity, jwt_required
from models import db, Products, Purchases
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

jwt = JWTManager(app)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "super-secret-key") 

db.init_app(app)

with app.app_context():
    db.create_all()
    print("Tables created successfully!")


@app.route("/add_products", methods=["POST"])

@jwt_required()
def add_product():
    identity = get_jwt_identity()
    data = request.get_json()
    product_name = data.get("product_name")
    quantity = data.get("quantity")
    amount = data.get("amount")

    if not all([product_name, quantity, amount]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        new_product = Products(
            product_name=product_name,
            quantity=quantity,
            amount=amount
        )
        db.session.add(new_product)
        db.session.commit()
        return jsonify({"message": f"Product added successfully{ identity }", "product_id": new_product.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to add product: {str(e)}"}), 500

@app.route("/buy_products", methods=["POST"])
@jwt_required()
def buy_products():
    user_id = get_jwt_identity()
    data = request.get_json()
    product_name = data.get("product_name")
    quantity_requested = data.get("quantity")

    if not all([product_name, quantity_requested]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        
        product = Products.query.filter_by(product_name=product_name).with_for_update().first()
        if not product:
            return jsonify({"error": f"Product '{product_name}' not found"}), 404

        if product.quantity < quantity_requested:
            return jsonify({"error": f"Insufficient stock. Available quantity: {product.quantity}"}), 400

        price_per_unit = product.amount
        total_cost = quantity_requested * price_per_unit
        purchase_time = datetime.utcnow()

    
        new_purchase = Purchases(
            product_id=product.id,
            quantity=quantity_requested,
            amount=price_per_unit,
            total_cost=total_cost,
            purchased_on=purchase_time
        )
        db.session.add(new_purchase)

     
        product.quantity -= quantity_requested

        db.session.commit()

        return jsonify({
            "message": "Wholesale purchase recorded successfully",
            "user_id": user_id,
            "purchase_id": new_purchase.id,
            "product_name": product_name,
            "quantity": quantity_requested,
            "price_per_unit": price_per_unit,
            "total_cost": total_cost,
            "purchased_on": purchase_time.isoformat(),
            "remaining_stock": product.quantity
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to process purchase: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(port=5001, debug=True)
