import csv
import psycopg
from ..config import Config
import os
from tqdm import tqdm

config = Config()
config.db_conn = "postgresql"

months = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12
}


def parse_date(date: str) -> str:
    (month, year) = date.split(" ")
    month_num = months[month]
    return f"{year}-{month_num:02}-01"


# no need for context managers due to the nature of the script
conn = psycopg.connect(config.db_uri)
cur = conn.cursor()
with cur.copy("COPY app_playercounts (app_id, month_date, playercount_average, playercount_peak)\
        FROM STDIN") as copy:

    PLAYERCOUNTS_DIR = os.path.join(config.data_dir, "raw", "playercounts")
    filenames = os.listdir(PLAYERCOUNTS_DIR)

    for filename in tqdm(filenames):
        app_id = int(filename[:-4])
        filepath = os.path.join(PLAYERCOUNTS_DIR, filename)
        with open(filepath, "r") as file:
            rows = csv.reader(file)
            next(rows)  # ignore column names
            next(rows)  # ignore "last 30 days row"

            for row in rows:
                row[0] = parse_date(row[0])
                copy.write_row([app_id, *row])
