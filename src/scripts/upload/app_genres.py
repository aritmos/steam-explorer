import json
import psycopg
from ...config import Config
import os
from tqdm import tqdm

config = Config()
config.db_conn = "postgresql"

# no need for context managers due to the nature of the script
with psycopg.connect(config.db_uri) as conn:
    with conn.cursor() as cur:

        with cur.copy("COPY app_genres (app_id, genre_id) FROM STDIN") as copy:

            APPINFO_DIR = os.path.join(config.data_dir, "raw", "appinfo")
            filenames = os.listdir(APPINFO_DIR)

            seen_appids = set()

            for filename in tqdm(filenames):
                filepath = os.path.join(APPINFO_DIR, filename)
                with open(filepath, "r") as file:
                    data = json.load(file)
                    if data["type"] not in ["game", "dlc", "demo"]:
                        continue

                    id = data["steam_appid"]

                    if id in seen_appids:
                        continue
                    else:
                        seen_appids.add(id)

                    try:
                        app_genres = data["genres"]
                    except Exception:
                        continue

                    app_genre_ids = set((genre["id"] for genre in app_genres))

                    for genre_id in app_genre_ids:
                        copy.write_row((id, genre_id))
