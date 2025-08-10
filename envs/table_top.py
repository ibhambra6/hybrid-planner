from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import time

import numpy as np

try:
    import pybullet as p
    import pybullet_data
except Exception:  # pragma: no cover - pybullet optional in CI
    p = None  # type: ignore
    pybullet_data = None  # type: ignore


WORKSPACE_SIZE = (60, 60)  # grid for navigation/CHOMP abstraction


@dataclass
class ObjectState:
    name: str
    pose_xy: Tuple[int, int]
    held: bool = False
    body_id: Optional[int] = None


class TableTopSim:
    def __init__(self, use_gui: Optional[bool] = None):
        self.use_gui = use_gui if use_gui is not None else (os.getenv("HP_BULLET_GUI") == "1")
        self.client = None
        self.objects: Dict[str, ObjectState] = {}
        self.gripper_xy: Tuple[int, int] = (5, 5)
        self.workspace = np.zeros(WORKSPACE_SIZE, dtype=bool)  # False=free, True=obstacle
        # Visualization state (only when pybullet GUI available)
        self._vis = {
            "gripper_id": None,
            "shelf_id": None,
        }

    # --- Coordinate transforms between grid (cells) and bullet (meters) ---
    @property
    def _scale(self) -> float:
        # meters per cell
        return 0.03

    def _cell_to_world(self, xy: Tuple[int, int], z: float = 0.05) -> Tuple[float, float, float]:
        return (xy[0] * self._scale, xy[1] * self._scale, z)

    def reset(self):
        if p is not None:
            mode = p.GUI if self.use_gui else p.DIRECT
            if self.client is None:
                self.client = p.connect(mode)
                if pybullet_data is not None:
                    p.setAdditionalSearchPath(pybullet_data.getDataPath())
            p.resetSimulation()
            p.setGravity(0, 0, -9.8)
            p.loadURDF("plane.urdf")
            if self.use_gui:
                # Spawn simple shelf as a thin box (doubled size)
                half_extents = [0.30, 0.30, 0.04]
                shelf_visual = p.createVisualShape(p.GEOM_BOX, halfExtents=half_extents, rgbaColor=[0.8, 0.8, 0.2, 1])
                shelf_collision = p.createCollisionShape(p.GEOM_BOX, halfExtents=half_extents)
                sx, sy, sz = self._cell_to_world((50, 10), z=half_extents[2])
                self._vis["shelf_id"] = p.createMultiBody(baseMass=0,
                                                           baseVisualShapeIndex=shelf_visual,
                                                           baseCollisionShapeIndex=shelf_collision,
                                                           basePosition=[sx, sy, sz])
                # Gripper marker
                grip_visual = p.createVisualShape(p.GEOM_SPHERE, radius=0.04, rgbaColor=[0.1, 0.8, 0.1, 1])
                self._vis["gripper_id"] = p.createMultiBody(baseMass=0, baseVisualShapeIndex=grip_visual,
                                                             basePosition=list(self._cell_to_world(self.gripper_xy)))
        # Table region obstacles near edges
        self.workspace[:, 0] = True
        self.workspace[:, -1] = True
        self.workspace[0, :] = True
        self.workspace[-1, :] = True
        # Place objects
        self.objects = {
            "red_mug": ObjectState("red_mug", (20, 20)),
            "blue_block": ObjectState("blue_block", (35, 40)),
        }
        if p is not None and self.use_gui:
            # Visualize objects as basic shapes (doubled size)
            for name, state in self.objects.items():
                if name == "red_mug":
                    vis = p.createVisualShape(p.GEOM_CYLINDER, radius=0.06, length=0.12, rgbaColor=[0.9, 0.1, 0.1, 1])
                    col = p.createCollisionShape(p.GEOM_CYLINDER, radius=0.06, height=0.12)
                    z = 0.06
                else:
                    vis = p.createVisualShape(p.GEOM_BOX, halfExtents=[0.06, 0.06, 0.06], rgbaColor=[0.1, 0.1, 0.9, 1])
                    col = p.createCollisionShape(p.GEOM_BOX, halfExtents=[0.06, 0.06, 0.06])
                    z = 0.06
                x, y, z = self._cell_to_world(state.pose_xy, z=z)
                bid = p.createMultiBody(baseMass=0.01, baseVisualShapeIndex=vis, baseCollisionShapeIndex=col,
                                         basePosition=[x, y, z])
                state.body_id = bid
        # Shelf area (target)
        self.shelf_region = (slice(45, 55), slice(5, 15))
        self.workspace[self.shelf_region] = False
        # Add a clutter obstacle
        self.workspace[25:30, 25:35] = True
        self.gripper_xy = (5, 5)

    def get_grid(self) -> np.ndarray:
        return self.workspace.copy()

    def perceive(self, object_name: str) -> Optional[Tuple[int, int]]:
        state = self.objects.get(object_name)
        return state.pose_xy if state else None

    def is_holding(self) -> bool:
        return any(obj.held for obj in self.objects.values())

    def set_gripper(self, xy: Tuple[int, int]):
        self.gripper_xy = xy
        # Update gripper marker and any held object in GUI
        if p is not None and self.use_gui and self._vis.get("gripper_id") is not None:
            gx, gy, gz = self._cell_to_world(self.gripper_xy)
            p.resetBasePositionAndOrientation(self._vis["gripper_id"], [gx, gy, gz], [0, 0, 0, 1])
        # If holding an object, make it follow the gripper in GUI
        if p is not None and self.use_gui:
            held_obj = next((o for o in self.objects.values() if o.held), None)
            if held_obj and held_obj.body_id is not None:
                ox, oy, oz = self._cell_to_world(self.gripper_xy, z=0.06)
                p.resetBasePositionAndOrientation(held_obj.body_id, [ox, oy, oz], [0, 0, 0, 1])

    def grasp(self, object_name: str) -> bool:
        state = self.objects.get(object_name)
        if not state:
            return False
        if np.linalg.norm(np.array(self.gripper_xy) - np.array(state.pose_xy)) <= 2.0:
            state.held = True
            # Snap visual object to gripper
            if p is not None and self.use_gui and state.body_id is not None:
                ox, oy, oz = self._cell_to_world(self.gripper_xy, z=0.06)
                p.resetBasePositionAndOrientation(state.body_id, [ox, oy, oz], [0, 0, 0, 1])
            return True
        return False

    def place(self, location: str) -> bool:
        target_cell = (50, 10) if location == "shelf_A" else (10, 50)
        held_obj = next((o for o in self.objects.values() if o.held), None)
        if held_obj is None:
            return False
        held_obj.pose_xy = target_cell
        held_obj.held = False
        if p is not None and self.use_gui and held_obj.body_id is not None:
            x, y, z = self._cell_to_world(target_cell, z=0.06)
            p.resetBasePositionAndOrientation(held_obj.body_id, [x, y, z], [0, 0, 0, 1])
        return True

    def detach(self):
        for o in self.objects.values():
            o.held = False

    def hold_gui(self, seconds: float = 5.0, step_hz: float = 60.0):
        """Keep the PyBullet GUI window open for a given duration.

        No-ops if PyBullet is not available or GUI is not enabled.
        """
        if p is None or not self.use_gui or self.client is None:
            return
        end_time = time.time() + max(0.0, seconds)
        dt = 1.0 / max(1.0, step_hz)
        while time.time() < end_time:
            try:
                p.stepSimulation()
            except Exception:
                break
            time.sleep(dt)


