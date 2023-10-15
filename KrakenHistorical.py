import requests
import datetime
import time
from Tools.Exchange.Crypto.Kraken import UserInterface

CRYPTO_STICKER = "BTC"
BASE_STICKER = "CAD"
JOINED_STICKER = "XXBTZCAD"

START = time.time()
BUY_SELL_ARC = 5.0  # ARC is average rate of change, used in decide() function
UPDATE_HISTORY = 3  # minutes between each historical OHLC update
HISTORY_LENGTH = 0.25  # hours to search into the past

UI = UserInterface.UI(CRYPTO_STICKER, BASE_STICKER, START, HISTORY_LENGTH)


def mean(data):
    if len(data) > 0:
        return sum(data) / len(data)
    raise Exception("Data provided for mean function has a length of 0")


def median(data):
    return data[int(len(data) / 2)]


def avg_rate_of_change(x1, y1, x2, y2):
    return (float(y2) - float(y1)) / (float(x2) - float(x1))


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


def decide(price, historical):
    timestamps = [float(pair[0]) for pair in historical]
    openPrices = [float(pair[1]) for pair in historical]
    average_price = mean(openPrices)
    average_time = median(timestamps)

    averageRateOfChange = avg_rate_of_change(average_price, average_time, price, datetime.datetime.now().timestamp()) * -1

    if averageRateOfChange > BUY_SELL_ARC:
        return "BUY", averageRateOfChange
    elif averageRateOfChange < -BUY_SELL_ARC:
        return "SELL", averageRateOfChange
    return "WAIT", averageRateOfChange


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
    theoretical = 0
    historical = get_historical()

    run = True
    while run:
        # time.sleep(0.5)
        # delay to make sure we don't overload the api

        price = get_price()
        decision, probability = decide(price, update_historical(historical))

        if decision == "BUY":
            money, crypto = buy(price, money, money, crypto)
        if decision == "SELL":
            money, crypto = sell(price, crypto, money, crypto)

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
        print(UI.price_graph.data)


if __name__ == "__main__":
    main()
