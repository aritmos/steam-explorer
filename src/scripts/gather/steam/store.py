if __name__ != "__main__":
    raise ImportError("This file must only be ran directly as a script")

# === IMPORTS ===

import bisect
import json
import os
import time
from enum import Enum, auto

from ....config import Config
from ..errors import ResponseFailure, RequestError

from argparse import ArgumentParser, RawDescriptionHelpFormatter
import logging
import requests
from tqdm import tqdm


# === ASSOCIATED OBJECTS ===

class StoreAPI(Enum):
    Info = auto()
    Reviews = auto()

    def __str__(self) -> str:
        match self:
            case StoreAPI.Info:
                return "info"
            case StoreAPI.Reviews:
                return "reviews"


# === SCRAPERS ===

config = Config()


class Scraper:
    """
    Scraper fom the steam store `appinfo` and `applist` APIs

    Constructor may raise:
    - `RequestError` if the request did not have a status code of 200.
    - `AppIdError` if the given appid did not return any information.
    """

    def __init__(self, api: StoreAPI, appid: int):
        self.api = api
        self.appid = appid

        self.request()
        self.get_json()
        self.check_response()
        self.check_success()
        self.get_data()
        self.save()

    def request(self):
        """
        Calls the API and stores the response in `self.response`
        """
        match self.api:
            case StoreAPI.Info:
                url = f"https://store.steampowered.com/api/appdetails?appids={
                    self.appid}&l=english&cc=es"
            case StoreAPI.Reviews:
                url = f"https://store.steampowered.com/appreviews/{
                    self.appid}?json=1&language=all&purchase_type=all"

        self.response = requests.get(url)

    def get_json(self):
        """
        Gets the JSON from the response and stores it in `self.json`.
        """
        self.json = self.response.json()

    def check_response(self):
        """
        Checks the inner response's (`self.response`) status code.
        Raises a `RequestError` if the status code does not equal 200.
        """
        status_code = self.response.status_code
        if status_code != 200:
            raise RequestError(status_code)

    def check_success(self):
        """
        Checks the inner response's JSON for the success flag.
        Raises a `AppIDError` if the JSON states the request was not successful.
        """
        match self.api:
            case StoreAPI.Info:
                success = self.json[str(self.appid)]["success"]
            case StoreAPI.Reviews:
                # The reviews API seems to always return a `success = true`,
                # so sucess is instead measured by the number of total reviews being
                # greater than zero.
                success = self.json["query_summary"]["total_reviews"] > 0

        if not success:
            raise ResponseFailure

    def get_data(self):
        """
        Extracts the main useful chunk of the json response into `self.data`.
        """
        match self.api:
            case StoreAPI.Info:
                self.data = self.json[str(self.appid)]["data"]
            case StoreAPI.Reviews:
                self.data = self.json["query_summary"]

    def save(self):
        """
        Saves the application info as JSON to file.
        Writes to `<DATA_DIR>/raw/<apifolder>/<appid>.json`.
        """

        # WARNING: the inner directory is also hardcoded in `ScraperController.set_files()`
        filepath = os.path.join(config.data_dir, "raw", f"app{self.api}", f"{self.appid:07}.json")

        with open(filepath, "w", encoding="UTF-8") as file:
            json.dump(self.data, file, indent=4)


class ScraperController:
    """
    TODO
    """

    def __init__(self):
        self.parse_args()
        self.set_files()
        self.set_start_appid()
        self.load()

        self.run()

    def parse_args(self):
        desc = """
    Calls the selected API and stores the relevant object block of the specified AppIDs to file.
    Automatically checks saved state from previous calls in order to select starting AppID.
    Uses `<DATA_DIR>/processed/indexes/appids.dat` to get an ordered list of AppIDs.
    Using the list, starting at the given AppID, processes `-n/--number` AppIDs.
    Continues on unsuccessful API calls (no store page exists); aborts on any error.
        """
        epilog = "IMPORTANT: Setting SLEEP < 1.5 with NUMBER > 200\
                requests will trigger an HTTP 429"
        parser = ArgumentParser(
            prog="scripts.gather.steam.store",
            description=desc,
            formatter_class=RawDescriptionHelpFormatter,
            epilog=epilog
        )
        parser.add_argument("-a", "--api", choices=["info", "reviews"],
                            required=True, help="[enum] selects which API to call")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-n", "--number", type=int,
                           help="[int] number of appids to process")
        group.add_argument("-m", "--manual", type=int, nargs="+",
                           help="[int/list(int)] manually select appids")
        parser.add_argument("-s", "--sleep", type=float, default="1.5",
                            help="[float] seconds to sleep in between requests (default: 1.5)")

        self.args = parser.parse_args()

    def set_files(self):
        """
        Loads state and logging files, configures logging, ensures save directory exists
        """

        self.STATE_FILEPATH = os.path.join(
            config.state_dir, "gather", f"app{self.args.api}.json")
        os.makedirs(os.path.dirname(self.STATE_FILEPATH), exist_ok=True)

        self.LOGS_FILEPATH = os.path.join(config.logs_dir, "gather", f"app{self.args.api}.log")
        os.makedirs(os.path.dirname(self.LOGS_FILEPATH), exist_ok=True)
        config.log(filepath=self.LOGS_FILEPATH)

        # WARNING: the inner directory is also hardcoded in `Scraper.save()`
        os.makedirs(os.path.join(config.data_dir, "raw", f"app{self.args.api}"), exist_ok=True)

    def set_start_appid(self):
        # automatic state management
        try:
            with open(self.STATE_FILEPATH, "r", encoding="UTF-8") as file:
                self.start_appid = int(json.load(file)["greatest_processed_appid"])
        except FileNotFoundError:
            with open(self.STATE_FILEPATH, "w", encoding="UTF-8") as file:
                # smallest real appid is 5, so this ensures starting at the start
                json.dump({"greatest_processed_appid": 1}, file)
                self.set_start_appid()
        except Exception as e:
            print(f"ERROR [automatic start AppID lookup]: {e}")
            quit()

    def load(self):
        """
        Loads the selected applist slice
        """
        if self.args.manual:
            self.appids = self.args.manual
            return

        # else use automatic state cache
        applist_filepath = os.path.join(
            config.data_dir, "processed", "indexes", "appids.dat")
        with open(applist_filepath, "r", encoding="UTF-8") as file:
            appids = [int(row) for row in file]

        # get the selected slice of appids
        start_idx = bisect.bisect_left(appids, self.start_appid)
        if len(appids[start_idx:]) < self.args.number:
            self.appids = appids[start_idx:]
        else:
            self.appids = appids[start_idx:][:self.args.number]

    def run(self):
        if self.args.manual:
            print(f"\nGathering app-{self.args.api} for\
                    {len(self.args.manual)} manually selected applications:\n")
        else:
            print(f"\nGathering app-{self.args.api} for {
                self.args.number} applications, starting at appid = {self.start_appid}:\n")

        def parse_api(api: str) -> StoreAPI:
            match api:
                case "info":
                    return StoreAPI.Info
                case "reviews":
                    return StoreAPI.Reviews
                case _:
                    # Unreachable
                    raise ValueError

        api = parse_api(self.args.api)

        # sentinel value (no application with appid=0 exists)
        last_successful_appid = 0
        for appid in tqdm(self.appids):
            time.sleep(self.args.sleep)
            try:
                Scraper(api, appid)

                logging.info(f"{appid:07} OK")
                last_successful_appid = appid
            except ResponseFailure as e:
                logging.warning(f"{appid:07} {e!r}")
                continue
            except Exception as e:
                message = f"{appid:07} {e!r}"
                print(message)
                logging.critical(message)
                break

        # save the last successful appid to file
        if last_successful_appid != 0:
            with open(self.STATE_FILEPATH, "w", encoding="UTF-8") as file:
                obj = {"greatest_processed_appid": last_successful_appid}
                json.dump(obj, file, indent=4)


ScraperController()
