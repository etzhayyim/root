"""isaaclab.sim — simulation lifecycle wrappers.

Mirror of `isaaclab.sim` (Isaac Lab 1.x). Provides:

  - SimulationCfg       — physics_dt / rendering_dt / gravity / device /
                          pipeline / scene-query toggles
  - SimulationContext   — singleton lifecycle wrapper used as a `with`
                          context: handles step/reset/pause/resume/stop,
                          physics + render callback registry, singleton
                          instance() lookup, simulation time + step
                          counter, on-exit cleanup
  - SimulationCfgError  — invalid cfg → ValueError subclass

Future R1.x adds:
  - SimulationViewer    — viewport / camera control
  - SimulationRecorder  — physics state checkpoint + restore
"""

from .simulation_context import (
    SimulationCfg,
    SimulationCfgError,
    SimulationContext,
)

__all__ = ["SimulationCfg", "SimulationCfgError", "SimulationContext"]
