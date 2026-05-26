from __future__ import annotations

import io
import math
import struct
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BaseObservation(BaseModel):
    model_config = ConfigDict(extra="allow")

    actorDid: str
    createdAt: int
    tier: Literal["A", "B", "C"]
    internal_only: bool = False


class TextObservation(BaseObservation):
    kind: Literal["text"] = "text"
    text: str
    _suspicious: bool = False

    @field_validator("text")
    @classmethod
    def normalize_and_check(cls, v: str) -> str:
        from pymagatama.organism.adversarial.normalizer import normalize_input
        res = normalize_input(v)
        if res.suspicious:
            raise ValueError("Suspicious adversarial input detected in text observation")
        return res.normalized


class ImageObservation(BaseObservation):
    kind: Literal["image"] = "image"
    image: Union[bytes, str]  # base64 encoded bytes or file path
    mime_type: str
    pii_filter_applied: bool = False


class AudioObservation(BaseObservation):
    kind: Literal["audio"] = "audio"
    audio: Union[bytes, str]
    sample_rate: int
    channels: int


class NumericObservation(BaseObservation):
    kind: Literal["numeric"] = "numeric"
    value: float
    unit: str
    context: dict[str, Union[str, float, int]] | None = None


class TimeseriesObservation(BaseObservation):
    kind: Literal["timeseries"] = "timeseries"
    values: list[float]
    timestamps: list[int]
    unit: str


Observation = Annotated[
    Union[
        TextObservation,
        ImageObservation,
        AudioObservation,
        NumericObservation,
        TimeseriesObservation,
    ],
    Field(discriminator="kind"),
]


@dataclass
class JouchoDelta:
    kankaku: int = 0
    kanjou: int = 0
    yokkyu: int = 0
    kakushin: int = 0
    seimei: int = 0


def image_joucho_delta(obs: ImageObservation) -> JouchoDelta:
    from PIL import Image

    if isinstance(obs.image, bytes):
        img = Image.open(io.BytesIO(obs.image))
    else:
        img = Image.open(obs.image)

    img = img.convert("HSV")
    h_data, s_data, _ = img.split()

    s_hist = s_data.histogram()
    total_pixels = sum(s_hist)
    if total_pixels == 0:
        return JouchoDelta()

    s_mean = sum(i * count for i, count in enumerate(s_hist)) / total_pixels

    h_hist = h_data.histogram()
    entropy = 0.0
    for count in h_hist:
        if count > 0:
            p = count / total_pixels
            entropy -= p * math.log2(p)

    # High saturation -> kanjou, seimei
    kanjou_delta = int((s_mean / 255.0) * 10)
    seimei_delta = int((s_mean / 255.0) * 5)

    # High hue entropy -> kankaku
    kankaku_delta = int(entropy)

    return JouchoDelta(kankaku=kankaku_delta, kanjou=kanjou_delta, seimei=seimei_delta)


def audio_joucho_delta(obs: AudioObservation) -> JouchoDelta:
    samples = []
    width = 2
    if isinstance(obs.audio, bytes):
        try:
            with wave.open(io.BytesIO(obs.audio), "rb") as w:
                frames = w.readframes(w.getnframes())
                width = w.getsampwidth()
                fmt = f"<{len(frames) // width}{'h' if width == 2 else 'B'}"
                samples = struct.unpack(fmt, frames)
        except wave.Error:
            # Fallback to raw 16-bit PCM
            frames = obs.audio
            fmt = f"<{len(frames) // 2}h"
            samples = struct.unpack(fmt, frames[: len(frames) // 2 * 2])
    else:
        with wave.open(str(obs.audio), "rb") as w:
            frames = w.readframes(w.getnframes())
            width = w.getsampwidth()
            fmt = f"<{len(frames) // width}{'h' if width == 2 else 'B'}"
            samples = struct.unpack(fmt, frames)

    if not samples:
        return JouchoDelta()

    rms = math.sqrt(sum(float(s) * s for s in samples) / len(samples))
    normalized_rms = rms / (32768.0 if width == 2 else 256.0)

    kankaku_delta = int(normalized_rms * 20)
    yokkyu_delta = int(normalized_rms * 10) # loud sounds increase drive

    return JouchoDelta(kankaku=kankaku_delta, yokkyu=yokkyu_delta)


def numeric_joucho_delta(obs: NumericObservation, baseline: float) -> JouchoDelta:
    drift = obs.value - baseline
    # Quantile-drift signed delta
    # Large drift reduces certainty (kakushin)
    kakushin_delta = -int(abs(drift) * 5)

    # Large drift increases alertness/drive (yokkyu)
    yokkyu_delta = int(abs(drift) * 2)

    return JouchoDelta(kakushin=kakushin_delta, yokkyu=yokkyu_delta)


def timeseries_joucho_delta(obs: TimeseriesObservation) -> JouchoDelta:
    if len(obs.values) < 2:
        return JouchoDelta()

    # Simple trend slope
    slope = obs.values[-1] - obs.values[0]

    yokkyu_delta = int(slope * 2)
    kakushin_delta = -int(abs(slope))

    return JouchoDelta(yokkyu=yokkyu_delta, kakushin=kakushin_delta)

