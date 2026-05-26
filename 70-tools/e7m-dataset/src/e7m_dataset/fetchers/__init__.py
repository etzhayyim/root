"""Dataset fetchers — download upstream sources into the staging directory.

Per ADR-2605241500 + ADR-2605231400 §"Phase 3 Tier B ingest" (DataLad+IPFS-
backed payloads). Each fetcher writes upstream data into

  ${ETZ_DATASET_ROOT}/datasets-staging/<dataset-name>/

and returns a `FetchResult` describing what was staged. Caller (operator
or chained CLI command) runs:

  datalad save -d 90-docs/baien/datasets/<subdataset> -m "..."
  e7m-dataset publish-ipfs <subdataset> --append-manifest --name ... --revision ... --kind ...

to land the bytes in git-annex + IPFS + PDS.

The fetchers do NOT touch git-annex or DataLad directly — separation of
concerns lets the operator inspect / curate before committing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FetchResult:
    """What a fetcher staged. `revision` uniquely identifies the snapshot
    so callers can match it to the eventual datasetPin `revision` field."""

    name: str
    """Canonical dataset name (e.g., 'wikidata:legal-entities-with-lei')."""

    revision: str
    """Snapshot identifier — content sha256 / etag / SPARQL hash / capture timestamp."""

    staging_path: Path
    """Absolute path the fetcher wrote files into."""

    file_count: int
    size_bytes: int

    source: dict[str, Any] = field(default_factory=dict)
    """Free-form source descriptor (URL, query, sensor, etc.) for the
    manifest row's `source` field."""


__all__ = ["FetchResult"]
