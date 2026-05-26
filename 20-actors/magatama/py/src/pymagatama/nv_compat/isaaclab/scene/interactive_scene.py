"""InteractiveScene + cfg — composition of terrain + assets + sensors + cloner.

Mirrors `isaaclab.scene.InteractiveScene` (Isaac Lab 1.x). The scene is a
declarative container: instantiate with a cfg, then call update(world) each
step to refresh sensor data against current env state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SensorMount:
    """Per-env sensor attachment.

    `sensor_factory(env_idx)` returns a fresh sensor instance for env_idx.
    `link_name` names the articulation link the sensor is rigidly attached to.
    """
    sensor_factory: Any  # callable: env_idx -> sensor (Camera / Lidar / Imu / ContactSensor)
    link_name: str = "base"


@dataclass
class InteractiveSceneCfg:
    """Declarative scene config.

    All fields are optional; an empty scene is valid (useful for unit tests).
    """
    num_envs: int = 1
    env_spacing: float = 4.0
    # Robot asset (Cartpole / DoublePendulum / PlanarChain / ...). Each env
    # gets its own articulation instance with the asset's URDF + defaults.
    robot: Any = None
    # Terrain HeightField (from isaaclab.terrains).
    terrain: Any = None
    # Cloner instance (typically a GridCloner). If None, a default GridCloner
    # with cfg.env_spacing is constructed.
    cloner: Any = None
    # Named sensor mounts; each materialized per env.
    sensors: Dict[str, SensorMount] = field(default_factory=dict)
    # Optional named "props" — additional asset entries (e.g. cubes, walls).
    props: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InteractiveScene:
    """Materializes an InteractiveSceneCfg into per-env asset / sensor instances.

    After construction:
      - .articulations[env_idx]  — list of N articulation instances (or empty)
      - .sensors[name][env_idx]  — sensor instances per env, per mount name
      - .env_positions[env_idx]  — world-frame (x, y, z) per env
      - .terrain                  — bound HeightField (or None)
    """
    cfg: InteractiveSceneCfg
    articulations: List[Any] = field(default_factory=list)
    sensors: Dict[str, List[Any]] = field(default_factory=dict)
    env_positions: List[tuple] = field(default_factory=list)
    terrain: Any = None

    def __post_init__(self):
        # Resolve cloner (default to GridCloner if none).
        cloner = self.cfg.cloner
        if cloner is None:
            from ...omni.isaac.cloner import GridCloner
            cloner = GridCloner(spacing=self.cfg.env_spacing)
        self._cloner = cloner

        # Compute per-env world positions.
        self.env_positions = cloner.positions_for_envs(self.cfg.num_envs)

        # Materialize articulations. Real instantiation happens when caller
        # wires articulations into a World; here we just store the asset
        # reference so subsequent code can spawn from it.
        self.articulations = [self.cfg.robot] * self.cfg.num_envs if self.cfg.robot else []

        # Materialize sensors per env.
        self.sensors = {}
        for name, mount in self.cfg.sensors.items():
            self.sensors[name] = [mount.sensor_factory(i) for i in range(self.cfg.num_envs)]

        # Bind terrain (no copy; one terrain shared across envs by default).
        self.terrain = self.cfg.terrain

    @property
    def num_envs(self) -> int:
        return self.cfg.num_envs

    def position_for_env(self, env_idx: int) -> tuple:
        """World-frame (x, y, z) for the named env."""
        return self.env_positions[env_idx]

    def get_sensor(self, name: str, env_idx: int) -> Any:
        """Specific sensor instance for (name, env_idx)."""
        return self.sensors[name][env_idx]

    def update(self, world: Any, time: float = 0.0) -> None:
        """Per-step hook — refresh sensor data, advance terrain animations, etc.

        For R1.x this is a no-op stub: sensors are sampled lazily by the
        caller (Camera.project_world_point, Lidar.acquire_data, ImuSensor.sample,
        ContactSensor.sample). Future versions auto-sample all bound sensors
        and stash results on scene._latest_observations[env_idx][sensor_name].
        """
        # Iterate over articulations from the world if available.
        # This is the hook point where a real implementation would call
        # each sensor's sample() against the current env state.
        self._last_update_time = time

    def get_terrain_height(self, world_x: float, world_y: float) -> Optional[float]:
        """Sample terrain elevation at a world-frame point (or None if no
        terrain bound). Assumes terrain is centred at origin."""
        if self.terrain is None:
            return None
        # Convert world position to cell index (terrain is centred at origin).
        cell_size = self.terrain.cell_size
        rows = self.terrain.rows
        cols = self.terrain.cols
        col_f = (world_x / cell_size) + (cols - 1) * 0.5
        row_f = (world_y / cell_size) + (rows - 1) * 0.5
        col = max(0, min(cols - 1, int(round(col_f))))
        row = max(0, min(rows - 1, int(round(row_f))))
        return self.terrain.height_at(row, col)
