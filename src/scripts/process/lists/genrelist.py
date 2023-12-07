import os
from ....config import Config
from tqdm import tqdm
import json
import logging

# """
# Updates the list of games in `<DATA_DIR>/processed/indexes/gameids.dat`
# by going through gathered files in `<DATA_DIR>/raw/appinfo` and checking
# the "type" field.
# """


def generate():
    config = Config()
    LOG_FILE = os.path.join(config.logs_dir, "process", "indexes", "genres.log")
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    config.log(LOG_FILE)

    APPINFO_DIR = os.path.join(config.data_dir, "raw", "appinfo")
    APPINFO_FILENAME_LIST = os.listdir(APPINFO_DIR)

    INDEX_FILEPATH = os.path.join(config.data_dir, "processed", "indexes", "genres.csv")
    os.makedirs(os.path.dirname(INDEX_FILEPATH), exist_ok=True)

    genre_set = set()

    print("Iterating through existing appinfo files to look for game genres:")
    for appinfo_filename in tqdm(APPINFO_FILENAME_LIST):
        appinfo_filepath = os.path.join(APPINFO_DIR, appinfo_filename)
        appid = appinfo_filename[:-5]
        with open(appinfo_filepath, "r") as file:
            appinfo = json.load(file)
            try:
                genres = appinfo["genres"]
            except KeyError:
                logging.warning(f"{appid} JSONError")
                continue

            for genre in genres:
                id = int(genre["id"])
                desc = genre["description"]
                genre_set.add((id, desc))

            logging.info(f"{appid} OK")

    genre_list = list(genre_set)
    genre_list.sort()

    with open(INDEX_FILEPATH, "w") as file:
        print("Storing genre index into file:")
        for genre in tqdm(genre_list):
            file.write(f"{genre[0]},{genre[1]}\n")


if __name__ == "__main__":
    generate()
