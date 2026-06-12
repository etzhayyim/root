#!/usr/bin/env python3
"""tate 盾 — static site generator tests (wave 35). Pure stdlib.

「Google 検索ですぐアクセスできるか」の供給側を検証する:
  - 1法域=1ページ + index が生成され, sitemap が全ページを列挙する
  - 全ページに非裁定/UPL 免責が常設され, 断定語 (無効です) がない
  - FAQPage JSON-LD が valid JSON で, critical 期限が ⚠ 表示される
  - 広告・トラッキング・外部スクリプトが一切ない (Charter Rider)
"""
import sys
import json
import pathlib
import tempfile

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from site_gen import generate  # noqa: E402
from respond_plan import load_jurisdictions  # noqa: E402

_TMP = pathlib.Path(tempfile.mkdtemp()) / "site"
_PAGES = generate(_TMP, base="https://example.test/tate")


def test_one_page_per_jurisdiction():
    juris = load_jurisdictions()
    assert len(_PAGES) == len(juris) + 1  # + index
    for jid in juris:
        assert (_TMP / f"{jid.lstrip(':')}.html").exists(), jid


def test_disclaimer_on_every_page():
    for p in _PAGES:
        text = (_TMP / p).read_text(encoding="utf-8")
        assert "法的助言" in text and "非裁定" in text, p
        assert "無効です" not in text, p  # 断定しない (G2)


def test_no_tracking_no_external_assets():
    for p in _PAGES:
        text = (_TMP / p).read_text(encoding="utf-8").lower()
        for bad in ("gtag", "analytics", "googletagmanager", "facebook", "pixel",
                    "<script src=", "cdn."):
            assert bad not in text, (p, bad)


def test_faq_jsonld_valid_and_critical_marked():
    de = (_TMP / "de.html").read_text(encoding="utf-8")
    start = de.index('application/ld+json">') + len('application/ld+json">')
    end = de.index("</script>", start)
    ld = json.loads(de[start:end])
    assert ld["@type"] == "FAQPage" and len(ld["mainEntity"]) >= 4
    assert "⚠" in de and 'class="crit"' in de  # KSchG 3週間 etc.


def test_sitemap_lists_all_pages():
    sm = (_TMP / "sitemap.xml").read_text(encoding="utf-8")
    for p in _PAGES:
        assert f"https://example.test/tate/{p}</loc>" in sm
    assert (_TMP / "robots.txt").read_text(encoding="utf-8").startswith("User-agent: *")


def test_native_keywords_in_titles():
    """Wave 39 SEO: 現地語の手続き名が title/meta に入る — 現地ユーザーの検索語で
    届く (Mahnbescheid / desahucio / 지급명령 / dagvaarding …)."""
    checks = {"de.html": "Mahnbescheid", "es.html": "desahucio",
              "kr.html": "지급명령", "nl.html": "dagvaarding", "fr.html": "licenciement"}
    for page, kw in checks.items():
        head = (_TMP / page).read_text(encoding="utf-8").split("</head>")[0].casefold()
        assert kw.casefold() in head, (page, kw)


def test_deploy_copy_in_sync():
    """Wave 36: worker static (50-infra/etzhayyim-did-web/public/tate) の deploy copy
    は registry と同じページ集合でなければならない — registry が伸びたら
    site_gen.py --out ...public/tate で再生成を強制する (counts-sync と同じ forcing
    function; worker デプロイ自体は operator)."""
    deploy = ACTOR_DIR.parent.parent / "50-infra" / "etzhayyim-did-web" / "public" / "tate"
    assert deploy.exists(), "deploy copy missing — run site_gen --out .../public/tate"
    deployed = {p.name for p in deploy.glob("*.html")}
    fresh = {p for p in _PAGES if p.endswith(".html")}
    assert deployed == fresh, (sorted(fresh - deployed), sorted(deployed - fresh))
    sm = (deploy / "sitemap.xml").read_text(encoding="utf-8")
    assert "https://etzhayyim.com/tate/index.html" in sm
    assert not (deploy / "robots.txt").exists()  # robots はルート専用 — サブパスでは無効


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok {fn.__name__}")
    print(f"{len(fns)} passed")
