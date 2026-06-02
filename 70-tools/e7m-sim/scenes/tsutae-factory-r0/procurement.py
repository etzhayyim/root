#!/usr/bin/env python3
"""tsutae-factory-r0 — procurement enrichment (調達もと / 原産国 / リードタイム).

`building.edn` is the SSoT for 企業名 (:part/manufacturer) + 機器名/型番
(:part/product / :part/mpn / :part/purl). This module adds a *representative*
procurement layer on top — the 調達もと (商社・代理店・プラント), 原産国, and
nominal lead-time — without editing the SSoT, so the manufacturer data stays
authoritative and the supply-chain data is clearly a derived design assumption.

Everything here is `:representative` (R0 design selection), NOT a quotation,
purchase order, or confirmed distributor agreement. Confirm before buying.

`enrich_part(part) -> dict` returns extra kg/claim/part/* claims for one part:
  part/supplier   調達もと (商社・代理店・プラント)
  part/origin     原産国 (representative)
  part/leadTime   nominal lead-time (weeks)
  part/channel    direct (メーカー直販) | distributor (商社経由) | local (地場)
"""

# manufacturer(企業名) → (調達もと 商社/代理店, 原産国, lead_weeks, channel)
# Representative Japanese supply-chain routing for an industrial fit-out.
_SUPPLIER = {
    # ── structural steel / fasteners ──
    "JFE Steel": ("メタルワン (商社)", "JP", 8, "distributor"),
    "Nippon Steel": ("伊藤忠丸紅鉄鋼 (商社)", "JP", 10, "distributor"),
    "Nisshin Steel": ("阪和興業 (商社)", "JP", 8, "distributor"),
    "Hilti": ("ヒルティ・ジャパン (直販)", "LI/CN", 3, "direct"),
    # ── envelope / openings ──
    "IG Kogyo": ("アイジー工業 特約店", "JP", 6, "distributor"),
    "Bunka Shutter": ("文化シヤッター 直需", "JP", 7, "direct"),
    "Sankyo Tateyama": ("三協アルミ建材代理店", "JP", 5, "distributor"),
    "Lonseal": ("ロンシール工業 特約店", "JP", 4, "distributor"),
    # ── electrical ──
    "Nitto Kogyo": ("因幡電機産業 (電材商社)", "JP", 6, "distributor"),
    "Hitachi": ("日立産機システム 代理店", "JP", 10, "distributor"),
    "Panasonic": ("因幡電機産業 (電材商社)", "JP", 4, "distributor"),
    "Kawamura": ("河村電器 特約店", "JP", 5, "distributor"),
    "Nichido Denko": ("ネグロス/日動電工 商社", "JP", 4, "distributor"),
    "Furukawa Electric": ("古河電工 → 電線商社", "JP", 6, "distributor"),
    "Fujikura": ("フジクラ → 電線商社", "JP", 5, "distributor"),
    "Denyo": ("デンヨー 代理店", "JP", 6, "distributor"),
    "Iwasaki Electric": ("岩崎電気 特約店", "JP", 4, "distributor"),
    # ── water / sanitary ──
    "Kubota": ("クボタケミックス → 橋本総業", "JP", 4, "distributor"),
    "Sekisui": ("積水化学 → 橋本総業 (管材商社)", "JP", 3, "distributor"),
    "Ebara": ("荏原製作所 代理店", "JP", 6, "distributor"),
    "Mitsubishi": ("三菱電機 住環境 代理店", "JP", 5, "distributor"),
    "TOTO": ("TOTO → 住設商社 (橋本総業)", "JP", 4, "distributor"),
    "Hinode Suido": ("日之出水道機器 代理店", "JP", 5, "distributor"),
    # ── gas ──
    "Aichi Tokei": ("愛知時計電機 代理店", "JP", 6, "distributor"),
    "Yazaki": ("矢崎エナジーシステム 代理店", "JP", 5, "distributor"),
    # ── HVAC / pneumatics ──
    "Daikin": ("ダイキン工業 → 空調設備業者", "JP", 8, "distributor"),
    "SMC": ("SMC → エア機器商社 (山善)", "JP", 4, "distributor"),
    # ── fire / life-safety ──
    "Hochiki": ("ホーチキ → 消防設備業者", "JP", 8, "distributor"),
    "Morita Miyata": ("モリタ宮田工業 代理店", "JP", 3, "distributor"),
    "Senju Sprinkler": ("千住スプリンクラー → 消防設備業者", "JP", 8, "distributor"),
    # ── production machine tools / truck-line equipment ──
    "DMG Mori": ("DMG森精機 (直販)", "JP/DE", 16, "direct"),
    "Okuma": ("オークマ (直販)", "JP", 14, "direct"),
    "Mitutoyo": ("ミツトヨ (直販)", "JP", 10, "direct"),
    "Okura Yusoki": ("オークラ輸送機 直需", "JP", 12, "direct"),
    "Daifuku": ("ダイフク 直需", "JP", 18, "direct"),
    "Komatsu": ("コマツ産機 (直販)", "JP", 28, "direct"),
    "Taikisha": ("大気社 (直販, 塗装プラント)", "JP", 30, "direct"),
    "Meidensha": ("明電舎 (直販, ダイナモ)", "JP", 20, "direct"),
    # ── site / 外構 ──
    "Sankin": ("三協立山/サンキン 代理店", "JP", 4, "distributor"),
    "Saga Tekkohsho": ("佐賀鉄工所 代理店", "JP", 4, "distributor"),
    "Landes": ("ランデス 特約店", "JP", 4, "distributor"),
    "NIPPO": ("NIPPO 合材プラント (地場)", "JP", 1, "local"),
    "NTT": ("NTT東日本/西日本 (引込工事)", "JP", 8, "direct"),
    # ── raw materials / 原材料 ──
    "Sika": ("シーカ・ジャパン 代理店", "JP/CH", 3, "distributor"),
    "Nippon Paint": ("日本ペイント → 塗料商社", "JP", 3, "distributor"),
    "ABC Trading": ("ABC商会 (直販)", "JP", 3, "direct"),
    # ── tsutae handheld: electronics / cleanroom / passives (representative) ──
    "Murata": ("村田製作所 → 電子部品商社 (マクニカ/UKC)", "JP", 6, "distributor"),
    "Senju Metal": ("千住金属工業 (はんだ材, 直販)", "JP", 3, "direct"),
    "Oji Holdings": ("王子ホールディングス (パルプ成形, 直需)", "JP", 4, "direct"),
    "Daikin": ("ダイキン工業 → 空調設備業者", "JP", 8, "distributor"),
    "Organo": ("オルガノ (純水装置, 直販)", "JP", 8, "direct"),
    "Nicca": ("日華化学/エアシャワー専門業者", "JP", 6, "distributor"),
    "Nitta": ("ニッタ (FFU/HEPA, 代理店)", "JP", 6, "distributor"),
    "Atlas Copco": ("アトラスコプコ (直販)", "SE/JP", 8, "direct"),
    "Nohmi Bosai": ("能美防災 → 消防設備業者", "JP", 8, "distributor"),
    "Mitsubishi Electric": ("三菱電機 → 電材商社", "JP", 6, "distributor"),
    "Ube Mitsubishi Cement": ("UBE三菱セメント 生コンプラント (地場)", "JP", 1, "local"),
    "Panasonic": ("因幡電機産業 (電材商社)", "JP", 4, "distributor"),
    "JFE Steel": ("メタルワン (商社)", "JP", 8, "distributor"),
    "Nippon Steel": ("伊藤忠丸紅鉄鋼 (商社)", "JP", 10, "distributor"),
    "Nisshin Steel": ("阪和興業 (商社)", "JP", 8, "distributor"),
    "IG Kogyo": ("アイジー工業 特約店", "JP", 6, "distributor"),
    "Bunka Shutter": ("文化シヤッター 直需", "JP", 7, "direct"),
    "Sankyo Tateyama": ("三協アルミ建材代理店", "JP", 5, "distributor"),
    "Hitachi": ("日立産機システム 代理店", "JP", 10, "distributor"),
    "TOTO": ("TOTO → 住設商社 (橋本総業)", "JP", 4, "distributor"),
    "Hochiki": ("ホーチキ → 消防設備業者", "JP", 8, "distributor"),
    "open-hardware": ("オープンHW設計 → 受託製造 (EMS)", "JP/global", 8, "direct"),
    "open-hardware (GKG-iso)": ("オープンHW設計 → 受託製造 (EMS)", "JP/global", 8, "direct"),
}

# internal supplier DID → (friendly actor name, nominal R-phase availability).
# tsutae device parts (group P) sourced from sibling etzhayyim actors — the
# vendor-independence chain. NOT external procurement; an internal hand-off.
_INTERNAL_ACTOR = {
    "did:web:etzhayyim.com:silicon":  ("silicon (iwakura SoC/PMIC)", "R2+ gated"),
    "did:web:etzhayyim.com:igata":    ("igata (HPDC Al 筐体)", "R3 gated"),
    "did:web:etzhayyim.com:hikari":   ("hikari (LFP 電池/BMS)", "R2+ gated"),
    "did:web:etzhayyim.com:kuni-umi": ("kuni-umi (Otete/Mimi ロボ)", "R0 reuse"),
    "did:web:etzhayyim.com:tsutae":   ("tsutae (Tedama 自前装置)", "R2+ design"),
}

# manufacturers whose names start with a phrase → bucketed to a local plant
_LOCAL_HINTS = ("近隣", "地場", "水道局", "Tokyo Gas", "JIS")


def enrich_part(part):
    """Return extra procurement claims for a single building.edn part map."""
    mfr = part.get("part/manufacturer", "")
    proc = part.get("part/procurement", "")
    out = {}

    if proc == "internal" or part.get("part/supplier-did"):
        # supplied by a sibling etzhayyim actor (vendor-independence chain)
        did = part.get("part/supplier-did", "")
        name, phase = _INTERNAL_ACTOR.get(did, (did or "internal actor", "gated"))
        out["part/supplier"] = f"{name} (internal hand-off)"
        out["part/origin"] = "internal (etzhayyim actor)"
        out["part/leadTime"] = phase
        out["part/channel"] = "internal"
        return out

    # external ":representative" placeholder (string keyword) → not yet selected
    if mfr in (":representative", "representative"):
        out["part/supplier"] = "要選定 (external, :representative)"
        out["part/origin"] = "要確認"
        out["part/leadTime"] = "要見積"
        out["part/channel"] = "distributor"
        return out

    if proc == "custom-fab" and not mfr:
        # commissioned / cast / welded on site
        out["part/supplier"] = "施工JV / 専門工事業者 (発注)"
        out["part/origin"] = "JP (on-site fab)"
        out["part/leadTime"] = "施工計画依存"
        out["part/channel"] = "subcontract"
        return out

    # exact match, else hint-based local, else generic distributor fallback
    entry = _SUPPLIER.get(mfr)
    if entry is None and any(h in mfr for h in _LOCAL_HINTS):
        out["part/supplier"] = f"{mfr} (地場プラント/指定業者)"
        out["part/origin"] = "JP"
        out["part/leadTime"] = "1-2 週"
        out["part/channel"] = "local"
        return out
    if entry is None:
        out["part/supplier"] = f"{mfr} 代理店 (要確認)" if mfr else "要選定"
        out["part/origin"] = "要確認"
        out["part/leadTime"] = "要見積"
        out["part/channel"] = "distributor"
        return out

    supplier, origin, weeks, channel = entry
    out["part/supplier"] = supplier
    out["part/origin"] = origin
    out["part/leadTime"] = f"{weeks} 週 (代表値)"
    out["part/channel"] = channel
    return out


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path
    from kotoba_gen import parse_edn  # reuse the EDN reader

    here = Path(__file__).resolve().parent
    doc = parse_edn((here / "building.edn").read_text(encoding="utf-8"))
    parts = doc["bom/parts"]
    rows = []
    for p in parts:
        e = enrich_part(p)
        rows.append({"id": p["part/id"], "manufacturer": p.get("part/manufacturer", ""),
                     "product": p.get("part/product", ""), **e})
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    n_dist = sum(1 for r in rows if r.get("part/channel") == "distributor")
    n_dir = sum(1 for r in rows if r.get("part/channel") == "direct")
    n_loc = sum(1 for r in rows if r.get("part/channel") == "local")
    n_sub = sum(1 for r in rows if r.get("part/channel") == "subcontract")
    print(f"# parts={len(rows)} direct={n_dir} distributor={n_dist} local={n_loc} subcontract={n_sub}",
          file=sys.stderr)
