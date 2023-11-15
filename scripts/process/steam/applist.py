import json

from argparse import ArgumentParser

# -- MAIN SCRIPT --

APPLIST_JSON = "data/raw/applist/applist.json"
APPLIST_TXT = "data/raw/applist/applist.txt"

desc = f"""
Parses `{APPLIST_JSON}` into `{APPLIST_TXT}`, keeping only the AppIDs (one per line).
"""
parser = ArgumentParser(description=desc)
parser.parse_args()

with open(APPLIST_JSON, "r", encoding="UTF-8") as file:
    applist = json.load(file)["applist"]["apps"]
    appids = [app["appid"] for app in applist]
    appids.sort()

with open(APPLIST_TXT, "w", encoding="UTF-8") as file:
    file.writelines([str(id) + "\n" for id in appids])
