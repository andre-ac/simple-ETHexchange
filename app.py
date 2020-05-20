import os
import sys
import uuid
import time,datetime
import flask

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helper import login_required, usd, timeformater


app = flask.Flask(__name__)
FLASK_DEBUG=1


@app.route('/', methods=['GET'])
def home():
    return render_template("home.html")

@app.route('/ap/itest', methods=['GET'])
def api():
    test = time.time()
    testreturn = [{'time':test,'name':'Andre'}, {'time':test,'name':'Tobias'}]
    return jsonify(testreturn)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)