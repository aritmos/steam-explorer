import json
import os
import logging

# === Configuration Module ===


class Config:
    def __init__(self):
        try:
            CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
            CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
            with open(CONFIG_FILE, "r") as file:
                self.config = json.load(file)
        except Exception as e:
            print(f"Could not load config file: {e}. Aborting.")
            quit()

    def __getattr__(self, name) -> str:
        # absolute/relative filepath logic
        root = self.config["root_dir"]
        prefix_root = self.config["prefix_root"]

        if name in ["data_dir", "logs_dir", "state_dir"]:
            dir = self.config["dirs"][name[:-4]]
            return os.path.join(root, dir) if prefix_root else dir

        raise AttributeError

    @staticmethod
    def log(filepath: str):
        logging.basicConfig(
            filename=filepath,
            encoding="UTF-8",
            style="{",
            format="{levelname:8} {message}",
            level=logging.INFO
        )


# If called directly check config
if __name__ == "__main__":
    SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_FILEPATH = os.path.join(SCRIPTS_DIR, "config.json")

    print("Checking Config:")
    if os.path.exists(CONFIG_FILEPATH):
        print("Config file found.")
    else:
        print("Creating default config file `scripts/config.json`. "
              "See documentation for customising config options.")

        config = {
            "root_dir": os.path.dirname(SCRIPTS_DIR),
            "prefix_root": True,
            "dirs": {
                "data": "data",
                "logs": ".logs",
                "state": ".state",
            },
            "logging": {
                "version": 1,
                "formatters": {
                    "format": "%(message)s"
                }
            }
        }

        with open(CONFIG_FILEPATH, "w") as file:
            json.dump(config, file, indent=4)
