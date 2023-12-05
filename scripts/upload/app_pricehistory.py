import csv
import psycopg
from ..config import Config
import os
from tqdm import tqdm

config = Config()
config.db_conn = "postgresql"


# no need for context managers due to the nature of the script
conn = psycopg.connect(config.db_uri)
cur = conn.cursor()
with cur.copy("COPY app_pricehistory (app_id, time, price_full, price_current)\
        FROM STDIN") as copy:

    PRICEHISTORY_DIR = os.path.join(config.data_dir, "raw", "itad", "pricehistory")
    filenames = os.listdir(PRICEHISTORY_DIR)

    counter = 0

    for filename in filenames:
        app_id = int(filename[:-4])
        filepath = os.path.join(PRICEHISTORY_DIR, filename)
        with open(filepath, "r") as file:
            rows = csv.reader(file)
            next(rows)  # ignore column names

            row_set = set()
            for row in rows:
                key = row[0]
                if key in row_set:
                    counter += 1
                else:
                    row_set.add(key)
    print(counter)

    # for row in rows:
    #     copy.write_row([app_id, *row])
