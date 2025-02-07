from flask import Flask, render_template, session, redirect
from functools import wraps
from pymongo import MongoClient

# Create Flask app
app = Flask(__name__)
app.secret_key = b'\xcc^\x91\xea\x17-\xd0W\x03\xa7\xf8J0\xac8\xc5'

# Setup MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["Cluster1"]

# Decorators
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect('/')
    return wrap

# Routes
@app.route('/')
def home():
    return "Welcome to home page"

@app.route('/dashboard/')
@login_required
def dashboard():
    return "Welcome to dashboard"

# Register blueprints
from user.routes import user_bp
from product.routes import product_bp

app.register_blueprint(user_bp)
app.register_blueprint(product_bp)

if __name__ == '__main__':
    app.run(debug=True)