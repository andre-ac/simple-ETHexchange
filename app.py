import os
import sys
import uuid
import time,datetime
import flask
import sqlite3

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helper import login_required, usd, timeformater


app = flask.Flask(__name__)
app.secret_key = os.urandom(24)
FLASK_DEBUG=1

db = SQL('sqlite:///DB.db')

@app.route('/', methods=['GET'])
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET","POST"])
def login():
    """Login user"""
    if request.method == "POST":
        if not request.form.get("username"):
            return render_template("login.html",error="must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html",error="must provide username")
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password_hash"], request.form.get("password")):
            return render_template("login.html",error="invalid username or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]
        session['logged_in'] = True

        # Redirect user to home page
        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register new user"""
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("register.html",error="must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("register.html",error="must provide password")

        # Check if password and password confirmation match
        elif request.form.get("password")!=request.form.get("confirmation"):
            return render_template("register.html",error="passwords must match")

        # get number of users with same username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        
        # assign username id based on number of rows (users) + 1 
        fresh_username_id = len(db.execute("SELECT * FROM users"))+1

        # ensures username doesn't exist
        if len(rows)==0:
            #inserts
            db.execute("INSERT INTO users (user_id,username,password_hash) VALUES(?,?,?)", fresh_username_id, request.form.get("username"), generate_password_hash(request.form.get("password")))
            session["user_id"] = fresh_username_id
            session['logged_in'] = True
            return redirect("/")
        else:
            return render_template("register.html",error="username already taken")
    else:
        return render_template("register.html")

@app.route('/ap/itest', methods=['GET'])
def api():
    test = time.time()
    testreturn = [{'time':test,'name':'Andre'}, {'time':test,'name':'Tobias'}]
    return jsonify(testreturn)

if __name__ == "__main__":
    app.run(debug=False, use_reloader=False)