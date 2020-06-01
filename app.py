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
app.config['SECRET_KEY'] = app.secret_key
FLASK_DEBUG=1

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd
app.jinja_env.filters["timeformater"] = timeformater

db = SQL('sqlite:///DB.db')

@app.route('/', methods=['GET'])
def home():
    return render_template("home.html")

@app.route("/trade")
@login_required
def trade():
    """Trading Interface"""
    return render_template("trade.html")

@app.route("/login", methods=["GET","POST"])
def login():
    """Login user"""
    if request.method == "POST":
        if not request.form.get("username"):
            return render_template("login.html",alert_error="must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html",alert_error="must provide username")
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password_hash"], request.form.get("password")):
            return render_template("login.html",alert_error="invalid username or password")

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
            return render_template("register.html",alert_error="must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("register.html",alert_error="must provide password")

        # Check if password and password confirmation match
        elif request.form.get("password")!=request.form.get("confirmation"):
            return render_template("register.html",alert_error="passwords must match")

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
            return render_template("register.html",alert_error="username already taken")
    else:
        return render_template("register.html")

@app.route('/api/sendorder', methods=['POST',"DELETE"])
@login_required
def sendorder():
    if request.method == "POST":
        new_order_id = str(uuid.uuid4())
        pair = request.form.get("pair")
        price = request.form.get("price")
        quantity = request.form.get("quantity")
        type = request.form.get("type")
        ordertype = request.form.get("ordertype")
        filled = 0
        time_requested = int(time.time())
        db.execute("INSERT INTO open_orders (order_id,user_id,pair,type,ordertype,price,quantity,filled,time) VALUES(?,?,?,?,?,?,?,?,?)", new_order_id, session["user_id"], pair, type, ordertype, price, quantity, filled, time_requested)
        return jsonify(result = "success", time = time_requested, pair = pair , price = price, quantity = quantity), 201
    
    elif request.method == "DELETE":
        orderid = request.form.get("order_id")
        db.execute("DELETE FROM open_orders WHERE order_id = :orderid", orderid = orderid)
        return jsonify("Deleted"), 200
    
    else:
        return 405

@app.route('/api/userinfo', methods=["GET"])
@login_required
def userinfo():
    if request.method == "GET":
        time_requested = time.time()
        basic_userinfo = db.execute("SELECT eth_balance,usd_balance,username FROM users WHERE user_id = :id", id= session["user_id"])[0]
        basic_userinfo.update(time = time_requested)
        return jsonify(basic_userinfo), 200
    else:
        return 405
        
@app.route('/api/orderhistory', methods=["GET"])
@login_required
def orderhistory():
    if request.method == "GET":
        time_requested = time.time()
        testreturn = db.execute("SELECT * FROM users")
        return jsonify(testreturn), 200
    else:
        return 405

@app.route('/api/tradehistory', methods=["GET"])
@login_required
def tradehistory():
    if request.method == "GET":
        time_requested = time.time()
        testreturn = db.execute("SELECT * FROM users")
        return jsonify(testreturn), 200
    else:
        return "error ", 405

@app.route('/api/openorders', methods=["GET"])
@login_required
def openorders():
    if request.method == "GET":
        time_requested = time.time()
        ordersopen = db.execute("SELECT order_id, pair, type, ordertype, price, quantity, filled, time FROM open_orders WHERE user_id = :user", user=session["user_id"])
        return jsonify(ordersopen, time_requested), 200
    else:
        return "error ", 405

if __name__ == "__main__":
    app.run(debug=False, use_reloader=False)