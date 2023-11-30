import csv
import psycopg
from ..config import Config
import os

config = Config()
config.db_conn = "postgresql"

with psycopg.connect(config.db_uri) as conn:
    with conn.cursor() as cur:
        with cur.copy("copy genres (id, name) from stdin") as copy:
            categories_filepath = os.path.join(
                config.data_dir, "processed", "indexes", "genres.csv")
            with open(categories_filepath, "r") as file:
                csv_reader = csv.reader(file, delimiter=",")
                for row in csv_reader:
                    copy.write_row(row)
