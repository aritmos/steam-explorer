import csv
import psycopg
from ..config import Config
import os

config = Config()
config.db_conn = "postgresql"


with psycopg.connect(config.db_uri) as conn:
    # appids = set(a[0] for a in conn.execute("SELECT id FROM apps").fetchall())

    with conn.cursor() as cur:
        with cur.copy("COPY languages (language_code, name) FROM STDIN") as copy:
            LANGS_FILEPATH = os.path.join(config.data_dir, "processed", "indexes", "langs.csv")
            with open(LANGS_FILEPATH, "r") as file:
                rows = csv.reader(file)
                next(rows)  # ignore comments
                next(rows)  # ignore comments

                for row in rows:
                    lang_name = row[0]
                    lang_code = row[1]

                    copy.write_row((lang_code, lang_name))
