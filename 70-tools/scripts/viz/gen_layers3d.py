#!/usr/bin/env python3
"""maxwell-1 (Gemma 4 E4B) — 42-layer 3D connection structure, fanning white-fiber
style. Real architecture: 42 layers, hidden 2560 (subsampled to a ring per layer),
GQA 8/2 heads, FFN 10240. Inter-layer fibers = the weight connections."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection

rng = np.random.default_rng(5)
plt.rcParams.update({"font.family": ["Hiragino Sans", "DejaVu Sans"]})

L = 42                 # real num_hidden_layers
K = 28                 # nodes drawn per layer (subsample of hidden=2560)
dx = 0.6
R = 1.0

# node positions: layer l = a jittered ring in the (y,z) plane at depth x=l*dx
pos = np.zeros((L, K, 3))
for l in range(L):
    th = np.linspace(0, 2*np.pi, K, endpoint=False) + 0.06*l
    r = R + 0.05*rng.standard_normal(K)
    pos[l, :, 0] = l*dx
    pos[l, :, 1] = r*np.cos(th) + 0.04*rng.standard_normal(K)
    pos[l, :, 2] = r*np.sin(th) + 0.04*rng.standard_normal(K)

# inter-layer fibers: each node → a small fan of nodes in the next layer
segs = []
for l in range(L-1):
    for k in range(K):
        for off in (-2, 0, 1, 3, K//2):       # local + a long-range (fan) target
            t = (k+off) % K
            segs.append([pos[l, k], pos[l+1, t]])

fig = plt.figure(figsize=(15, 8.4), facecolor="#05050a")
ax = fig.add_subplot(111, projection="3d")
ax.set_facecolor("#05050a"); ax.set_axis_off()

ax.add_collection3d(Line3DCollection(segs, colors=(1, 1, 1, 0.10), linewidths=0.3))
# nodes colored by depth (embedding→output) for a faint rainbow core
cols = plt.cm.plasma(np.repeat(np.linspace(0, 1, L), K))
P = pos.reshape(-1, 3)
ax.scatter(P[:, 0], P[:, 1], P[:, 2], s=7, c=cols, alpha=0.85, depthshade=True)

# endpoint labels
ax.text(0, 0, 1.7, "input\nembedding\n(vocab 262144)", color="#9fe7ff", fontsize=9, ha="center")
ax.text((L-1)*dx, 0, 1.7, "LM head\n→ logits", color="#ffcaa0", fontsize=9, ha="center")
ax.text((L//2)*dx, 0, -1.85, "× 42 layers  (each = causal self-attn GQA 8/2  +  FFN 10240)",
        color="#c9b8f0", fontsize=10, ha="center")

ax.view_init(elev=12, azim=-74)
ax.set_xlim(-1, (L-1)*dx+1); ax.set_ylim(-1.6, 1.6); ax.set_zlim(-1.6, 1.6)
ax.set_box_aspect(((L-1)*dx+2, 3.2, 3.2))

fig.suptitle("maxwell-1（Gemma 4 E4B）— 42 層の 3D 接続構造", color="white", fontsize=18, fontweight="bold", y=0.93)
fig.text(0.5, 0.10, "real architecture: 42 layers · hidden 2560 · GQA 8/2 heads · FFN 10240 · vocab 262K  "
                    "（fiber = 層間の重み接続 / node = hidden ユニット subsample）",
         ha="center", color="#9aa0b4", fontsize=11)
fig.subplots_adjust(left=0, right=1, top=0.96, bottom=0.06)

base = "/Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/90-docs/baien/maxwell1-layers-3d"
fig.savefig(base + ".png", dpi=190, facecolor=fig.get_facecolor())
print("wrote", base + ".png", "| segs", len(segs))
