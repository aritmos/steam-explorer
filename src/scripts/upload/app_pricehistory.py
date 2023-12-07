import csv
import psycopg
from ...config import Config
import os
from tqdm import tqdm

config = Config()
config.db_conn = "postgresql"


# no need for context managers due to the nature of the script
with psycopg.connect(config.db_uri) as conn:
    db_appids = set(a[0] for a in conn.execute("SELECT id FROM apps").fetchall())

    with conn.cursor() as cur:
        with cur.copy("COPY app_pricehistory (app_id, time, price_full, price_current)\
                FROM STDIN") as copy:

            PRICEHISTORY_DIR = os.path.join(config.data_dir, "raw", "itad", "pricehistory")
            filenames = os.listdir(PRICEHISTORY_DIR)

            for filename in tqdm(filenames):
                app_id = int(filename[:-4])

                # some tracked items are audio, movies, etc. dont include them.
                if app_id not in db_appids:
                    continue

                filepath = os.path.join(PRICEHISTORY_DIR, filename)
                with open(filepath, "r") as file:
                    rows = csv.reader(file)
                    next(rows)  # ignore column names

                    rows = set((tuple(r) for r in rows))  # remove duplicate entries

                    for row in rows:
                        copy.write_row([app_id, *row])
