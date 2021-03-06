import os
import requests
import urllib.parse
import time
import datetime


from flask import redirect, render_template, request, session
from functools import wraps


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login"), 403
        return f(*args, **kwargs)

    return decorated_function


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"


def timeformater(time):
    """Turn unix time to date format"""
    return datetime.datetime.utcfromtimestamp(time)
