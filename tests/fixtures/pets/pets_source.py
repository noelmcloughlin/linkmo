"""A Python data source for the pets fixture: the records as plain dicts, and one question
of its own, adopted_by, which the exposure file adds to the Animal listing.

It sits at the host root, beside data/, as a module of the host's own would."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

KINDS = {"Animal": None, "Dog": "Dog", "Cat": "Cat"}


def _matches(record: dict[str, Any], name: str, value: Any) -> bool:
    field = record.get(name)
    if isinstance(field, list):
        return value in field
    return field == value or str(field) == str(value)


class PetsSource:
    def __init__(self) -> None:
        folder = Path(__file__).resolve().parent / "data"
        self.data = yaml.safe_load((folder / "Registry-001.yaml").read_text(encoding="utf-8"))

    def query(self, class_name: str, *, adopted_by: str | None = None, **filters: Any) -> list[dict[str, Any]]:
        if class_name == "Person":
            records = self.data["people"]
        elif class_name == "Shelter":
            records = self.data["shelters"]
        else:
            kind = KINDS[class_name]
            records = [a for a in self.data["animals"] if kind in (None, a.get("type"))]
        if adopted_by is not None:
            person = next((p for p in self.data["people"] if p["id"] == adopted_by), {})
            records = [a for a in records if a["id"] in person.get("adopted", [])]
        return [r for r in records if all(_matches(r, k, v) for k, v in filters.items())]
