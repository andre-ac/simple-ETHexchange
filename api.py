import os
import sys
import uuid
import time
import datetime
import flask
import sqlite3

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helper import login_required, usd, timeformater
from engine import add_order_orderbook, del_order_orderbook, add_order_history
from app import app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQL('sqlite:///DB.db')

limiter = Limiter(
    app,
    key_func=get_remote_address
)

@app.route('/api/sendorder', methods=['POST', "DELETE"])
@login_required
@limiter.limit("1/second")
def sendorder():
    if request.method == "POST":
        new_order_id = str(uuid.uuid4())
        pair = request.form.get("pair")
        price = float(request.form.get("price"))
        quantity = float(request.form.get("quantity"))
        type = request.form.get("type")
        user_balances = db.execute(
            "SELECT available_eth_balance,available_usd_balance FROM users WHERE user_id = :id", id=session["user_id"])[0]
        ordertype = request.form.get("ordertype")
        filled = 0
        time_requested = int(time.time())
        if type == "S":
            if quantity >= float(user_balances["available_eth_balance"]):
                return jsonify(result="not enough balances", time=time_requested, pair=pair, price=price, quantity=quantity), 400
            else:
                pass 
        else:
            if (quantity*price) >= float(user_balances["available_usd_balance"]):
                return jsonify(result="not enough balances", time=time_requested, pair=pair, price=price, quantity=quantity), 400
            else:
                pass
        db.execute("INSERT INTO open_orders (order_id,user_id,pair,type,ordertype,price,quantity,filled,time) VALUES(?,?,?,?,?,?,?,?,?)",
                   new_order_id, session["user_id"], pair, type, ordertype, price, quantity, filled, time_requested)
        add_order_orderbook(new_order_id)
        return jsonify(result="success", time=time_requested, pair=pair, price=price, quantity=quantity), 201

    elif request.method == "DELETE":
        orderid = request.form.get("order_id")
        add_order_history(orderid,"CANCELLED")
        del_order_orderbook(orderid)
        db.execute(
            "DELETE FROM open_orders WHERE order_id = :orderid", orderid=orderid)
        return jsonify("Deleted"), 200

    else:
        return 405


@app.route('/api/userinfo', methods=["GET"])
@login_required
def userinfo():
    if request.method == "GET":
        time_requested = time.time()
        basic_userinfo = db.execute(
            "SELECT eth_balance,usd_balance,username FROM users WHERE user_id = :id", id=session["user_id"])[0]
        basic_userinfo.update(time=time_requested)
        return jsonify(basic_userinfo), 200
    else:
        return 405


@app.route('/api/orderhistory', methods=["GET"])
@login_required
def orderhistory():
    if request.method == "GET":
        orderhistory = db.execute(
            "SELECT * FROM order_history WHERE user_id = :id ORDER BY time DESC", id=session["user_id"])
        return jsonify(orderhistory), 200
    else:
        return 405


@app.route('/api/tradehistory', methods=["GET"])
def tradehistory():
    if request.method == "GET":
        tradehistory = db.execute("SELECT * FROM trade_history")
        return jsonify(tradehistory), 200
    else:
        return "error ", 405


@app.route('/api/openorders', methods=["GET"])
@login_required
def openorders():
    if request.method == "GET":
        time_requested = time.time()
        ordersopen = db.execute(
            "SELECT order_id, pair, type, ordertype, price, quantity, filled, time FROM open_orders WHERE user_id = :user", user=session["user_id"])
        return jsonify(ordersopen, time_requested), 200
    else:
        return "error ", 405


@app.route('/api/orderbook', methods=["GET"])
def orderbook():
    if request.method == "GET":
        orderbook = db.execute("SELECT * FROM orderbook")
        return jsonify(orderbook), 200
    else:
        return "error ", 405
