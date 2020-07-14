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


db = SQL('sqlite:///DB.db')


def add_order_orderbook(new_order_id):
    """ Adds order to both orderbooks (hidden and visible) """

    order = db.execute("SELECT * FROM open_orders WHERE user_id = :user AND order_id = :order_id",
                       user=session["user_id"], order_id=new_order_id)[0]

    # check if order was fully executed
    if try_execution(order) == True:
        print("match1")
    else:
        updated_order = db.execute("SELECT * FROM open_orders WHERE user_id = :user AND order_id = :order_id",
                                   user=session["user_id"], order_id=new_order_id)[0]

        orderbook_for_price = db.execute(
            "SELECT * FROM orderbook WHERE price = :price", price=order["price"])

        # if there are no order at that price
        if len(orderbook_for_price) == 0:
            db.execute("INSERT INTO orderbook (pair,price,quantity,type) VALUES (?,?,?,?)", updated_order["pair"], updated_order["price"], round(
                updated_order["quantity"]-updated_order["filled"], 2), order["type"])

        elif len(orderbook_for_price) == 1:

            if orderbook_for_price[0]["type"] == order["type"]:
                db.execute("UPDATE orderbook SET quantity = :quantity WHERE pair = :pair AND price = :price AND type = :type", quantity=round(
                    updated_order["quantity"]+orderbook_for_price[0]["quantity"]-updated_order["filled"], 2), pair=order["pair"], price=order["price"], type=order["type"])
            else:
                print(order["order_id"] + " MATCHED - ERROR 700")
                db.execute("DELETE FROM orderbook WHERE price =:price",
                           price=order["price"])
                #db.execute("INSERT INTO orderbook (pair,price,quantity,type) VALUES (?,?,?,?)", updated_order["pair"], updated_order["price"], round(updated_order["quantity"]-updated_order["filled"],2), order["type"])
                # if the price is the same and type is different then it means that someone is buying/selling for our desired price


def try_execution(order):
    """ Checks and executes order if applicable """
    db.execute("INSERT INTO hidden_orderbook (pair,price,quantity_left,order_id,timeplaced,type, user_id) VALUES(?,?,?,?,?,?,?)",
               order["pair"], order["price"], round(order["quantity"]-order["filled"], 2), order["order_id"], order["time"], order["type"], session["user_id"])

    if order["type"] == "S":
        matching_side = db.execute(
            "SELECT * FROM hidden_orderbook WHERE pair=:pair AND type=:type ORDER BY price DESC, timeplaced DESC", pair=order["pair"], type="B")

        if len(matching_side) == 0:
            return False

        # check if order price is under market price
        if matching_side[0]["price"] >= order["price"]:

            # Order should execute right away
            print("sell order would execute")
            order_quantity_left = order["quantity"]-order["filled"]

            for buy_order in matching_side:

                # check if order should execute
                if buy_order["price"] >= order["price"]:

                    # if the quantity of the buy order is enough to fill the new order
                    if buy_order["quantity_left"] >= order_quantity_left:
                        #buy order is enough to cover the sell order

                        print(f"sell order : was enough {order}")
                        orderbook_for_price = db.execute(
                            "SELECT * FROM orderbook WHERE price=:price", price=buy_order["price"])[0]

                        if buy_order["quantity_left"] == order_quantity_left:
                            #buy order has the exact same vol as sell order size needed

                            add_order_history(buy_order["order_id"],"EXECUTED", buy_order["price"])
                            add_order_history(order["order_id"],"EXECUTED", buy_order["price"])

                            db.execute(
                                "DELETE FROM open_orders WHERE order_id = :orderid", orderid=buy_order["order_id"])
                            db.execute(
                                "DELETE FROM hidden_orderbook WHERE order_id = :orderid", orderid=buy_order["order_id"])

                            if orderbook_for_price["quantity"] == buy_order["quantity_left"]:
                                #the buy order the only order in the price level in public orderbook

                                db.execute("DELETE FROM orderbook WHERE price=:price AND pair=:pair",
                                           price=orderbook_for_price["price"], pair=buy_order["pair"])
                        else:
                            #buy order is bigger than the sell order

                            add_order_history(order["order_id"],"EXECUTED",buy_order["price"])

                            db.execute("UPDATE hidden_orderbook SET quantity_left = :quantity WHERE order_id = :order_id", quantity=round(
                                buy_order["quantity_left"]-order_quantity_left, 2), order_id=buy_order["order_id"])
                            buy_order_openorders = db.execute(
                                "SELECT * FROM open_orders WHERE order_id = :orderid", orderid=buy_order["order_id"])[0]
                            db.execute("UPDATE open_orders SET filled = :filled WHERE order_id = :order_id", filled=round(
                                buy_order_openorders["filled"]+order_quantity_left, 2), order_id=buy_order["order_id"])

                            db.execute("UPDATE orderbook SET quantity=:quantity WHERE price=:price", quantity=round(
                                orderbook_for_price["quantity"]-order_quantity_left, 2), price=buy_order["price"])

                        db.execute(
                            "DELETE FROM open_orders WHERE order_id = :orderid", orderid=order["order_id"])
                        db.execute(
                            "DELETE FROM hidden_orderbook WHERE order_id = :orderid", orderid=order["order_id"])

                        # if it got here, buy order in the book was enough to cover the sell order
                        db.execute("INSERT INTO trade_history (trade_id,pair,price,quantity,taker_order,maker_order,time) VALUES (?,?,?,?,?,?,?)",
                                   str(uuid.uuid4()), "ETHUSD", buy_order["price"], order_quantity_left, order["order_id"], buy_order["order_id"], int(time.time()))

                        order_quantity_left = 0

                        return True

                    else:
                        print("sell order : wasn't enough")
                        #buy order wasn't enough
                        add_order_history(buy_order["order_id"],"EXECUTED", buy_order["price"])

                        db.execute(
                            "DELETE FROM hidden_orderbook WHERE order_id = :orderid", orderid=buy_order["order_id"])
                        db.execute(
                            "DELETE FROM open_orders WHERE order_id = :orderid", orderid=buy_order["order_id"])

                        orderbook_for_price = db.execute(
                            "SELECT * FROM orderbook WHERE price=:price", price=buy_order["price"])[0]

                        if orderbook_for_price["quantity"] == buy_order["quantity_left"]:
                            #the buy order the only order in the price level in public orderbook 

                            db.execute(
                                "DELETE FROM orderbook WHERE price=:price", price=buy_order["price"])
                        else:
                            db.execute("UPDATE orderbook SET quantity=:quantity WHERE price=:price", quantity=round(
                                orderbook_for_price["quantity"]-buy_order["quantity_left"], 2), price=buy_order["price"])

                        order_openorders = db.execute(
                            "SELECT * FROM open_orders WHERE order_id = :orderid", orderid=order["order_id"])[0]
                        db.execute("UPDATE open_orders SET filled = :filled WHERE order_id = :order_id", filled=round(
                            order_openorders["filled"]+buy_order["quantity_left"], 2), order_id=order["order_id"])
                        order_quantity_left = round(
                            order_openorders["quantity"]-order_openorders["filled"]-buy_order["quantity_left"], 2)
                        db.execute("UPDATE hidden_orderbook SET quantity_left = :quantity WHERE order_id = :order_id",
                                   quantity=order_quantity_left, order_id=order["order_id"])
                                   
                        db.execute("INSERT INTO trade_history (trade_id,pair,price,quantity,taker_order,maker_order,time) VALUES (?,?,?,?,?,?,?)",
                                   str(uuid.uuid4()), "ETHUSD", buy_order["price"], buy_order["quantity_left"], order["order_id"], buy_order["order_id"], int(time.time()))

                # if the
                else:

                    return False

            if order_quantity_left > 0:

                print(
                    "sell order : orders in the orderbook weren't enough to completely fill")
                return False

        else:
            return False

    else:
        matching_side = db.execute(
            "SELECT * FROM hidden_orderbook WHERE pair=:pair AND type=:type ORDER BY price ASC, timeplaced DESC", pair=order["pair"], type="S")

        if len(matching_side) == 0:
            return False

        # check if order price is under market price
        if matching_side[0]["price"] <= order["price"]:

            # Order should execute right away
            print("buy order would execute")
            order_quantity_left = order["quantity"]-order["filled"]

            for sell_order in matching_side:

                # check if order should execute
                if sell_order["price"] <= order["price"]:

                    # if the quantity of the buy order is enough to fill the new order
                    if sell_order["quantity_left"] >= order_quantity_left:
                        print(f"buy order : was enough {order}")
                        

                        orderbook_for_price = db.execute(
                            "SELECT * FROM orderbook WHERE price=:price AND pair=:pair", price=sell_order["price"], pair=sell_order["pair"])[0]

                        if sell_order["quantity_left"] == order_quantity_left:
                            #sell order has the exact same vol as buy order size needed

                            add_order_history(sell_order["order_id"],"EXECUTED",sell_order["price"])
                            add_order_history(order["order_id"],"EXECUTED",sell_order["price"])

                            db.execute(
                                "DELETE FROM open_orders WHERE order_id = :orderid", orderid=sell_order["order_id"])
                            db.execute(
                                "DELETE FROM hidden_orderbook WHERE order_id = :orderid", orderid=sell_order["order_id"])

                            if orderbook_for_price["quantity"] == sell_order["quantity_left"]:
                                db.execute("DELETE FROM orderbook WHERE price=:price AND pair=:pair",
                                           price=orderbook_for_price["price"], pair=sell_order["pair"])

                        else:

                            add_order_history(order["order_id"],"EXECUTED", sell_order["price"])

                            db.execute("UPDATE hidden_orderbook SET quantity_left = :quantity WHERE order_id = :order_id", quantity=round(
                                sell_order["quantity_left"]-order_quantity_left, 2), order_id=sell_order["order_id"])
                            sell_order_openorders = db.execute(
                                "SELECT * FROM open_orders WHERE order_id = :orderid", orderid=sell_order["order_id"])[0]
                            db.execute("UPDATE open_orders SET filled = :filled WHERE order_id = :order_id", filled=round(
                                sell_order_openorders["filled"]+order_quantity_left, 2), order_id=sell_order["order_id"])

                            db.execute("UPDATE orderbook SET quantity=:quantity WHERE price=:price", quantity=round(
                                orderbook_for_price["quantity"]-sell_order["quantity_left"], 2), price=sell_order["price"])

                        db.execute(
                            "DELETE FROM open_orders WHERE order_id = :orderid", orderid=order["order_id"])
                        db.execute(
                            "DELETE FROM hidden_orderbook WHERE order_id = :orderid", orderid=order["order_id"])

                        db.execute("INSERT INTO trade_history (trade_id,pair,price,quantity,taker_order,maker_order,time) VALUES (?,?,?,?,?,?,?)",
                                   str(uuid.uuid4()), "ETHUSD", sell_order["price"], order_quantity_left, order["order_id"], sell_order["order_id"], int(time.time()))

                        order_quantity_left = 0

                        return True

                    else:
                        print("buy order : Wasn't enough")

                        add_order_history(sell_order["order_id"],"EXECUTED",sell_order["price"])

                        db.execute(
                            "DELETE FROM hidden_orderbook WHERE order_id = :orderid", orderid=sell_order["order_id"])
                        db.execute(
                            "DELETE FROM open_orders WHERE order_id = :orderid", orderid=sell_order["order_id"])

                        orderbook_for_price = db.execute(
                            "SELECT * FROM orderbook WHERE price=:price", price=sell_order["price"])[0]

                        if orderbook_for_price["quantity"] == round(sell_order["quantity_left"], 2):
                            db.execute("DELETE FROM orderbook WHERE price=:price and pair=:pair",
                                       price=sell_order["price"], pair=sell_order["pair"])
                        else:
                            db.execute("UPDATE orderbook SET quantity=:quantity WHERE price=:price", quantity=round(
                                orderbook_for_price["quantity"]-sell_order["quantity_left"], 2), price=sell_order["price"])

                        order_openorders = db.execute(
                            "SELECT * FROM open_orders WHERE order_id = :orderid", orderid=order["order_id"])[0]
                        db.execute("UPDATE open_orders SET filled = :filled WHERE order_id = :order_id", filled=round(
                            order_openorders["filled"]+sell_order["quantity_left"], 2), order_id=order["order_id"])
                        order_quantity_left = round(
                            order_openorders["quantity"]-order_openorders["filled"]-sell_order["quantity_left"], 2)
                        db.execute("UPDATE hidden_orderbook SET quantity_left = :quantity WHERE order_id = :order_id",
                                   quantity=order_quantity_left, order_id=order["order_id"])
                        db.execute("INSERT INTO trade_history (trade_id,pair,price,quantity,taker_order,maker_order,time) VALUES (?,?,?,?,?,?,?)",
                                   str(uuid.uuid4()), "ETHUSD", sell_order["price"], round(sell_order["quantity_left"],2), order["order_id"], sell_order["order_id"], int(time.time()))

                # if the
                else:
                    "buy order : partially filled, but not fully"
                    return False

            if order_quantity_left > 0:

                print(
                    "buy order : Orders in the orderbook weren't enough to completely fill")
                return False

        else:
            return False


def add_order_history(order_id,order_status,*price):
    """Adds order to order history, only call this when the order is either fully executed or cancelled"""
    #order_status should be either EXECUTED or CANCELLED
         
    #check if already in order history
    history_of_order = db.execute(
        "SELECT * FROM order_history WHERE order_id = :order_id", order_id=order_id)
    
    if len(history_of_order)==1:
        print("Order already in order history")
        return True
    
    elif len(history_of_order)==0:
        order_details = db.execute(
                            "SELECT * FROM open_orders WHERE order_id = :order_id", order_id=order_id)[0]
        #get prices from trade history and divide by sum, if order was maker then it's the order price if it was taker then it is the execution price
        order_executions = db.execute(
                            "SELECT * FROM trade_history WHERE taker_order = :order_id OR maker_order = :order_id", order_id= order_id)
        #if there are no executions then order avg price is 0
        

        if order_status=="CANCELLED":
            #if status is cancelled 
            sum_cost=0
            for execution in order_executions:
                sum_cost = sum_cost + float(execution["quantity"]*execution["price"])

            avg_price=sum_cost/order_details["filled"]

            db.execute("INSERT INTO order_history (order_id,user_id,pair,type,ordertype,price,avg_price,quantity_filled,time,status) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        order_id,session["user_id"],order_details["pair"],order_details["type"],order_details["ordertype"],order_details["price"],avg_price,order_details["filled"],int(time.time()),"CANCELLED")
            return False

        elif order_status=="EXECUTED":
            price=price[0]

            if len(order_executions)==0:
                avg_price=float(price)

            else:
                sum_cost=float(price)*(float((order_details["quantity"])-float(order_details["filled"])))
                
                for execution in order_executions:
                    sum_cost = sum_cost + float(execution["quantity"]*execution["price"])

                avg_price=sum_cost/order_details["quantity"]

            db.execute("INSERT INTO order_history (order_id,user_id,pair,type,ordertype,price,avg_price,quantity_filled,time,status) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        order_id,session["user_id"],order_details["pair"],order_details["type"],order_details["ordertype"],order_details["price"],avg_price,order_details["quantity"],int(time.time()),"EXECUTED")
            return False

        else:
            print("ERROR order_status not found")
            return 0


def del_order_orderbook(order_id):
    """ Deletes order to both orderbooks (hidden and visible) """

    order = db.execute(
        "SELECT * FROM open_orders WHERE order_id = :order_id", order_id=order_id)[0]
    db.execute(
        "DELETE FROM hidden_orderbook WHERE order_id = :order_id", order_id=order_id)

    orderbook_for_price = db.execute(
        "SELECT * FROM orderbook WHERE price = :price AND type= :type", price=order["price"], type=order["type"])[0]
    quantity_left = order["quantity"]-order["filled"]

    if quantity_left < orderbook_for_price["quantity"]:
        db.execute("UPDATE orderbook SET quantity = :quantity WHERE pair = :pair AND price = :price AND type = :type",
                   quantity=orderbook_for_price["quantity"]-quantity_left, pair=order["pair"], price=order["price"], type=order["type"])
    else:
        db.execute("DELETE FROM orderbook WHERE price=:price",
                   price=order["price"])


def orderbook_sync():
    """ Syncs both orderbook DB with all user's open orders.
        This uses a considerable amount of resources use wisely"""

    open_orders = db.execute("SELECT * FROM open_orders")
    hidden_orderbook = db.execute("SELECT * FROM hidden_orderbook")

    db.execute("DELETE FROM orderbook")
    # pass to orderbook

    list_order_ids_on_hidden = []
    list_order_ids_on_openorder = []

    # get order ids available in the hidden orderbook before sync
    for openorders in hidden_orderbook:
        list_order_ids_on_hidden.append(openorders["order_id"])

    print(open_orders)
    # check if all open orders and if the quantities left are correct in the hidden orderbook
    for order in open_orders:
        orderid = order["order_id"]

        # get order ids available in the hidden orderbook before sync
        list_order_ids_on_openorder.append(orderid)
        quantity_left = round(order["quantity"]-order["filled"], 2)

        if orderid in list_order_ids_on_hidden:
            print(f"{orderid} already there")

        else:
            print(f"{orderid} not here, adding it")
            print("Here is " + str(quantity_left))
            db.execute("INSERT INTO hidden_orderbook (pair,price,quantity_left,order_id,timeplaced,type, user_id) VALUES(?,?,?,?,?,?,?)",
                       order["pair"], order["price"], quantity_left, order["order_id"], order["time"], order["type"], order["user_id"])

        hidden_order = db.execute(
            "SELECT * FROM hidden_orderbook WHERE order_id = :orderid", orderid=orderid)[0]

        if quantity_left != hidden_order["quantity_left"]:
            print("Here is " + str(quantity_left))
            db.execute("UPDATE hidden_orderbook SET quantity_left = :quantity WHERE order_id = :orderid",
                       quantity=quantity_left, orderid=orderid)
            print(f"{orderid} had wrong quantity in hidden, updated")
        else:
            print(f"{orderid} quantity was correct")

    # check if all orders in hidden are also in openorders
    for order in hidden_orderbook:
        orderid = order["order_id"]

        if orderid in list_order_ids_on_openorder:
            print(f"{orderid} is in hidden and openorder, good")
        else:
            print(f"{orderid} was in hidden but not in open, deleted from hidden")
            db.execute(
                "DELETE FROM hidden_orderbook WHERE order_id = :orderid", orderid=orderid)

    # add to orderbook
    list_prices_already_on_orderbook = []
    for order in open_orders:

        if order["price"] in list_prices_already_on_orderbook:
            quantity_left = order["quantity"]-order["filled"]
            query = db.execute(
                "SELECT * FROM orderbook WHERE price = :price", price=order["price"])[0]
            db.execute("UPDATE orderbook SET quantity= :quantity WHERE price=:price AND type = :type AND pair = :pair", quantity=round(
                query["quantity"]+quantity_left, 2), price=order["price"], type=order["type"], pair=order["pair"])

        else:
            db.execute("INSERT INTO orderbook (pair,price,quantity,type) VALUES(?,?,?,?)",
                       order["pair"], order["price"], round(order["quantity"]-order["filled"], 2), order["type"])
            list_prices_already_on_orderbook.append(order["price"])
            print(str(order["price"]) + " added to orderbook")


if __name__ == "__main__":
    start_time = time.time()
    orderbook_sync()
    print("Orderbook Synced in " +
          str(round((time.time() - start_time)*100, 2)) + " ms")