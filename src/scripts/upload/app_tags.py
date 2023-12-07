import json
import psycopg
from ...config import Config
import os
from tqdm import tqdm

config = Config()
config.db_conn = "postgresql"

appid_set = set()

with psycopg.connect(config.db_uri) as conn:
    with conn.cursor() as cur:
        with cur.copy("COPY app_tags (app_id, tag_id, votes) FROM STDIN") as copy:
            APPTAGS_DIR = os.path.join(config.data_dir, "raw", "apptags")
            apptag_filenames = os.listdir(APPTAGS_DIR)
            for filename in tqdm(apptag_filenames):
                app_id = int(filename[:-5])
                filepath = os.path.join(APPTAGS_DIR, filename)
                with open(filepath, "r") as file:
                    if app_id in appid_set:
                        continue
                    else:
                        appid_set.add(app_id)

                    data = [[str(app_id), str(obj["tagid"]), str(obj["count"])]
                            for obj in json.load(file)]
                    for row in data:
                        copy.write_row(row)
