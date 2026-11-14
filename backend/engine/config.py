"""Încărcare configurare: contracts/weights.yaml (tabelul unic de ponderi, proprietar B)."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
WEIGHTS_FILE = ROOT / "contracts" / "weights.yaml"


def load_weights(path: Path = WEIGHTS_FILE) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
