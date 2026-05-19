import logging
import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".datagouv_config.json"


def save_config(environment: str, api_key: str | None):
    config = {"environment": environment}
    if api_key:
        config["api_key"] = api_key
    CONFIG_PATH.write_text(json.dumps(config))


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        logging.warning(
            "No config has been specified, defaulting to prod environment. "
            "Run `datagouv setup` to create a config file and get rid of this message."
        )
        return {}
    return json.loads(CONFIG_PATH.read_text())


def _delete_config():
    CONFIG_PATH.unlink()
