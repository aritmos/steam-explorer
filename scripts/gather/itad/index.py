if __name__ != "__main__":
    raise ImportError("This file can only be ran directly as a script")

# === IMPORTS ===

import time
import os

from ...config import Config
from ..errors import RequestError, ResponseFailure

import requests
from bs4 import BeautifulSoup
from argparse import ArgumentParser


# === SCRAPERS ===


config = Config()


class Scraper:
    def __init__(self, offset, limit):
        self.offset = offset
        self.limit = limit

    def request(self):
        url = "https://isthereanydeal.com/ajax/data/lazy.deals.php"

        # I am not sure how the `seen`, `id`, and `timestamp` timestamps work,
        # plugging in relative values with respect to `time.now()` as seen by api calls
        # often gives an unsucessful response.
        # For now I manually load the site and copy over the observed values in its call
        # to this internal api.
        payload = {
            "offset": self.offset,
            "limit": self.limit,
            "filter": "steam",
            "options": "",
            "by": "trending:desc",
            "seen": 1700663982,
            "id": 1700687162,
            "timestamp": 1700688015,
        }

        self.response = requests.post(url, data=payload)

    def check_response(self):
        status_code = self.response.status_code
        if status_code != 200:
            raise RequestError(status_code)

    def get_data(self):

        response_json = self.response.json()
        if response_json["status"] != "success":
            print(self.response.text)
            raise ResponseFailure

        self.done: bool = response_json["data"]["done"]
        self.next_offset: int = response_json["data"]["offset"]
        self.data = []

        soup = BeautifulSoup(response_json["data"]["html"], "html.parser")

        for game in soup.find_all("div", class_="game"):
            plain = game["data-plain"]
            steam_id = game["data-steamid"]
            self.data.append(f"{plain},{steam_id}\n")


class ScraperController:

    def __init__(self):
        self.parse_args()
        self.set_files()
        self.run()

    def parse_args(self):
        desc = """
        TODO
        """
        parser = ArgumentParser(description=desc, prog="scripts.gather.itad.index")
        parser.add_argument("-c", "--chunks", type=int, required=True,
                            help="[int] Chunk sizes to request at a time (max 1000)")
        parser.add_argument("-s", "--sleep", type=float, default=1.0,
                            help="[float] seconds to sleep in between requests (default: 1.0)")

        self.args = parser.parse_args()

    def set_files(self):
        self.SAVE_FILEPATH = os.path.join(config.data_dir, "raw", "itad", "index.csv")
        os.makedirs(os.path.dirname(self.SAVE_FILEPATH), exist_ok=True)

    def run(self):
        csv_lines = ["plain,steam_id\n"]
        offset = 0
        done = False

        while not done:
            time.sleep(self.args.sleep)
            try:
                s = Scraper(offset, self.args.chunks)
            except Exception as e:
                print(f"ERROR: {e}")
                print("Saving accumulated data to file")
                break

            done = s.done
            csv_lines += s.data
            next_offset = s.next_offset

            print(f"Processed range {
                  offset:04}-{next_offset:04}: {len(s.data)} games; finished? {done}")

        with open(self.SAVE_FILEPATH, "w") as file:
            file.writelines(csv_lines)


ScraperController()
