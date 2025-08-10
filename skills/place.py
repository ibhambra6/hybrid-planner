from __future__ import annotations

from typing import Tuple

from planners.chomp import chomp_optimize


def place(env, location: str) -> bool:
    # Map location to target cell (mirror of env.place logic for planning)
    target = (50, 10) if location == "shelf_A" else (10, 50)
    start = tuple(map(float, env.gripper_xy))
    occ = env.get_grid()
    res = chomp_optimize(occ, start, target)
    if res is None:
        return False
    for pt in res.path:
        env.set_gripper((int(pt[0]), int(pt[1])))
    return env.place(location)


