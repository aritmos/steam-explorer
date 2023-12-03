import os
from ...config import Config
from tqdm import tqdm
import json
import logging


def generate():
    config = Config()
    LOG_FILE = os.path.join(config.logs_dir, "process", "indexes", "genres.log")
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    config.log(LOG_FILE)

    APPTAGS_DIR = os.path.join(config.data_dir, "raw", "apptags")
    APPTAGS_FILENAME_LIST = os.listdir(APPTAGS_DIR)

    INDEX_FILEPATH = os.path.join(config.data_dir, "processed", "indexes", "tags.csv")
    os.makedirs(os.path.dirname(INDEX_FILEPATH), exist_ok=True)

    genre_set = set()

    print("Iterating through existing apptag files to look for application tags:")
    for apptags_filename in tqdm(APPTAGS_FILENAME_LIST):
        apptags_filepath = os.path.join(APPTAGS_DIR, apptags_filename)
        appid = apptags_filename[:-5]
        with open(apptags_filepath, "r") as file:
            apptags = json.load(file)
            try:
                genres = apptags["genres"]
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
