"""isaaclab.utils — small utility surfaces shared across isaaclab.*.

R1.x scope:
  - dr     — domain randomisation primitives (sim2real config)
  - math   — quaternion + Euler + axis-angle + slerp + frame transform helpers
  - dict   — cfg serialization (class_to_dict / update_class_from_dict /
             deep_update / print_dict / dict_to_md_table / slice round-trip)
  - string — regex name matching (resolve_matching_names_*) + string ↔
             callable round-trip + case conversion + lambda detection
  - io     — save/load helpers (yaml / pickle / json + auto-dispatch by
             extension); minimal YAML emitter+parser for the
             dict/list/scalar subset Isaac Lab actually uses
  - timer  — perf timing (Timer class + TimerError + module-level named
             timer registry + time_function decorator + format_seconds)
"""

from . import dict, dr, io, math, string, timer

__all__ = ["dict", "dr", "io", "math", "string", "timer"]
