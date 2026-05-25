"""isaacsim.sensors — Camera / LidarRtx / IMUSensor / ContactSensor mirror.

R1.1 scope: pinhole Camera (formula parity with kami-sensor-sim Rust crate).
R1.6+ adds LidarRtx + IMU + Contact.
"""

from .camera import Camera, CameraIntrinsics, DepthImage, Projection

__all__ = ["Camera", "CameraIntrinsics", "DepthImage", "Projection"]
