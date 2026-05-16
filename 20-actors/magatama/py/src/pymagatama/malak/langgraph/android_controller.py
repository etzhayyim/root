"""android_controller — LangGraph node wrapping ADB for Android device drive.

Surfaces a small set of safe primitives + a `scrape_line_screen` composite
that captures the current LINE app screen as PNG + UI hierarchy XML.

Prerequisites
-------------
- adb installed (homebrew: `brew install --cask android-commandlinetools`)
- ANDROID_HOME / PATH set (see Yoro CLAUDE.md §Android)
- Device paired:
    USB:  enable USB debugging → `adb devices` shows `<serial>\tdevice`
    WiFi: enable Wireless debugging → `adb pair <ip>:<port>` (one-time)
          → `adb connect <ip>:5555` (persistent)

Usage
-----
    from pymagatama.malak.langgraph.android_controller import (
        AndroidController, scrape_line_screen_node
    )

    ctrl = AndroidController()  # auto-pick first connected device
    print(ctrl.list_devices())
    print(ctrl.foreground_app())
    res = ctrl.scrape_line_screen()  # returns {"png_b64":..., "ui_xml":...}

Or as a LangGraph node:
    g.add_node("scrape_line", scrape_line_screen_node)
"""

from __future__ import annotations

import base64
import os
import shlex
import subprocess
from dataclasses import dataclass
from typing import Any, TypedDict


ADB = os.environ.get(
    "ADB_BIN",
    "/opt/homebrew/share/android-commandlinetools/platform-tools/adb",
)

LINE_PACKAGE = "jp.naver.line.android"
LINE_LAUNCH_INTENT = (
    "monkey -p jp.naver.line.android -c android.intent.category.LAUNCHER 1"
)


class AdbError(RuntimeError):
    """adb call failed."""


@dataclass
class Device:
    serial: str
    state: str  # 'device' | 'offline' | 'unauthorized' | ...


class AndroidController:
    """Thin sync wrapper over adb."""

    def __init__(self, serial: str | None = None, adb: str = ADB) -> None:
        self.adb = adb
        self.serial = serial

    def _run(self, args: list[str], *, binary: bool = False, timeout: float = 30.0) -> bytes | str:
        cmd = [self.adb]
        if self.serial:
            cmd += ["-s", self.serial]
        cmd += args
        try:
            out = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                timeout=timeout,
            )
        except subprocess.CalledProcessError as e:
            raise AdbError(f"adb {' '.join(map(shlex.quote, args))} failed: "
                           f"rc={e.returncode} stderr={e.stderr.decode(errors='replace')!r}") from e
        except FileNotFoundError as e:
            raise AdbError(f"adb not found at {self.adb!r}") from e
        return out.stdout if binary else out.stdout.decode("utf-8", errors="replace")

    def list_devices(self) -> list[Device]:
        text = self._run(["devices"])  # type: ignore[assignment]
        assert isinstance(text, str)
        devs: list[Device] = []
        for line in text.splitlines()[1:]:
            parts = line.split("\t")
            if len(parts) == 2:
                devs.append(Device(serial=parts[0].strip(), state=parts[1].strip()))
        return devs

    def ensure_device(self) -> Device:
        devs = [d for d in self.list_devices() if d.state == "device"]
        if not devs:
            raise AdbError("no connected device in 'device' state (pair via USB or `adb connect <ip>`)")
        if self.serial is None:
            self.serial = devs[0].serial
        return devs[0]

    def shell(self, cmd: str, *, timeout: float = 15.0) -> str:
        out = self._run(["shell", cmd], timeout=timeout)
        assert isinstance(out, str)
        return out

    def foreground_app(self) -> str:
        text = self.shell("dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'")
        return text.strip()

    def launch_line(self) -> None:
        self.shell(LINE_LAUNCH_INTENT)

    def screencap_png(self, *, timeout: float = 15.0) -> bytes:
        png = self._run(["exec-out", "screencap", "-p"], binary=True, timeout=timeout)
        assert isinstance(png, bytes)
        return png

    def ui_hierarchy_xml(self, *, timeout: float = 20.0) -> str:
        # `uiautomator dump /dev/tty` is unreliable across versions; dump to file then pull.
        dump_path = "/sdcard/window_dump.xml"
        self.shell(f"uiautomator dump {dump_path}", timeout=timeout)
        out = self._run(["exec-out", "cat", dump_path], binary=True, timeout=timeout)
        assert isinstance(out, bytes)
        return out.decode("utf-8", errors="replace")

    def tap(self, x: int, y: int) -> None:
        self.shell(f"input tap {int(x)} {int(y)}")

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> None:
        self.shell(
            f"input swipe {int(x1)} {int(y1)} {int(x2)} {int(y2)} {int(duration_ms)}"
        )

    def back(self) -> None:
        self.shell("input keyevent KEYCODE_BACK")

    def home(self) -> None:
        self.shell("input keyevent KEYCODE_HOME")

    def scrape_line_screen(self) -> dict[str, str]:
        """Composite: bring LINE foreground, capture screen + UI XML."""
        self.ensure_device()
        self.launch_line()
        # let UI settle; uiautomator dump fails on transitions
        self.shell("sleep 1.2")
        png = self.screencap_png()
        ui = self.ui_hierarchy_xml()
        return {
            "png_b64": base64.b64encode(png).decode("ascii"),
            "ui_xml": ui,
            "foreground": self.foreground_app(),
        }


# ────────────────────────────────────────────────────────────────────
# LangGraph node helpers
# ────────────────────────────────────────────────────────────────────

class AndroidState(TypedDict, total=False):
    adb_serial: str
    foreground: str
    png_b64: str
    ui_xml: str
    error: str


def scrape_line_screen_node(state: AndroidState) -> dict:
    """LangGraph sync node — returns LINE screen capture + UI tree."""
    try:
        ctrl = AndroidController(serial=state.get("adb_serial"))
        return ctrl.scrape_line_screen()
    except AdbError as e:
        return {"error": str(e)}


def list_devices_node(state: AndroidState) -> dict:
    try:
        ctrl = AndroidController(serial=state.get("adb_serial"))
        devs = [{"serial": d.serial, "state": d.state} for d in ctrl.list_devices()]
        return {"devices": devs}  # type: ignore[return-value]
    except AdbError as e:
        return {"error": str(e)}
