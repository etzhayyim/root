"""Per-machine path resolver.

Resolution order:
  1. ETZ_DATASET_ROOT env var
  2. ~/.etzhayyim/local-paths.toml — [machine.<hostname>] section
  3. No default. Tool errors out if neither set.

Returns a frozen `Paths` dataclass with all derived locations.
"""

from __future__ import annotations

import os
import socket
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path


CONFIG_PATH = Path.home() / ".etzhayyim" / "local-paths.toml"


@dataclass(frozen=True)
class Paths:
    root: Path  # /Volumes/260317/etzhayyim
    ipfs_data: Path  # root/ipfs-data
    annex_store: Path  # root/annex-store
    staging: Path  # root/datasets-staging
    kubo_api: str  # http://127.0.0.1:5001  (local self-pin / add tier)
    node_did: str | None
    kotobase_pin_url: str  # https://kotobase.net (canonical remote pin, ADR-2606091500)

    def subdataset_annex_dir(self, subdataset_name: str) -> Path:
        return self.annex_store / subdataset_name


def _from_env() -> str | None:
    return os.environ.get("ETZ_DATASET_ROOT")


def _from_toml() -> tuple[str | None, str | None, str | None]:
    if not CONFIG_PATH.exists():
        return None, None, None
    hostname = socket.gethostname().split(".")[0]
    with CONFIG_PATH.open("rb") as f:
        cfg = tomllib.load(f)
    machine = cfg.get("machine", {}).get(hostname)
    if not machine:
        # Fall back to any single [machine.*] block when hostname doesn't match.
        machines = cfg.get("machine", {})
        if len(machines) == 1:
            machine = next(iter(machines.values()))
        else:
            return None, None, None
    return (
        machine.get("dataset_root"),
        machine.get("kubo_api"),
        machine.get("node_did"),
    )


def resolve() -> Paths:
    root_str = _from_env()
    kubo_api = os.environ.get("ETZ_KUBO_API")
    node_did = os.environ.get("ETZ_NODE_DID")

    if root_str is None or kubo_api is None or node_did is None:
        toml_root, toml_kubo, toml_did = _from_toml()
        root_str = root_str or toml_root
        kubo_api = kubo_api or toml_kubo or "http://127.0.0.1:5001"
        node_did = node_did or toml_did

    if not root_str:
        print(
            "e7m-dataset: ETZ_DATASET_ROOT is unset and no matching "
            f"[machine.<hostname>] section in {CONFIG_PATH}.\n"
            "Set the env var or create the config file. "
            "See ADR-2605241500 §D5 and 70-tools/e7m-dataset/README.md.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    # Canonical remote IPFS pin = kotobase.net (ADR-2606091500). Overridable via
    # ETZ_KOTOBASE_PIN; the local kubo_api stays the add/self-pin tier.
    kotobase_pin_url = os.environ.get("ETZ_KOTOBASE_PIN") or "https://kotobase.net"

    root = Path(root_str).expanduser().resolve()
    return Paths(
        root=root,
        ipfs_data=root / "ipfs-data",
        annex_store=root / "annex-store",
        staging=root / "datasets-staging",
        kubo_api=kubo_api,
        node_did=node_did,
        kotobase_pin_url=kotobase_pin_url,
    )
