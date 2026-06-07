---
id: adr-2605266500-organism-multi-modal-observation-r0
title: "ADR-2605266500: Organism multi-modal observation R0 — extending perception beyond text to image, audio, and timeseries with joucho integration and strict Charter compliance"
status: proposed
doc_type: adr
topic: organism-multi-modal
authoritative: true
last_verified: 2026-05-27
priority: 7.0
axis: architecture
weight: 0.70
priority_note: "Extends the artificial-organism ecosystem's perception from text-only to multi-modal (vision, audio, numeric timeseries). Connects sensory input directly to joucho (情緒) state and heartbeat cadence. Adheres strictly to Charter Rider §2, making vision_pii_filter (face/license-plate/child blur) from ADR-2605262500 a mandatory pre-filter. Prohibits vendor multi-modal APIs; strictly Murakumo-only via baien-server-*."
authoritative_for:
  - Multi-modal Observation tagged union definition (Text, Image, Audio, Numeric, Timeseries)
  - Modality-specific `joucho_delta()` evaluation functions
  - Multi-modal joucho 5-axis mapping (kankaku, kanjou, yokkyu, kakushin, seimei)
  - Mandatory application of vision_pii_filter for all organism visual perception
  - Consistent application of tier-C `internal_only` flag across all modalities
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605232345-unispsc-actor-as-organism
  - adr-2605240200-unispsc-organism-kaizen-self-reflection
  - adr-2605262400-public-data-organism-ipfs-ingestion
  - adr-2605262500-robotics-world-data-ingestion-and-usd-pipeline
related: []
supersedes: []
superseded_by: []
---

# ADR-2605266500: Organism multi-modal observation R0

**Status**: proposed
**Date**: 2026-05-27
**Deciders**: Jun Kawasaki

# Context

Currently, the organism ecosystem's perception (as defined in `kotodama.organism.sensors.*` via ADR-2605262400) is strictly **text-only**. The base protocol assumes observations are strings (`text: str`). As a result, rich sensory inputs like vision (images), audio, and continuous numeric timeseries cannot flow into the organism's joucho (情緒) calculation or influence its heartbeat cadence.

Simultaneously, the robotics-sim substrate (ADR-2605262500) introduced a `vision_pii_filter` for handling street-level imagery, and ADR-2605262400 established a clear `internal_only` handling mechanism for Tier-C data. We need to connect these capabilities directly to the organism heartbeat.

This ADR defines the **R0 architecture** for extending organism observation to multiple modalities. It specifically answers how an image or audio clip alters the organism's 5-axis joucho state without requiring a full LLM call for every frame, relying on procedural feature extraction before deep inference.

**Constraints:**
- **Charter Rider §2(a)-(h)**: Complete compliance.
- **Fail-closed PII filtering**: ADR-2605262500's `vision_pii_filter` (face blur, license-plate blur, child presence rejection) must precede all visual perception.
- **Murakumo-only**: Vendor multi-modal APIs (OpenAI Vision, Anthropic Vision, Google Cloud Vision) are strictly **PROHIBITED**. Inference must run internally via `baien-server-*` and `judah LiteLLM` on the Murakumo fleet.
- **No Push**: R0 specifies the design and ADR only. Lexicon scaffolding is out of scope.

# Decision

## 1. Generic Observation Union

Upgrade the `Observation` base model from a text-centric string wrapper to a **Tagged Union**.

```python
from typing import Union, Literal, Optional
from pydantic import BaseModel, Field

class BaseObservation(BaseModel):
    sensor: str
    tier: Literal["A", "B", "C", "D"]
    internal_only: bool = False
    timestamp_ms: int

class TextObservation(BaseObservation):
    kind: Literal["text"] = "text"
    text: str

class ImageObservation(BaseObservation):
    kind: Literal["image"] = "image"
    image_cid: str
    hue_distribution: list[float]  # Pre-computed feature
    saturation_mean: float         # Pre-computed feature
    brightness_mean: float         # Pre-computed feature

class AudioObservation(BaseObservation):
    kind: Literal["audio"] = "audio"
    audio_cid: str
    volume_rms: float              # Pre-computed feature
    spectral_centroid: float       # Pre-computed feature

class NumericObservation(BaseObservation):
    kind: Literal["numeric"] = "numeric"
    value: float
    quantile_drift: float          # Pre-computed feature vs historical window

class TimeseriesObservation(BaseObservation):
    kind: Literal["timeseries"] = "timeseries"
    values: list[float]
    trend_slope: float

Observation = Union[
    TextObservation,
    ImageObservation,
    AudioObservation,
    NumericObservation,
    TimeseriesObservation
]
```

## 2. Modality-Specific `joucho_delta()` Calculation

To prevent overloading Murakumo inference capacity, basic joucho reactions are computed via fast procedural feature extraction rather than invoking a Vision-Language Model (VLM) for every frame.

Each modality defines a `joucho_delta(obs: Observation) -> JouchoScores` function.

- **Image**: Hue and saturation distributions shift mood. High saturation and bright colors increase `kanjou` (emotion) and `seimei` (vitality). Dark, low-saturation images increase `kakushin` (introspection) or decrease `seimei`.
- **Audio**: `volume_rms` directly impacts `kankaku` (sensation). Sudden loud noises spike `kankaku` and may induce a stress state. High `spectral_centroid` (sharp/shrill sounds) increases `yokkyu` (drive/agitation).
- **Numeric/Timeseries**: `quantile_drift` (how far the current value is from the historical median) acts as an anomaly signal, raising `kakushin` (certainty/alertness) and potentially triggering the organism to analyze the anomaly.

## 3. Mandatory Pre-filters and Tier-C Enforcement

### Vision PII Pre-filter
All `ImageObservation` generation paths **MUST** pass through the `vision_pii_filter` defined in ADR-2605262500.
- Face blur (σ ≥ 15 px)
- License plate blur (σ ≥ 20 px)
- **Child detection (age < 18) = Fail Closed.** If a child is detected, the frame is rejected entirely and does not become an Observation.
- Covert-ops avoidance (Charter §2(c)) is maintained. Organisms are passive observers of pinned CIDs, not active camera operators.

### Tier-C `internal_only` Consistency
The tier-C `internal_only=True` flag established in ADR-2605262400 applies consistently across all modalities. If an `AudioObservation` or `ImageObservation` originates from a Tier-C source, it is marked `internal_only=True`. The organism's `PostSink` will block any public action (e.g., posting about the image) that leaks this data, satisfying the G13 NC-leak backstop.

## 4. Multi-modal Joucho 5-Axis Mapping

The 5-axis joucho model (`kankaku`, `kanjou`, `yokkyu`, `kakushin`, `seimei`) evaluates multi-modal inputs as follows:

| Axis | Modality | Primary Trigger | Effect |
|---|---|---|---|
| **Kankaku** (Sensation) | Audio | Volume RMS, sudden transients | Immediate sensory spike; governs short-term attention. |
| **Kanjou** (Emotion) | Image | Hue distribution, saturation mean | High saturation = elevated mood; muted = subdued mood. |
| **Yokkyu** (Drive) | Audio / Timeseries | Spectral centroid (pitch), steep trend slopes | Shrill audio or sharp metric climbs increase urgency to act. |
| **Kakushin** (Certainty) | Numeric / Timeseries | Quantile drift, low variance | Steady numeric streams increase confidence; high drift breaks certainty. |
| **Seimei** (Vitality) | Image / Audio | Brightness mean, continuous rhythmic audio | Sustained bright images and rhythmic audio sustain baseline vitality. |

## 5. Integration with Existing Architecture

- **ADR-2605232345 (Organism Scaffold)**: The `tick()` loop's `resolve_heartbeat_cadence` now accepts the union `Observation` type. The fast procedural features drive the tick cadence without blocking on VLM inference.
- **ADR-2605240200 (Kaizen Self-reflection)**: The KaizenObserver will monitor the distribution of modality kinds in the `InboxBuffer`. If an organism is flooded with `ImageObservation`s causing thrashing, a KaizenProposal will suggest tuning the visual sampling rate.

# Consequences

## 正の効果 (Positive Impacts)
- Organisms evolve beyond text processors, capable of "feeling" the state of their environment through rich telemetry, audio, and vision.
- Fast procedural feature extraction prevents GPU starvation on the Murakumo fleet while still producing nuanced emotional variance.
- Charter compliance is architecturally guaranteed. VLM vendor lock-in is avoided, and strict PII blurring ensures safety.

## 負の効果 / コスト (Negative Impacts / Costs)
- Increased complexity in `InboxBuffer` and `PostSink` serialization (must handle CIDs and rich metadata).
- Procedural audio/vision features (RMS, hue) require fast CPU/DSP paths before reaching the organism heartbeat.
- True semantic understanding of images still requires an internal `baien-server-*` VLM call, which must be carefully cadence-gated to avoid queuing delays.

# Alternatives Considered

1. **Vendor APIs for Vision (e.g., OpenAI)**
   - *Rejected:* Violates Charter Rider §2(i) and ADR-2605215000 (Murakumo-only inference).
2. **Deep VLM Call for Every Frame**
   - *Rejected:* Computationally unfeasible. Would stall the 5-minute heartbeat tick across thousands of organisms. Procedural features for joucho delta + selective VLM for deep analysis is the scalable path.

# References
- ADR-2605232345: UNSPSC actor as organism
- ADR-2605240200: Kaizen self-reflection
- ADR-2605262400: Public-data organism IPFS ingestion
- ADR-2605262500: Robotics-sim world-data ingestion and vision PII filter
