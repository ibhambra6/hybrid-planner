from __future__ import annotations

import argparse

from dsl.parse_llm import parse_text_to_task
from envs.table_top import TableTopSim
from executor.executor import Executor


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gui", action="store_true", help="Enable PyBullet GUI")
    parser.add_argument("--gui-hold", type=float, default=5.0, help="Seconds to keep GUI window open")
    parser.add_argument("--text", type=str, default="tidy the red mug onto the shelf")
    args = parser.parse_args()

    env = TableTopSim(use_gui=args.gui)
    ex = Executor(env)
    task = parse_text_to_task(args.text)
    result = ex.run(task.model_dump())
    print("Task:", task.model_dump())
    print("Success:", result.metrics.success)
    print("Metrics:", result.metrics)
    print("Notes:", result.notes)
    if args.gui:
        env.hold_gui(seconds=args.gui_hold)


if __name__ == "__main__":
    main()


