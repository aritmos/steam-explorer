import os
import requests
import math
import time

from ...config import Config
from ..gather.errors import RequestError, ResponseFailure

import logging
from tqdm import tqdm

config = Config()

LOG_FILEPATH = os.path.join(config.logs_dir, "gather", "currency.log")
BAD_CURRENCY_FILEPATH = os.path.join(config.data_dir, "processed", "bad_currency.csv")
SAVE_FILEPATH = os.path.join(config.data_dir, "processed", "good_prices.csv")


config.log(LOG_FILEPATH)

with open(BAD_CURRENCY_FILEPATH, "r") as file:
    bad_currency_appids = [line.split(", ")[0] for line in file.readlines()]

L = len(bad_currency_appids)
GROUP_SIZE = 50
N = math.ceil(L / GROUP_SIZE)

app_prices = []

for i in tqdm(range(N)):
    time.sleep(1.5)
    appids = bad_currency_appids[GROUP_SIZE * i: GROUP_SIZE * (i + 1)]
    url = f"https://store.steampowered.com/api/appdetails?appids={
        ','.join(appids)}&cc=es&filters=price_overview"

    try:
        response = requests.get(url)

        status_code = response.status_code
        if status_code != 200:
            raise RequestError(status_code)

        data = response.json()
        appids = data.keys()

        for appid in appids:
            appid_response = data[appid]
            if not appid_response["success"]:
                logging.warning(f"{appid:07} {ResponseFailure()}")
                continue

            price = appid_response["data"].get("price_overview", {}).get("initial", 0)

            app_prices.append((appid, price))

            logging.info(f"{appid:07} OK")

    except RequestError as e:
        logging.warning(f"0000000 {e!r} (Batch failed: Size {GROUP_SIZE}, Index: {i})")
    except Exception as e:
        logging.critical(e)

with open(SAVE_FILEPATH, "w") as file:
    file.writelines((f"{appid},{price}\n" for (appid, price) in app_prices))
