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


db = SQL('sqlite:///DB.db')


def orderbook_sync():
    """ Syncs orderbook DB """
    open_orders = db.execute("SELECT * FROM open_orders WHERE user_id = :user", user=session["user_id"])
    hidden_orderbook = db.execute("SELECT * FROM hidden_orderbook WHERE user_id = :user", user=session["user_id"])
    
    list = []
    for openorders in hidden_orderbook:
      list.append(openorders["order_id"])
      #here we get sum

    for order in open_orders:
      orderid = {order["order_id"]}

      if order["order_id"] in list:
        print(f"{orderid} already there")

      else:
        print(f"{orderid} not here, adding it")
        db.execute("INSERT INTO hidden_orderbook (pair,price,quantity_left,order_id,timeplaced,type, user_id) VALUES(?,?,?,?,?,?,?)", order["pair"], order["price"], order["quantity"]-order["filled"], order["order_id"],order["time"],order["type"], session["user_id"])
        #here we update sums if needed

    #we make dict with pair and price and quantity, 
    orderbook_dict = {"pair","price","quantity"}