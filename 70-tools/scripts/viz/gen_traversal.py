#!/usr/bin/env python3
"""How baien / oka-sheaf / maxwell-diffusion traverse the SAME energy landscape —
three different gradient/map-progression operators, side by side."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

rng = np.random.default_rng(7)

# ---- shared energy landscape (top-down contour map) ----
def E(x, y):
    memo = -1.05 * np.exp(-(((x + 1.5) ** 2 + (y + 1.3) ** 2) / 2.6))   # wide shallow LOCAL min (memorization)
    gen  = -2.35 * np.exp(-(((x - 1.6) ** 2 + (y - 1.5) ** 2) / 0.50))  # deep narrow GLOBAL min (generalization)
    barr =  0.62 * np.exp(-(((x - 0.1) ** 2 + (y - 0.1) ** 2) / 1.10))  # barrier between
    bowl =  0.04 * (x ** 2 + y ** 2)
    rip  =  0.05 * np.sin(2 * x) * np.cos(2 * y)
    return memo + gen + barr + bowl + rip

def grad(x, y, h=1e-3):
    return ((E(x + h, y) - E(x - h, y)) / (2 * h), (E(x, y + h) - E(x, y - h)) / (2 * h))

L = 3.0
gx = np.linspace(-L, L, 240)
gy = np.linspace(-L, L, 240)
GX, GY = np.meshgrid(gx, gy)
GZ = E(GX, GY)

START = (-0.7, -0.9)        # all three start in/near the memorization basin
GLOBAL = (1.6, 1.5)

plt.rcParams.update({"font.family": ["-apple-system", "Hiragino Sans", "DejaVu Sans"]})
fig, axes = plt.subplots(1, 3, figsize=(18, 6.6), facecolor="#08080e")

def base(ax, title, sub):
    ax.contourf(GX, GY, GZ, levels=28, cmap="Purples_r", alpha=0.92)
    ax.contour(GX, GY, GZ, levels=14, colors="white", linewidths=0.35, alpha=0.22)
    ax.set_facecolor("#08080e")
    ax.scatter(*GLOBAL, s=70, marker="*", c="#ffd23f", edgecolors="k", linewidths=0.5, zorder=6)
    ax.text(GLOBAL[0]+0.12, GLOBAL[1]+0.18, "global min", color="#ffd23f", fontsize=8)
    ax.scatter(*START, s=42, c="white", edgecolors="k", linewidths=0.6, zorder=6)
    ax.text(START[0]-0.2, START[1]-0.55, "start", color="#ddd", fontsize=8)
    ax.set_title(title, color="white", fontsize=14, fontweight="bold", pad=10)
    ax.text(0.5, 1.005, sub, transform=ax.transAxes, ha="center", va="bottom",
            color="#9aa0b4", fontsize=9.5)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_color("#333")

# ===== Panel A — baien: quantized greedy descent (STE), discrete lattice =====
axA = axes[0]
base(axA, "baien — BitNet 1.58b", "量子化勾配 (STE): 離散3値ステップ・最寄りの谷で停止")
D = 0.42  # ternary lattice step
for v in np.arange(-L, L + D, D):
    axA.axhline(v, color="#39d353", lw=0.25, alpha=0.18)
    axA.axvline(v, color="#39d353", lw=0.25, alpha=0.18)
moves = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]
px, py = round(START[0] / D) * D, round(START[1] / D) * D
path = [(px, py)]
for _ in range(40):
    cur = E(px, py)
    best, bxy = cur, None
    for dx, dy in moves:
        nx, ny = px + dx * D, py + dy * D
        if abs(nx) <= L and abs(ny) <= L and E(nx, ny) < best:
            best, bxy = E(nx, ny), (nx, ny)
    if bxy is None:
        break
    px, py = bxy
    path.append((px, py))
pa = np.array(path)
axA.step(pa[:, 0], pa[:, 1], where="mid", color="#39d353", lw=2.2, zorder=7)
axA.scatter(pa[:, 0], pa[:, 1], s=16, c="#39d353", zorder=8)
axA.scatter(pa[-1, 0], pa[-1, 1], s=130, facecolors="none", edgecolors="#ff5555", lw=2, zorder=9)
axA.text(pa[-1, 0]-1.7, pa[-1, 1]+0.35, "stuck (local)", color="#ff7777", fontsize=9, fontweight="bold")

# ===== Panel B — oka sheaf: Laplacian diffusion across the graph (lateral spread) =====
axB = axes[1]
base(axB, "oka — MMSheaf (sheaf diffusion)", "Laplacian 拡散: 点の降下ではなく、graph 上を横へ拡散し大域整合へ")
g = 9
nodes = np.linspace(-2.4, 2.4, g)
NX, NY = np.meshgrid(nodes, nodes)
# initial rough field on the graph (two localized 'beliefs'); diffuse toward consensus
val = (np.exp(-(((NX + 1.5) ** 2 + (NY + 1.3) ** 2) / 0.8))
       + 0.9 * np.exp(-(((NX - 1.6) ** 2 + (NY - 1.5) ** 2) / 0.6)))
# draw graph edges
segs = []
for i in range(g):
    for j in range(g):
        if i + 1 < g: segs.append([(NX[i, j], NY[i, j]), (NX[i+1, j], NY[i+1, j])])
        if j + 1 < g: segs.append([(NX[i, j], NY[i, j]), (NX[i, j+1], NY[i, j+1])])
axB.add_collection(LineCollection(segs, colors="#b39ddb", linewidths=0.4, alpha=0.45, zorder=4))
# Laplacian flow arrows: each node pulled toward neighbour mean (heat diffusion direction)
def nmean(F):
    s = np.zeros_like(F); c = np.zeros_like(F)
    for di, dj in ((1,0),(-1,0),(0,1),(0,-1)):
        rs = np.roll(np.roll(F, di, 0), dj, 1)
        s += rs; c += 1
    return s / c
flow = nmean(val) - val  # Laplacian (toward consensus)
# arrows point along the lateral diffusion; color by node value (the 'heat')
axB.quiver(NX, NY, flow * 0, flow * 0, alpha=0)  # keep autoscale sane
# spread arrows from high to low along the field gradient (lateral)
fx = np.gradient(val, nodes, axis=1) * -1
fy = np.gradient(val, nodes, axis=0) * -1
axB.quiver(NX, NY, fx, fy, val, cmap="cool", scale=14, width=0.006, alpha=0.9, zorder=7)
axB.scatter(NX, NY, s=22 + 120 * (val / val.max()), c=val, cmap="cool", edgecolors="white",
            linewidths=0.3, zorder=8)
axB.text(-2.3, -2.75, "局所 stalk → 大域 consensus (調和) へ並列に緩和", color="#9fe7ff", fontsize=9)

# ===== Panel C — maxwell-diffusion: stochastic annealed descent (temperature crosses barrier) =====
axC = axes[2]
base(axC, "maxwell-diffusion (block diffusion)", "焼きなまし探索: 高温で障壁を越え → 低温で精錬 → 大域最小へ")
x, y = START
T0, Tf, steps, lr = 0.55, 0.004, 600, 0.018
traj = [(x, y)]
samples = []
for t in range(steps):
    T = T0 * (Tf / T0) ** (t / steps)            # exponential annealing (temperature schedule)
    dx, dy = grad(x, y)
    x = x - lr * dx + np.sqrt(2 * lr * T) * rng.standard_normal()
    y = y - lr * dy + np.sqrt(2 * lr * T) * rng.standard_normal()
    x, y = np.clip(x, -L, L), np.clip(y, -L, L)
    traj.append((x, y))
    if t % 6 == 0:
        samples.append((x, y, t))
tc = np.array(traj)
sc = np.array(samples)
axC.scatter(sc[:, 0], sc[:, 1], s=10, c=sc[:, 2], cmap="autumn_r", alpha=0.5, zorder=6)  # exploration cloud
pts = tc.reshape(-1, 1, 2)
segc = np.concatenate([pts[:-1], pts[1:]], axis=1)
lc = LineCollection(segc, cmap="autumn_r", linewidths=1.6, alpha=0.9, zorder=7)
lc.set_array(np.arange(len(segc)))
axC.add_collection(lc)
axC.scatter(tc[-1, 0], tc[-1, 1], s=130, facecolors="none", edgecolors="#39d353", lw=2, zorder=9)
axC.text(tc[-1, 0]-2.0, tc[-1, 1]+0.3, "reaches global", color="#39d353", fontsize=9, fontweight="bold")
axC.annotate("crosses barrier\n(high-T)", xy=(0.2, 0.4), xytext=(-0.4, 1.7), color="#ffae6b",
             fontsize=8.5, ha="center", arrowprops=dict(arrowstyle="->", color="#ffae6b", lw=1.2))

fig.suptitle("勾配・マップの進め方の違い — baien (量子化降下) / oka (sheaf 拡散) / maxwell-diffusion (焼きなまし)",
             color="white", fontsize=17, fontweight="bold", y=0.99)
fig.text(0.5, 0.025,
         "同じ地形・同じ start。baien=離散greedyで局所停止 · oka=graph上を横方向に拡散して大域整合 · "
         "maxwell-diffusion=確率的に温度で障壁を越え大域最小へ",
         ha="center", color="#9aa0b4", fontsize=11)
fig.subplots_adjust(left=0.02, right=0.98, top=0.86, bottom=0.10, wspace=0.06)

base_out = "/Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/90-docs/baien/weight-family-traversal"
fig.savefig(base_out + ".png", dpi=170, facecolor=fig.get_facecolor())
fig.savefig(base_out + ".svg", facecolor=fig.get_facecolor())
print("wrote", base_out + ".png/.svg")
