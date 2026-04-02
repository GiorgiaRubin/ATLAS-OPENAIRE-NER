# Config loader, to load settings from a YAML file

from dataclasses import dataclass
from pathlib import Path
import yaml


@dataclass
class Config:
    atlas: dict
    openaire: dict
    nlp: dict
    policy: dict
    report: dict
    cache: dict


def load_config(path: str) -> Config:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {p}")

    with p.open('r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    return Config(**data)
