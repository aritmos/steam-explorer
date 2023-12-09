from ...config import Config
import json
import os
from tqdm import tqdm

config = Config()
APPINFO_DIR = os.path.join(config.data_dir, "raw", "appinfo")
filenames = os.listdir(APPINFO_DIR)

app_redirects = {}

for filename in tqdm(filenames):
    app_id = int(filename[:-5])

    filepath = os.path.join(APPINFO_DIR, filename)
    with open(filepath, "r") as appinfo_file:
        data = json.load(appinfo_file)
        id = data["steam_appid"]
        if app_id != id:
            app_redirects[app_id] = id


out_filepath = os.path.join(config.data_dir, "processed", "redirects.json")
with open(out_filepath, "w") as out_file:
    json.dump(app_redirects, out_file, indent=4)
