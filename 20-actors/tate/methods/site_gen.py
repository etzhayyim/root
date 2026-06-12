#!/usr/bin/env python3
"""tate 盾 — crawlable static site generator (wave 35, R2).

「google 検索したらすぐアクセスできるか?」への答えを作る: registry を人間可読・
クロール可能な静的 HTML に射影する。1法域 = 1ページ (受け取った通知への応答期限・
防御選択肢・相談先・詐欺ガード + 不利条項パターン), index は coverage matrix と
critical 失権期限 census。schema.org FAQPage JSON-LD で検索リッチリザルトに対応し,
sitemap.xml / robots.txt を同梱する。

CONSTITUTIONAL:
  - 全ページに G2/G3 免責ヘッダ常設 (非裁定 — 法的助言ではない / UPL / 専門家確認)
  - 広告・トラッキング・外部アセットは一切なし (Charter Rider §2; inline CSS のみ)
  - :verify-current-law — 全アンカーに「改正確認」注記
  - デプロイ (etzhayyim.com/tate/ への配置・Search Console 登録) は operator ステップ
    (このスクリプトは out/site/ に生成するだけ — 公開行為そのものは外向きゲート)

Pure stdlib. Usage:
    python3 site_gen.py [--out OUTDIR] [--base https://etzhayyim.com/tate]
"""
from __future__ import annotations
import sys, json, html, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from terms_scan import load_patterns, HERE  # noqa: E402
from respond_plan import load_procs, load_jurisdictions  # noqa: E402
from coverage_report import coverage  # noqa: E402

BASE_DEFAULT = "https://etzhayyim.com/tate"

DISCLAIMER = (
    "本ページは <strong>一般的な法情報 (legal information)</strong> であり、個別の法的助言"
    " (legal advice) ではありません。tate 盾 は条項・手続きを<strong>開示済みの法令アンカー</strong>"
    "に対応付けるだけで、有効・無効の判断はしません (非裁定)。期限の起算点 (送達日) は必ず"
    "ご自身で確認し、重要な判断は各法域の専門家・無料相談窓口へ。法令は改正されます — "
    "アンカーは現行条文で必ず確認してください。")

CSS = ("body{font-family:sans-serif;max-width:50em;margin:1em auto;padding:0 1em;line-height:1.6}"
       "h1,h2{border-bottom:1px solid #ccc}.crit{color:#b00;font-weight:bold}"
       ".box{background:#f6f6f6;border-left:4px solid #888;padding:.5em 1em;margin:1em 0}"
       "table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:.2em .6em}"
       "footer{margin-top:2em;font-size:.85em;color:#555}")


def _page(title: str, desc: str, body: str, canonical: str, jsonld: dict | None = None) -> str:
    ld = (f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>'
          if jsonld else "")
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canonical}">
<style>{CSS}</style>
{ld}
</head>
<body>
<div class="box">{DISCLAIMER}</div>
{body}
<footer>tate 盾 — etzhayyim citizen legal-defense concierge · 広告・トラッキングなし ·
ソース: <a href="https://github.com/etzhayyim/root/tree/main/20-actors/tate">github.com/etzhayyim/root</a>
(Apache 2.0 + Charter Rider)</footer>
</body>
</html>
"""


def juris_page(jid: str, juris: dict, procs: list, patterns: list, base: str) -> str:
    label = juris[":juris/label"]
    my_procs = [p for p in procs if p.get(":proc/jurisdiction", ":jp") == jid]
    my_pats = [p for p in patterns if p.get(":clause/jurisdiction", ":jp") == jid]
    B = [f"<h1>{html.escape(label)} — 受け取った法的通知への応答ガイド</h1>"]
    B.append(f"<p>詐欺通知の見分け方: 本物の書類の経路は「{html.escape(juris[':juris/service-note'])}」。"
             f"疑わしい場合は送信者に接触せず: {html.escape(' / '.join(juris[':juris/fake-help']))}</p>")
    faq = []
    B.append("<h2>手続きと期限</h2>")
    for p in my_procs:
        B.append(f"<h3>{html.escape(p[':proc/label'])}</h3><ul>")
        for dl in p.get(":proc/deadline-rules", []):
            crit = ' class="crit"' if dl.get(":dl/critical") else ""
            mark = "⚠ " if dl.get(":dl/critical") else ""
            B.append(f"<li{crit}>{mark}<strong>{html.escape(dl[':dl/label'])}</strong>: "
                     f"{html.escape(dl[':dl/rule'])} <em>({html.escape(dl[':dl/anchor'])} — 要改正確認)</em></li>")
            faq.append({"@type": "Question",
                        "name": f"{p[':proc/label']} — {dl[':dl/label']}",
                        "acceptedAnswer": {"@type": "Answer",
                                           "text": f"{dl[':dl/rule']} (根拠: {dl[':dl/anchor']}。"
                                                   "法的助言ではありません — 専門家に確認を)"}})
        for o in p.get(":proc/options", []):
            star = "🛡 " if o.get(":opt/protective") else ""
            B.append(f"<li>{star}{html.escape(o[':opt/label'])}</li>")
        sl = "tate-" + p[":proc/id"].split(":", 1)[1]
        root = base[:-5] if base.endswith("/tate") else base
        B.append(f'<li>DL: <a href="{root}/actor/{sl}/checklist.md">チェックリスト</a> · '
                 f'<a href="{root}/actor/{sl}/case.json">データ (JSON)</a> · '
                 f'<a href="{root}/actor/{sl}/profile.json">case actor profile</a></li>')
        B.append(f"<li>相談先: {html.escape(' / '.join(p.get(':proc/refer-when', [])))}</li></ul>")
    if my_pats:
        B.append("<h2>契約の不利条項パターン (非裁定 — 可能性の指摘のみ)</h2><ul>")
        for p in my_pats:
            B.append(f"<li><strong>{html.escape(p[':clause/label'])}</strong> — "
                     f"{html.escape(p[':clause/anchor'])}</li>")
        B.append("</ul>")
    B.append(f"<p>無料相談: {html.escape(' / '.join(juris[':juris/referrals']))}</p>")
    B.append(f'<p><a href="{base}/index.html">← 全法域一覧</a></p>')
    jsonld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": faq} if faq else None
    # SEO (wave 39): 現地語の手続き名を title/meta に — 現地ユーザーは現地語で検索する
    native = []
    for p in my_procs:
        head = p[":proc/label"].split(" (")[0]
        if head not in native:
            native.append(head)
    kw = "・".join(native[:4])
    desc = (f"{label}: {kw} などへの応答期限・防御選択肢・無料相談先 — 非裁定の法情報"
            if kw else f"{label}: 法的通知への応答期限と無料相談先 — 非裁定の法情報")
    title = f"{label} — {kw} 応答ガイド | tate 盾" if kw else f"{label} — 法的通知への応答ガイド | tate 盾"
    return _page(title, desc, "\n".join(B),
                 f"{base}/{jid.lstrip(':')}.html", jsonld)


TRACK_LABELS = {":labor": "解雇・労働", ":housing": "立退き・賃貸借", ":enforcement": "差押え・強制執行",
                ":insolvency": "取引先の倒産 (債権者側)", ":family": "離婚・家事"}


def track_page(track: str, juris: dict, procs: list, base: str) -> str:
    label = TRACK_LABELS[track]
    my = [p for p in procs if p.get(":proc/track") == track]
    B = [f"<h1>{html.escape(label)} — 管轄×期限の比較表</h1>",
         f"<p>{len(my)}管轄の応答期限と防御の一手を1ページで比較 (詳細・DL は各法域ページ/case actor へ)。</p>",
         "<table><tr><th>管轄</th><th>手続き</th><th>主要期限 (⚠=失権)</th><th>守る一手 🛡</th></tr>"]
    for p in my:
        jid = p.get(":proc/jurisdiction", ":jp")
        jl = juris[jid][":juris/label"]
        dls = p.get(":proc/deadline-rules", [])
        d0 = dls[0] if dls else None
        crit = "⚠ " if (d0 and d0.get(":dl/critical")) else ""
        rule = html.escape((d0[":dl/rule"][:80] + "…") if d0 and len(d0[":dl/rule"]) > 80
                           else (d0[":dl/rule"] if d0 else "—"))
        prot = next((o[":opt/label"] for o in p.get(":proc/options", [])
                     if o.get(":opt/protective")), "—")
        prot = html.escape(prot[:60] + ("…" if len(prot) > 60 else ""))
        B.append(f'<tr><td><a href="{base}/{jid.lstrip(":")}.html">{html.escape(jl)}</a></td>'
                 f"<td>{html.escape(p[':proc/label'])}</td>"
                 f"<td>{crit}{rule}</td><td>🛡 {prot}</td></tr>")
    B.append("</table>")
    B.append(f'<p><a href="{base}/index.html">← 全法域一覧</a></p>')
    return _page(f"{label} — 世界{len(my)}管轄の期限比較 | tate 盾",
                 f"{label}: 各国の応答期限・失権期限・member を守る一手の比較表 (非裁定の法情報)",
                 "\n".join(B), f"{base}/track-{track.lstrip(':')}.html")


def index_page(juris: dict, cov: dict, base: str) -> str:
    B = ["<h1>tate 盾 — 世界の法的通知 応答ガイド (非裁定)</h1>",
         f"<p>{cov['covered_count']}法域 + 米国全{cov['us_states_total']}州を収載。"
         "受け取った通知 (支払督促・解雇・立退き・差押え・倒産・離婚) の期限・防御選択肢・無料相談先。</p>",
         "<h2>法域一覧</h2><ul>"]
    for jid in cov["jurisdictions"]:
        if jid == ":eu":
            pass
        B.append(f'<li><a href="{base}/{jid.lstrip(":")}.html">'
                 f"{html.escape(juris[jid][':juris/label'])}</a></li>")
    root = base[:-5] if base.endswith("/tate") else base
    B.append(f'</ul><p>全 case の actor 索引: <a href="{root}/actor/tate/cases.json">cases.json</a> '
             f"(1手続き=1 case actor — profile から checklist/データ DL と相談先へ)</p>")
    B.append("<h2>⚠ 徒過で権利が消える期限 (critical census)</h2><ul>")
    for cd in cov["critical_deadlines"]:
        B.append(f"<li class=\"crit\">[{cd['juris']}] {html.escape(cd['label'])} "
                 f"({html.escape(cd['anchor'])})</li>")
    B.append("</ul>")
    return _page("tate 盾 — 世界の法的通知 応答ガイド (30法域+米50州)",
                 "支払督促・解雇通知・立退き・差押え・倒産・離婚 — 30法域の応答期限と無料相談先 (非裁定の法情報)",
                 "\n".join(B), f"{base}/index.html")


def generate(outdir: pathlib.Path, base: str = BASE_DEFAULT) -> list:
    juris = load_jurisdictions()
    procs = load_procs()
    patterns = load_patterns()
    cov = coverage()
    outdir.mkdir(parents=True, exist_ok=True)
    pages = []
    (outdir / "index.html").write_text(index_page(juris, cov, base), encoding="utf-8")
    pages.append("index.html")
    for jid, j in juris.items():
        name = f"{jid.lstrip(':')}.html"
        (outdir / name).write_text(juris_page(jid, j, procs, patterns, base), encoding="utf-8")
        pages.append(name)
    for tk in TRACK_LABELS:
        name = f"track-{tk.lstrip(':')}.html"
        (outdir / name).write_text(track_page(tk, juris, procs, base), encoding="utf-8")
        pages.append(name)
    (outdir / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(f"  <url><loc>{base}/{p}</loc></url>" for p in pages)
        + "\n</urlset>\n", encoding="utf-8")
    (outdir / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n", encoding="utf-8")
    return pages


def main(argv):
    out = HERE / "out" / "site"
    base = BASE_DEFAULT
    if "--out" in argv:
        out = pathlib.Path(argv[argv.index("--out") + 1])
    if "--base" in argv:
        base = argv[argv.index("--base") + 1].rstrip("/")
    pages = generate(out, base)
    print(f"tate: {len(pages)} crawlable pages + sitemap → {out} "
          f"(デプロイ/Search Console は operator ステップ)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
