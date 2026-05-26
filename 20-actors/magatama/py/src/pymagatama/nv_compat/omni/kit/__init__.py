"""omni.kit — Omniverse Kit framework namespace.

R1.x scope:
  - app: Application + IExt + extension.toml parser (lifecycle: startup → shutdown)

Future R1.x adds:
  - viewport, timeline, ui, commands, settings, notifications.
"""

from . import app

__all__ = ["app"]
