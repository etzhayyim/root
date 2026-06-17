#!/usr/bin/env python3
"""Generate an energy-landscape (地形図) SVG comparing baien / maxwell-diffusion / oka
through the grokking physics framing."""
import re

# base energy curve E(theta): high-left → WIDE shallow memorization basin → barrier
# ridge → NARROW deep generalization well → rise right. (SVG y down: larger y = lower energy)
BASE = ("M 110,190 C 190,330 240,418 330,420 C 400,422 440,420 470,400 "
        "C 540,360 560,300 605,285 C 660,300 700,362 772,432 "
        "C 818,478 838,508 866,508 C 902,508 917,472 947,420 "
        "C 1002,350 1042,320 1086,300")

def offset_path(d, dy):
    nums = re.findall(r"-?\d+\.?\d*", d)
    toks = re.findall(r"[MC]|-?\d+\.?\d*", d)
    out, i = [], 0
    for t in toks:
        if t in "MC":
            out.append(t)
        else:
            # coords come in x,y pairs; shift every 2nd number (y)
            out.append(t)
    # rebuild: walk numbers in pairs, add dy to y
    parts = re.split(r"([MC])", d)
    res = ""
    for seg in parts:
        if seg in ("M", "C"):
            res += seg
        elif seg.strip():
            coords = re.findall(r"-?\d+\.?\d*", seg)
            pairs = [f"{coords[k]},{float(coords[k+1])+dy:g}" for k in range(0, len(coords), 2)]
            res += " " + " ".join(pairs) + " "
    return res.strip()

contours = "".join(
    f'<path d="{offset_path(BASE, dy)}" fill="none" stroke="#9ec5e8" '
    f'stroke-width="1" opacity="{op}"/>\n  '
    for dy, op in [(26, .55), (52, .42), (78, .3), (104, .2)]
)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720" viewBox="0 0 1200 720" font-family="-apple-system,'Hiragino Sans',Arial,sans-serif">
  <defs>
    <marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10z" fill="#b5561a"/></marker>
    <marker id="ar2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10z" fill="#9b59b6"/></marker>
    <linearGradient id="fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#eaf2fb"/><stop offset="1" stop-color="#f7fbff"/></linearGradient>
    <style>.t{{font-size:25px;font-weight:700;fill:#1a1a2e}}.s{{font-size:13px;fill:#666}}.ax{{font-size:12px;fill:#888}}.h{{font-size:14px;font-weight:700}}.l{{font-size:12px;fill:#333}}.lb{{font-size:11px;fill:#555}}</style>
  </defs>
  <rect width="1200" height="720" fill="#fff"/>
  <text x="600" y="38" text-anchor="middle" class="t">地形図比較 — grokking のエネルギー地形上の 3 weight</text>
  <text x="600" y="62" text-anchor="middle" class="s">記憶の広い谷 → 障壁 → 汎化の狭い深い谷（動画: energy landscape / phase transition / circuit efficiency）</text>

  <!-- axes -->
  <line x1="90" y1="120" x2="90" y2="600" stroke="#ccc" stroke-width="1"/>
  <line x1="90" y1="600" x2="1110" y2="600" stroke="#ccc" stroke-width="1"/>
  <text x="84" y="130" text-anchor="end" class="ax">高</text>
  <text x="84" y="595" text-anchor="end" class="ax">低</text>
  <text x="70" y="360" text-anchor="middle" class="ax" transform="rotate(-90 70,360)">energy / loss</text>
  <text x="600" y="620" text-anchor="middle" class="ax">解空間 / 回路空間   （記憶 ←————————→ 汎化）</text>

  <!-- oka = the terrain structure itself: contour lines under the curve -->
  {contours}
  <!-- main energy curve -->
  <path d="{BASE} L 1086,600 L 110,600 Z" fill="url(#fill)" opacity="0.5"/>
  <path d="{BASE}" fill="none" stroke="#2a3142" stroke-width="2.4"/>

  <!-- region labels -->
  <text x="300" y="470" text-anchor="middle" class="h" fill="#777">記憶の谷</text>
  <text x="300" y="488" text-anchor="middle" class="lb">広い・高エントロピー（volume 大）</text>
  <text x="605" y="262" text-anchor="middle" class="h" fill="#a33">汎化障壁</text>
  <text x="605" y="246" text-anchor="middle" class="lb" fill="#a33">汎化解は学習が遅い（circuit efficiency）</text>
  <text x="866" y="560" text-anchor="middle" class="h" fill="#1f7a1f">汎化の谷</text>
  <text x="866" y="577" text-anchor="middle" class="lb">狭い・最小エントロピー・効率回路</text>

  <!-- maxwell-diffusion: rolling ball + denoise trajectory crossing the barrier -->
  <path d="M 300,420 C 430,430 520,330 605,300 C 690,330 740,470 820,500" fill="none" stroke="#b5561a" stroke-width="1.8" stroke-dasharray="5 4" marker-end="url(#ar)"/>
  <circle cx="700" cy="392" r="11" fill="#e8804f" stroke="#b5561a" stroke-width="2"/>
  <text x="700" y="396" text-anchor="middle" font-size="11" fill="#fff" font-weight="700">M</text>
  <rect x="470" y="120" width="270" height="58" rx="8" fill="#fff0e8" stroke="#d98a4f"/>
  <text x="482" y="140" class="h" fill="#b5561a">maxwell-diffusion  🟡R0</text>
  <text x="482" y="158" class="l">= 力学：denoise が地形を横断</text>
  <text x="482" y="172" class="lb">block diffusion・相転移を駆動（base 80%✓）</text>

  <!-- baien: deepest narrow well -->
  <circle cx="866" cy="508" r="9" fill="#52a052" stroke="#1f7a1f" stroke-width="2"/>
  <rect x="905" y="470" width="285" height="74" rx="8" fill="#e8ffe8" stroke="#52a052"/>
  <text x="917" y="490" class="h" fill="#1f7a1f">baien — BitNet 1.58b  🟢active</text>
  <text x="917" y="508" class="l">= 到達点：三値＝最圧縮の効率回路</text>
  <text x="917" y="524" class="lb">grokking が落ち着く「狭く深い谷」</text>
  <text x="917" y="539" class="lb">edge / WASM・iPhone・Android</text>

  <!-- oka: the terrain itself -->
  <rect x="100" y="120" width="300" height="74" rx="8" fill="#e8f0ff" stroke="#5b86c5"/>
  <text x="112" y="140" class="h" fill="#1f4e9c">oka — MMSheaf  🟠R0 scaffold</text>
  <text x="112" y="158" class="l">= 地形そのもの（青い等高線）</text>
  <text x="112" y="174" class="lb">cellular sheaf diffusion が局所(modality)を</text>
  <text x="112" y="189" class="lb">大域に接着し、谷の形＝topology を定義</text>
  <path d="M 250,196 C 230,230 210,300 220,360" fill="none" stroke="#5b86c5" stroke-width="1.4" stroke-dasharray="3 3"/>

  <!-- RSi drive: push ball over barrier -->
  <path d="M 360,405 C 470,300 540,250 600,250" fill="none" stroke="#9b59b6" stroke-width="2.2" marker-end="url(#ar2)"/>
  <text x="455" y="300" class="l" fill="#6c2b8f" font-weight="700">RSi = 継続学習</text>
  <text x="455" y="316" class="lb" fill="#6c2b8f">記憶を越え障壁を押し越える駆動力</text>

  <text x="600" y="690" text-anchor="middle" class="lb" fill="#999">同じ汎化の物理を別量子化で：oka=地形 / maxwell-diffusion=力学 / baien=到達点 ・ ref: grokking energy-landscape (YouTube Zn4fApSAtsc)</text>
</svg>'''

open("/Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/90-docs/baien/weight-family-landscape.svg", "w").write(svg)
print("wrote weight-family-landscape.svg")
