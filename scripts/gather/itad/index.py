import requests
from bs4 import BeautifulSoup
import time
import os

from ...config import Config


url = "https://isthereanydeal.com/ajax/data/lazy.deals.php"


payload = {
    "offset": "0",
    "limit": "1000",
    "filter": "steam",
    "options": "",
    "by": "trending:desc",
    "seen": 1700663982,
    "id": 1700687162,
    "timestamp": 1700687527,
}


csv_lines = ["plain,steam_id\n"]
CHUNK_SIZE = 1000
SLEEP_TIME = 1.0

print("Getting database index: ")

offset = 0
done = False
while not done:
    time.sleep(SLEEP_TIME)

    payload = {
        "offset": offset,
        "limit": CHUNK_SIZE,
        "filter": "steam",
        "options": "",
        "by": "trending:desc",
        "seen": 1700663982,
        "id": 1700687162,
        "timestamp": 1700688015,
    }

    response = requests.post(url, data=payload)

    if response.status_code != 200:
        print(f"HTTPError {response.status_code}")
        break
    response_json = response.json()
    if response_json["status"] != "success":
        print("POST Query failed")
        print(response.text)
        break

    done = response_json["data"]["done"]
    next_offset = response_json["data"]["offset"]
    message = response_json["message"]

    offset = next_offset

    soup = BeautifulSoup(response_json["data"]["html"], "html.parser")

    counter = 0
    for game in soup.find_all("div", class_="game"):
        counter += 1

        plain = game["data-plain"]
        steam_id = game["data-steamid"]
        csv_lines.append(f"{plain},{steam_id}\n")

    print(f"Processed range {offset:04}-{next_offset:04}: {counter} games; finished? {done}")

config = Config()

filepath = os.path.join(config.data_dir, "raw", "itad", "index.csv")
with open(filepath, "w") as file:
    file.writelines(csv_lines)
