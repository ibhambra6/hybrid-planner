from __future__ import annotations

from typing import Tuple

import numpy as np

from planners.chomp import chomp_optimize


def grasp(env, object_name: str) -> bool:
    obj_pose = env.perceive(object_name)
    if obj_pose is None:
        return False
    start = tuple(map(float, env.gripper_xy))
    goal = tuple(map(float, obj_pose))
    occ = env.get_grid()
    res = chomp_optimize(occ, start, goal)
    if res is None:
        return False
    for pt in res.path:
        env.set_gripper((int(pt[0]), int(pt[1])))
    return env.grasp(object_name)


