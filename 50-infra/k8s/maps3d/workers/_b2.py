"""B2 (Backblaze) upload helper for maps3d.

Wraps b2sdk so the colmap_worker can upload raw + simplified meshes
without re-implementing auth / dedup logic. Content-addressed key path
keeps the bucket dedup-friendly: same SHA-256 ⇒ same key ⇒ B2 head()
short-circuits the upload.
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import Optional

log = logging.getLogger("maps3d.b2")


class B2Client:
    """Thin wrapper around b2sdk.v2 with lazy auth + path conventions.

    Path conventions:
      mapillary/{sha256}.jpg      — raw imagery (content-addressed)
      maps3d/raw/{tile_h3}.ply    — COLMAP delaunay_mesher output
      maps3d/tile/{tile_h3}.glb   — Open3D-simplified vertex-color GLB
    """

    def __init__(
        self,
        bucket: str,
        key_id: Optional[str] = None,
        application_key: Optional[str] = None,
    ):
        self.bucket_name = bucket
        self._key_id = key_id or os.environ.get("B2_KEY_ID", "")
        self._app_key = application_key or os.environ.get("B2_APPLICATION_KEY", "")
        self._bucket = None  # lazy

    @property
    def bucket(self):
        if self._bucket is None:
            from b2sdk.v2 import B2Api, InMemoryAccountInfo

            if not self._key_id or not self._app_key:
                raise RuntimeError("B2_KEY_ID / B2_APPLICATION_KEY not set")
            info = InMemoryAccountInfo()
            api = B2Api(info)
            api.authorize_account("production", self._key_id, self._app_key)
            self._bucket = api.get_bucket_by_name(self.bucket_name)
        return self._bucket

    def upload(self, local_path: Path, remote_key: str) -> str:
        """Upload `local_path` to `b2://<bucket>/<remote_key>`. Returns
        the b2:// URI. Idempotent: re-upload of the same content
        replaces the file (b2sdk handles versioning)."""
        self.bucket.upload_local_file(
            local_file=str(local_path),
            file_name=remote_key,
        )
        uri = f"b2://{self.bucket_name}/{remote_key}"
        log.info("b2 upload %s → %s (%d bytes)", local_path, uri, local_path.stat().st_size)
        return uri

    def upload_image(self, local_path: Path) -> str:
        """Upload an image with a content-addressed key. Same content
        ⇒ same key ⇒ B2 dedup hits. Returns b2:// URI."""
        sha = sha256_of_file(local_path)
        key = f"mapillary/{sha}{local_path.suffix or '.jpg'}"
        return self.upload(local_path, key)


def sha256_of_file(p: Path, chunk: int = 1 << 20) -> str:
    """Streaming SHA-256 (1 MiB chunks)."""
    h = hashlib.sha256()
    with p.open("rb") as f:
        while True:
            buf = f.read(chunk)
            if not buf:
                break
            h.update(buf)
    return h.hexdigest()
