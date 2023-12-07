import os
from ....config import Config
from tqdm import tqdm
import json

# """
# Updates the list of games in `<DATA_DIR>/processed/indexes/gameids.dat`
# by going through gathered files in `<DATA_DIR>/raw/appinfo` and checking
# the "type" field.
# """


def update():
    config = Config()

    APPINFO_DIR = os.path.join(config.data_dir, "raw", "appinfo")
    APPINFO_FILENAME_LIST = os.listdir(APPINFO_DIR)
    APPINFO_FILENAME_LIST.sort()
    GAMELIST_FILEPATH = os.path.join(config.data_dir, "processed", "indexes", "gameids.dat")
    os.makedirs(os.path.dirname(GAMELIST_FILEPATH), exist_ok=True)

    game_appids = []

    print("Iterating through existing appinfo files to look for game appids:")
    for appinfo_filename in tqdm(APPINFO_FILENAME_LIST):
        appinfo_filepath = os.path.join(APPINFO_DIR, appinfo_filename)
        with open(appinfo_filepath, "r") as file:
            appinfo = json.load(file)
            if appinfo["type"] == "game":
                appid = appinfo["steam_appid"]
                if str(appid) == "8780":
                    print(appinfo_filename, appid)
                    quit()
                game_appids.append(str(appid))

    with open(GAMELIST_FILEPATH, "w") as file:
        print("Storing game appids into file:")
        for appid in tqdm(game_appids):
            file.write(str(appid) + "\n")
