import json
import psycopg
from ...config import Config
import os
from tqdm import tqdm

config = Config()

config.db_conn = "postgresql"

with psycopg.connect(config.db_uri) as conn:
    with conn.cursor() as cur:
        with cur.copy("COPY app_categories (app_id, category_id) FROM STDIN") as copy:
            APPINFO_DIR = os.path.join(config.data_dir, "raw", "appinfo")
            filenames = os.listdir(APPINFO_DIR)

            appid_set = set()

            for filename in tqdm(filenames):
                app_id = int(filename[:-5])
                filepath = os.path.join(APPINFO_DIR, filename)
                with open(filepath, "r") as file:
                    data = json.load(file)

                    if data["type"] not in ["game", "dlc", "demo"]:
                        continue

                    id = data["steam_appid"]
                    if id in appid_set:
                        continue
                    else:
                        appid_set.add(id)

                    try:
                        app_categegories = data["categories"]
                    except Exception:
                        continue

                    # some apps have repeated categories
                    category_ids = set((category["id"] for category in app_categegories))

                    for category_id in category_ids:
                        copy.write_row((id, category_id))
