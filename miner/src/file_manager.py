import json
import os
from datetime import datetime, timezone

DEFAULT_CHECKPOINT = {"page": 1}


def load_checkpoint(path):
    if not os.path.exists(path):
        return DEFAULT_CHECKPOINT.copy()

    try:
        with open(path, "r") as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, OSError):
        return DEFAULT_CHECKPOINT.copy()


def save_checkpoint(path, data):
    write_file(path, data)


def write_words(path, words, stats):
    snapshot = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "stats": stats,
        "words": words,
    }
    write_file(path, snapshot)


def write_file(path, data):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)

    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, path)
    except OSError as e:
        print(e)
