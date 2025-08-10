from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException

from dsl.parse_llm import parse_text_to_task
from dsl.schema import Task, validate_task_dsl
from envs.table_top import TableTopSim
from executor.executor import Executor


app = FastAPI(title="Hybrid Planner Skill Server")


env = TableTopSim(use_gui=os.getenv("HP_BULLET_GUI") == "1")
executor = Executor(env)


@app.post("/parse")
def parse_endpoint(payload: Dict[str, Any]):
    text = payload.get("text")
    if not isinstance(text, str):
        raise HTTPException(400, "Missing 'text' field")
    task = parse_text_to_task(text)
    return task.model_dump()


@app.post("/plan")
def plan_endpoint(payload: Dict[str, Any]):
    task_obj = payload.get("task")
    if not isinstance(task_obj, dict):
        raise HTTPException(400, "Missing 'task' field")
    task = validate_task_dsl(task_obj)
    # For this reference server, planning happens during execution.
    # We return the validated task as the "plan" artifact.
    return {"validated_task": task.model_dump(), "notes": "Planning occurs during execution in this reference."}


@app.post("/execute")
def execute_endpoint(payload: Dict[str, Any]):
    task_obj = payload.get("task")
    if not isinstance(task_obj, dict):
        raise HTTPException(400, "Missing 'task' field")
    result = executor.run(task_obj)
    return {
        "success": result.metrics.success,
        "metrics": {
            "total_time_s": result.metrics.total_time_s,
            "planning_time_s": result.metrics.planning_time_s,
            "corrections": result.metrics.corrections,
        },
        "notes": result.notes,
    }


@app.post("/run_task")
def run_task_endpoint(payload: Dict[str, Any]):
    text = payload.get("text")
    if not isinstance(text, str):
        raise HTTPException(400, "Missing 'text' field")
    task = parse_text_to_task(text)
    result = executor.run(task.model_dump())
    return {
        "task": task.model_dump(),
        "success": result.metrics.success,
        "metrics": {
            "total_time_s": result.metrics.total_time_s,
            "planning_time_s": result.metrics.planning_time_s,
            "corrections": result.metrics.corrections,
        },
        "notes": result.notes,
    }


