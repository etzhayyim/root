#!/usr/bin/env python3
"""Seed curated Hugging Face dataset quality catalog rows into RisingWave.

This intentionally stores catalog/reliability metadata, not full dataset
payloads. Huge audio/image/video/text corpora should pass a separate artifact
availability, license, PII, and dedupe gate before row/blob ingest.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

import psycopg2 # kotoba-datomic-projection: historical offline script


OWNER_DID = "did:web:ingest.etzhayyim.com"
COLLECTION_ID = "multimodal-poc-curated-v1"
COLLECTION_VID = f"hf:dataset-collection:{COLLECTION_ID}"
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
HF_API = "https://huggingface.co/api/datasets"


@dataclass(frozen=True)
class Candidate:
    repo_id: str
    modality: str
    stage: str
    role: str
    rank: int
    license_hint: str
    commercial_use: str
    artifact_availability: str
    text_alignment: str
    card_quality: float
    license_score: float
    availability_score: float
    alignment_score: float
    curation_score: float
    contamination_risk: int
    pii_risk: int
    copyright_risk: int
    eval_leakage_risk: int
    duplicate_risk: int
    decision: str
    rationale: str


CANDIDATES: list[Candidate] = [
    Candidate("openslr/librispeech_asr", "audio", "encoder_pretraining", "english_asr_alignment", 1, "cc-by-4.0", "yes", "hosted", "strong", 0.92, 0.86, 0.92, 0.95, 0.94, 1, 1, 1, 1, 2, "use", "Stable ASR baseline; audio and transcript alignment are explicit."),
    Candidate("google/fleurs", "audio", "text_alignment", "multilingual_asr_alignment", 2, "cc-by-4.0", "yes", "hosted", "strong", 0.90, 0.86, 0.90, 0.95, 0.92, 1, 1, 1, 1, 2, "use", "Multilingual speech/text coverage across 100+ languages."),
    Candidate("lmms-lab/DocVQA", "document", "instruction_tuning", "document_vqa", 1, "unknown", "review", "hosted", "strong", 0.86, 0.55, 0.86, 0.92, 0.90, 1, 2, 2, 2, 2, "pilot", "Useful for document QA; license and source constraints need per-use review."),
    Candidate("ds4sd/DocLayNet", "document", "encoder_pretraining", "layout_detection", 2, "cdla-permissive-2.0", "yes", "hosted", "medium", 0.91, 0.90, 0.88, 0.70, 0.92, 1, 1, 1, 1, 1, "use", "Curated document layout annotations with permissive license."),
    Candidate("BIFOLD-BigEarthNetv2-0/BigEarthNet.txt", "geospatial", "text_alignment", "geo_image_text_alignment", 1, "cc-by-4.0", "yes", "hosted", "strong", 0.90, 0.86, 0.84, 0.94, 0.92, 1, 1, 1, 1, 2, "use", "Sentinel image pairs plus text annotations; good geo-image-text alignment source."),
    Candidate("HuggingFaceM4/COCO", "image", "text_alignment", "image_caption_detection", 1, "coco-terms", "review", "hosted", "strong", 0.88, 0.60, 0.86, 0.95, 0.93, 1, 1, 2, 2, 2, "pilot", "Canonical image-caption/detection dataset; commercial/legal review still needed."),
    Candidate("ranjaykrishna/visual_genome", "image", "instruction_tuning", "region_grounding_vqa", 2, "visual-genome-terms", "review", "external_or_partial", "strong", 0.84, 0.50, 0.68, 0.96, 0.92, 2, 1, 2, 2, 3, "pilot", "Strong local region descriptions and VQA; artifact availability varies."),
    Candidate("ai-for-data/TabBench", "tabular", "evaluation", "tabular_reasoning_benchmark", 1, "mit", "yes", "hosted", "medium", 0.87, 0.95, 0.84, 0.70, 0.90, 1, 2, 1, 2, 2, "use", "Aggregated tabular benchmark for classification/regression."),
    Candidate("inria-soda/tabular-benchmark", "tabular", "evaluation", "tabular_baseline_suite", 2, "bsd-3-clause", "yes", "hosted", "medium", 0.84, 0.92, 0.84, 0.68, 0.88, 1, 2, 1, 2, 2, "use", "Research-grade tabular benchmark suite."),
    Candidate("HuggingFaceFW/fineweb-edu", "text", "encoder_pretraining", "educational_web_text", 1, "odc-by", "yes", "hosted", "text_native", 0.90, 0.82, 0.88, 1.00, 0.92, 2, 2, 2, 2, 3, "use", "Curated educational subset; preferred first text backbone for PoC."),
    Candidate("HuggingFaceFW/fineweb", "text", "encoder_pretraining", "web_text_backbone", 2, "odc-by", "yes", "hosted", "text_native", 0.86, 0.82, 0.88, 1.00, 0.84, 3, 2, 3, 2, 3, "pilot", "Large CommonCrawl-derived corpus; useful after dedupe and filtering."),
    Candidate("allenai/dolma", "text", "encoder_pretraining", "mixed_text_backbone", 3, "odc-by", "yes", "hosted", "text_native", 0.88, 0.82, 0.86, 1.00, 0.88, 2, 2, 2, 2, 3, "pilot", "Well-documented large mixed corpus for text backbone comparison."),
    Candidate("Monash-University/monash_tsf", "timeseries", "evaluation", "forecasting_benchmark", 1, "custom", "review", "hosted", "weak", 0.87, 0.60, 0.86, 0.40, 0.92, 1, 1, 1, 1, 1, "pilot", "Established forecasting benchmark collection; text alignment is weak by design."),
    Candidate("HuggingFaceM4/ActivitiyNet_Captions", "video", "text_alignment", "video_caption_alignment", 1, "activitynet-terms", "review", "external_links", "strong", 0.82, 0.45, 0.55, 0.92, 0.86, 2, 1, 3, 2, 3, "pilot", "Useful video-caption baseline, but URL availability and rights require review."),
    Candidate("SakanaAI/JA-VG-VQA-500", "japanese_multimodal", "evaluation", "japanese_vqa_smoke", 1, "unknown", "review", "hosted", "strong", 0.78, 0.55, 0.80, 0.90, 0.80, 1, 1, 2, 2, 2, "pilot", "Small Japanese VQA smoke set for Japanese multimodal regression checks."),
    Candidate("Roman1111111/claude-opus-4.6-10000x", "text", "instruction_tuning", "reasoning_conversation_sft", 4, "mit", "yes", "hosted", "text_native", 0.66, 0.95, 0.90, 1.00, 0.58, 3, 2, 2, 3, 3, "pilot", "Already ingested; synthetic reasoning data, useful but needs contamination checks."),
    Candidate("angrygiraffe/claude-opus-4.6-4.7-reasoning-8.7k", "text", "instruction_tuning", "reasoning_conversation_sft", 5, "apache-2.0", "yes", "hosted", "text_native", 0.70, 0.95, 0.90, 1.00, 0.62, 3, 2, 2, 3, 3, "pilot", "Already ingested from canonical full_train.jsonl; synthetic reasoning SFT."),
]


def hf_info(repo_id: str) -> dict[str, Any]:
    url = f"{HF_API}/{repo_id}"
    headers = {"Accept": "application/json"}
    token = os.environ.get("HF_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {"id": repo_id, "status_error": f"http_{exc.code}"}
    except Exception as exc:
        return {"id": repo_id, "status_error": f"{type(exc).__name__}: {exc}"}


def clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def risk_penalty(c: Candidate) -> float:
    return (
        c.contamination_risk
        + c.pii_risk
        + c.copyright_risk
        + c.eval_leakage_risk
        + c.duplicate_risk
    ) / 25.0


def trust_score(c: Candidate, info: dict[str, Any]) -> float:
    metadata_penalty = 0.08 if info.get("status_error") else 0.0
    score = (
        0.18 * c.card_quality
        + 0.18 * c.license_score
        + 0.16 * c.availability_score
        + 0.18 * c.alignment_score
        + 0.20 * c.curation_score
        + 0.10 * (1.0 - risk_penalty(c))
        - metadata_penalty
    )
    return round(clamp(score), 4)


def tier(score: float) -> str:
    if score >= 0.88:
        return "A"
    if score >= 0.78:
        return "B"
    if score >= 0.70:
        return "C"
    return "D"


def card_license(info: dict[str, Any], fallback: str) -> str:
    card = info.get("cardData") if isinstance(info.get("cardData"), dict) else {}
    lic = info.get("license") or card.get("license") or fallback
    if isinstance(lic, list):
        return ",".join(str(x) for x in lic)
    return str(lic or fallback)


def main() -> None:
    rw_url = os.environ.get("KOTOBA_URL") or os.environ.get("DATABASE_URL")
    if not rw_url:
        raise SystemExit("Set KOTOBA_URL or DATABASE_URL")

    def exec_retry(sql: str, params: tuple[Any, ...]) -> None:
        last: Exception | None = None
        for attempt in range(4):
            conn = None
            cur = None
            try:
                conn = psycopg2.connect(rw_url)
                conn.autocommit = True
                cur = conn.cursor()
                cur.execute(sql, params)
                cur.close()
                conn.close()
                return
            except Exception as exc:  # RisingWave may reset connections during recovery.
                last = exc
                try:
                    if cur is not None:
                        cur.close()
                    if conn is not None:
                        conn.close()
                except Exception:
                    pass
                time.sleep(5 * (attempt + 1))
        assert last is not None
        raise last

    def fetch_one(sql: str, params: tuple[Any, ...] = ()) -> tuple[Any, ...]:
        conn = psycopg2.connect(rw_url)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(sql, params)
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row or (None,)

    exec_retry(
        """INSERT INTO vertex_hf_dataset_collection
        (vertex_id, sensitivity_ord, owner_did, collection_id, display_name,
         purpose, selection_policy, target_model_scope, status, created_at,
         updated_at, org_id, user_id, actor_id)
        VALUES (%s, 0, %s, %s, %s, %s, %s, %s, 'active', %s, %s, %s, %s, %s)""",
        (
            COLLECTION_VID,
            OWNER_DID,
            COLLECTION_ID,
            "Curated multimodal PoC dataset set v1",
            "Bootstrap a multimodal training/evaluation dataset catalog with reliability gates.",
            "Curated over trending: license, artifact availability, text alignment, risk, and role separation.",
            "text,image,document,audio,video,geospatial,tabular,timeseries,japanese-multimodal",
            NOW,
            NOW,
            OWNER_DID,
            OWNER_DID,
            "sys.hf.dataset.quality.seed",
        ),
    )

    for c in CANDIDATES:
        info = hf_info(c.repo_id)
        repo_id = str(info.get("id") or c.repo_id)
        author = repo_id.split("/", 1)[0] if "/" in repo_id else ""
        downloads = int(info.get("downloads") or 0)
        likes = int(info.get("likes") or 0)
        license_value = card_license(info, c.license_hint)
        trust = trust_score(c, info)
        vid = f"hf:dataset-reliability:{c.repo_id}"
        hfhub_vid = f"hf:dataset:{c.repo_id}"
        hf_dataset_vid = f"at://{OWNER_DID}/com.etzhayyim.apps.hfDataset.dataset/{c.repo_id.replace('/', '-')}"

        exec_retry(
            """INSERT INTO vertex_hfhub_dataset
            (vertex_id, repo_id, author, sha, license, downloads_month, likes,
             gated, disabled, private, description, card_data, status,
             last_scanned_at, actor_did, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s::timestamp, %s, %s::timestamp)""",
            (
                hfhub_vid,
                c.repo_id,
                author,
                str(info.get("sha") or ""),
                license_value,
                downloads,
                likes,
                bool(info.get("gated") or False),
                bool(info.get("disabled") or False),
                bool(info.get("private") or False),
                str(info.get("description") or "")[:4000],
                json.dumps(info.get("cardData") or {}, ensure_ascii=False)[:8000],
                "error" if info.get("status_error") else "active",
                NOW.replace("T", " ").replace("Z", ""),
                OWNER_DID,
                NOW.replace("T", " ").replace("Z", ""),
            ),
        )

        exec_retry(
            """INSERT INTO vertex_hf_dataset_reliability
            (vertex_id, sensitivity_ord, owner_did, repo_id, hf_dataset_vertex_id,
             hfhub_dataset_vertex_id, primary_modality, training_stage,
             recommended_role, license, commercial_use, artifact_availability,
             text_alignment, card_quality_score, license_score,
             availability_score, alignment_score, curation_score,
             contamination_risk_ord, pii_risk_ord, copyright_risk_ord,
             eval_leakage_risk_ord, duplicate_risk_ord, hub_downloads_month,
             hub_likes, trust_score, trust_tier, decision, rationale,
             source_url, observed_at, status, created_at, updated_at, org_id,
             user_id, actor_id)
            VALUES (%s, 0, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, 'active', %s, %s, %s, %s, %s)""",
            (
                vid,
                OWNER_DID,
                c.repo_id,
                hf_dataset_vid,
                hfhub_vid,
                c.modality,
                c.stage,
                c.role,
                license_value,
                c.commercial_use,
                c.artifact_availability,
                c.text_alignment,
                c.card_quality,
                c.license_score,
                c.availability_score,
                c.alignment_score,
                c.curation_score,
                c.contamination_risk,
                c.pii_risk,
                c.copyright_risk,
                c.eval_leakage_risk,
                c.duplicate_risk,
                downloads,
                likes,
                trust,
                tier(trust),
                c.decision,
                c.rationale if not info.get("status_error") else f"{c.rationale} metadata_status={info['status_error']}",
                f"https://huggingface.co/datasets/{c.repo_id}",
                NOW,
                NOW,
                NOW,
                OWNER_DID,
                OWNER_DID,
                "sys.hf.dataset.quality.seed",
            ),
        )

        exec_retry(
            """INSERT INTO edge_hf_dataset_collection_member
            (edge_id, sensitivity_ord, owner_did, src_vid, dst_vid,
             collection_id, repo_id, primary_modality, training_stage,
             rank_in_modality, required_for_poc, member_status, rationale,
             created_at, org_id, user_id, actor_id)
            VALUES (%s, 0, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active',
                    %s, %s, %s, %s, %s)""",
            (
                f"hf:dataset-collection-member:{COLLECTION_ID}:{c.repo_id}",
                OWNER_DID,
                COLLECTION_VID,
                vid,
                COLLECTION_ID,
                c.repo_id,
                c.modality,
                c.stage,
                c.rank,
                c.rank == 1 or c.decision == "use",
                c.rationale,
                NOW,
                OWNER_DID,
                OWNER_DID,
                "sys.hf.dataset.quality.seed",
            ),
        )

        exec_retry(
            """INSERT INTO edge_hf_dataset_reliability_about
            (edge_id, sensitivity_ord, owner_did, src_vid, dst_vid, repo_id,
             relation_kind, confidence, created_at, org_id, user_id, actor_id)
            VALUES (%s, 0, %s, %s, %s, %s, 'scores_hfhub_dataset', %s,
                    %s, %s, %s, %s)""",
            (
                f"hf:dataset-reliability-about:{c.repo_id}",
                OWNER_DID,
                vid,
                hfhub_vid,
                c.repo_id,
                0.9 if not info.get("status_error") else 0.4,
                NOW,
                OWNER_DID,
                OWNER_DID,
                "sys.hf.dataset.quality.seed",
            ),
        )

    reliability_count = int(fetch_one(
        "SELECT count(*) FROM vertex_hf_dataset_reliability WHERE status = 'active'"
    )[0])
    member_count = int(fetch_one(
        "SELECT count(*) FROM edge_hf_dataset_collection_member WHERE collection_id = %s",
        (COLLECTION_ID,),
    )[0])
    print({"ok": True, "collection_id": COLLECTION_ID, "reliability_rows": reliability_count, "member_rows": member_count})


if __name__ == "__main__":
    main()
