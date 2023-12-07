import json
import psycopg
from ...config import Config
import os
from tqdm import tqdm

config = Config()
config.db_conn = "postgresql"


with psycopg.connect(config.db_uri) as conn:
    with conn.cursor() as cur:
        with cur.copy("COPY app_publishers (app_id, publisher) FROM STDIN") as copy:
            APPINFO_DIR = os.path.join(config.data_dir, "raw", "appinfo")
            filenames = os.listdir(APPINFO_DIR)

            appid_set = set()

            for filename in tqdm(filenames):
                app_id = filename[:-5]
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
                        # some games have duplicate publishers
                        app_publishers = set(data["publishers"])
                    except Exception:
                        # continue if no publishers found
                        continue

                    for publisher in app_publishers:
                        copy.write_row((id, publisher))
