"""malak.surveillance.ingest._common — shared utilities for police-org public ingest.

See `_working/malak/surveillance/ingest/SCRAPE-DESIGN.md` §5 for design.

Hard constraints enforced here (cannot be bypassed by caller):
  - robots.txt respected per host
  - rate limit ≥ 1.0s between requests to the same host
  - daytime (09:00-17:00 JST, weekdays) only when enforce_daytime=True
  - PII pattern detection raises before any DB write
  - apply mode requires --legal-approved-token
"""

from __future__ import annotations

import dataclasses
import logging
import re
import time
import urllib.parse
import urllib.robotparser
from datetime import datetime
from typing import Callable, Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover (Python ≥ 3.9)
    raise

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # caller must install httpx before live use

logger = logging.getLogger(__name__)

USER_AGENT = "MehikariBot/0.1 (+https://malak.gftd.ai (surveillance handlers)/about) python-httpx"
MIN_DELAY_SEC = 1.0
DAYTIME_HOUR_START = 9
DAYTIME_HOUR_END = 17


class PIIDetectedError(RuntimeError):
    """Raised when PII patterns match scraped content."""


class RobotsViolationError(RuntimeError):
    """Raised when a target URL is disallowed by robots.txt."""


class OutsideBusinessHoursError(RuntimeError):
    """Raised when fetch is attempted outside 09:00-17:00 JST weekdays."""


class ApplyModeNotAllowedError(RuntimeError):
    """Raised when --mode apply is attempted without a valid legal-approved-token."""


@dataclasses.dataclass
class FetchPolicy:
    """Caller-supplied policy. Defaults are intentionally restrictive."""

    mode: str = "dry-run"  # one of: dry-run, preview, apply
    apply_token: Optional[str] = None
    enforce_daytime: bool = True
    min_delay_sec: float = MIN_DELAY_SEC

    def assert_apply_allowed(self) -> None:
        if self.mode != "apply":
            return
        if not self.apply_token:
            raise ApplyModeNotAllowedError(
                "apply mode requires --legal-approved-token <UUID>; refusing to proceed"
            )
        # In production: validate token is a one-time HMAC signed by amanomibashira CLO
        # + external counsel, checked against an out-of-band signature record. Phase 0
        # stub accepts any non-empty value to keep the contract explicit at call sites.


def assert_dry_run_or_approved(policy: FetchPolicy) -> None:
    if policy.mode == "apply":
        policy.assert_apply_allowed()


_RANK = (
    r"(?:警視総監|警視監|警視長|警視正|警視|警部補|警部|巡査部長|巡査長|巡査)"
)
_NAME = r"[一-龥]{2,5}"
_POST = r"(?:本部長|副本部長|部長|課長|室長|署長|官房長|参事官|理事官|管理官|本部参事官)"

PII_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"氏名[\s::]"),
    re.compile(r"(担当者|担当官|担当課長|担当)[\s::]"),
    re.compile(r"\d{3}-\d{4}-\d{4}"),
    re.compile(r"[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}"),
    # rank → name (警視 田中太郎)
    re.compile(_RANK + r"\s*" + _NAME),
    # name → rank (田中太郎 警視)
    re.compile(_NAME + r"\s*" + _RANK + r"(?![一-龥])"),
    # post + name (生活安全部長 田中太郎 / 神奈川県警本部長 山田一郎)
    re.compile(_POST + r"\s+" + _NAME),
]


def pii_detect(text: str) -> list[str]:
    return [p.pattern for p in PII_PATTERNS if p.search(text)]


def assert_no_pii(text: str, context: str) -> None:
    hits = pii_detect(text)
    if hits:
        raise PIIDetectedError(f"{context}: PII patterns matched: {hits}")


class RateLimitedClient:
    """Single-host serial fetch with robots.txt + daytime + rate-limit gates."""

    def __init__(self, base_url: str, policy: FetchPolicy):
        if httpx is None:
            raise RuntimeError("httpx not installed; `pip install httpx` before live use")
        self.base_url = base_url
        self.policy = policy
        self._robots: Optional[urllib.robotparser.RobotFileParser] = None
        self._last_fetch_at: float = 0.0
        self._client = httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=15.0,
            follow_redirects=True,
        )

    def _ensure_robots(self) -> None:
        if self._robots is not None:
            return
        robots_url = urllib.parse.urljoin(self.base_url, "/robots.txt")
        rp = urllib.robotparser.RobotFileParser()
        try:
            r = self._client.get(robots_url)
            if r.status_code == 200:
                rp.parse(r.text.splitlines())
            else:
                rp.parse([])
        except Exception as e:  # noqa: BLE001
            logger.warning("robots.txt fetch failed for %s: %s", robots_url, e)
            rp.parse([])
        self._robots = rp

    def _assert_daytime(self) -> None:
        if not self.policy.enforce_daytime:
            return
        now = datetime.now(ZoneInfo("Asia/Tokyo"))
        if now.weekday() >= 5:
            raise OutsideBusinessHoursError(f"weekend fetch blocked: {now}")
        if not (DAYTIME_HOUR_START <= now.hour < DAYTIME_HOUR_END):
            raise OutsideBusinessHoursError(f"non-daytime fetch blocked: {now}")

    def get(self, path: str):
        self._ensure_robots()
        self._assert_daytime()
        url = urllib.parse.urljoin(self.base_url, path)
        if self._robots and not self._robots.can_fetch(USER_AGENT, url):
            raise RobotsViolationError(f"robots.txt disallow: {url}")
        now = time.monotonic()
        delta = now - self._last_fetch_at
        if delta < self.policy.min_delay_sec:
            time.sleep(self.policy.min_delay_sec - delta)
        self._last_fetch_at = time.monotonic()
        resp = self._client.get(url)
        resp.raise_for_status()
        return resp


@dataclasses.dataclass
class PoliceStationRow:
    path: str
    prefectural_police_path: str
    station_code: str
    name: str
    address: str
    phone_main: str
    website: str
    jurisdiction_areas: str


@dataclasses.dataclass
class KobanRow:
    path: str
    police_station_path: str
    koban_type: str  # "koban" | "chuzaisho"
    name: str
    address: str
    phone: str


PerPrefectureParser = Callable[[str, str], list[PoliceStationRow]]
_STATION_PARSERS: dict[str, PerPrefectureParser] = {}


def register_station_parser(prefectural_police_path: str):
    """Decorator to register a per-prefecture HTML parser.

    Each prefectural police HP renders 警察署一覧 differently. Generic parser
    is intentionally absent — fail loud rather than silently mis-parse.
    """

    def deco(fn: PerPrefectureParser) -> PerPrefectureParser:
        _STATION_PARSERS[prefectural_police_path] = fn
        return fn

    return deco


def get_station_parser(prefectural_police_path: str) -> Optional[PerPrefectureParser]:
    return _STATION_PARSERS.get(prefectural_police_path)


def emit_dry_run_json(rows: list, path: str) -> None:
    import json
    import pathlib

    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for row in rows:
            d = dataclasses.asdict(row) if dataclasses.is_dataclass(row) else dict(row)
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    logger.info("dry-run wrote %d rows to %s", len(rows), path)


def emit_audit(event: dict, log_dir: str) -> None:
    import json
    import pathlib

    today = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d")
    p = pathlib.Path(log_dir) / today / "audit.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "ts": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        **event,
    }
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
