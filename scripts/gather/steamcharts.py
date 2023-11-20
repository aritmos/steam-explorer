import json
import os
import bisect
import time

from ..config import Config

import requests
from bs4 import BeautifulSoup
from argparse import ArgumentParser, RawDescriptionHelpFormatter, Namespace
from tqdm import tqdm
import logging


class RequestError(Exception):
    """
    Request did not return an HTTP 200
    """

    def __init__(self, status_code: int):
        self.status_code = status_code


class TableError(Exception):
    pass


class SteamCharts:
    """
    Handler for steamcharts websraping
    """

    @staticmethod
    def get_appids(start_appid: int, count: int) -> list[int]:
        filepath = os.path.join(config.data_dir, "raw", "applist", "applist-games.dat")
        with open(filepath, "r") as file:
            appids = [int(line) for line in file]

        start_idx = bisect.bisect_left(appids, start_appid)
        if len(appids[start_idx:]) < count:
            return appids[start_idx:]
        else:
            return appids[start_idx: start_idx + count]

    def load(self):
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

    def get_table(self):
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
        Writes to `<DATA_DIR>/raw/playercounts/<appid>.csv`.
        """
        filepath = os.path.join(config.data_dir, "raw", "playercounts", f"{self.appid:07}.csv")

        with open(filepath, "w", encoding="UTF-8") as file:
            file.write("date,avg_playercount,peak_playercount\n")
            file.writelines(self.table)

    def __init__(self, appid: int):
        self.appid = appid
        self.load()
        self.check_response()
        self.get_table()
        self.save()

    @staticmethod
    def process_multi(appids: list[int], timeout_sec: float):
        """
        Extracts the playercount data for each game in the given appids and stores the data to file
        (`<DATA_DIR>/raw/playercounts/<appid>.csv`). Waits `timeout_sec` between requests.
        """

        state_filepath = os.path.join(config.state_dir, "steamcharts.json")
        log_filepath = os.path.join(config.logs_dir, "steamchart-gather.log")
        logging.basicConfig(filename=log_filepath, encoding="UTF-8", level=logging.INFO)

        # sentinel value (no application with appid=0 exists)
        last_successful_appid = 0
        for appid in tqdm(appids):
            time.sleep(timeout_sec)
            try:
                SteamCharts(appid).save()

                logging.info(f"{appid:07} OK")
                last_successful_appid = appid
            except Exception as e:
                if isinstance(e, RequestError):
                    message = f"{appid: 07} HTTPError {e.status_code}"
                    if e.status_code == 500:  # only allowed error
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
            with open(state_filepath, "w", encoding="UTF-8") as file:
                obj = {"greatest_processed_appid": last_successful_appid}
                json.dump(obj, file, indent=4)


def update_game_applist():
    """
    Updates the list of games in `<DATA_DIR>/raw/applist/applist-games.dat`
    by going through gathered files in `<DATA_DIR>/raw/appinfo` and checking
    the "type" field.
    """
    appinfo_dir = os.path.join(config.data_dir, "raw", "appinfo")
    appinfo_filenames = os.listdir(appinfo_dir)
    appinfo_filenames.sort()

    game_appids = []

    print("Iterating through existing appinfo files to look for game appids:")
    for appinfo_filename in tqdm(appinfo_filenames):
        appinfo_filepath = os.path.join(appinfo_dir, appinfo_filename)
        with open(appinfo_filepath, "r") as file:
            appinfo = json.load(file)
            if appinfo["type"] == "game":
                appid = appinfo["steam_appid"]
                game_appids.append(str(appid))

    applist_games_filepath = os.path.join(
        config.data_dir, "raw", "applist", "applist-games.dat")
    with open(applist_games_filepath, "w") as file:
        print("Storing game appids into file:")
        for appid in tqdm(game_appids):
            file.write(str(appid) + "\n")


# -- Main Script --

def parse_args() -> Namespace:
    # TODO: add proper description
    desc = """
    Extract playercount data from steamcharts site via scraping.
    """
    parser = ArgumentParser(prog="scripts.gather.steamcharts", description=desc)
    parser.add_argument("-u", "--update", action="store_true",
                        help="Update the game appid list")
    parser.add_argument("-n", "--number", type=int, required=True,
                        help="[int] number of appids to process")
    parser.add_argument("-s", "--sleep", type=float, default="3.0",
                        help="[float] seconds to sleep in between requests (default: 3.0)")
    parser.add_argument("-m", "--manual", type=int, help="[int] manually select start appid")

    return parser.parse_args()


def set_start_appid(args: Namespace) -> int:
    """
    Sets the start AppID using the passed in arguments.
    Quits the script if it encounters an error.

    Requires a `config: Config` to exist in the caller's scope (if mode is set to automatic)
    """
    if args.manual:
        return args.manual

    # automatic state management
    state_file = os.path.join(config.state_dir, "game_playercounts.json")
    try:
        with open(state_file, "r", encoding="UTF-8") as file:

            return int(json.load(file)["greatest_processed_appid"])
    except FileNotFoundError:
        with open(state_file, "w", encoding="UTF-8") as file:
            # smallest real appid is 5
            json.dump({"greatest_processed_appid": 1}, file)
            return set_start_appid(args)
    except Exception as e:
        print(f"Error using automatic start AppID lookup: {e}")
        quit()


if __name__ == "__main__":
    config = Config()
    args = parse_args()

    if args.update:
        update_game_applist()

    start_appid = set_start_appid(args)
    appids = SteamCharts.get_appids(start_appid, args.number)

    print(f"\nGathering playercount records for {
        args.number} games, starting at appid = {start_appid}:\n")

    SteamCharts.process_multi(appids, args.sleep)
