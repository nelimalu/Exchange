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
PREV_PRICE = 0

UI = UserInterface.UI(CRYPTO_STICKER, BASE_STICKER, START, HISTORY_LENGTH)


class Purchase:
    def __init__(self, price, amount):
        self.price = price
        self.amount = amount


def sigmoid(x):
    try:
        return 1 / (1 + math.exp(-x))
    except OverflowError:
        return -1 if x < 0 else 1


def mean(data):
    if len(data) > 0:
        return sum(data) / len(data)
    raise Exception("Data provided for mean function has a length of 0")


def median(data):
    return data[int(len(data) / 2)]


def avg_rate_of_change(x1, y1, x2, y2):
    try:
        avg = (float(y2) - float(y1)) / (float(x2) - float(x1))
    except ZeroDivisionError:
        avg = 0
    return avg


def get_price():
    resp = requests.get('https://api.kraken.com/0/public/Ticker?pair=' + CRYPTO_STICKER + BASE_STICKER)
    json = resp.json()

    if not json["error"]:
        price = json["result"][JOINED_STICKER]["a"][0]  # change this if using different currency
        return float(price)
    else:
        raise Exception(json["error"])


def get_historical_OHLC(interval, since):  # interval in minutes, since in
    url = "https://api.kraken.com/0/public/OHLC?pair=" + CRYPTO_STICKER + BASE_STICKER
    url += "&interval=" + str(interval)
    url += "&since=" + str(since)

    resp = requests.get(url)
    json = resp.json()

    if not json["error"]:
        price = json["result"]
        return price
    else:
        raise Exception(json["error"])


def update_historical(historical):
    global START
    time_since_update = (time.time() - START)

    if time_since_update > 60 * UPDATE_HISTORY:
        START = time.time()
        return get_historical()
    return historical


def get_historical():
    since = datetime.datetime.now() - datetime.timedelta(hours=HISTORY_LENGTH)
    data = get_historical_OHLC(1, since.timestamp())[JOINED_STICKER]

    return data


def decide(price, historical, saved_data=None):
    if saved_data is None:
        saved_data = []
    timestamps = [float(pair[0]) for pair in historical[::-1]]
    openPrices = [float(pair[1]) for pair in historical[::-1]]

    average_changes = []
    for i in USE_HISTORICAL_MIN:
        _price = openPrices[i - 1]
        timestamp = timestamps[i - 1]
        change = avg_rate_of_change(_price, timestamp, price, datetime.datetime.now().timestamp())
        average_changes.append(change)

    print(saved_data)
    if len(saved_data) > 0:
        update_time = UI.price_graph.update_time
        for i in USE_HISTORICAL_SEC:
            try:
                _price = saved_data[round(i / update_time)]
            except IndexError:
                break
            timestamp = datetime.datetime.now().timestamp() - (i * update_time)
            change = avg_rate_of_change(_price, timestamp, price, datetime.datetime.now().timestamp())
            average_changes.append(change)

    averageRateOfChange = mean(average_changes) # sigmoid(mean(average_changes))

    if averageRateOfChange > BUY_SELL_ARC_MAX:
        return "BUY", averageRateOfChange
    elif averageRateOfChange < BUY_SELL_ARC_MIN:
        return "SELL", averageRateOfChange
    return "WAIT", averageRateOfChange


def buy(price, amount, money, crypto):
    if money > amount:
        money -= amount
        crypto += amount / price
    else:
        crypto += money / price
        money = 0

    purchase = Purchase(price, amount)

    return money, crypto, purchase


def sell(price, amount, money, crypto, purchases):
    valid_purchases = []
    for purchase in purchases:
        if purchase.price >= price:
            valid_purchases.append(purchase)

    if len(valid_purchases) == 0:
        return False

    closest_purchase_price = min([x.amount / x.price for x in valid_purchases], key=lambda x: abs(x - (amount * price)))
    closest_purchase = None
    for purchase in valid_purchases:
        if purchase.amount / purchase.price == closest_purchase_price:
            closest_purchase = purchase

    if closest_purchase is None:
        return False

    if crypto >= amount:
        crypto -= amount
        money += amount * price
    else:
        money += crypto * price
        crypto = 0

    return money, crypto, closest_purchase


def main():
    money = 100
    crypto = 0
    purchases = []
    historical = get_historical()

    run = True
    while run:
        # time.sleep(0.5)
        # delay to make sure we don't overload the api

        price = get_price()
        decision, probability = decide(price, update_historical(historical), saved_data=UI.price_graph.data)

        if decision == "BUY":
            money, crypto, purchase = buy(price, money, money, crypto)
            purchases.append(purchase)
        if decision == "SELL":
            sell_result = sell(price, crypto, money, crypto, purchases)
            if sell_result:
                money, crypto, closest_purchase = sell_result
                purchases.remove(closest_purchase)

        theoretical = money + (crypto * price)

        '''
        print(
            "Money:", str('{:.15f}'.format(money)),
            "Crypto", str('{:.15f}'.format(crypto)),
            "Theoretical", str('{:.15f}'.format(theoretical)),
            "Decision", decision
        )
        '''

        UI.update(money, crypto, theoretical, price, decision, probability)
        # print(UI.price_graph.data_)


if __name__ == "__main__":
    main()
