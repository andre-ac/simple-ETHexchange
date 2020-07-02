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


app = flask.Flask(__name__)
from views import *
from api import *


app.secret_key = os.urandom(24)
app.config['SECRET_KEY'] = app.secret_key
FLASK_DEBUG = 1

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filters
app.jinja_env.filters["usd"] = usd
app.jinja_env.filters["timeformater"] = timeformater

db = SQL('sqlite:///DB.db')

if __name__ == "__main__":
    app.run(debug=False, use_reloader=False)
