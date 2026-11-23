"""JSON seed data for local development databases. Never load into prod."""

import json
from pathlib import Path

SEED_DATA_DIR = Path(__file__).resolve().parent


def load_seed_data(name: str):
    with (SEED_DATA_DIR / f"{name}.json").open(encoding="utf-8") as file:
        return json.load(file)
