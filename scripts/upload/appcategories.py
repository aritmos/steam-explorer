import json
import psycopg
from ..config import Config
import os
from tqdm import tqdm

config = Config()

config.db_conn = "postgresql"

with psycopg.connect(config.db_uri) as conn:
    with conn.cursor() as cur:
        with cur.copy("COPY app_categories (app_id, category_id) FROM STDIN") as copy:
            APPINFO_DIR = os.path.join(config.data_dir, "raw", "appinfo")
            filenames = os.listdir(APPINFO_DIR)

            # some apps have repeated categories
            app_category_set = set()

            for filename in tqdm(filenames):
                app_id = int(filename[:-5])
                filepath = os.path.join(APPINFO_DIR, filename)
                with open(filepath, "r") as file:
                    data = json.load(file)
                    if data["type"] not in ["game", "dlc", "demo"]:
                        continue

                    try:
                        app_categegories = data["categories"]
                    except Exception:
                        continue

                    category_ids = set((category["id"] for category in app_categegories))

                    for category_id in category_ids:
                        app_category_set.add((app_id, category_id))
