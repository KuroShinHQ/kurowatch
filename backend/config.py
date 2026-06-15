import json
import os

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def get_config() -> dict:
    if os.path.exists(_CONFIG_PATH):
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}
