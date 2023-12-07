import os
from ...config import Config

config = Config()
APP_PRICEHISTORY_DIR = os.path.join(config.data_dir, "raw", "itad", "pricehistory")

bad_apps = [210350]

for appid in bad_apps:
    filepath = os.path.join(APP_PRICEHISTORY_DIR, f"{appid:07}.csv")
    try:
        os.remove(filepath)
    except Exception:
        continue

rename_apps = [(404730, 240760)]

for (old_appid, new_appid) in rename_apps:
    old_filepath = os.path.join(APP_PRICEHISTORY_DIR, f"{old_appid:07}.csv")
    os.rename(old_filepath, f"{new_appid:07}.csv")
