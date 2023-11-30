import json
import os

from ..config import Config

from tqdm import tqdm

# Errors


class AppTypeError(Exception):
    """
    App is not "game", "dlc", or "demo"
    """
    pass


class FileError(Exception):
    """
    Necessary file does not exist
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.message = f"Necessary file {self.filepath} does not exist"

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        name = self.__class__.__name__
        return f"{name}: {self.message}" if self.message else name

# Processors


config = Config()


class Processor:
    def __init__(self, appid: int):
        self.appid = appid
        self.load()
        self.process()
        self.save()

    def load(self):
        appinfo_filepath = os.path.join(config.data_dir, "raw", "appinfo", f"{self.appid:07}.json")
        with open(appinfo_filepath, "r", encoding="utf-8") as file:
            self.json = json.load(file)

    def process(self):
        self.data = None
        apptype = self.json["type"]
        if apptype not in ["game", "dlc", "demo"]:
            raise TypeError

        self.data = {
            "id": self.appid,
            "kind": apptype,
            "name": self.json["name"],
            "supports_windows": self.json["platforms"]["windows"],
            "supports_mac": self.json["platforms"]["mac"],
            "supports_linux": self.json["platforms"]["linux"],
            "price": self.json.get("price_overview", {}).get("initial", 0),
            "metacritic_score": self.json.get("metacritic", {}).get("score"),
            "reviews_total": None,
            "reviews_positive": None,
            "age_check": self.json["required_age"],
            "release_date": self.json["release_date"].get("date", None),
            "has_drm": False if self.json.get("drm_notice") is None else True,
            "has_ext_acc": False if self.json.get("ext_user_account_notice") is None else True,
            "achievements": self.json.get("achievements", {}).get("total", 0)
        }

    def save(self):
        filepath = os.path.join(config.data_dir, "processed", "appinfo", f"{self.appid:07}.json")
        with open(filepath, "w") as file:
            json.dump(self.data, file, indent=4)


class ProcessorController:
    def __init__(self):
        self.set_files()
        self.run()

    def set_files(self):
        self.APPINFO_DIR = os.path.join(config.data_dir, "raw", "appinfo")
        self.PROCESSED_DIR = os.path.join(config.data_dir, "processed", "appinfo")
        os.makedirs(self.PROCESSED_DIR, exist_ok=True)

        self.appids = [int(appid[:-5]) for appid in os.listdir(self.APPINFO_DIR)]

    def run(self):
        for appid in tqdm(self.appids):
            try:
                Processor(appid)
            except TypeError:
                continue


ProcessorController()
