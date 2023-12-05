import json
import psycopg
from ..config import Config
import os
from tqdm import tqdm

config = Config()
config.db_conn = "postgresql"

# with psycopg.connect(config.db_uri) as conn:


with psycopg.connect(config.db_uri) as conn:
    appids = set(a[0] for a in conn.execute("SELECT id FROM apps").fetchall())

    with conn.cursor() as cur:
        with cur.copy("COPY app_dlcs (game_app_id, dlc_app_id) FROM STDIN") as copy:
            APPINFO_DIR = os.path.join(config.data_dir, "raw", "appinfo")
            filenames = os.listdir(APPINFO_DIR)

            for filename in tqdm(filenames):
                app_id = int(filename[:-5])
                filepath = os.path.join(APPINFO_DIR, filename)
                with open(filepath, "r") as file:
                    data = json.load(file)
                    if data["type"] != "game":
                        continue

                    try:
                        # sometimes dlcs are duplicated
                        app_dlc_ids = set(data["dlc"])
                    except Exception:
                        continue

                    for dlc_id in app_dlc_ids:
                        # skip if dlc is not a game
                        if dlc_id not in appids:
                            continue
                        copy.write_row((app_id, dlc_id))
