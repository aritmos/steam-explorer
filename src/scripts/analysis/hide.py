# Hide all code cells in notebooks within the jupyter-book compilation

import os
import json

from ...config import Config

root_dir = Config().root_dir

notebook_dir = os.path.join(root_dir, "src", "book", "notebooks")
filenames = os.listdir(notebook_dir)

for filename in filenames:
    if not filename.endswith(".ipynb"):
        continue

    filepath = os.path.join(notebook_dir, filename)

    with open(filepath, "r") as file:
        notebook_data = json.load(file)

    for cell in notebook_data["cells"]:
        if cell["cell_type"] != "code":
            continue

        if cell.get("metadata", {}).get("tags") is None:
            cell["metadata"]["tags"] = ["remove-cell"]

        elif "remove-cell" not in cell["metadata"]["tags"]:
            cell["metadata"]["tags"].append("remove-cell")

    with open(filepath, "w") as file:
        json.dump(notebook_data, file, indent=1)
