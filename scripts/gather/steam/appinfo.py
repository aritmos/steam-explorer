import json
import bisect
import time

import logging
from tqdm import tqdm
import requests
from argparse import ArgumentParser, RawDescriptionHelpFormatter, Namespace


class AppIdError(Exception):
    pass


class RequestError(Exception):
    def __init__(self, status_code: int):
        self.status_code = status_code


class AppInfoRaw:
    """
    Stores the information of a given application

    Constructor may raise:
    - `RequestError` if the request did not have a status code of 200.
    - `AppIdError` if the given appid did not return any information.
    """

    @staticmethod
    def api_url(appid: int) -> str:
        """
        URL for Steam's `appdetails` API call
        """
        return f"https://store.steampowered.com/api/appdetails?appids={appid}&l=english"

    def __init__(self, appid: int):
        r = requests.get(self.api_url(appid))

        if r.status_code != 200:
            raise RequestError(r.status_code)

        appinfo = r.json()

        success = appinfo[str(appid)]["success"]
        if not success:
            raise AppIdError

        self.appid = appid
        self.data = appinfo[str(appid)]["data"]

    def save(self, filepath: str | None = None):
        """
        Saves the application info as JSON in the given file location.
        Defaults to `data/raw/appinfo/<appid>.json` if not specified (or passed an empty string).
        """

        filepath = filepath or f"data/raw/appinfo/{self.appid:07}.json"
        with open(filepath, "w", encoding="UTF-8") as file:
            json.dump(self.data, file, indent=4)


def save_appinfo_list(appids: list[int]):
    """
    Iterates through the list creating `AppInfoRaw`s and saving them to the
    default file location. Handles any exceptions in constructing `AppInfoRaw`s
    by skipping to the next `appid`.
    """


def save_appinfo_batched(
        batch_size: int,
        start_appid: int,
        timeout_sec: float):
    """
    Iterates through the specified range of `appid`s in the raw `applist.csv` file,
    then calls `save_appinfo_list` to generate and store the respective appinfo data.
    """

    applist_filepath = APPLIST_FILE
    with open(applist_filepath, "r", encoding="UTF-8") as file:
        appids = [int(row) for row in file]

    # get the selected slice of appids
    idx = bisect.bisect_left(appids, start_appid)
    if len(appids[idx:]) < batch_size:
        appid_batch = appids[idx:]
    else:
        appid_batch = appids[idx: idx + batch_size]

    # request and store appinfo
    last_successful_appid = 0
    for appid in tqdm(appid_batch):
        try:
            time.sleep(timeout_sec)
            AppInfoRaw(appid).save()
            logging.info(f"{appid:07} OK")
            last_successful_appid = appid
        except RequestError as e:
            # too many requests error, abort
            if e.status_code == 429:
                message = f"{appid:07} HTTPError {e.status_code} (Too Many Requests) ABORTING"
                logging.critical(message)
                print("AppID ", message)
                break
            else:
                logging.error(f"{appid:07} HTTPError {e.status_code}")
        except Exception as e:
            logging.warning(f"{appid:07} {e.__class__.__name__}")
            continue

        # save the last successful appid to file
        if last_successful_appid != 0:
            with open(STATE_FILE, "w", encoding="UTF-8") as file:
                obj = {"greatest_processed_appid": last_successful_appid}
                json.dump(obj, file, indent=4)


# Main program
def parse_args() -> Namespace:
    desc = """Requests and stores the application info of the specified AppIDs.
    Uses `data/raw/applist/applist.csv` to get an ordered list of AppIDs.
    Begins at the AppID given by the specified mode and processes `batch_size` AppIDs.
    Aborts if a request returns an HTTP 429 (Too many requests)"""

    parser = ArgumentParser(description=desc, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("-n", "--batch-size", type=int, required=True,
                        help="[int] batch size (number of appids to process)")
    parser.add_argument("-s", "--sleep", type=float, default="0.1",
                        help="[float] seconds to sleep in between requests (default: 0.1)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-a", "--automatic", action="store_true",
                       help="Automatic start-appid lookup using a state file")
    group.add_argument("-m", "--manual", type=int, metavar="APPID", help="[int] start-appid")

    return parser.parse_args()


def set_start_appid(args: Namespace) -> int:
    """
    Sets the start AppID using the passed in arguments.
    Quits the script if it encounters an error.
    """
    if args.automatic:
        try:
            with open(STATE_FILE, "r", encoding="UTF-8") as file:
                return int(json.load(file)["greatest_processed_appid"])
        except FileNotFoundError:
            with open(STATE_FILE, "w", encoding="UTF-8") as file:
                # smallest appid is 5, so this sets the automatic mode to begin at the start
                json.dump({"greatest_processed_appid": 1}, file)
                return set_start_appid(args)
        except Exception as e:
            print(f"Error using automatic start AppID lookup: {e.__class__.__name__}")
            quit()
    else:  # `args.manual` is guaranteed to exist in this case by the arg check
        return args.manual

# -- MAIN SCRIPT --


APPLIST_FILE = "data/raw/applist/applist.txt"
STATE_FILE = ".state/appinfo.json"
LOG_FILE = ".logs/appinfo-gather.txt"

args = parse_args()
start_appid = set_start_appid(args)

print(f"\nGathering AppInfo for {
      args.batch_size} applications, starting at appid = {start_appid}:\n")

logging.basicConfig(filename=LOG_FILE, encoding="UTF-8", level=logging.INFO)

save_appinfo_batched(args.batch_size, start_appid, args.sleep)
