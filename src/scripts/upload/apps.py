import json
import psycopg
from ...config import Config
import os
from tqdm import tqdm


column_names = [
    "id",
    "kind",
    "name",
    "supports_windows",
    "supports_mac",
    "supports_linux",
    "price",
    "metacritic_score",
    "reviews_total",
    "reviews_positive",
    "age_check",
    "release_date",
    "has_drm",
    "has_ext_acc",
    "achievements"
]


months = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12
}


def parse_date(date: str) -> str | None:
    try:
        [day, month, year] = date.split(' ')
        day = int(day)
        month = months[month.rstrip(",")]
        year = int(year)
        return f"{year}-{month:02}-{day:02}"
    except Exception:
        return None


config = Config()
config.db_conn = "postgresql"


APPINFO_DIR = os.path.join(config.data_dir, "processed", "appinfo")
apptag_filenames = os.listdir(APPINFO_DIR)

# we cant fstring the column names due to injection protection
SQL_STATEMENT = "COPY apps (id, kind, name, supports_windows, supports_mac,\
        supports_linux, price, metacritic_score, reviews_total, reviews_positive,\
        age_check, release_date, has_drm, has_ext_acc, achievements) FROM STDIN"

# avoid duplicates
appid_set = set()

with psycopg.connect(config.db_uri) as conn:
    with conn.cursor() as cur:
        with cur.copy(SQL_STATEMENT) as copy:
            for filename in tqdm(apptag_filenames):
                if filename != "0404090.json":
                    continue
                filepath = os.path.join(APPINFO_DIR, filename)
                with open(filepath, "r") as file:
                    data = json.load(file)

                    if data["id"] in appid_set:
                        continue
                    else:
                        appid_set.add(data["id"])

                    try:
                        # for some reason a game chose these characters
                        data["age_check"] = data["age_check"].replace("１８", "18")
                        # some games denote the age check as "7+" etc
                        data["age_check"] = data["age_check"].rstrip("+")
                    except Exception:
                        pass

                    data["release_date"] = parse_date(data["release_date"])

                    row = [data.get(col) for col in column_names]
                    copy.write_row(row)
    conn.commit()
