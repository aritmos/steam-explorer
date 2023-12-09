import json
import psycopg
from ...config import Config
import os
from tqdm import tqdm

config = Config()
config.db_conn = "postgresql"

APP_REDIRECT_FILEPATH = os.path.join(config.data_dir, "processed", "redirects.json")
with open(APP_REDIRECT_FILEPATH, "r") as file:
    appid_redirects = json.load(file)

APP_REVIEWS_DIRECTORY = os.path.join(config.data_dir, "raw", "appreviews")
appreview_filenames = os.listdir(APP_REVIEWS_DIRECTORY)


with psycopg.connect(config.db_uri) as conn:
    with conn.cursor() as cur:
        # create a temporary table where we store the app reviews
        query = ("CREATE TEMPORARY TABLE temp_apps AS "
                 "SELECT * "
                 "FROM apps "
                 "WHERE FALSE;")
        cur.execute(query)

        with cur.copy("COPY temp_apps (id, reviews_positive, reviews_total) FROM STDIN") as copy:
            for filename in tqdm(appreview_filenames):
                appid = int(filename[:-5])  # strips the `.json`
                appid = appid_redirects.get(appid, appid)

                filepath = os.path.join(APP_REVIEWS_DIRECTORY, filename)
                with open(filepath, "r") as file:
                    data = json.load(file)

                    reviews_positive = data["total_positive"]
                    reviews_total = data["total_reviews"]

                    copy.write_row((appid, reviews_positive, reviews_total))

        # add review values in `temp_apps` into `apps` table
        query = ("UPDATE apps "
                 "SET reviews_positive = temp_apps.reviews_positive, "
                 "    reviews_total    = temp_apps.reviews_total "
                 "FROM temp_apps "
                 "WHERE apps.id = temp_apps.id;")
        cur.execute(query)
