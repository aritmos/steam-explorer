if __name__ != "__main__":
    raise ImportError("This file must only be ran directly as a script")


# === IMPORTS ===

import bisect
import json
import os
import time
import re

from ....config import Config
from ..errors import RequestError, HTMLError

from argparse import ArgumentParser, RawDescriptionHelpFormatter
import requests
import logging
from tqdm import tqdm
from bs4 import BeautifulSoup, Tag

# === SCRAPERS ===
config = Config()


class Scraper():
    def __init__(self, appid: int):
        self.appid = appid

        self.request()
        self.check_response()
        self.get_data()
        self.save()

    def request(self):
        """
        Calls the API and stores the response in `self.response`
        """
        url = f"https://store.steampowered.com/app/{self.appid}/"
        self.response = requests.get(url)

    def check_response(self):
        """
        Checks the inner response's (`self.response`) status code.
        Raises a `RequestError` if the status code does not equal 200.
        """
        status_code = self.response.status_code
        if status_code != 200:
            raise RequestError(status_code)

    def get_data(self):
        """
        Extracts the tags from the embedded JS scripts in the main HTML element
        (This gives more information than scraping the rendered elements directly)
        """

        soup = BeautifulSoup(self.response.text, "html.parser")
        user_reviews_div = soup.find("div", id="userReviews")
        if not isinstance(user_reviews_div, Tag):
            raise HTMLError(str(type(user_reviews_div)))

        def parse_tooltip(div_attr: str) -> tuple[int, int]:
            """
            Parse the `data-tooltip-html` attribute into review count and positive percentage:
            '85% of the 865 user reviews in the last 30 days are positive.' => (85, 865)
            '92% of the 149,403 user reviews for this game are positive.' => (92, 149403)
            """
            if div_attr == "No user reviews":
                return (0, 0)

            try:
                perc_symbol_idx = div_attr.find("%")
                perc_positive = int(div_attr[:perc_symbol_idx])
                div_attr = div_attr[perc_symbol_idx + 9:]
                review_count = int(div_attr[:div_attr.find(" ")].replace(",", ""))
                return (perc_positive, review_count)
            except Exception:
                raise HTMLError

        divs = user_reviews_div.find_all("div", class_="user_reviews_summary_row")

        try:
            match len(divs):
                case 0:
                    self.data = ((0, 0), (0, 0))
                case 1:
                    self.data = ((0, 0), parse_tooltip(divs[0].attrs["data-tooltip-html"]))
                case 2:
                    [reviews_recent, reviews_total] = [parse_tooltip(
                        div.attrs["data-tooltip-html"]) for div in divs[:2]]
                    self.data = (reviews_recent, reviews_total)
        except Exception as e:
            raise HTMLError(str(e))

    def save(self):
        """
        Saves the appid's tags to file
        Writes to `<DATA_DIR>/raw/<apifolder>/<appid>.json`.
        """

        # WARNING: the inner directory is also hardcoded in `ScraperController.set_files()`
        filepath = os.path.join(config.data_dir, "raw", "appreviews-scrape",
                                f"{self.appid:07}.json")

        with open(filepath, "w", encoding="UTF-8") as file:
            json.dump(self.data, file, indent=4)


class ScraperController:
    """
    TODO
    """

    def __init__(self):
        self.parse_args()
        self.set_files()
        self.load()

        self.run()

    def parse_args(self):
        desc = """
        TODO
        """
        epilog = """
        IMPORTANT: Setting SLEEP < 1.5 with NUMBER > 200 \
        requests will trigger an HTTP 429"
        """
        parser = ArgumentParser(
            prog="scripts.gather.steam.apptags",
            description=desc,
            formatter_class=RawDescriptionHelpFormatter,
            epilog=epilog
        )
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-n", "--number", type=int,
                           help="number of appids to automatically process using cached state")
        group.add_argument("-m", "--manual", nargs="+", type=int,
                           help="manually select single game appids")
        parser.add_argument("-s", "--sleep", type=float, default="1.5",
                            help="seconds to sleep in between requests (default: 1.5)")

        self.args = parser.parse_args()

    def set_files(self):
        """
        Loads state and logging files, configures logging, ensures save directory exists
        """

        self.STATE_FILEPATH = os.path.join(
            config.state_dir, "gather", "appreviews-scrape.json")
        os.makedirs(os.path.dirname(self.STATE_FILEPATH), exist_ok=True)

        self.LOGS_FILEPATH = os.path.join(config.logs_dir, "gather", "appreviews-scrape.log")
        os.makedirs(os.path.dirname(self.LOGS_FILEPATH), exist_ok=True)
        config.log(filepath=self.LOGS_FILEPATH)

        # WARNING: the inner directory is also hardcoded in `Scraper.save()`
        os.makedirs(os.path.join(config.data_dir, "raw", "appreviews-scrape"), exist_ok=True)

        self.APPLIST_GAMES_FILEPATH = os.path.join(
            config.data_dir, "processed", "indexes", "gameids.dat")

    def load(self):
        """
        Loads the selected applist slice
        """
        if self.args.manual:
            self.appids = self.args.manual
            return

        # automatic state management
        try:
            with open(self.STATE_FILEPATH, "r", encoding="UTF-8") as file:
                self.start_appid = int(json.load(file)["greatest_processed_appid"])
        except FileNotFoundError:
            with open(self.STATE_FILEPATH, "w", encoding="UTF-8") as file:
                # smallest real appid is 5, so this ensures starting at the start
                json.dump({"greatest_processed_appid": 1}, file, indent=4)
                self.load()
        except Exception as e:
            print(f"ERROR [automatic start AppID lookup]: {e}")
            quit()

        with open(self.APPLIST_GAMES_FILEPATH, "r", encoding="UTF-8") as file:
            appids = [int(row) for row in file]

        # get the selected slice of appids
        start_idx = bisect.bisect_left(appids, self.start_appid)
        if len(appids[start_idx:]) < self.args.number:
            self.appids = appids[start_idx:]
        else:
            self.appids = appids[start_idx:][:self.args.number]

    def run(self):
        if self.args.manual:
            print(f"\nGathering game tags for {len(self.appids)} manually selected applications:\n")
        else:
            print(f"\nGathering game tags for {
                  self.args.number} applications, starting at appid = {self.start_appid}:\n")

        # sentinel value (no application with appid=0 exists)
        last_successful_appid = 0
        for appid in tqdm(self.appids):
            time.sleep(self.args.sleep)
            try:
                Scraper(appid)

                logging.info(f"{appid:07} OK")
                last_successful_appid = appid
            except HTMLError as e:
                logging.warning(f"{appid:07} {e!r}")
                continue
            except Exception as e:
                message = f"{appid:07} {e!r}"
                if isinstance(e, RequestError) and e.status_code == 502:
                    logging.warning(f"{appid:07} {e!r}")
                    continue

                print(message)
                logging.critical(message)
                break

        # save the last successful appid to file
        if not self.args.manual and last_successful_appid != 0:
            with open(self.STATE_FILEPATH, "w", encoding="UTF-8") as file:
                obj = {"greatest_processed_appid": last_successful_appid}
                json.dump(obj, file, indent=4)


ScraperController()
