import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".datagouv_config.json"


def save_config(environment: str, api_key: str):
    CONFIG_PATH.write_text(json.dumps({"api_key": api_key, "environment": environment}))


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise RuntimeError("Please run `datagouv setup` to set up the config.")
    return json.loads(CONFIG_PATH.read_text())


def _delete_config():
    CONFIG_PATH.unlink()
