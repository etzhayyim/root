---
id: adr-2605265000-creative-pd-substrate-for-baien-training-r0
title: "ADR-2605265000: Public-domain creative-works substrate (film / video / music / audio) for baien training via IPFS-pinned DataLad subdatasets — sibling of ADR-2605262400 + ADR-2605262800 + ADR-2605263800 + ADR-2605263900"
status: proposed
doc_type: adr
topic: creative-pd-substrate-r0
authoritative: true
last_verified: 2026-05-26
priority: 6.5
axis: training-corpus
weight: 0.55
priority_note: "Extends the religious-corp public-data ingestion family (ADR-2605262400 geo/netreg/web + ADR-2605262800 legal + ADR-2605263800 corporate + ADR-2605263900 open-government) with the `creative-pd/` bucket family covering four modalities: 映画 (film) + 映像 (video) + 音楽 (music; both symbolic and recordings) + 音声 (audio; speech + sound). Powers baien-distill creative-foundations recipe family + manabi arts/civic-literacy curriculum primary-source citations + ossekai Public-Domain-Day annual Jan 1 advisory. **Constitutional decet G1..G10**: G1 per-work PD attestation MANDATORY (7-jurisdiction matrix; no blanket-PD assumption) / G2 multi-juris pessimistic threshold (admitted only if PD in ALL of US/EU/UK/JP/AU/CA/CN; defaults to most-restrictive 70-yr p.m.a. baseline) / G3 music dual-copyright STRUCTURAL (composition PD AND recording PD both required for audio bucket; symbolic-only sidesteps recording layer) / G4 PASSIVE-ONLY ingestion (inherit ADR-2605262400 §G7; no live scraping; pre-pinned IPFS snapshot only) / G5 NO commercial vendor (Adobe Stock / Getty / Shutterstock / Pond5 / Audio Network / paid PD-collections PROHIBITED per Charter Rider §2(e)) / G6 memorization guardrail (3-pronged eval: verbatim regurgitation probe ≤1% / DP-SGD ε≤8.0 R3+ / Chromaprint spectral-fingerprint distance ≥0.2 for audio) / G7 Charter Rider §2(d) Wellbecoming framing scan per work (pre-1929 content auto-flag for racial-content review; manual at R1, rule-encoded R2+) / G8 attribution chain MANDATORY (every baien-distill artifact traces back to source work via attestation CID) / G9 Murakumo-only inference (inherit ADR-2605215000) / G10 memorization eval evidence emission to `90-docs/baien/creative-memorization-eval-{R-step}.jsonl` per training run. **Cross-juris contradiction resolution** (URAA + similar): per-work `jurisdictionConflictResolution` field captures conflicts; pessimistic algorithm rejects ANY work failing PD in even one of 7 jurisdictions; URAA-restored 1925-1935 European works become eligible only after US restoration expires + other jurisdictions remain PD. **8 non-goals N1..N8**: NOT training on copyright-active works (no fair-use carve-out R0-R3) / NOT orphan-works training (research-only carve-out R3+ Council Lv6+ ≥3) / NOT commercial-license-vendor ingestion / NOT blanket-PD-assumption (per-work attestation mandatory) / NOT memorization-infringing generative output (G6 enforces) / NOT removal of attribution chain (G8 mandatory) / NOT Tier-B NHK external publication (G13 fleet-internal carve-out per ADR-2605262100 precedent) / NOT US-only PD (multi-juris pessimistic threshold mandatory). 7 Lexicons under `com.etzhayyim.creative.*`: publicDomainStatusAttestation (G1+G2+G3 STRUCTURAL) + tierBNhkLicenseAttestation (CC-BY 2.1 JP carve-out) + tierBCcByAttestation (CC-BY 3.0/4.0 + CC-BY-SA carve-out with attribution-chain) + orphanWorkResearchAttestation (R3+ Council Lv6+ ≥3; research-only) + wellbecomingFramingScan (G7) + creativeMemorizationEvalReport (G6) + jurisdictionConflictResolution (URAA + similar)."
authoritative_for:
  - creative-pd substrate single SoT
  - com.etzhayyim.creative.* Lexicon namespace boundary
  - baien-distill creative-foundations recipe family
  - per-work PD attestation methodology
  - multi-jurisdictional pessimistic threshold algorithm
  - memorization guardrail eval methodology
  - prohibition on commercial creative-content vendors (Adobe Stock / Getty / Shutterstock / Pond5 / Audio Network)
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605231300-baien-distill-react-loop
  - adr-2605241500-etzhayyim-dataset-cid-substrate
  - adr-2605262100-baien-moemoekyun-r1-phase0-coding-train
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605262400-public-data-organism-ipfs-ingestion
  - adr-2605262800-public-data-legal-corpus-ipfs-ingestion
  - adr-2605264000-ossekai-information-arbitrage-tier-b-actor-r0
  - adr-2605261045
related: []
supersedes: []
superseded_by: []
---

# ADR-2605265000: Public-domain creative-works substrate (film / video / music / audio) for baien training via IPFS-pinned DataLad subdatasets

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

Religious-corp has substantial training-corpus infrastructure for
**textual** public-data (legal corpus per ADR-2605262800; geographic
/ netreg / web per ADR-2605262400; corporate disclosure per
ADR-2605263800; open government per ADR-2605263900). What it lacks
is a substrate for **creative works in non-textual modalities** —
film, video, music, audio — drawn from the global public-domain
commons.

User request (2026-05-26 /loop session):

> 映画、映像、音楽、音声などで著作権が切れているものを
> datalad, ipfs remote pin で 学習できるように設計してください.

The design need spans four modalities with distinct copyright
mechanics:

| Modality | Primary copyright layer(s) | Conservative-cutoff complication |
|---|---|---|
| 映画 (film) | Single work copyright | Multi-juris term variance (US 95 yr from publication for pre-1978; EU 70 yr p.m.a.) |
| 映像 (video, broader) | Single work copyright; sometimes orphan | Newsreels often orphan; field recordings sometimes orphan |
| 音楽 (music) | **Dual layer**: composition + sound recording (each separate copyright) | Symbolic-only sidesteps recording layer; audio requires both PD |
| 音声 (audio) | Sound-recording copyright + sometimes performer's right | Pre-1972 US sound recordings governed by state law until MMA 2018 phased PD |

Critical constitutional constraints:

- **NOT training on copyright-active works** (N1) — religious-corp
  has no fair-use carve-out at R0-R3; per-work PD attestation is
  mandatory before any work enters baien-distill training corpus;
- **NOT blanket-PD assumption** (N4) — many sources publish under
  "Public Domain" labels but per-work verification is required
  (publisher may have misattributed; work may be URAA-restored in
  some jurisdictions);
- **NOT memorization-infringing generative output** (N5) — even when
  training data is PD, trained model output must NOT reproduce
  non-PD memorized content from training-set adjacency;
- **NOT commercial-license-vendor ingestion** (N3) — Adobe Stock /
  Getty / Shutterstock / Pond5 / Audio Network / paid PD-collections
  PROHIBITED per Charter Rider §2(e) anti-gatekeeping;
- **NOT US-only PD** (N8) — multi-jurisdictional pessimistic
  threshold required (work must be PD in ALL of US/EU/UK/JP/AU/CA/CN);
- **NOT orphan-works training** (N2) — orphan works carry unbounded
  copyright-claim risk; research-only carve-out at R3+ via Council
  Lv6+ ≥3, NEVER admitted to training corpus.

# Decision

Create the `creative-pd/` bucket family under the existing IPFS-pinned
DataLad substrate (per ADR-2605241500 + ADR-2605262400), covering
four modalities (film / video / music / audio) with per-work PD
attestation + multi-juris pessimistic threshold + memorization
guardrail at training-time + Charter Rider §2(d) Wellbecoming
framing scan.

## §1. Scope (4 modalities)

| Modality | Tier-A primary sources (R1) | Tier-B carve-out | Tier-C / R3+ |
|---|---|---|---|
| **Film** | Internet Archive `/details/feature_films` PD subset / EYE Filmmuseum PD / Library of Congress NAVCC / NASA + US federal AV | NHK Creative Library video (CC-BY 2.1 JP) | Orphan films research carve-out (Council Lv6+ ≥3) |
| **Video** | Prelinger newsreels / NASA imagery+video / Wikimedia Commons CC0+PD-flagged | NHK Creative Library video | Orphan newsreels research carve-out |
| **Music (symbolic)** | Mutopia Project (scores) / IMSLP (scores) | — | — |
| **Music (recordings)** | Musopen PD-flagged audio / Wikimedia Commons PD audio | NHK Creative Library audio | Pre-1923 78rpm orphan recordings (R3+ Council) |
| **Audio (speech)** | LibriVox (CC0+PD audiobook narration) / LoC American Folklife PD subset | NHK Creative Library audio | Oral history orphan recordings |
| **Audio (sound)** | British Library Sounds PD-flagged / archive.org `oldtimeradio` PD subset | NHK Creative Library audio | Pre-1972 radio orphan recordings |

## §2. Bucket layout

```
e7m-dataset:creative-pd/
├── films/<source>/<work-id>/
│   ├── <media-file>.{mp4,mkv}     (IPFS-pinned)
│   ├── attestation.json            → publicDomainStatusAttestation
│   ├── source-metadata.json
│   └── wellbecoming-framing.json   → Charter Rider §2(d) scan
├── video/<source>/<work-id>/
├── music/
│   ├── compositions/<source>/<work-id>/    (Mutopia, IMSLP symbolic)
│   └── recordings/<source>/<work-id>/      (audio recordings — dual-attestation)
└── audio/
    ├── speech/<source>/<work-id>/           (LibriVox audiobooks)
    ├── folklife/<source>/<work-id>/         (oral history)
    └── radio-pd/<source>/<work-id>/         (pre-1972 US radio PD subset)
```

Per-work directory structure mirrors the legal-corpus pattern of
ADR-2605262800. Per-source datasetPin records under
`com.etzhayyim.substrate.datasetPin` per ADR-2605241500.

## §3. Multi-jurisdictional PD term matrix (2026 baseline)

| Jurisdiction | Composition term | Sound recording term | Performer's right | Conservative cutoff |
|---|---|---|---|---|
| **US** | 70 yr p.m.a. post-1978 / 95 yr from publication pre-1978 | Pre-1972 state law → 2067 (MMA 2018); 1923-1956 progressive PD | (no traditional separate right) | Pre-1929 baseline; URAA §104A check |
| **EU/EEA** | 70 yr p.m.a. | 70 yr from publication | 70 yr from performance/release | d.≤1956 + recording ≥70 yr |
| **UK** | 70 yr p.m.a. | 70 yr from publication | 70 yr from publication | Same as EU |
| **JP** | 50 yr p.m.a. (pre-2018) / 70 yr p.m.a. (post-2018 TPP) | 70/50 yr from publication | 70/50 yr | Pessimistic: d.≤1956 + ≥70 yr recording |
| **AU** | 70 yr p.m.a. | 70 yr from publication | 70 yr from performance | Same as EU (AUSFTA 2005) |
| **CA** | 70 yr p.m.a. (post-2022 CUSMA) / 50 yr (pre-2022) | 70/50 yr | 50 yr from performance | Pessimistic: d.≤1956 |
| **CN** | 50 yr p.m.a. | 50 yr | 50 yr | Aligned via intersection rule |

**Pessimistic algorithm** (`admit_audio_recording`):
```
if composition_pd_in_all_7_jurisdictions(work) is False: return REJECT
if recording_pd_in_all_7_jurisdictions(work) is False: return REJECT
if has_performer(work) and performer_right_pd_in_all_7(work) is False: return REJECT
return ADMIT
```

**2026 safe-cutoff**: composition author d.≤1956 + recording ≥56 yr +
all performers d.≤1956. Symbolic-only (Mutopia/IMSLP) sidesteps
recording layer entirely.

**URAA + cross-juris contradiction**: per-work
`jurisdictionConflictResolution` field; pessimistic = REJECT any work
failing in even one jurisdiction.

## §4. Sensor families (`kotodama.organism.sensors.creative.*`)

R1 W1 anchor sensors:

| Sensor | Source | Tier | Modality |
|---|---|---|---|
| `creative_audio_librivox_sensor` | LibriVox.org CC0 audiobook narration | A | audio-speech |
| `creative_music_mutopia_sensor` | Mutopia Project sheet music + MIDI + MusicXML | A+B | music-symbolic |
| `creative_film_internet_archive_sensor` | archive.org `/details/feature_films` PD subset | A | film |

R2 expansion:

| Sensor | Source | Tier | Modality |
|---|---|---|---|
| `creative_video_prelinger_sensor` | Prelinger Archive (newsreels) | A | video |
| `creative_video_nasa_sensor` | NASA public AV catalog | A | video |
| `creative_music_imslp_sensor` | IMSLP CC0/PD audio + scores | A+B | music-symbolic + music-recording |
| `creative_audio_lc_folklife_sensor` | Library of Congress American Folklife | A | audio-speech + audio-sound |
| `creative_video_wikimedia_commons_sensor` | Wikimedia Commons CC0+PD video | A+B | video |

R3+ Tier-B + orphan-works:

| Sensor | Source | Tier | Notes |
|---|---|---|---|
| `creative_nhk_library_sensor` | NHK Creative Library (CC-BY 2.1 JP) | B (NC carve-out) | Fleet-internal G13; not externally published |
| `creative_orphan_research_sensor` | Per-work Council Lv6+ ≥3 attested orphans | R3+ research-only | NOT admitted to training |

`pd_status_cross_verifier_sensor` — cross-references HathiTrust /
Standard Ebooks / Public Domain Review for status confirmation.

## §5. Lexicons (7, all under `com.etzhayyim.creative.*`)

| # | Lexicon | Purpose |
|---|---|---|
| L1 | `publicDomainStatusAttestation` | Per-work PD status × jurisdiction matrix (G1+G2+G3 STRUCTURAL; minLength 7 jurisdictions; pessimisticThresholdYearsPostMortem ≥70; music modality requires both compositionPdStatus AND recordingPdStatus) |
| L2 | `tierBNhkLicenseAttestation` | NHK Creative Library CC-BY 2.1 JP per-clip tracker (G13 fleet-internal carve-out; nonCommercialAffirmation const true) |
| L3 | `tierBCcByAttestation` | CC-BY 3.0/4.0 + CC-BY-SA 3.0/4.0 per-work attribution chain (Wikimedia Commons + Mutopia Tier-B carve-out) |
| L4 | `orphanWorkResearchAttestation` | R3+ orphan-works research carve-out (Council Lv6+ ≥3; diligent-search documented; work ≥95 yr old; research-only NOT training) |
| L5 | `wellbecomingFramingScan` | G7 Charter Rider §2(d) per-work review (R1 manual; R2+ rule-encoded; auto-flag → Council ≥3 queue) |
| L6 | `creativeMemorizationEvalReport` | G6 3-pronged eval at `commit_node` (verbatim probe + DP-SGD ε≤8.0 R3+ + Chromaprint distance ≥0.2 for audio) |
| L7 | `jurisdictionConflictResolution` | URAA + similar cross-juris conflicts; pessimistic-REJECT default |

## §6. Gates (10, immutable R0..R3, Council Lv6+ to amend)

| Gate | Description |
|---|---|
| **G1** | Per-work PD attestation MANDATORY (`publicDomainStatusAttestation` REQUIRED before fetch admission; multi-juris matrix ≥7 jurisdictions covered) |
| **G2** | Multi-jurisdictional pessimistic threshold — work admitted only if PD in ALL of {US, EU, UK, JP, AU, CA, CN}; defaults to most-restrictive jurisdiction (typically 70 yr p.m.a.) |
| **G3** | Music dual-copyright STRUCTURAL — symbolic-only admitted; composition PD + recording PD admitted to audio bucket; composition PD + recording locked = REJECT for audio (symbolic still OK) |
| **G4** | PASSIVE-ONLY ingestion (inherit ADR-2605262400 §G7; pre-pinned IPFS snapshot only) |
| **G5** | NO commercial vendor — Adobe Stock / Getty / Shutterstock / Pond5 / Audio Network / paid PD-collections PROHIBITED per Charter Rider §2(e) |
| **G6** | Memorization guardrail — `creativeMemorizationEvalReport` REQUIRED at every `commit_node`; verbatim regurgitation ≤1% on 50-token probe; DP-SGD ε ≤8.0 / δ ≤1e-5 where feasible (R3+); spectral-fingerprint Chromaprint distance ≥0.2 vs non-PD reference for audio |
| **G7** | Charter Rider §2(d) Wellbecoming framing scan per work — pre-1929 racist/sexist content flagged; R1 manual review per-work; R2+ rule-encoded heuristics (pre-1929 + US Southern setting / WWI/WWII newsreels / 1920s exotic travelogue) auto-flag to Council Lv6+ ≥3 queue (admit / admit-with-context / exclude) |
| **G8** | Attribution chain MANDATORY — every baien-distill artifact carries source-work CID chain |
| **G9** | Murakumo-only inference (inherit ADR-2605215000; commercial AI for memorization eval prohibited) |
| **G10** | Memorization eval evidence emission to `90-docs/baien/creative-memorization-eval-{R-step}.jsonl` per training run |

## §7. Non-goals (8, immutable R0..R3)

| # | Non-goal |
|---|---|
| N1 | NOT training on copyright-active works (no fair-use carve-out at R0-R3) |
| N2 | NOT orphan-works training (research-only carve-out R3+ via Council Lv6+ ≥3; NEVER admitted to baien-distill corpus) |
| N3 | NOT commercial-license-vendor ingestion (Adobe Stock / Getty / Shutterstock / Pond5 / Audio Network / paid PD-collections PROHIBITED) |
| N4 | NOT blanket-PD assumption — per-work attestation MANDATORY; publisher's PD label is necessary but insufficient |
| N5 | NOT memorization-infringing generative output — G6 enforces |
| N6 | NOT removal of attribution chain (G8 mandatory) |
| N7 | NOT Tier-B NHK external publication — G13 fleet-internal carve-out per ADR-2605262100 R1.4 precedent |
| N8 | NOT US-only PD — multi-jurisdictional pessimistic threshold mandatory |

## §8. Roadmap (R0 → R3)

| Phase | Date / gate | Scope | Per-fleet-node storage |
|---|---|---|---|
| **R0** | 2026-05-26 (this ADR) | Scaffold only. Sensors path-reserved. 7 Lexicons schema skeleton. | 0 GB |
| **R1** | post-Bootstrap-Council ratify + baien-distill `commit_node` G6 eval framework live + Charter Rider scan extension for §2(d) | 3 sensors (creative_audio_librivox + creative_music_mutopia + creative_film_internet_archive) + first baien-distill recipe per modality + first verbatim regurgitation + Chromaprint eval | ~50 GB |
| **R2** | post-R1 + 30-day public objection + first 4-source attestation cycle + manabi arts-literacy curriculum integration | +5 sensors (creative_video_prelinger + creative_video_nasa + creative_music_imslp + creative_audio_lc_folklife + creative_video_wikimedia_commons) + Wikimedia Commons per-file filter live + manabi cross-actor wired | ~200 GB |
| **R3** | post-R2 + Council Lv7+ unanimity + DP-SGD eval framework + 4-quarter G6 compliance + first published `baien-creative-*` artifact | All sources + NHK Tier-B carve-out activated + orphan-works research carve-out (per-work Council Lv6+ ≥3) + DP-SGD ε≤8.0 enabled | ~500 GB |

## §9. Cross-actor

| Cross-actor | Direction | Purpose |
|---|---|---|
| `e7m-dataset` (ADR-2605262400) | ← | Parent ingestion framework + PASSIVE-ONLY discipline + datasetPin pattern |
| `baien-moemoekyun` (ADR-2605262100) | ↔ | `commit_node` G6 memorization-eval enforcement; training-time inference via Murakumo |
| `manabi` (ADR-2605261045) | ↔ | Arts-literacy + civic-literacy curriculum primary-source citations (Tier-A only) |
| `ossekai` (ADR-2605264000) | ↔ | Annual "Public Domain Day" Jan 1 advisory feed-post — newly-PD works of the year |
| `chigiri` (ADR-2605262700) | ↔ | Multi-juris PD verification consultation at R2+ + orphan-works carve-out procedural attestation |
| `kotoba` (ADR-2605262130) | ← | Storage substrate; kotoba-kqe arrangements |

## §10. Cold-path corpus assembler

```
70-tools/baien-moemoekyun-train/scripts/assemble-creative-pd-corpus.py
```

Streams source → per-work attestation → Charter Rider §2(d) scan →
modality-specific preprocessing → NDJSON shard write → IPFS pin →
publish-ipfs CID → `com.etzhayyim.substrate.datasetPin` emit.

Per-modality preprocessing handlers at
`70-tools/baien-moemoekyun-train/scripts/preprocess/`:
- `audio_speech_handler.py` (pyAudio 16kHz mono + 30-sec chunks)
- `audio_sound_handler.py` (chunk + spectrogram + Chromaprint)
- `music_symbolic_handler.py` (MusicXML → REMI-style token sequence)
- `music_recording_handler.py` (audio preprocess + Chromaprint)
- `video_film_handler.py` (24→8 fps frame downsample + scene-boundary + audio sidecar)
- `video_general_handler.py` (similar; lower constraints)

## §11. R1 training recipes

`70-tools/baien-moemoekyun-train/recipes/creative/`:

| Recipe | Modality | Sources |
|---|---|---|
| `creative-audio-speech-foundations-r1.toml` | audio-speech | LibriVox |
| `creative-music-symbolic-foundations-r1.toml` | music-symbolic | Mutopia |
| `creative-film-vision-foundations-r1.toml` | film | Internet Archive PD feature_films |

R2 recipes:
| Recipe | Modality | Sources |
|---|---|---|
| `creative-video-temporal-foundations-r1.toml` | video | Prelinger + NASA |
| `creative-music-recording-foundations-r1.toml` | music-recording | Musopen PD + Wikimedia Commons |
| `creative-audio-sound-foundations-r1.toml` | audio-sound | British Library + archive.org oldtimeradio |
| `creative-audio-folklife-foundations-r1.toml` | audio-speech | LoC American Folklife |

## §12. R0 deliverables (this commit)

1. This ADR (`90-docs/adr/2605265000-creative-pd-substrate-for-baien-training-r0.md`);
2. 7 Lexicon JSON schema skeletons under `00-contracts/lexicons/com/etzhayyim/creative/` (R0 paths reserved; iteration 6+ writes);
3. Sensor scaffold paths reserved under `kotodama.organism.sensors.creative.*` (R0 path-reserved; iteration 7+ writes);
4. Recipe templates path-reserved under `70-tools/baien-moemoekyun-train/recipes/creative/` (R1 writes);
5. Cold-path corpus assembler skeleton at `70-tools/baien-moemoekyun-train/scripts/assemble-creative-pd-corpus.py` (R1 writes);
6. deps.toml [[adrs]] + [[modules]] entries;
7. 90-docs/adr/README.md index update;
8. CLAUDE.md Status table row.

No code activation in R0.

# Consequences

**Positive**:

- Closes the creative-modality gap in religious-corp training-corpus
  infrastructure — baien-distill creative-foundations recipes are now
  defined, multi-modality (film + video + music + audio);
- Per-work PD attestation + multi-juris pessimistic threshold +
  memorization guardrail = three-layer defense against copyright
  infringement claims;
- Symbolic-only music subset (Mutopia + IMSLP scores) sidesteps the
  music recording-copyright complication and offers a clean R1
  starting point;
- LibriVox is the cleanest first audio sensor — CC0 by donor
  declaration + PD-text source (Gutenberg etc.) double-clean;
- Internet Archive PD feature_films is the cleanest first film
  sensor — already curated by archivists with per-work PD basis;
- Cross-actor manabi arts-literacy integration gives religious-corp
  members + community direct primary-source access to PD creative
  heritage;
- ossekai annual Public-Domain-Day Jan 1 advisory creates a
  community ritual surfacing newly-PD works each year (cross-actor
  Wellbecoming nudge);
- G7 Charter Rider §2(d) scan + R1 manual + R2+ rule-encoded
  curation framework prevents naive ingestion of historically
  harmful content (1920s newsreels with racial caricature, etc.);
- G6 3-pronged memorization-eval methodology (verbatim probe +
  Chromaprint + DP-SGD R3+) is a structural defense against
  generative output infringing non-PD content via memorization.

**Negative / cost**:

- Per-work PD attestation is operationally expensive — each work
  requires 7-jurisdiction status verification + legal-basis-document
  generation; ramp at R1 limited to ~1000 works per source;
- Multi-juris pessimistic threshold REJECTS many works that would be
  PD in some jurisdictions but not others (URAA-restored 1925-1935
  European works; CC vs CA pre-2022 deltas);
- Charter Rider §2(d) curation is manual at R1 — operational burden;
  R2+ rule-encoded auto-flag reduces but doesn't eliminate human review;
- G6 memorization eval at every `commit_node` adds eval compute
  overhead; DP-SGD at R3+ adds 2-3× training compute;
- Storage scale-up (~500 GB per fleet node at R3) is substantial;
  Murakumo fleet capacity headroom check required;
- Orphan-works deferred to R3+ research-only means some valuable
  PD-but-attribution-unknown works are out of scope through R2;
- NHK Creative Library Tier-B G13 fleet-internal carve-out means
  NHK-trained artifacts cannot be externally published (constrains
  baien-creative-* model release);
- Cross-actor with ossekai requires ossekai R1+ active for annual
  Public-Domain-Day advisory; bootstrap dependency.

**Forward-compatibility**:

- Future modalities (3D models from PD source; haptic data;
  smell/taste data via PD chemistry archives) can extend the
  `creative-pd/` bucket family without re-architecting;
- Cross-religious-corp federation potential: PD creative corpus is
  jurisdiction-agnostic and could federate via AT Protocol if a
  future federated religious-corp emerges;
- baien-creative-* model lineage establishes a creative-modality
  branch separate from baien-coder (ADR-2605262100) and
  baien-server-moemoekyun-* (ADR-2605261900);
- manabi arts-literacy curriculum could extend to community-creative
  programs (workshop curricula citing PD primary sources);
- ossekai annual Public-Domain-Day pattern could extend to other
  annual milestones (Charter Rider anniversaries, Council elections,
  etc.).

# Alternatives Considered

1. **Use Creative Commons CC-BY licenses indiscriminately**.
   Rejected — CC-BY ≠ PD; attribution chain mandatory creates
   downstream artifact tagging complexity. Tier-B carve-out admits
   CC-BY 3.0/4.0 with explicit attribution-chain Lexicon.

2. **US-only PD (forgo multi-juris check)**. Rejected per N8 —
   religious-corp operates multi-jurisdictionally; US-only PD has
   substantial cross-juris exposure (URAA-restored works, etc.).

3. **Include orphan works in R1 training corpus**. Rejected per N2 —
   post-hoc copyright-claim risk is unbounded; orphan-works carve-out
   is research-only at R3+ via Council Lv6+ ≥3.

4. **Skip memorization guardrail (rely on training-set-size dilution
   alone)**. Rejected per N5 + G6 — recent research demonstrates LLMs
   can memorize and verbatim-regurgitate ≥50-token sequences from
   small subsets of training data; structural eval mandatory.

5. **Use Getty Images PD-collection or similar commercial vendor for
   cleaner metadata**. Rejected per N3 + Charter Rider §2(e) anti-
   gatekeeping + §2(c) vendor query-tracking exposes member training-
   data interest profile.

6. **Train baien-creative-* directly without cold-path assembler**.
   Rejected — Charter Rider §2(d) scan + PII filter + per-work
   attestation generation requires cold-path; hot-path organism
   sensor is for perception (bounded sample), not training corpus.

7. **Allow Tier-C deferred for unverifiable PD claims**. Rejected at
   R0-R3 — pessimistic = REJECT unverified; R3+ Council Lv6+ ≥3 per
   work for any non-Tier-A admission.

# References

- ADR-2605170900 — etzhayyim/root canonical home for ADRs
- ADR-2605192100 — Mission Charter (G7 Charter Rider §2(d) source)
- ADR-2605192200 — Charter Compliance Rider v2.0 (G5 + Charter Rider §2(e) source)
- ADR-2605215000 — Inference Murakumo-only (G9 source)
- ADR-2605231300 — baien-distill commit_node gate (G6 + G10 emission point)
- ADR-2605241500 — Dataset CID substrate via DataLad + IPFS pinner
- ADR-2605261045 — manabi education actor (cross-actor arts-literacy curriculum)
- ADR-2605262100 — baien-moemoekyun R1 (G13 fleet-internal NC carve-out precedent)
- ADR-2605262130 — Kotoba storage substrate
- ADR-2605262400 — Public-data ingestion via IPFS-pinned DataLad (parent framework)
- ADR-2605262800 — Global legal corpus ingestion (sibling pattern)
- ADR-2605264000 — ossekai information-arbitrage actor (cross-actor Public-Domain-Day advisory)
- US Copyright Office "Orphan Works: Statement of Best Practices" 2015
- 17 USC §302 (US copyright term post-1978)
- Directive 2006/116/EC (EU copyright term harmonization)
- 著作権法 第51条 (Japan copyright term post-2018 TPP)
- Sonny Bono Copyright Term Extension Act 1998 (US)
- Music Modernization Act 2018 (US pre-1972 sound recordings)
- Uruguay Round Agreements Act 1994 §104A (US URAA restoration)
- LibriVox Project (CC0 PD audiobook narration)
- Mutopia Project (PD sheet music)
- Internet Archive `/details/feature_films` PD subset
- Chromaprint / AcoustID (audio fingerprint library)
- opacus (PyTorch DP-SGD library)
