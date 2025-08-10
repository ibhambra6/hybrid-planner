from __future__ import annotations

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator


ActionName = Literal["perceive", "navigate", "grasp", "place"]


class Step(BaseModel):
    action: ActionName
    args: Dict[str, object] = Field(default_factory=dict)

    @field_validator("args")
    @classmethod
    def validate_args(cls, v: Dict[str, object], info):
        action: ActionName = info.data.get("action")
        allowed_by_action = {
            "perceive": {"object"},
            "navigate": {"goal", "x", "y"},
            "grasp": {"object", "x", "y"},
            "place": {"location", "x", "y"},
        }
        if action not in allowed_by_action:
            raise ValueError(f"Unknown action {action}")
        unknown = set(v.keys()) - allowed_by_action[action]
        if unknown:
            raise ValueError(f"Unknown args for {action}: {unknown}")
        return v


class Task(BaseModel):
    goal: str
    steps: List[Step]
    metadata: Dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_semantics(self):
        # Basic semantic guardrails: must start with perceive before grasping an unknown object
        known_objects: set[str] = set()
        for step in self.steps:
            if step.action == "perceive":
                obj = step.args.get("object")
                if isinstance(obj, str):
                    known_objects.add(obj)
            if step.action == "grasp":
                obj = step.args.get("object")
                if isinstance(obj, str) and obj not in known_objects:
                    # Allow, but mark for correction in executor guardrails
                    self.metadata.setdefault("needs_perceive_injection", True)
        return self


def validate_task_dsl(obj: Dict[str, object]) -> Task:
    try:
        return Task.model_validate(obj)
    except ValidationError as e:
        raise ValueError(f"Invalid Task DSL: {e}")


