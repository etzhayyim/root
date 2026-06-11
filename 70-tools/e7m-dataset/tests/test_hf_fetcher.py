"""fetchers/hf.py — light unit tests with an injected httpx.MockTransport."""

from __future__ import annotations

import httpx
import pytest

from e7m_dataset.fetchers import hf as hf_fetcher


def _handler_for(repo_files: list[dict], sha: str = "deadbeefcafebabe1234567890abcdef12345678"):
    """Return a httpx mock handler that serves a minimal HF dataset."""
    def handler(req: httpx.Request) -> httpx.Response:
        url = str(req.url)
        if "/revision/" in url:
            return httpx.Response(200, json={
                "sha": sha,
                "cardData": {"license": "apache-2.0"},
            })
        if "/tree/" in url:
            return httpx.Response(200, json=[
                {"type": "file", "path": f["path"], "size": f["size"]}
                for f in repo_files
            ])
        if "/resolve/" in url:
            # Find which file by the trailing path.
            for f in repo_files:
                if url.endswith(f["path"]):
                    return httpx.Response(
                        200, content=b"\x00" * f["size"], headers={"content-type": "application/octet-stream"}
                    )
            return httpx.Response(404)
        return httpx.Response(404)
    return handler


def test_fetch_resolves_and_downloads(tmp_path):
    files = [
        {"path": "data/a.json", "size": 8},
        {"path": "data/b.bin", "size": 16},
    ]
    client = httpx.Client(transport=httpx.MockTransport(_handler_for(files)), follow_redirects=True)
    fr = hf_fetcher.fetch(
        tmp_path,
        hf_fetcher.HfFetchOpts(owner="o", repo="r", client=client),
    )
    assert fr.name == "hf-dataset:o/r"
    assert fr.revision.startswith("git:deadbeef")
    assert fr.file_count == 2
    assert fr.size_bytes == 24
    assert (fr.staging_path / "data" / "a.json").read_bytes() == b"\x00" * 8


def test_max_bytes_enforced(tmp_path):
    files = [{"path": "huge.bin", "size": 1 << 20}]
    client = httpx.Client(transport=httpx.MockTransport(_handler_for(files)), follow_redirects=True)
    with pytest.raises(hf_fetcher.HfFetchError):
        hf_fetcher.fetch(
            tmp_path,
            hf_fetcher.HfFetchOpts(owner="o", repo="r", max_bytes=1024, client=client),
        )


def test_include_exclude(tmp_path):
    files = [
        {"path": "data/keep.json", "size": 4},
        {"path": "data/drop.bin", "size": 4},
    ]
    client = httpx.Client(transport=httpx.MockTransport(_handler_for(files)), follow_redirects=True)
    fr = hf_fetcher.fetch(
        tmp_path,
        hf_fetcher.HfFetchOpts(
            owner="o",
            repo="r",
            include_globs=["*.json"],
            client=client,
        ),
    )
    assert fr.file_count == 1
    assert (fr.staging_path / "data" / "keep.json").exists()
    assert not (fr.staging_path / "data" / "drop.bin").exists()
