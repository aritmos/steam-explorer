import json
import psycopg
from ...config import Config
import os
from tqdm import tqdm

config = Config()
config.db_conn = "postgresql"


with psycopg.connect(config.db_uri) as conn:
    # appids = set(a[0] for a in conn.execute("SELECT id FROM apps").fetchall())

    with conn.cursor() as cur:
        with cur.copy("COPY app_developers (app_id, developer) FROM STDIN") as copy:
            APPINFO_DIR = os.path.join(config.data_dir, "raw", "appinfo")
            filenames = os.listdir(APPINFO_DIR)

            appid_set = set()

            for filename in tqdm(filenames):
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
                        # some games have duplicate developers
                        app_developers = set(data["developers"])
                    except Exception:
                        continue

                    for developer in app_developers:
                        copy.write_row((id, developer))
