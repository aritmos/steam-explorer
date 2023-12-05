import json
import psycopg
from ..config import Config
import os
from tqdm import tqdm

config = Config()
config.db_conn = "postgresql"

# no need for context managers due to the nature of the script
conn = psycopg.connect(config.db_uri)
cur = conn.cursor()
with cur.copy("COPY app_genres (app_id, genre_id) FROM STDIN") as copy:

    APPINFO_DIR = os.path.join(config.data_dir, "raw", "appinfo")
    filenames = os.listdir(APPINFO_DIR)

    for filename in tqdm(filenames):
        app_id = int(filename[:-5])
        filepath = os.path.join(APPINFO_DIR, filename)
        with open(filepath, "r") as file:
            data = json.load(file)
            if data["type"] not in ["game", "dlc", "demo"]:
                continue

            try:
                app_genres = data["genres"]
            except Exception:
                continue

            app_genre_ids = set((genre["id"] for genre in app_genres))

            for genre_id in app_genre_ids:
                copy.write_row((app_id, genre_id))
