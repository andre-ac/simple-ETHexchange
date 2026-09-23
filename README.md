# simple-ETHexchange

A small ETH/USD exchange built for [CS50's final project](https://cs50.harvard.edu/x/2020/project/). It has account registration, a limit-order trading page, an order book, and order and trade history.

## Run locally

From the repository directory, create a virtual environment, install the dependencies, and start the Flask app:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000/`. The app uses the included `DB.db` SQLite file and opens it relative to the current working directory, so start it from the repository directory. The database contains application state; use a copy if you want to keep its current contents intact.

## What the demo does

- New accounts start with 10 ETH and 5,000 USD in simulated balances. Funding is not implemented.
- The trading interface submits ETH/USD limit orders. Prices must be positive multiples of 0.1 USD, and quantities must be positive multiples of 0.01 ETH. Orders cannot exceed the user's available balance.
- Users can cancel their own open orders. The order and trade history pages show past activity.
- Order submission and cancellation share an API limit of one request per second per client IP address.

This is a demo, not a production exchange. Orders can match against the same user's orders, and there is no slippage protection.
