from flask_sqlalchemy import SQLAlchemy 

db=SQLAlchemy()

class User(db.Model):
     __tablename__='customer'
     id=db.Column(db.Integer,primary_key=True)
     username=db.Column(db.String(50),unique=True,nullable=False)
     email=db.Column(db.String(50),nullable=False)
     password=db.Column(db.String(500),nullable=False)