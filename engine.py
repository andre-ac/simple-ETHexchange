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

def add_order_orderbook(new_order_id):
  """ Adds order to both orderbooks (hidden and visible) """

  order = db.execute("SELECT * FROM open_orders WHERE user_id = :user AND order_id = :order_id", user=session["user_id"], order_id = new_order_id)[0]
  db.execute("INSERT INTO hidden_orderbook (pair,price,quantity_left,order_id,timeplaced,type, user_id) VALUES(?,?,?,?,?,?,?)", order["pair"], order["price"], order["quantity"]-order["filled"], order["order_id"],order["time"],order["type"], session["user_id"])

  orderbook_for_price = db.execute("SELECT * FROM orderbook WHERE price = :price", price=order["price"])

  # if there are no order at that price
  if len(orderbook_for_price) == 0:
    db.execute("INSERT INTO orderbook (pair,price,quantity,type) VALUES (?,?,?,?)", order["pair"], order["price"], order["quantity"], order["type"])
  
  elif len(orderbook_for_price) == 1:

    if orderbook_for_price[0]["type"] == order["type"]:
      db.execute("UPDATE orderbook SET quantity = :quantity WHERE pair = :pair AND price = :price AND type = :type", quantity = order["quantity"]+orderbook_for_price[0]["quantity"], pair = order["pair"], price = order["price"], type = order["type"] )
    else:
      print(order["order_id"] + " MATCHED")
      # if the price is the same and type is different then it means that someone is buying/selling for our desired price

def del_order_orderbook(order_id):
  """ Deletes order to both orderbooks (hidden and visible) """

  order = db.execute("SELECT * FROM open_orders WHERE order_id = :order_id", order_id = order_id)[0]
  db.execute("DELETE FROM hidden_orderbook WHERE order_id = :order_id", order_id = order_id )

  orderbook_for_price = db.execute("SELECT * FROM orderbook WHERE price = :price AND type= :type", price=order["price"], type=order["type"])[0]
  quantity_left = order["quantity"]-order["filled"]
  
  if quantity_left < orderbook_for_price["quantity"]:
    db.execute("UPDATE orderbook SET quantity = :quantity WHERE pair = :pair AND price = :price AND type = :type", quantity = orderbook_for_price["quantity"]-quantity_left, pair = order["pair"], price = order["price"], type = order["type"] )
  else:
    db.execute("DELETE FROM orderbook WHERE price=:price", price=order["price"])



def orderbook_sync():
    """ Syncs both orderbook DB with all user's open orders"""

    open_orders = db.execute("SELECT * FROM open_orders")
    hidden_orderbook = db.execute("SELECT * FROM hidden_orderbook")
    
    #db.execute("DELETE FROM orderbook") 

    #pass to orderbook

    list_order_ids = []
    list_prices = []

    for openorders in hidden_orderbook:
      list_order_ids.append(openorders["order_id"])

    for order in open_orders:
      orderid = order["order_id"]

      if order["order_id"] in list_order_ids:
        print(f"{orderid} already there")

      else:
        print(f"{orderid} not here, adding it")
        db.execute("INSERT INTO hidden_orderbook (pair,price,quantity_left,order_id,timeplaced,type, user_id) VALUES(?,?,?,?,?,?,?)", order["pair"], order["price"], order["quantity"]-order["filled"], order["order_id"],order["time"],order["type"], order["user_id"])
    
    for openorders in hidden_orderbook:
      list_order_ids.append(openorders["order_id"])

      if openorders["price"] in list_prices:
        pass
      else:
        list_prices.append(openorders["price"])

    print(list_prices)


if __name__ == "__main__":
    orderbook_sync()
    print("Orderbook Synced")