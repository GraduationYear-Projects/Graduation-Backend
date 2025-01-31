from flask import Flask
from app import app
from user.models import User


@app.route('/signup/', methods=['POST'])
def signup():
  return User().signup()

@app.route('/signout/')
def signout():
  return User().signout()

@app.route('/login/', methods=['POST'])
def login():
  return User().login()