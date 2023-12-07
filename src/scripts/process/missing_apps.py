import json
import psycopg
from ...config import Config
import os
from tqdm import tqdm

config = Config()
config.db_conn = "postgresql"

with psycopg.connect(config.db_uri) as conn:
    appids = set(a[0] for a in conn.execute("SELECT id FROM apps").fetchall())

    with conn.cursor() as cur:
        with cur.copy("COPY game_demos (game_app_id, demo_app_id) FROM STDIN") as copy:
            APPINFO_DIR = os.path.join(config.data_dir, "raw", "appinfo")
            filenames = os.listdir(APPINFO_DIR)

            appid_set = set()

            for filename in tqdm(filenames):
                app_id = int(filename[:-5])
                filepath = os.path.join(APPINFO_DIR, filename)
                with open(filepath, "r") as file:
                    data = json.load(file)
                    if data["type"] != "game":
                        continue
                    try:
                        dlcs = data["dlc"]
                    except Exception:
                        continue

                    for dlc in dlcs:
                        if dlc not in appids:
                            print(dlc)
