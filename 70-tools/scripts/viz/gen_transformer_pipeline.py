#!/usr/bin/env python3
"""Decoder-only Transformer (= maxwell-1 / Gemma 系) train/infer pipeline,
same style as the sheaf one + a 3-paradigm decode contrast strip."""
import math
W, H = 1480, 1040
P = []
def add(s): P.append(s)

def box(x, y, w, h, title, lines, fill="#ffffff", stroke="#4a5fc1", tcol="#2a358f"):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>')
    add(f'<text x="{x+12}" y="{y+22}" font-size="13" font-weight="700" fill="{tcol}">{title}</text>')
    yy = y + 42
    for ln in lines:
        add(f'<text x="{x+12}" y="{yy}" font-size="11" fill="#2a2f3a">{ln}</text>'); yy += 17

def arrow(x1, y1, x2, y2, col="#7a8295", w=1.6, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{w}"{d} marker-end="url(#ar)"/>')

add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="-apple-system,Hiragino Sans,Arial,sans-serif">')
add('<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10z" fill="#7a8295"/></marker>'
    '<marker id="arb" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10z" fill="#c0392b"/></marker></defs>')
add(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')
add(f'<text x="{W/2}" y="38" text-anchor="middle" font-size="24" font-weight="700" fill="#16213e">通常の Transformer（decoder-only / 自己回帰 LM = maxwell-1・Gemma 系）: train / infer</text>')
add(f'<text x="{W/2}" y="62" text-anchor="middle" font-size="13" fill="#667">明示グラフ無し・全結合 causal attention・1トークンずつ逐次デコード（sheaf の場の緩和 / diffusion の並列 denoise と対比）</text>')

# ---- concept row ----
# A: structure stack
ax, ay, aw, ah = 24, 84, 410, 232
box(ax, ay, aw, ah, "① decoder-only Transformer の対象", [], fill="#f3f5ff")
sx, sw = ax+24, 150
ys = [("token emb + RoPE 位置", "#cfd8f5"), ("causal self-attention", "#aebef0"), ("FFN (W₂·σ(W₁x))", "#aebef0"),
      ("…  N× blocks (+RMSNorm/残差)", "#cfd8f5"), ("LM head → logits ℝ^|V|", "#9fb0ec")]
yb = ay+44
for lbl,c in ys:
    add(f'<rect x="{sx}" y="{yb}" width="{sw+150}" height="26" rx="5" fill="{c}" stroke="#5b6fc9"/>')
    add(f'<text x="{sx+(sw+150)/2}" y="{yb+17}" text-anchor="middle" font-size="10.5" fill="#1a2050">{lbl}</text>')
    yb += 33
add(f'<text x="{ax+aw-12}" y="{ay+ah-10}" text-anchor="end" font-size="9.5" fill="#667">各トークン = 1ベクトル列（stalk/グラフは無い）</text>')

# B: attention core
bx, by, bw, bh = 452, 84, 506, 232
box(bx, by, bw, bh, "② 中核 = self-attention（明示グラフの代わり）", [
    "Attention(Q,K,V) = softmax( QKᵀ/√d_k + mask ) V",
    "  causal mask: 位置 i は j≤i のみ参照",
    "Multi-Head: h 個を並列 → 連結 → W_O",
    "FFN: W₂·σ(W₁·x)（位置ごとに独立）",
    "残差 + RMSNorm で深く積む（N 層）",
], fill="#f3f5ff")
add(f'<text x="{bx+12}" y="{by+bh-10}" font-size="9.5" fill="#667">「整合」は Laplacian でなく attention の重みとして学習で創発</text>')

# C: how it differs
cx2, cy2, cw, ch = 976, 84, 480, 232
box(cx2, cy2, cw, ch, "③ sheaf / diffusion との違い", [
    "・グラフ/restriction map を持たない",
    "  → 全トークン all-to-all（causal）に密結合",
    "・学習目的 = next-token 予測（CE）",
    "  energy 最小化でも denoise でもない",
    "・デコード = 1トークンずつ逐次（autoregressive）",
    "  ← diffusion は全 canvas を並列 denoise",
    "  ← sheaf は graph 上を拡散して整合",
    "",
    "・maxwell-1 = Gemma4 E4B の LoRA 微調整",
], fill="#fff7f0", stroke="#d98a4f", tcol="#b5561a")

# ---- TRAIN lane ----
add(f'<rect x="24" y="338" width="{W-48}" height="186" rx="10" fill="#eef1fb" stroke="#c9d0ee"/>')
add(f'<text x="40" y="360" font-size="15" font-weight="700" fill="#2a358f">TRAIN（teacher forcing・並列）  ★ = 学習対象</text>')
train = [
    ("T0 データ", ["text → tokenize", "→ token ids", "（コーパス）"]),
    ("T1 embed", ["token emb +", "RoPE 位置符号", "→ X∈ℝ^{L×d}"]),
    ("T2 N× block ★", ["causal self-attn", "+ FFN(+RMSNorm,残差)", "全位置を並列計算"]),
    ("T3 LM head ★", ["h_i → logits", "∈ ℝ^|V|", "（各位置）"]),
    ("T4 loss", ["next-token CE", "(1 シフト)", "teacher forcing"]),
    ("T5 backprop ★", ["AdamW で全weight更新", "maxwell-1=LoRA r16", "/Gemma4 E4B"]),
]
tx, ty, tw, th, step = 24, 376, 222, 132, 238
for i,(t,ls) in enumerate(train):
    x = tx + i*step
    box(x, ty, tw, th, t, ls, stroke="#d98a4f" if "★" in t else "#4a5fc1", tcol="#b5561a" if "★" in t else "#2a358f")
    if i < len(train)-1: arrow(x+tw, ty+th/2, x+step, ty+th/2)
s1c, s5c = tx+2*step+tw/2, tx+5*step+tw/2
add(f'<path d="M{s5c},{ty} C{s5c},344 {s1c},344 {s1c},{ty}" fill="none" stroke="#c0392b" stroke-width="1.8" stroke-dasharray="5 4" marker-end="url(#arb)"/>')
add(f'<text x="{(s1c+s5c)/2}" y="352" text-anchor="middle" font-size="10.5" fill="#c0392b">∂loss → 全 weight（または LoRA アダプタ）</text>')

# ---- INFER lane ----
add(f'<rect x="24" y="560" width="{W-48}" height="178" rx="10" fill="#f0fff4" stroke="#bfe3c8"/>')
add(f'<text x="40" y="582" font-size="15" font-weight="700" fill="#1f7a1f">INFER（autoregressive・逐次・1トークンずつ）</text>')
infer = [
    ("I0 prompt", ["prompt → tokens"]),
    ("I1 forward", ["前向き1パス →", "次トークン logits", "(KV-cache 再利用)"]),
    ("I2 sample", ["temperature/top-p", "で 1 トークン選択", "(argmax or 標本)"]),
    ("I3 append→繰返し", ["列に1トークン追加", "→ I1 へ戻る", "(1 token / step)"]),
    ("I4 stop", ["EOS で停止", "→ 出力テキスト"]),
]
ix, iy, iw, ih, istep = 24, 598, 268, 124, 282
for i,(t,ls) in enumerate(infer):
    x = ix + i*istep
    box(x, iy, iw, ih, t, ls, stroke="#52a052", tcol="#1f7a1f")
    if i < len(infer)-1: arrow(x+iw, iy+ih/2, x+istep, iy+ih/2, col="#5aa86a")
# loop arrow I3 -> I1
add(f'<path d="M{ix+3*istep+iw/2},{iy+ih} C{ix+3*istep+iw/2},{iy+ih+22} {ix+istep+iw/2},{iy+ih+22} {ix+istep+iw/2},{iy+ih}" '
    f'fill="none" stroke="#1f7a1f" stroke-width="1.5" stroke-dasharray="4 3" marker-end="url(#ar)"/>')

# ---- bottom contrast strip: 3 decode paradigms ----
yb2 = 770
add(f'<rect x="24" y="{yb2}" width="{W-48}" height="190" rx="10" fill="#fbfbfe" stroke="#ddd"/>')
add(f'<text x="40" y="{yb2+24}" font-size="14" font-weight="700" fill="#16213e">デコードの進め方の違い（3 パラダイム）</text>')
def dots(x, y, n, col, sequential=True):
    for k in range(n):
        add(f'<circle cx="{x+k*30}" cy="{y}" r="8" fill="{col}"/>')
        if sequential and k < n-1:
            add(f'<line x1="{x+k*30+9}" y1="{y}" x2="{x+(k+1)*30-9}" y2="{y}" stroke="{col}" stroke-width="1.6" marker-end="url(#ar)"/>')
# transformer AR
add(f'<text x="48" y="{yb2+58}" font-size="12" font-weight="700" fill="#2a358f">Transformer (自己回帰)</text>')
dots(48, yb2+82, 6, "#4a5fc1", True)
add(f'<text x="48" y="{yb2+108}" font-size="10.5" fill="#555">1トークンずつ逐次 / causal / KV-cache（速いが直列）</text>')
# diffusion parallel
add(f'<text x="540" y="{yb2+58}" font-size="12" font-weight="700" fill="#b5561a">maxwell-diffusion</text>')
for k in range(6):
    add(f'<circle cx="{540+k*30}" cy="{yb2+82}" r="8" fill="#e08a4f" opacity="0.5"/>')
add(f'<text x="540" y="{yb2+108}" font-size="10.5" fill="#555">全 canvas を同時に K-step で denoise（並列・温度で探索）</text>')
add(f'<text x="540" y="{yb2+128}" font-size="9.5" fill="#999">(256トークンの canvas を 48 step で精錬)</text>')
# sheaf diffusion
add(f'<text x="1010" y="{yb2+58}" font-size="12" font-weight="700" fill="#1f4e9c">oka — sheaf</text>')
ccx, ccy = 1070, yb2+86
for k in range(7):
    a = 2*math.pi*k/7
    add(f'<line x1="{ccx}" y1="{ccy}" x2="{ccx+34*math.cos(a):.0f}" y2="{ccy+22*math.sin(a):.0f}" stroke="#5b86c5" stroke-width="1.4"/>')
    add(f'<circle cx="{ccx+34*math.cos(a):.0f}" cy="{ccy+22*math.sin(a):.0f}" r="5" fill="#7c9fd6"/>')
add(f'<circle cx="{ccx}" cy="{ccy}" r="7" fill="#1f4e9c"/>')
add(f'<text x="1010" y="{yb2+128}" font-size="10.5" fill="#555">graph 上を K-step 拡散し中心で整合（並列・大域整合）</text>')

add(f'<text x="{W/2}" y="{H-16}" text-anchor="middle" font-size="10.5" fill="#7a8295">'
    'Transformer=逐次AR・next-token CE ・ diffusion=並列 denoise・温度探索 ・ sheaf=場の緩和・Dirichlet energy ・ Murakumo-only 学習</text>')
add('</svg>')

out = "/Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/90-docs/baien/transformer-train-infer-pipeline.svg"
open(out, "w").write("\n".join(P))
print("wrote", out)
