if __name__ != "__main__":
    raise ImportError("This file can only be ran directly as a script")

# === IMPORTS ===


import os
import time

from ....config import Config
from ..errors import RequestError, HTMLError

from argparse import ArgumentParser
import logging
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup, Tag


# === SCRAPERS ===


config = Config()

# kept in global scope so `makedirs` only executes once
SAVE_DIR = os.path.join(config.data_dir, "raw", "itad", "pricehistory")
os.makedirs(SAVE_DIR, exist_ok=True)


class Scraper:
    """
    Handler for isthereanydeal.com price history scraping
    """

    def __init__(self, plain: str, id: int):
        self.plain = plain
        self.id = id

        self.request()
        self.check_response()
        self.get_data()
        self.save()

    def request(self):
        url = f"https://isthereanydeal.com/game/{self.plain}/history/?shop[]=steam"
        self.response = requests.get(url)

    def check_response(self):
        status_code = self.response.status_code
        if status_code != 200:
            raise RequestError(status_code)

    def get_data(self):
        soup = BeautifulSoup(self.response.text, 'html.parser')
        price_history_content = soup.find("div", id="historyLogContent")

        if not isinstance(price_history_content, Tag):
            raise HTMLError

        self.data = ["datetime,full_price,curr_price\n"]

        def format_price(p: str) -> str:
            """
            Simplifies price formatting: 24,99€ => 2499
            """
            return p.removesuffix("€").replace(",", "")

        # this is a sloppy way to get the entries, but i can't get `.children` to work
        for entry in price_history_content.find_all("div", attrs={"data-shop": "steam"}):
            datetime = entry.find("span").contents[0].strip()
            full_price: str = format_price(entry.find("span", class_="lg2__price").text)
            curr_price: str = format_price(entry.find("span", class_="lg2__price--new").text)

            self.data.append(f"{datetime},{full_price},{curr_price}\n")

    def save(self):
        filepath = os.path.join(SAVE_DIR, f"{self.id:07}.csv")
        with open(filepath, "w") as file:
            file.writelines(self.data)


class ScraperController:
    def __init__(self):
        self.parse_args()
        self.set_files()
        self.load()
        self.run()

    def parse_args(self):
        desc = """
        Extract application price history from isthereanydeal.com via scraping.
        """
        parser = ArgumentParser(description=desc, prog="scripts.gather.itad.pricehistory")
        parser.add_argument("-n", "--number", type=int, required=True,
                            help="[int] Number of apps to process")
        parser.add_argument("-s", "--sleep", type=float, default=2.0,
                            help="[float] seconds to sleep in between requests (default: 2.0)")

        self.args = parser.parse_args()

    def set_files(self):
        """
        Sets the input, state, and logging files (as well as logging configuration)
        """
        self.STATE_FILEPATH = os.path.join(config.state_dir, "gather", "itad.dat")
        os.makedirs(os.path.dirname(self.STATE_FILEPATH), exist_ok=True)

        self.LOGGING_FILEPATH = os.path.join(config.logs_dir, "gather", "itad.log")
        os.makedirs(os.path.dirname(self.LOGGING_FILEPATH), exist_ok=True)
        config.log(filepath=self.LOGGING_FILEPATH)

        self.LIST_FILEPATH = os.path.join(config.data_dir, "raw", "itad", "index.csv")

    def load(self):
        """
        Loads the state file and applist
        """
        with open(self.STATE_FILEPATH, "r") as file:
            self.done = set([line.strip() for line in file.readlines()])

        self.applist = []

        with open(self.LIST_FILEPATH, "r") as file:
            for line in file.readlines()[1:]:
                plain, steam_id = line.strip().split(",")
                kind, id = steam_id.split("/")

                if kind not in ["bundle", "sub"] and plain not in self.done:
                    self.applist.append((plain.strip(), int(id)))

    def run(self):
        with open(self.STATE_FILEPATH, "a") as file:
            applist_iter = iter(self.applist)
            for _ in tqdm(range(self.args.number)):
                time.sleep(self.args.sleep)
                vals = next(applist_iter)
                if vals is None:
                    print("Exhausted application list. Consider updating it.")
                    quit()
                (plain, id) = vals
                try:
                    Scraper(plain, id)
                    logging.info(f"{id:07} OK")
                except Exception as e:
                    if isinstance(e, RequestError):
                        message = f"{id:07} HTTPError {e.status_code}"
                        # Only non-critical error
                        if e.status_code == 500:
                            logging.warning(message)
                        else:
                            logging.critical(message)
                            print(message + ". Aborting.")
                            break
                    else:
                        message = f"{id:07} Error: {e}"
                        print(message + ". Aborting.")
                        logging.critical(message)
                        break

                file.write(plain + "\n")


ScraperController()
