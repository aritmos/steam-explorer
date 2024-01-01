import csv
import psycopg
from ...config import Config
import os
from tqdm import tqdm

config = Config()
config.db_conn = "postgresql"

APP_PRICE_FILEPATH = os.path.join(config.data_dir, "processed", "good_prices.csv")
with open(APP_PRICE_FILEPATH, "r") as file:
    app_prices = list(csv.reader(file))
    app_prices = [[int(appid), int(price)] for [appid, price] in app_prices]


with psycopg.connect(config.db_uri) as conn:
    with conn.cursor() as cur:
        # create a temporary table where we store the app reviews
        query = ("CREATE TEMPORARY TABLE temp_apps AS "
                 "SELECT * "
                 "FROM apps "
                 "WHERE FALSE;")
        cur.execute(query)

        with cur.copy("COPY temp_apps (id, price) FROM STDIN") as copy:
            for [appid, price] in tqdm(app_prices):
                copy.write_row((appid, price))

        # update pricing to ensure currency is in euros
        query = ("UPDATE apps "
                 "SET price = temp_apps.price, "
                 "    reviews_total    = temp_apps.reviews_total "
                 "FROM temp_apps "
                 "WHERE apps.id = temp_apps.id;")
        cur.execute(query)
