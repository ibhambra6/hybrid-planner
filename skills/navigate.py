from __future__ import annotations

from typing import Tuple

import numpy as np

from planners.a_star import a_star


def navigate(env, goal_xy: Tuple[int, int]) -> bool:
    grid = env.get_grid()
    start = tuple(map(int, env.gripper_xy))
    goal = tuple(map(int, goal_xy))
    result = a_star(grid, start, goal)
    if result is None:
        return False
    # Follow path
    for cell in result.path:
        env.set_gripper(cell)
    return np.linalg.norm(np.array(env.gripper_xy) - np.array(goal)) <= 1.0


