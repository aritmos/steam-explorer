import json
import os

from ....config import Config

from argparse import ArgumentParser


config = Config()


APPLIST_JSON = os.path.join(config.data_dir, "raw", "applist", "applist.json")
APPLIST_FILE = os.path.join(config.data_dir, "processed", "indexes", "appids.dat")

desc = f"""
Parses `{APPLIST_JSON}` into `{APPLIST_FILE}`, keeping only the AppIDs.
"""
parser = ArgumentParser(description=desc)
parser.parse_args()

with open(APPLIST_JSON, "r", encoding="UTF-8") as file:
    applist = json.load(file)["applist"]["apps"]
    appids = [app["appid"] for app in applist]
    # appids = list(set(appids))  # remove duplicates
    appids.sort()

with open(APPLIST_FILE, "w") as file:
    file.writelines([str(id) + "\n" for id in appids])
