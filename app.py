from flask import Flask, render_template, session, redirect
from functools import wraps
import pymongo
import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
app.secret_key = b'\xcc^\x91\xea\x17-\xd0W\x03\xa7\xf8J0\xac8\xc5'

# Database
remote_mongo_uri = os.getenv('MONGO_URI', 'mongodb+srv://mohamedsamir170569:Kw9pAkJNqCzTZdF@cluster0.ua2dr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
client = pymongo.MongoClient(remote_mongo_uri)
db = client.website

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
from user import routes

@app.route('/')
def home():
    return "Welcome to home page"

@app.route('/dashboard/')
@login_required
def dashboard():
    return "Welcome to dashboard"

if __name__ == '__main__':
    app.run(debug=True)