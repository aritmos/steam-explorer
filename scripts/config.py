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
        """
        Artificial attribute getters for directory paths.
        Exposes `.data_dir`, ".logs_dir", and ".state_dir".
        """
        # absolute/relative filepath logic
        root = self.config["root_dir"]
        prefix_root = self.config["prefix_root"]

        if name in ["data_dir", "logs_dir", "state_dir"]:
            dir = self.config["dirs"][name[:-4]]
            return os.path.join(root, dir) if prefix_root else dir

        raise AttributeError

    def log(self, filepath: str):
        """
        Sets local logger configuration; to be called within scripts.
        `filepath` is relative to the `self.logs_dir` directory.
        """
        logging.basicConfig(
            filename=filepath,
            encoding="UTF-8",
            style="{",
            format=self.config["logging"]["format"],
            level=logging.INFO
        )


# If called directly check config
if __name__ == "__main__":
    SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_FILEPATH = os.path.join(SCRIPTS_DIR, "config.json")

    print("Checking Config: ", end="")
    if os.path.exists(CONFIG_FILEPATH):
        print("Config file found.")
    else:
        print("No config file found.")
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
                "format": "{levelname:8} {message}"
            }
        }

        with open(CONFIG_FILEPATH, "w") as file:
            json.dump(config, file, indent=4)
