import json

from argparse import ArgumentParser
import requests
from requests.exceptions import JSONDecodeError

# -- MAIN SCRIPT --

APPLIST_JSON = "data/raw/applist/applist.json"
API_URL = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"

desc = f"""
Requests a list of all steam applications.
Stores the received JSON in `{APPLIST_JSON}`
"""
parser = ArgumentParser(description=desc)
parser.parse_args()

response = requests.get(API_URL)

if response.status_code != 200:
    print("ERROR: HTTPError {r.status_code}\nAborting.")
    quit()

with open(APPLIST_JSON, "w", encoding="UTF-8") as file:
    try:
        data = response.json()
    except JSONDecodeError:
        print("ERROR: JSONDecodeError\nAborting.")
        quit()

    json.dump(data, file, indent=4)
