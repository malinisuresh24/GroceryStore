from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Purchases(db.Model):
   
    __tablename__ = "purchases"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)  
    total_cost = db.Column(db.Float, nullable=False)
    purchased_on = db.Column(db.DateTime, default=datetime.utcnow)


class Sales(db.Model):
    __tablename__ = 'sales'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('purchases.id'), nullable=False)
    product_name=db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    sold_by = db.Column(db.Integer, nullable=False)  
    sold_at = db.Column(db.DateTime, default=datetime.utcnow)

    
    product = db.relationship('Purchases', backref=db.backref('sales', lazy=True))
