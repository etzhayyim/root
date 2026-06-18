#!/usr/bin/env python3
"""oka / baien / maxwell-diffusion as 3D 'neural-brain' fiber structures.
Each model's ARCHITECTURE = a distinct fiber topology, rendered in the
white-glow-on-dark radial style of the reference clips."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rng = np.random.default_rng(11)
plt.rcParams.update({"font.family": ["Hiragino Sans", "DejaVu Sans"]})

fig = plt.figure(figsize=(18, 7.2), facecolor="#05050a")

def style(ax, title, sub, core_color):
    ax.set_facecolor("#05050a")
    ax.set_axis_off()
    ax.set_title(title, color="white", fontsize=15, fontweight="bold", pad=2)
    ax.text2D(0.5, 0.95, sub, transform=ax.transAxes, ha="center",
              color=core_color, fontsize=10)

# ============ oka — sheaf: radially-symmetric mandala (9 modality stalks glued) ============
axO = fig.add_subplot(131, projection="3d")
style(axO, "oka — MMSheaf (sheaf diffusion)",
      "9-modality stalks を大域接着：放射対称・全結合の曼荼羅", "#b39ddb")
petals = 9
for k in range(petals):
    th = 2 * np.pi * k / petals
    for f in range(46):
        r = np.linspace(0.08, 2.5, 60)
        spread = 0.20 * np.sin(np.pi * (f / 46))
        ang = th + (f / 46 - 0.5) * 0.55
        x = r * np.cos(ang) + spread * np.sin(4 * r)
        y = r * np.sin(ang) + spread * np.cos(4 * r)
        z = 0.45 * np.sin(1.6 * r + th) * (r / 2.5)
        axO.plot(x, y, z, color="white", lw=0.35, alpha=0.16)
# sheaf gluing: cross-links between adjacent petals near the core
for k in range(petals):
    th1, th2 = 2*np.pi*k/petals, 2*np.pi*(k+1)/petals
    for rr in (0.7, 1.2, 1.8):
        a = np.linspace(th1, th2, 20)
        axO.plot(rr*np.cos(a), rr*np.sin(a), 0.1*np.sin(a*6), color="#c9b8f0", lw=0.4, alpha=0.25)
# colored core
cc = rng.standard_normal((260, 3)) * 0.22
axO.scatter(cc[:,0], cc[:,1], cc[:,2]*0.4, s=6,
            c=np.linspace(0,1,260), cmap="cool", alpha=0.9)
axO.view_init(elev=68, azim=35)
axO.set_xlim(-2.6,2.6); axO.set_ylim(-2.6,2.6); axO.set_zlim(-2,2)
axO.set_box_aspect((1,1,0.7))

# ============ baien — BitNet 1.58b: sparse angular ternary lattice ============
axB = fig.add_subplot(132, projection="3d")
style(axB, "baien — BitNet 1.58b",
      "三値 {-1,0,+1}：疎・角ばった格子（最圧縮の骨格）", "#39d353")
g = 5
pts = np.array([(i,j,k) for i in range(g) for j in range(g) for k in range(g)], float)
pts = (pts - (g-1)/2) / ((g-1)/2) * 2.0
# ternary sparsity: keep only ~32% of axis/diagonal edges
for a in range(len(pts)):
    for b in range(a+1, len(pts)):
        d = pts[b] - pts[a]
        if 0 < np.sum(d != 0) <= 2 and np.allclose(np.abs(d[d!=0]), np.abs(d[d!=0])[0]) \
           and np.linalg.norm(d) < 1.3 and rng.random() < 0.32:
            seg = np.linspace(pts[a], pts[b], 2)
            axB.plot(seg[:,0], seg[:,1], seg[:,2], color="#bfeccb", lw=0.6, alpha=0.45)
keep = rng.random(len(pts)) < 0.5
axB.scatter(pts[keep,0], pts[keep,1], pts[keep,2], s=14, c="#39d353", alpha=0.85, edgecolors="white", linewidths=0.2)
axB.view_init(elev=22, azim=40)
axB.set_xlim(-2.2,2.2); axB.set_ylim(-2.2,2.2); axB.set_zlim(-2.2,2.2)
axB.set_box_aspect((1,1,1))

# ============ maxwell-diffusion: fanning denoise sheet (128-expert MoE blocks) ============
axM = fig.add_subplot(133, projection="3d")
style(axM, "maxwell-diffusion (block diffusion)",
      "反復 denoise の層 × 128-expert：扇状に展開する場", "#f0a06a")
layers = 16
for li in range(layers):
    t = li / (layers - 1)
    spine = -2.2 + 4.4 * t                     # position along the spine
    nfan = 34
    for f in range(nfan):
        u = f / (nfan - 1) - 0.5
        ang = u * np.pi * (0.55 + 0.5 * t)     # fan widens along denoise steps
        rr = np.linspace(0.05, 1.7 + 0.6*t, 40)
        x = spine + 0.25*np.sin(3*rr)*u
        y = rr * np.sin(ang)
        z = rr * np.cos(ang) - 0.3
        col = plt.cm.plasma(0.25 + 0.6*t)
        axM.plot(x, y, z, color="white", lw=0.3, alpha=0.13)
        if f % 8 == 0:
            axM.plot(x, y, z, color=col, lw=0.5, alpha=0.5)
# bright core spine
axM.plot(np.linspace(-2.2,2.2,40), np.zeros(40), np.full(40,-0.3), color="#ffcaa0", lw=1.2, alpha=0.7)
axM.view_init(elev=18, azim=-72)
axM.set_xlim(-2.6,2.6); axM.set_ylim(-2.3,2.3); axM.set_zlim(-2.3,2.3)
axM.set_box_aspect((1.3,1,1))

fig.suptitle("etzhayyim の3モデルを 3D neural-structure として可視化",
             color="white", fontsize=17, fontweight="bold", y=0.99)
fig.text(0.5, 0.03,
         "oka = 放射対称の sheaf 曼荼羅（全結合・大域整合） · baien = 疎な三値格子（最圧縮の骨格） · "
         "maxwell-diffusion = 扇状に展開する denoise 場（128-expert）",
         ha="center", color="#9aa0b4", fontsize=11)
fig.subplots_adjust(left=0.0, right=1.0, top=0.9, bottom=0.08, wspace=0.0)

base = "/Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/90-docs/baien/weight-family-brains-3d"
fig.savefig(base + ".png", dpi=200, facecolor=fig.get_facecolor())
print("wrote", base + ".png")
