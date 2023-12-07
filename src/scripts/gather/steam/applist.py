if __name__ != "__main__":
    raise ImportError("This file can only be ran directly as a script")

# === IMPORTS ===

import json
import os

from ....config import Config
from ..errors import RequestError, FileError

from argparse import ArgumentParser
import requests


# === SCRAPERS ===


config = Config()


class Scraper:
    def __init__(self):
        self.set_files()
        self.parse_args()

        self.request()
        self.check_response()

        self.save()

    def parse_args(self):
        desc = f"""
        Requests a list of all steam applications.
        Stores the received JSON in `{self.APPLIST_JSON_FILEPATH}`
        """
        parser = ArgumentParser(description=desc, prog="scripts.gather.steam.applist")
        self.args = parser.parse_args()

    def set_files(self):
        self.APPLIST_JSON_FILEPATH = os.path.join(config.data_dir, "raw", "applist", "applist.json")
        if not os.path.exists(self.APPLIST_JSON_FILEPATH):
            raise FileError(self.APPLIST_JSON_FILEPATH)

    def request(self):
        url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
        self.response = requests.get(url)

    def check_response(self):
        status_code = self.response.status_code
        if status_code != 200:
            raise RequestError(status_code)

    def save(self):
        os.makedirs(os.path.dirname(self.APPLIST_JSON_FILEPATH))
        with open(self.APPLIST_JSON_FILEPATH, "w", encoding="UTF-8") as file:
            try:
                data = self.response.json()
            except Exception as e:
                print(f"ERROR: {e}")
                quit()

            json.dump(data, file, indent=4)
