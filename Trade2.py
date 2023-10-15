import requests
import datetime
import time
import math
from Tools.Exchange.Crypto.Kraken import UserInterface

CRYPTO_STICKER = "BTC"
BASE_STICKER = "CAD"
JOINED_STICKER = "XXBTZCAD"

START = time.time()
BUY_SELL_ARC_MAX = 20.0  # ARC is average rate of change, used in decide() function
BUY_SELL_ARC_MIN = -10.0
UPDATE_HISTORY = 1  # minutes between each historical OHLC update
HISTORY_LENGTH = 0.25  # hours to search into the past
USE_HISTORICAL_MIN = [15, 10, 5, 2, 1]
USE_HISTORICAL_SEC = [45, 30, 10, 5, 3]

UI = UserInterface.UI(CRYPTO_STICKER, BASE_STICKER, START, HISTORY_LENGTH)


def get_price():
    resp = requests.get('https://api.kraken.com/0/public/Ticker?pair=' + CRYPTO_STICKER + BASE_STICKER)
    json = resp.json()

    if not json["error"]:
        price = json["result"][JOINED_STICKER]["a"][0]  # change this if using different currency
        return float(price)
    else:
        raise Exception(json["error"])


def decide(price, prev_price):
    price = int(price)
    prev_price = int(prev_price)
    if price > prev_price:
        return "BUY"
    elif price < prev_price:
        return "SELL"
    return "WAIT"


def buy(price, amount, money, crypto):
    if money > amount:
        money -= amount
        crypto += amount / price
    else:
        crypto += money / price
        money = 0

    return money, crypto


def sell(price, amount, money, crypto):

    if crypto >= amount:
        crypto -= amount
        money += amount * price
    else:
        money += crypto * price
        crypto = 0

    return money, crypto


def main():
    money = 100
    crypto = 0
    prev_price = get_price()

    run = True
    while run:
        # time.sleep(0.5)
        # delay to make sure we don't overload the api

        price = get_price()
        decision = decide(price, prev_price)
        prev_price = price

        if decision == "BUY":
            money, crypto = buy(price, money, money, crypto)
        if decision == "SELL":
            money, crypto = sell(price, crypto, money, crypto)

        theoretical = money + (crypto * price)

        UI.update(money, crypto, theoretical, price, decision, 0)
        # print(UI.price_graph.data_)


if __name__ == "__main__":
    main()
