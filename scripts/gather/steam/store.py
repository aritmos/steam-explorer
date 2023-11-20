import bisect
import json
import os
import time
from enum import Enum

from ...config import Config

from argparse import ArgumentParser, RawDescriptionHelpFormatter, Namespace
import logging
import requests
from tqdm import tqdm


class AppIdError(Exception):
    """
    AppID does not have an associated store page
    """
    pass


class RequestError(Exception):
    """
    API call did not return an HTTP 200
    """

    def __init__(self, status_code: int):
        self.status_code = status_code


class StoreAPI(Enum):
    Info = None
    Reviews = None

    def __str__(self):
        match self:
            case StoreAPI.Info:
                return "info"
            case StoreAPI.Reviews:
                return "reviews"


class StoreResponse:
    """
    Responses from the steam store API

    Constructor may raise:
    - `RequestError` if the request did not have a status code of 200.
    - `AppIdError` if the given appid did not return any information.
    """
    config = Config()

    def call_api(self):
        """
        Calls the API and stores the response in `self.response`
        """
        match self.api:
            case StoreAPI.Info:
                url = f"https://store.steampowered.com/api/appdetails?appids={self.appid}&l=english"
            case StoreAPI.Reviews:
                url = f"https://store.steampowered.com/appreviews/{self.appid}?json=1&language=all"

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
            raise AppIdError

    def get_data(self):
        """
        Extracts the main useful chunk of the json response into `self.data`.
        """
        match self.api:
            case StoreAPI.Info:
                self.data = self.json[str(self.appid)]["data"]
            case StoreAPI.Reviews:
                self.data = self.json["query_summary"]

    # Testing out this incremental instantiation technique using "Python's dynamicness".
    # The supporting methods would be private in other languages, as they only aid in
    # the constructing of the class instance
    def __init__(self, api: StoreAPI, appid: int):
        self.api = api
        self.appid = appid
        self.call_api()
        self.get_json()

        self.check_response()
        self.check_success()

        self.get_data()

    def save(self):
        """
        Saves the application info as JSON to file.
        Writes to `<DATA_DIR>/raw/<apifolder>/<appid>.json`.
        """
        filepath = os.path.join(config.data_dir, "raw", f"app{self.api}", f"{self.appid:07}.json")

        with open(filepath, "w", encoding="UTF-8") as file:
            json.dump(self.data, file, indent=4)

    @staticmethod
    def get_appids(applist_filepath: str, start_appid: int, count: int) -> list[int]:
        with open(applist_filepath, "r", encoding="UTF-8") as file:
            appids = [int(row) for row in file]

        # get the selected slice of appids
        start_idx = bisect.bisect_left(appids, start_appid)
        if len(appids[start_idx:]) < count:
            return appids[start_idx:]
        else:
            return appids[start_idx: start_idx + count]

    @staticmethod
    def create_and_store_multi(
        api: StoreAPI,
        appids: list[int],
        timeout_sec: float
    ):
        """
        Calls the specified API on each of the given AppIDs and stores the data to file
        (`<DATA_DIR>/raw/<api>/<appid>.json`). Waits `timeout_sec` between requests.
        """

        state_filepath = os.path.join(config.state_dir, f"app{api}.json")
        log_filepath = os.path.join(config.logs_dir, f"app{api}-gather.log")
        logging.basicConfig(filename=log_filepath, encoding="UTF-8", level=logging.INFO)

        last_successful_appid = 0  # sentinel value (no application with appid=0 exists)
        for appid in tqdm(appids):
            time.sleep(timeout_sec)
            try:
                StoreResponse(api, appid).save()

                logging.info(f"{appid:07} OK")
                last_successful_appid = appid
            except AppIdError as e:
                logging.warning(f"{appid:07} {e.__class__.__name__}")
                continue
            except Exception as e:
                if isinstance(e, RequestError):
                    message = f"{appid: 07} HTTPError {e.status_code}"
                else:
                    message = f"{appid: 07} Error: {e}"
                print(message + ". Aborting.")
                logging.critical(message)
                break

        # save the last successful appid to file
        if last_successful_appid != 0:
            with open(state_filepath, "w", encoding="UTF-8") as file:
                obj = {"greatest_processed_appid": last_successful_appid}
                json.dump(obj, file, indent=4)

# Main program


def parse_args() -> Namespace:
    desc = """
Calls the selected API and stores the relevant object block of the specified AppIDs to file.
Automatically checks saved state from previous calls in order to select starting AppID.
Uses `<DATA_DIR>/raw/applist/applist.dat` to get an ordered list of AppIDs.
Using the list, starting at the given AppID, processes `-n/--number` AppIDs.
Continues on unsuccessful API calls (no store page exists); aborts on any error.
    """
    epilog = "IMPORTANT: Setting SLEEP < 1.5 with NUMBER > 200 requests will trigger an HTTP 429"
    parser = ArgumentParser(
        prog="scripts.gather.steam.store",
        description=desc,
        formatter_class=RawDescriptionHelpFormatter,
        epilog=epilog
    )
    parser.add_argument("-a", "--api", choices=["info", "reviews"],
                        required=True, help="[enum] selects which API to call")
    parser.add_argument("-n", "--number", type=int, required=True,
                        help="[int] number of appids to process")
    parser.add_argument("-s", "--sleep", type=float, default="1.5",
                        help="[float] seconds to sleep in between requests (default: 1.5)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-m", "--manual", type=int, help="[int] manually select start appid")

    return parser.parse_args()


def parse_api(api: str) -> StoreAPI:
    """
    Parses string version of API into enum.
    Raises ValueError if no such API exists.
    """
    match api:
        case "info":
            return StoreAPI.Info
        case "reviews":
            return StoreAPI.Reviews
        case _:
            raise ValueError


def set_start_appid(args: Namespace) -> int:
    """
    Sets the start AppID using the passed in arguments.
    Quits the script if it encounters an error.

    Requires a `config: Config` to exist in the caller's scope (if mode is set to automatic)
    """
    if args.manual:
        return args.manual

    # automatic state management
    state_file = os.path.join(config.state_dir, f"app{args.api}.json")
    try:
        with open(state_file, "r", encoding="UTF-8") as file:
            return int(json.load(file)["greatest_processed_appid"])
    except FileNotFoundError:
        with open(state_file, "w", encoding="UTF-8") as file:
            # smallest appid is 5, so this sets the automatic mode to begin at the start
            json.dump({"greatest_processed_appid": 1}, file)
            return set_start_appid(args)
    except Exception as e:
        print(f"Error using automatic start AppID lookup: {e.__class__.__name__}")
        quit()

# -- MAIN SCRIPT --


config = Config()
args = parse_args()
start_appid = set_start_appid(args)

print(f"\nGathering AppInfo for {
    args.number} applications, starting at appid = {start_appid}:\n")

APPLIST_FILE = os.path.join(config.data_dir, "raw", "applist", "applist.dat")
appids = StoreResponse.get_appids(APPLIST_FILE, start_appid, args.number)
api = parse_api(args.api)
StoreResponse.create_and_store_multi(api, appids, args.sleep)
