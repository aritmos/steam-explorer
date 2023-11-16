# steam-insights
 Exploratory data analysis of games on the Steam platform

## Installation

- Clone the repo
```
> git clone https://www.github.com/aritmos/steam-insights
> cd steam-insights
```
- Install external libraries
```
> pip install -r requirements.txt
```

## Data Gathering and Processing

Python scripts for data aggregation, preprocessing, processing, and database manipulation are stored in the `scripts` directory.
The scripts make use of a configuration file that must be initialised upon cloning the repo.
```
> py -m scripts.config
```

This configuration file specifies where the gathered data is to be saved or read from. It also specifies the directories for logging and script state. It is backed by the `scripts/config.json` file, which can be freely modified by the user, by default it has the values:
```json
{
    "root_dir": "<project-root>",
    "prefix_root": true,
    "data_dir": "data",
    "logs_dir": ".logs",
    "state_dir": ".state"
}
```
- If the `prefix_root` is set to `true`, then the `data_dir`, `logs_dir`, and `state_dir` paths are taken to be relative to the `root_dir` directory. If `prefix_root` is set to `false` then the directories are taken to be absolute paths, and `root_dir` is not used. This allows for the directories to be stored in different locations if wanted.

All the scripts are modules that make use of this configuration file, writing to files in the logs directory, using states stored in the states directory and manipulating data in the data directory. **Scripts can only be invoked from the project root**. Their functionality and required arguments can be accessed by passing in `-h` or `--help`:
```
> py -m scripts.gather.steam.appinfo -h
usage: appinfo.py [-h] -n BATCH_SIZE [-s SLEEP] [-a | -m APPID]

Requests and stores the application info of the specified AppIDs.
Uses `<DATA_DIR>/raw/applist/applist.dat` to get an ordered list of AppIDs.
Begins at the AppID given by the specified mode and processes `batch_size` AppIDs.
Aborts if a request returns an HTTP 429 (Too many requests)

options:
  -h, --help            show this help message and exit
  -n BATCH_SIZE, --batch-size BATCH_SIZE
                        [int] batch size (number of appids to process)
  -s SLEEP, --sleep SLEEP
                        [float] seconds to sleep in between requests (default: 0.1)
  -a, --automatic       Automatic start-appid lookup using a state file
  -m APPID, --manual APPID
                        [int] start-appid
```
