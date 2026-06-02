"""HakkenState — shared state across all pipeline nodes."""

from __future__ import annotations

from typing import Literal, TypedDict


class BrandedProduct(TypedDict):
    name: str
    brand: str
    category: str
    price_jpy: int
    url: str
    material: str | None


class OemCandidate(TypedDict):
    name: str
    platform: str          # "aliexpress" | "alibaba" | "1688"
    item_id: str
    url: str
    price_jpy: int
    weight_kg: float
    rating: float
    review_count: int
    material: str | None
    thickness_cm: int | None
    washable: bool
    lead_days: int
    min_order: int
    supplier_country: str
    equivalent_of: str | None  # branded product name


class ReviewScore(TypedDict):
    item_id: str
    grade: str             # "S" | "A" | "B" | "C" | "D"
    score: int             # 0-100
    quality: float
    usability: float
    cost_performance: float
    satisfaction: float
    sustainability: float


class ApprovedSku(TypedDict):
    oem_candidate: OemCandidate
    branded_product: BrandedProduct
    margin: float
    phase: Literal["dropship", "import", "oem"]
    review_score: ReviewScore
    sell_price_jpy: int


class HakkenState(TypedDict):
    category: str                          # e.g. "mattress" | "pillow"
    branded_products: list[BrandedProduct] # from kakaku XRPC
    oem_candidates: list[OemCandidate]     # from AliExpress / 1688 scraper
    kotoba_cids: list[str]                 # datom CIDs ingested into kotoba
    review_scores: dict[str, ReviewScore]  # item_id → score
    approved_skus: list[ApprovedSku]       # passed phase_router
    registered_okaimono_ids: list[str]     # okaimono item IDs created
    errors: list[str]                      # non-fatal errors accumulated
