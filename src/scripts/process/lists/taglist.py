import os
from ....config import Config
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

    tag_set = set()

    print("Iterating through existing apptag files to look for application tags:")
    for apptags_filename in tqdm(APPTAGS_FILENAME_LIST):
        apptags_filepath = os.path.join(APPTAGS_DIR, apptags_filename)
        appid = apptags_filename[:-5]
        with open(apptags_filepath, "r") as file:
            apptags = json.load(file)
            for tag in apptags:
                id = int(tag["tagid"])
                name = tag["name"]
                tag_set.add((id, name))

            logging.info(f"{appid} OK")

    tag_list = list(tag_set)
    tag_list.sort()

    with open(INDEX_FILEPATH, "w") as file:
        print("Storing tag index into file:")
        for genre in tqdm(tag_list):
            file.write(f"{genre[0]},{genre[1]}\n")


if __name__ == "__main__":
    generate()
