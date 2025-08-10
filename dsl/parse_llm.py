from __future__ import annotations

import re
from typing import Dict, List, Optional

from .schema import Task, Step


# Map natural language mentions to object ids used by the environment.
# The env has objects named `red_mug` and `blue_block`. Ensure generic words
# like "mug" resolve to `red_mug` instead of a non-existent "mug" key.
OBJECT_ALIASES = {
    "red_mug": ["mug", "cup", "red mug", "red cup"],
    "blue_block": ["blue block", "blue cube"],
}

LOCATION_ALIASES = {
    "shelf_A": ["shelf", "shelf a", "left shelf"],
    "bin1": ["bin 1", "first bin", "bin one"],
    "table": ["table", "desk", "workbench"],
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def match_alias(text: str, alias_map: Dict[str, List[str]]) -> Optional[str]:
    for key, aliases in alias_map.items():
        for alias in aliases:
            if alias in text:
                return key
    return None


def parse_text_to_task(text: str) -> Task:
    """Rule-based NL → DSL conversion.

    Heuristics:
    - If an object is requested to be tidied/put/placed, create perceive→grasp→place steps.
    - If a location is mentioned, map to a known location.
    - Inject navigate to target area before grasp/place when helpful.
    """
    t = normalize_text(text)

    goal = "tidy_table"
    obj_key = match_alias(t, OBJECT_ALIASES) or "red_mug"
    loc_key = match_alias(t, LOCATION_ALIASES) or "shelf_A"

    steps: List[Step] = []
    steps.append(Step(action="perceive", args={"object": obj_key}))
    steps.append(Step(action="grasp", args={"object": obj_key}))
    steps.append(Step(action="place", args={"location": loc_key}))

    return Task(goal=goal, steps=steps)


# Optional: Ollama stub for future extension
def parse_with_ollama(text: str, model: str = "llama3") -> Optional[Task]:
    """Return None if Ollama is not configured. Placeholder for future use."""
    _ = text, model
    return None


