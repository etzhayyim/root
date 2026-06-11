#!/usr/bin/env python3
"""cc-direct-ingest — Common Crawl WET → kotoba Datom log, no parquet.

Streams a Common Crawl WET file (.warc.wet.gz, extracted-text records) over
HTTP — or reads a local copy — parses WARC records incrementally, chunks the
page text, and writes `cc/chunk/*` datoms straight into the canonical
`cc:2026-12:chunks` named graph via `com.etzhayyim.apps.kotoba.datomic.transact`.

Persistence is therefore kotoba Datomic + IPFS end-to-end: every transact
commits content-addressed dag-cbor blocks through the server's
TieredBlockStore (Kubo/IPFS cold tier). parquet never appears anywhere in the
pipeline — neither as input wire nor at rest.

This is NOT a crawler (ADR-2606012300 keeps "no crawler" by design): the only
source is Common Crawl's published WET archives. The download is bounded —
the gzip stream is read incrementally and the connection is dropped as soon
as --max-pages records have been ingested, so a 150 MB WET file costs only a
few MB for a small batch.

Auth model: the kotoba edge is the trust boundary (see
kotoba-server::graph_auth) — the operator JWT carries the node operator DID
in `sub` and is not signature-verified by the server. Find the running
node's DID with:

    grep -a "node identity" ~/.local/kotoba-etzhayyim/serve.log | tail -1

Usage:
    # latest WET file of a crawl, 50 pages, then reindex BM25:
    ingest_wet.py --crawl CC-MAIN-2025-47 --max-pages 50 --reindex \
        --did did:key:z...

    # explicit WET url or local file:
    ingest_wet.py --wet https://data.commoncrawl.org/crawl-data/.../x.warc.wet.gz
    ingest_wet.py --wet /path/to/file.warc.wet.gz

Only the Python standard library is used.
"""

from __future__ import annotations

import functools

import argparse
import base64
import gzip
import hashlib
import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib

print = functools.partial(print, flush=True)  # progress visible when piped

CC_DATA_BASE = "https://data.commoncrawl.org/"
CHUNKS_GRAPH_NAME = "cc:2026-12:chunks"
# kotoba-server MAX_TX_EDN_LEN is 1 MiB, but commit latency grows with tx
# size AND with total corpus size (R0 full-index rewrite per commit) — keep
# batches small so each transact stays interactive. Tunable via --batch-kib.
DEFAULT_TX_EDN_BYTES = 96 * 1024
DEFAULT_CHUNK_CHARS = 800
MIN_CHUNK_CHARS = 80
USER_AGENT = "etzhayyim-cc-direct-ingest/0.1 (kotoba datom-native WET ingest)"

# ISO 639-3 → 639-1 for the languages WET headers actually carry most often.
LANG3_TO_2 = {
    "eng": "en", "jpn": "ja", "zho": "zh", "cmn": "zh", "kor": "ko",
    "deu": "de", "fra": "fr", "spa": "es", "por": "pt", "rus": "ru",
    "ita": "it", "nld": "nl", "pol": "pl", "tur": "tr", "vie": "vi",
    "ind": "id", "tha": "th", "ara": "ar", "hin": "hi", "ben": "bn",
    "ukr": "uk", "ces": "cs", "swe": "sv", "dan": "da", "fin": "fi",
    "nor": "no", "ell": "el", "heb": "he", "hun": "hu", "ron": "ro",
}


# ── kotoba CID (CIDv1 dag-cbor sha2-256, base32lower multibase) ──────────────

def kotoba_graph_cid(name: str) -> str:
    """Mirror kotoba_core::cid::KotobaCid::from_bytes + to_multibase."""
    digest = hashlib.sha256(name.encode()).digest()
    raw = bytes([0x01, 0x71, 0x12, 0x20]) + digest
    return "b" + base64.b32encode(raw).decode().lower().rstrip("=")


# ── operator JWT (edge-trust model; server checks sub + exp only) ────────────

def operator_token(did: str) -> str:
    def b64url(b: bytes) -> str:
        return base64.urlsafe_b64encode(b).decode().rstrip("=")

    header = b64url(b'{"alg":"EdDSA","typ":"JWT"}')
    exp = int(time.time()) + 3600
    payload = b64url(json.dumps({"sub": did, "exp": exp}).encode())
    return f"{header}.{payload}.cc-direct-ingest"


# ── WARC / WET streaming parser ──────────────────────────────────────────────

class WetRecord:
    __slots__ = ("url", "lang", "text")

    def __init__(self, url: str, lang: str, text: str):
        self.url = url
        self.lang = lang
        self.text = text


def _parse_warc_stream(stream: io.BufferedIOBase):
    """Yield WetRecord from an uncompressed WARC byte stream, incrementally."""
    while True:
        # WARC header block: lines until a blank line.
        line = stream.readline()
        if not line:
            return
        if line.strip() == b"":
            continue
        if not line.startswith(b"WARC/"):
            # Mid-stream garbage — skip until the next record marker.
            continue
        headers: dict[str, str] = {}
        while True:
            hline = stream.readline()
            if not hline or hline in (b"\r\n", b"\n"):
                break
            if b":" in hline:
                k, _, v = hline.partition(b":")
                headers[k.strip().decode("latin-1").lower()] = (
                    v.strip().decode("latin-1")
                )
        try:
            length = int(headers.get("content-length", "0"))
        except ValueError:
            length = 0
        body = stream.read(length) if length > 0 else b""
        # Trailing CRLFCRLF record separator (tolerate EOF).
        stream.readline()
        stream.readline()

        if headers.get("warc-type") != "conversion":
            continue
        url = headers.get("warc-target-uri", "")
        if not url:
            continue
        lang_hdr = headers.get("warc-identified-content-language", "")
        lang3 = lang_hdr.split(",")[0].strip().lower() if lang_hdr else ""
        lang = LANG3_TO_2.get(lang3, lang3[:2] if lang3 else "und")
        text = body.decode("utf-8", errors="replace")
        yield WetRecord(url=url, lang=lang, text=text)


class _GzipHttpStream(io.RawIOBase):
    """Incremental gzip decode over an HTTP response (or file object).

    Handles MULTI-MEMBER gzip — Common Crawl WET/WARC .gz files concatenate
    one gzip member per record, and a single zlib decompressobj stops at the
    first member boundary. Lets us stop reading a multi-hundred-MB WET file
    after N records without downloading the rest.
    """

    def __init__(self, raw):
        self._raw = raw
        self._z = zlib.decompressobj(16 + zlib.MAX_WBITS)
        self._buf = b""
        self._eof = False

    def readable(self) -> bool:
        return True

    def _decompress(self, compressed: bytes) -> bytes:
        out = []
        data = compressed
        while data:
            out.append(self._z.decompress(data))
            if not self._z.eof:
                break
            # Member boundary — restart on the next member's bytes.
            data = self._z.unused_data
            self._z = zlib.decompressobj(16 + zlib.MAX_WBITS)
        return b"".join(out)

    def readinto(self, b) -> int:
        while len(self._buf) < len(b) and not self._eof:
            compressed = self._raw.read(64 * 1024)
            if not compressed:
                self._buf += self._z.flush()
                self._eof = True
                break
            self._buf += self._decompress(compressed)
        n = min(len(b), len(self._buf))
        b[:n] = self._buf[:n]
        self._buf = self._buf[n:]
        return n


def open_wet(source: str):
    """Open a WET source (URL or local path) as an uncompressed WARC stream."""
    if source.startswith(("http://", "https://")):
        req = urllib.request.Request(source, headers={"User-Agent": USER_AGENT})
        resp = urllib.request.urlopen(req, timeout=120)
        return io.BufferedReader(_GzipHttpStream(resp), buffer_size=256 * 1024), resp
    fh = open(source, "rb")
    if source.endswith(".gz"):
        return io.BufferedReader(
            _GzipHttpStream(fh), buffer_size=256 * 1024
        ), fh
    return io.BufferedReader(fh), fh  # already-uncompressed .warc.wet


def resolve_wet_url_from_crawl(crawl: str) -> str:
    """First WET path of a crawl, via the small wet.paths.gz index."""
    url = f"{CC_DATA_BASE}crawl-data/{crawl}/wet.paths.gz"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        first = gzip.decompress(resp.read()).decode().splitlines()[0].strip()
    return CC_DATA_BASE + first


# ── chunking ─────────────────────────────────────────────────────────────────

def chunk_text(text: str, target: int = DEFAULT_CHUNK_CHARS) -> list[str]:
    """Split page text into ~target-char chunks on line boundaries."""
    chunks: list[str] = []
    cur: list[str] = []
    cur_len = 0
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if cur_len + len(line) > target and cur_len >= MIN_CHUNK_CHARS:
            chunks.append(" ".join(cur))
            cur, cur_len = [], 0
        cur.append(line)
        cur_len += len(line) + 1
    if cur_len >= MIN_CHUNK_CHARS:
        chunks.append(" ".join(cur))
    return chunks


# ── EDN tx assembly ──────────────────────────────────────────────────────────

def edn_escape(s: str) -> str:
    """Escape a Python string into an EDN double-quoted string body."""
    out = []
    for ch in s:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch in ("\n", "\r", "\t"):
            out.append(" ")
        elif ord(ch) < 0x20:
            continue
        else:
            out.append(ch)
    return "".join(out)


def chunk_datoms_edn(subject: str, url: str, domain: str, lang: str,
                     text: str) -> str:
    return (
        f'[:db/add "{subject}" "cc/chunk/text" "{edn_escape(text)}"] '
        f'[:db/add "{subject}" "cc/chunk/url" "{edn_escape(url)}"] '
        f'[:db/add "{subject}" "cc/chunk/domain" "{edn_escape(domain)}"] '
        f'[:db/add "{subject}" "cc/chunk/lang" "{edn_escape(lang)}"]'
    )


def page_subject_prefix(url: str) -> str:
    return "cc-wet:" + hashlib.sha256(url.encode()).hexdigest()[:16]


# ── kotoba XRPC client ───────────────────────────────────────────────────────

class KotobaClient:
    def __init__(self, base: str, did: str, timeout: int = 900):
        self.base = base.rstrip("/")
        self.timeout = timeout
        self.headers = {
            "Authorization": "Bearer " + operator_token(did),
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        }

    def call(self, nsid: str, *, method: str = "GET", body=None, params=None):
        url = f"{self.base}/xrpc/{nsid}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, headers=self.headers,
                                     method=method)
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.load(resp)

    def transact(self, graph_cid: str, tx_edn: str) -> dict:
        return self.call(
            "com.etzhayyim.apps.kotoba.datomic.transact",
            method="POST",
            body={"graph": graph_cid, "tx_edn": f"[{tx_edn}]"},
        )

    def reindex(self) -> dict:
        return self.call("com.etzhayyim.apps.kotoba.search.reindex",
                         method="POST", body={})

    def status(self) -> dict:
        return self.call("com.etzhayyim.apps.kotoba.cc.status")


# ── main ─────────────────────────────────────────────────────────────────────

def run(args) -> int:
    did = args.did or os.environ.get("KOTOBA_OPERATOR_DID", "")
    if not did:
        print("error: operator DID required (--did or KOTOBA_OPERATOR_DID)",
              file=sys.stderr)
        return 2

    if args.wet:
        wet_source = args.wet
    elif args.crawl:
        print(f"resolving first WET path of {args.crawl} …")
        wet_source = resolve_wet_url_from_crawl(args.crawl)
    else:
        print("error: --wet or --crawl required", file=sys.stderr)
        return 2
    print(f"WET source: {wet_source}")

    client = KotobaClient(args.server, did, timeout=args.timeout)
    graph = kotoba_graph_cid(CHUNKS_GRAPH_NAME)
    max_tx_bytes = args.batch_kib * 1024
    print(f"target graph {CHUNKS_GRAPH_NAME} = {graph}")

    stream, underlying = open_wet(wet_source)
    pages = chunks_total = tx_count = 0
    batch: list[str] = []
    batch_bytes = 0
    last_commit = None

    def flush():
        nonlocal batch, batch_bytes, tx_count, last_commit
        if not batch:
            return
        resp = client.transact(graph, " ".join(batch))
        tx_count += 1
        last_commit = resp.get("commit_cid")
        print(f"  tx#{tx_count}: {resp.get('datom_count')} datoms "
              f"commit={last_commit} ipns_seq={resp.get('ipns_sequence')}")
        batch, batch_bytes = [], 0

    try:
        for rec in _parse_warc_stream(stream):
            if args.lang and rec.lang != args.lang:
                continue
            parts = chunk_text(rec.text, args.chunk_chars)
            if not parts:
                continue
            pages += 1
            domain = urllib.parse.urlsplit(rec.url).hostname or ""
            prefix = page_subject_prefix(rec.url)
            for i, part in enumerate(parts[: args.max_chunks_per_page]):
                edn = chunk_datoms_edn(f"{prefix}:{i}", rec.url, domain,
                                       rec.lang, part)
                if batch and batch_bytes + len(edn.encode()) > max_tx_bytes:
                    flush()
                batch.append(edn)
                batch_bytes += len(edn.encode()) + 1
                chunks_total += 1
            if pages % 10 == 0:
                print(f"… {pages} pages / {chunks_total} chunks")
            if pages >= args.max_pages:
                break
        flush()
    finally:
        try:
            underlying.close()
        except Exception:
            pass

    print(f"ingested {pages} pages → {chunks_total} chunks in {tx_count} tx; "
          f"head commit {last_commit}")

    if args.reindex:
        print("rebuilding search indexes (BM25 + PageRank) …")
        print("  " + json.dumps(client.reindex()))
    print("cc.status: " + json.dumps(client.status()))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--server", default=os.environ.get(
        "KOTOBA_URL", "http://127.0.0.1:8077"))
    p.add_argument("--did", default="",
                   help="operator DID (or KOTOBA_OPERATOR_DID env)")
    src = p.add_mutually_exclusive_group()
    src.add_argument("--wet", help="WET url or local .warc.wet[.gz] path")
    src.add_argument("--crawl",
                     help="crawl id (e.g. CC-MAIN-2025-47) → first WET file")
    p.add_argument("--max-pages", type=int, default=50)
    p.add_argument("--max-chunks-per-page", type=int, default=8)
    p.add_argument("--chunk-chars", type=int, default=DEFAULT_CHUNK_CHARS)
    p.add_argument("--lang", default="",
                   help="keep only this 2-letter language (e.g. ja)")
    p.add_argument("--batch-kib", type=int,
                   default=DEFAULT_TX_EDN_BYTES // 1024,
                   help="max EDN tx size in KiB per transact (server cap 1024)")
    p.add_argument("--timeout", type=int, default=900,
                   help="per-request timeout seconds (commits slow as corpus grows)")
    p.add_argument("--reindex", action="store_true",
                   help="rebuild BM25/PageRank after ingest")
    return run(p.parse_args())


if __name__ == "__main__":
    sys.exit(main())
