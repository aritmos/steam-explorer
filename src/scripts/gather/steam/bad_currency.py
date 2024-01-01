import os
import json
from ...config import Config
from tqdm import tqdm

config = Config()
appinfo_dir = os.path.join(config.data_dir, "raw", "appinfo")

filenames = os.listdir(appinfo_dir)

bad_currency_list = []

for filename in tqdm(filenames):
    app_id = filename[:-5]
    filepath = os.path.join(appinfo_dir, filename)

    with open(filepath, "r") as file:
        data = json.load(file)
        currency = data.get("price_overview", {}).get("initial")
        if currency is not None and currency != "EUR":
            bad_currency_list.append((app_id, currency))

save_filepath = os.path.join(config.data_dir, "processed", "bad_currency.csv")

with open(save_filepath, "w") as file:
    file.writelines((f'{app_id}, {currency}\n' for (app_id, currency) in bad_currency_list))
