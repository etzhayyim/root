#!/usr/bin/env python3
"""oka MMSheaf — train(S0..S6)/infer(I0..I4) pipeline + sheaf objects + Dirichlet-energy descent.
Hand-laid SVG (light theme, oka-blue). Pure string build, no deps."""
import math

W, H = 1480, 1000
P = []
def add(s): P.append(s)

def box(x, y, w, h, title, lines, fill="#eef3fb", stroke="#5b86c5", tcol="#1f4e9c", num=None):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>')
    add(f'<text x="{x+12}" y="{y+22}" font-size="13" font-weight="700" fill="{tcol}">{title}</text>')
    yy = y + 42
    for ln in lines:
        add(f'<text x="{x+12}" y="{yy}" font-size="11" fill="#2a2f3a">{ln}</text>')
        yy += 17

def arrow(x1, y1, x2, y2, col="#7a8295", w=1.6, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{w}"{d} marker-end="url(#ar)"/>')

add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="-apple-system,Hiragino Sans,Arial,sans-serif">')
add('<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
    'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10z" fill="#7a8295"/></marker>'
    '<marker id="arb" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" '
    'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10z" fill="#c0392b"/></marker></defs>')
add(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')
add(f'<text x="{W/2}" y="38" text-anchor="middle" font-size="24" font-weight="700" fill="#16213e">'
    'oka — MMSheaf (sheaf diffusion): train / infer パイプライン</text>')
add(f'<text x="{W/2}" y="62" text-anchor="middle" font-size="13" fill="#667">'
    'なぜ放射構造か = ハブ&amp;スポークの cellular sheaf を「全モダリティが中心で一致」するまで拡散するから（ADR-2605250700）</text>')

# ---------- Top: concept row ----------
# A: sheaf objects (hub-spoke)
ax, ay, aw, ah = 24, 84, 410, 232
box(ax, ay, aw, ah, "① cellular sheaf の対象", [], fill="#f4f8ff")
cx, cy, rr = ax+150, ay+135, 64
add(f'<circle cx="{cx}" cy="{cy}" r="13" fill="#1f4e9c"/>')
add(f'<text x="{cx}" y="{cy+34}" text-anchor="middle" font-size="9.5" fill="#1f4e9c">entity (大域切断)</text>')
mods = ["audio","image","text","3d","tabular","time","geo","video","doc"]
for i,m in enumerate(mods):
    a = 2*math.pi*i/len(mods) - math.pi/2
    nx, ny = cx+rr*math.cos(a), cy+rr*math.sin(a)
    add(f'<line x1="{cx}" y1="{cy}" x2="{nx:.0f}" y2="{ny:.0f}" stroke="#9bb4d8" stroke-width="1.2"/>')
    add(f'<circle cx="{nx:.0f}" cy="{ny:.0f}" r="6" fill="#7c9fd6"/>')
add(f'<text x="{ax+aw-12}" y="{ay+58}" text-anchor="end" font-size="10.5" fill="#2a2f3a">stalk F(v)=ℝ^d（各モダリティ）</text>')
add(f'<text x="{ax+aw-12}" y="{ay+76}" text-anchor="end" font-size="10.5" fill="#2a2f3a">edge stalk F(e)=ℝ^d（共有空間）</text>')
add(f'<text x="{ax+aw-12}" y="{ay+94}" text-anchor="end" font-size="10.5" fill="#2a2f3a">restriction map</text>')
add(f'<text x="{ax+aw-12}" y="{ay+110}" text-anchor="end" font-size="10.5" fill="#b5561a">F_(v⊴e): F(v)→F(e)（d×d 線形）</text>')
add(f'<text x="{ax+aw-12}" y="{ay+210}" text-anchor="end" font-size="9.5" fill="#667">spoke=モダリティ / 中心=整合表現</text>')

# B: energy / harmonic
bx, by, bw, bh = 452, 84, 506, 232
box(bx, by, bw, bh, "② 整合 = sheaf Dirichlet energy 最小 = 調和", [
    "余境界:  (δx)_e = F_(v⊴e)·x_v − F_(u⊴e)·x_u   （2視点の食い違い）",
    "sheaf Laplacian:  L_F = δᵀδ",
    "E(x) = ½ xᵀ L_F x = ½ Σ_e ‖F_(v⊴e)x_v − F_(u⊴e)x_u‖²",
    "ker L_F = 大域切断 = 全モダリティが輸送後に一致する点",
], fill="#f4f8ff")
# mini energy descent curve
ex, ey = bx+18, by+150
add(f'<path d="M{ex},{ey} C{ex+70},{ey+10} {ex+120},{ey+48} {ex+180},{ey+50} '
    f'C{ex+240},{ey+52} {ex+300},{ey+50} {ex+360},{ey+50}" fill="none" stroke="#1f4e9c" stroke-width="2"/>')
add(f'<circle cx="{ex}" cy="{ey}" r="5" fill="#c0392b"/><text x="{ex+6}" y="{ey-4}" font-size="9.5" fill="#c0392b">初期(食い違い大)</text>')
add(f'<circle cx="{ex+360}" cy="{ey+50}" r="5" fill="#2a7d2a"/><text x="{ex+360}" y="{ey+66}" text-anchor="end" font-size="9.5" fill="#2a7d2a">E→0 = ker L_F（整合コア）</text>')
add(f'<text x="{bx+12}" y="{by+bh-8}" font-size="9.5" fill="#667">推論 = この energy を下げる場の緩和（grokking 地形図の「oka=大域整合」の中身）</text>')

# C: why structure
cx2, cy2, cw, ch = 976, 84, 480, 232
box(cx2, cy2, cw, ch, "③ なぜ「潰れず」構造が残るか", [
    "GNN: エッジ重み=スカラー（1次元輸送）",
    "  → 全ノードが1点へ収束（over-smoothing）",
    "",
    "sheaf: エッジ写像=d×d 行列（向き付き輸送）",
    "  → モダリティを区別したまま整合できる",
    "  → ker L_F が高次元 = クラスが分離",
    "",
    "∴ ハブ・スポーク+restriction の幾何が",
    "   放射状の構造として残る（Bodnar 2022）",
], fill="#fff7f0", stroke="#d98a4f", tcol="#b5561a")

# ---------- TRAIN lane ----------
add(f'<rect x="24" y="338" width="{W-48}" height="186" rx="10" fill="#f0f6ff" stroke="#c9d8ee"/>')
add(f'<text x="40" y="360" font-size="15" font-weight="700" fill="#1f4e9c">TRAIN  （★ = 学習対象）</text>')
train = [
    ("S0 データ", ["9 モダリティを", "凍結エンコーダ→", "各 stalk に x_v∈ℝ^d"]),
    ("S1 sheaf 生成 ★", ["F_(v⊴e)=Φ_θ(x_v,x_u)", "MLP が restriction", "map を生成=幾何学習"]),
    ("S2 Laplacian", ["L_F=δᵀδ を組立", "対角 Σ FᵀF /", "非対角 −FᵀF"]),
    ("S3 拡散層 ×K", ["X_{t+1}=X_t −", "σ((I⊗W₁)L_F X_t W₂)", "輸送+比較 MP"]),
    ("S4 readout", ["拡散後 stalk を", "プール →", "タスクヘッド"]),
    ("S5 loss+backprop ★", ["勾配が拡散層を貫き", "Φ_θ・W へ流れる", "(幾何を最適化)"]),
    ("S6 潰さない学習", ["Φ が直交写像を学習", "ker L_F 高次元 →", "区別+整合 を両立"]),
]
tx, ty, tw, th, step = 24, 376, 190, 132, 202
for i,(t,ls) in enumerate(train):
    x = tx + i*step
    box(x, ty, tw, th, t, ls, fill="#ffffff",
        stroke="#d98a4f" if "★" in t else "#5b86c5",
        tcol="#b5561a" if "★" in t else "#1f4e9c")
    if i < len(train)-1:
        arrow(x+tw, ty+th/2, x+step, ty+th/2)
# backprop loopback S5 -> S1 (above boxes)
s1c = tx + 1*step + tw/2
s5c = tx + 5*step + tw/2
add(f'<path d="M{s5c},{ty} C{s5c},344 {s1c},344 {s1c},{ty}" fill="none" stroke="#c0392b" '
    f'stroke-width="1.8" stroke-dasharray="5 4" marker-end="url(#arb)"/>')
add(f'<text x="{(s1c+s5c)/2}" y="352" text-anchor="middle" font-size="10.5" fill="#c0392b">'
    '∂loss → Φ_θ, W（restriction map=幾何そのものを学習）</text>')

# ---------- INFER lane ----------
add(f'<rect x="24" y="560" width="{W-48}" height="210" rx="10" fill="#f0fff4" stroke="#bfe3c8"/>')
add(f'<text x="40" y="582" font-size="15" font-weight="700" fill="#1f7a1f">INFER  （前向きのみ）</text>')
infer = [
    ("I0 特徴", ["新サンプル → 9 モダリティ", "凍結エンコーダ特徴 x_v"]),
    ("I1 sheaf 生成", ["Φ_θ がこのサンプルの", "restriction map を生成"]),
    ("I2 Laplacian", ["L_F=δᵀδ を組立"]),
    ("I3 前向き拡散 ×K = 場の緩和", ["X←X−σ(L_F(I⊗W)X)", "横方向に拡散 →", "コンセンサス(調和)へ"]),
    ("I4 readout", ["融合表現 →", "予測 / 生成"]),
]
ix, iy, iw, ih, istep = 24, 598, 268, 150, 282
for i,(t,ls) in enumerate(infer):
    x = ix + i*istep
    box(x, iy, iw, ih, t, ls, fill="#ffffff", stroke="#52a052", tcol="#1f7a1f")
    if i < len(infer)-1:
        arrow(x+iw, iy+ih/2, x+istep, iy+ih/2, col="#5aa86a")
# mini relaxation curve inside I3
rx, ry = ix+3*istep+14, iy+96
add(f'<path d="M{rx},{ry} C{rx+40},{ry+6} {rx+70},{ry+34} {rx+120},{ry+36} C{rx+170},{ry+38} {rx+200},{ry+36} {rx+232},{ry+36}" '
    f'fill="none" stroke="#1f7a1f" stroke-width="1.6"/>')
add(f'<circle cx="{rx}" cy="{ry}" r="4" fill="#c0392b"/><circle cx="{rx+232}" cy="{ry+36}" r="4" fill="#2a7d2a"/>')
add(f'<text x="{rx+232}" y="{ry+50}" text-anchor="end" font-size="9" fill="#2a7d2a">E→0 整合</text>')

# footer
add(f'<text x="{W/2}" y="{H-46}" text-anchor="middle" font-size="12" fill="#16213e">'
    'train は restriction map Φ_θ（=幾何）を学習 ・ infer はその幾何で K-step 拡散して大域整合へ緩和</text>')
add(f'<text x="{W/2}" y="{H-24}" text-anchor="middle" font-size="10.5" fill="#7a8295">'
    'MMSheafV4 = FP8 server / V3 = BitNet 1.58 edge ・ Murakumo-only 学習（ROCm+Mac fleet, RunPod 不可）・ ADR-2605250700 / Neural Sheaf Diffusion (Bodnar+ 2022)</text>')
add('</svg>')

out = "/Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/90-docs/baien/sheaf-train-infer-pipeline.svg"
open(out, "w").write("\n".join(P))
print("wrote", out)
