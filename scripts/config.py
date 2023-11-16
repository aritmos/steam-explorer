import json
import os

# === Configuration Module ===


class Config:
    def __init__(self):
        try:
            config_dir = os.path.dirname(os.path.abspath(__file__))
            config_file = os.path.join(config_dir, "config.json")
            with open(config_file, "r") as file:
                self.config = json.load(file)
        except Exception as e:
            print(f"Could not load config file: {e.__class__.__name__}. Aborting.")
            quit()

    def __getattr__(self, name) -> str:
        root = self.config["root_dir"]
        prefix_root = self.config["prefix_root"]

        if name in ["data_dir", "logs_dir", "state_dir"]:
            dir = self.config[name]
            return os.path.join(root, dir) if prefix_root else dir

        # no more config attributes, raise error
        raise AttributeError


# If called directly check config
if __name__ == "__main__":
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    config_filepath = os.path.join(scripts_dir, "config.json")

    print("Checking Config:")
    if os.path.exists(config_filepath):
        print("Config file found.")
    else:
        print("Creating default config file `scripts/config.json`."
              " See documentation for customising config options.")

        config = {
            "root_dir": os.path.dirname(scripts_dir),
            "prefix_root": True,
            "data_dir": "data",
            "logs_dir": ".logs",
            "state_dir": ".state"
        }

        with open(config_filepath, "w") as file:
            json.dump(config, file, indent=4)
