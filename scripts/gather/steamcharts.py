if __name__ != "__main__":
    raise ImportError("This file must only be ran directly as a script")

# === IMPORTS ===


import json
import os
import bisect
import time

from ..config import Config
from .errors import RequestError
from ..process.lists import gamelist

import requests
from bs4 import BeautifulSoup
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from tqdm import tqdm
import logging


# === ERRORS ===


class TableError(Exception):
    pass


class FileError(Exception):
    """
    Necessary file does not exist
    """

    def __init__(self, filepath: str):
        self.filepath = filepath

    def __str__(self) -> str:
        return f"Necessary file {self.filepath} does not exist"


# === SCRAPERS ===


config = Config()

# kept in global scope so `makedirs` only executes once
SAVE_DIR = os.path.join(config.data_dir, "raw", "playercounts")
os.makedirs(SAVE_DIR, exist_ok=True)


class Scraper:
    """
    Handler for steamcharts websraping
    """

    def __init__(self, appid: int):
        self.appid = appid
        self.request()
        self.check_response()
        self.get_data()
        self.save()

    def set_files(self):
        self.SAVE_FILEPATH = os.path.join(
            config.data_dir, "raw", "playercounts", f"{self.appid:07}.csv")

    def request(self):
        """
        Loads the website for the given appid and stores the response.
        """

        url = f"https://steamcharts.com/app/{self.appid}"
        self.response = requests.get(url)

    def check_response(self):
        """
        Checks the inner reponse's (`self.reponse`) status code.
        Raises a `RequestError` if the status code is not 200.

        NOTE: The appears to return an HTTP 500 for untracked games.
        """

        status_code = self.response.status_code
        if status_code != 200:
            raise RequestError(status_code)

    def get_data(self):
        soup = BeautifulSoup(self.response.text, "html.parser")

        rows = soup.find_all("tr")
        if not rows:
            raise TableError

        self.table = []
        for row in rows[1:]:  # skip the column names
            date = row.find("td", class_="month-cell").text.strip()
            avg = row.find("td", class_="num-f").text.strip()
            peak = row.find("td", class_="num").text.strip()

            self.table.append(f"{date},{avg},{peak}\n")

    def save(self):
        """
        Saves the table data into a CSV file.
        Writes to: `<SAVE_DIR>/<appid>.csv`
        """
        filepath = os.path.join(SAVE_DIR, f"{self.appid:07}.csv")
        with open(filepath, "w", encoding="UTF-8") as file:
            file.write("date,avg_playercount,peak_playercount\n")
            file.writelines(self.table)


class ScraperController:
    def __init__(self):
        self.set_files()
        self.parse_args()

        if self.args.update:
            gamelist.update()

        self.set_start_appid()
        self.load()
        self.run()

    def set_files(self):
        self.STATE_FILEPATH = os.path.join(config.state_dir, "gather", "steamcharts.json")
        os.makedirs(os.path.dirname(self.STATE_FILEPATH), exist_ok=True)

        self.LOGS_FILEPATH = os.path.join(config.logs_dir, "gather", "steamcharts.log")
        os.makedirs(os.path.dirname(self.LOGS_FILEPATH), exist_ok=True)
        config.log(filepath=self.LOGS_FILEPATH)

        self.APPLIST_FILEPATH = os.path.join(config.data_dir, "raw", "applist", "applist-games.dat")
        if not os.path.exists(self.APPLIST_FILEPATH):
            raise FileError(self.APPLIST_FILEPATH)

    def parse_args(self):
        # TODO: add proper description
        desc = f"""
    Extract playercount data from steamcharts site via scraping.
    Uses `{self.APPLIST_FILEPATH}` for the game appid index.
    This file is not automatically created on the first run and \
    requires the explicit use of the `-u` flag.
        """
        parser = ArgumentParser(
            prog="scripts.gather.steamcharts",
            description=desc,
            formatter_class=RawDescriptionHelpFormatter
        )
        parser.add_argument("-u", "--update", action="store_true",
                            help="Update the game appid list")
        parser.add_argument("-n", "--number", type=int, required=True,
                            help="[int] number of appids to process")
        parser.add_argument("-s", "--sleep", type=float, default="3.0",
                            help="[float] seconds to sleep in between requests (default: 3.0)")
        parser.add_argument("-m", "--manual", type=int, help="[int] manually select start appid")

        self.args = parser.parse_args()

    def set_start_appid(self):
        if self.args.manual:
            self.start_appid = self.args.manual

        # automatic state management
        try:
            with open(self.STATE_FILEPATH, "r", encoding="UTF-8") as file:
                self.start_appid = int(json.load(file)["greatest_processed_appid"])
        except FileNotFoundError:
            with open(self.STATE_FILEPATH, "w", encoding="UTF-8") as file:
                # smallest real appid is 5, so this is guaranteed to be at the start
                json.dump({"greatest_processed_appid": 1}, file)
                self.set_start_appid()
        except Exception as e:
            print(f"Error using automatic start AppID lookup: {e}")
            quit()

    def load(self):
        """
        Loads the selected appid slice
        """
        with open(self.APPLIST_FILEPATH, "r") as file:
            appids = [int(line) for line in file]

        start_idx = bisect.bisect_left(appids, self.start_appid)
        if len(appids[start_idx:]) < self.args.number:
            self.appids = appids[start_idx:]
        else:
            self.appids = appids[start_idx:][:self.args.number]

    def run(self):
        """
        Extracts the playercount data for each game in the given appids and stores the data to file
        (`<DATA_DIR>/raw/playercounts/<appid>.csv`). Waits `timeout_sec` between requests.
        """

        print(f"\nGathering playercount records for {
            self.args.number} games, starting at appid = {self.start_appid}:\n")

        # sentinel value (no application with appid=0 exists)
        last_successful_appid = 0
        for appid in tqdm(self.appids):
            time.sleep(self.args.sleep)
            try:
                Scraper(appid).save()

                logging.info(f"{appid:07} OK")
                last_successful_appid = appid
            except Exception as e:
                if isinstance(e, RequestError):
                    message = f"{appid: 07} HTTPError {e.status_code}"
                    if e.status_code in [404, 500]:  # only allowed error
                        logging.warning(message)
                    else:
                        logging.critical(message)
                        print(message + ". Aborting.")
                        break
                else:
                    message = f"{appid: 07} Error: {e}"
                    print(message + ". Aborting.")
                    logging.critical(message)
                    break

        # save the last successful appid to file
        if last_successful_appid != 0:
            with open(self.STATE_FILEPATH, "w", encoding="UTF-8") as file:
                obj = {"greatest_processed_appid": last_successful_appid}
                json.dump(obj, file, indent=4)


ScraperController()
