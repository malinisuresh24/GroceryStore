from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify
import requests
import os
from flask_sqlalchemy import SQLAlchemy 
from dotenv import load_dotenv
from models import db,User
import redis
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from bcrypt import hashpw, gensalt

app=Flask(__name__)

load_dotenv()


app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True


db.init_app(app)


with app.app_context():
    db.create_all()
    print("Tables created successfully!")
"""REDIS"""
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    STREAM_KEY = "login_stream"

except Exception as e:
    print(f" Redis connection failed: {e}")
    exit(1)
""""""

@app.route('/register',methods=['POST'])
def add_user():
     username=request.json['username']
     email=request.json['email']
     password=request.json['password']
     if not username or not password:
        
        return jsonify({'error': 'Username and password required'}), 400
     
     hashed_password = hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')
     ser=User(username=username,email=email,password=hashed_password)
     db.session.add(ser)
     db.session.commit()
     return jsonify({"message":"user added successfully"})

@app.route('/login',methods=['POST'])
def user_login():
     username=request.json['username']
     password=request.json['password']
     if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
     user=User.query.filter_by(username=username).first()
     if user:
        try:
            timestamp_plus_1hr = datetime.now(timezone.utc) + timedelta(hours=1)

            r.xadd(STREAM_KEY, {
    "user_id": str(user.id),
    "status": "success",
    "timestamp": timestamp_plus_1hr.isoformat()
})
        except Exception as e:
            return jsonify({"message": f"Redis error: {str(e)}"}), 500

        return jsonify({"message": "Login successful", "user_id": user.id}), 200
     else:
        return jsonify({"message": "Invalid credentials"}), 401


if __name__=='__main__':
     app.run(host='0.0.0.0',port='5000',debug=True)

