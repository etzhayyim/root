#!/usr/bin/env python3
"""oka — sheaf-diffusion ON the 3D energy landscape, animated GIF.
9 modality stalks (hub-spoke graph) relax under sheaf diffusion: each is pulled
toward consensus (Laplacian) AND descends the energy gradient → they converge at
the deep GLOBAL well (not stuck local), the star contracts to the harmonic core.
Slow camera rotation, white-glow-on-dark style."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

rng = np.random.default_rng(3)
plt.rcParams.update({"font.family": ["Hiragino Sans", "DejaVu Sans"]})

def E(x, y):
    memo = -1.05 * np.exp(-(((x + 1.6) ** 2 + (y + 1.6) ** 2) / 3.2))
    gen  = -2.55 * np.exp(-(((x - 1.6) ** 2 + (y - 1.6) ** 2) / 0.50))   # deep GLOBAL well
    struct = -0.70 * np.exp(-(((x + 1.7) ** 2 + (y - 1.6) ** 2) / 4.0))
    rip  = 0.10 * np.sin(1.8 * x) * np.cos(1.8 * y)
    bowl = 0.045 * (x ** 2 + y ** 2)
    return memo + gen + struct + rip + bowl

def gradE(x, y, h=1e-3):
    return ((E(x+h, y)-E(x-h, y))/(2*h), (E(x, y+h)-E(x, y-h))/(2*h))

L = 3.0
g = np.linspace(-L, L, 90)
GX, GY = np.meshgrid(g, g)
GZ = E(GX, GY)

# 9 modality stalks, initially scattered (disagreeing views)
M = 9
ang = np.linspace(0, 2*np.pi, M, endpoint=False)
px = -0.4 + 1.9*np.cos(ang) + 0.3*rng.standard_normal(M)
py = -0.4 + 1.9*np.sin(ang) + 0.3*rng.standard_normal(M)
px = np.clip(px, -L, L); py = np.clip(py, -L, L)

FR = 84
LR, ALPHA = 0.05, 0.085   # gradient descent / consensus(Laplacian) pull

fig = plt.figure(figsize=(9, 8), facecolor="#06060c")
ax = fig.add_subplot(111, projection="3d")

def step():
    global px, py
    cxx, cyy = px.mean(), py.mean()           # consensus centroid (hub)
    gx, gy = gradE(px, py)
    px = px - LR*gx + ALPHA*(cxx - px)
    py = py - LR*gy + ALPHA*(cyy - py)
    px[:] = np.clip(px, -L, L); py[:] = np.clip(py, -L, L)

def draw(frame):
    ax.clear()
    ax.set_facecolor("#06060c"); ax.set_axis_off()
    ax.plot_surface(GX, GY, GZ, color="#7c54c9", rstride=2, cstride=2,
                    edgecolor=(1,1,1,0.14), linewidth=0.3, antialiased=True, shade=True, alpha=0.9)
    if frame > 2:
        step(); step()
    pz = E(px, py) + 0.12
    cxx, cyy = px.mean(), py.mean(); cz = E(cxx, cyy) + 0.14
    # hub-spoke edges (the sheaf graph) — contract toward consensus over time
    for i in range(M):
        ax.plot([px[i], cxx], [py[i], cyy], [pz[i], cz], color="#cbb8f0", lw=0.9, alpha=0.55)
    ax.scatter(px, py, pz, s=42, c="#b39ddb", edgecolors="white", linewidths=0.5, depthshade=False)
    ax.scatter([cxx],[cyy],[cz], s=160, marker="*", c="#ffd23f", edgecolors="k", linewidths=0.5, depthshade=False)
    ax.scatter([1.6],[1.6],[E(1.6,1.6)+0.05], s=70, marker="x", c="#39d353", depthshade=False)
    spread = np.sqrt(((px-cxx)**2 + (py-cyy)**2).mean())
    ax.text2D(0.5, 0.95, "oka — sheaf diffusion: 9 stalks が大域整合へ緩和",
              transform=ax.transAxes, ha="center", color="white", fontsize=14, fontweight="bold")
    ax.text2D(0.5, 0.905, f"consensus 収束: 不一致 spread={spread:.2f}  →  全 stalk が一致(調和=ker L_F)",
              transform=ax.transAxes, ha="center", color="#b39ddb", fontsize=10)
    ax.view_init(elev=32, azim=-60 + frame*1.6)        # slow rotation
    ax.set_xlim(-L, L); ax.set_ylim(-L, L); ax.set_zlim(-2.8, 0.6)
    ax.set_box_aspect((1,1,0.55))
    return []

anim = FuncAnimation(fig, draw, frames=FR, interval=80, blit=False)
out = "/Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/90-docs/baien/oka-sheaf-diffusion-3d.gif"
anim.save(out, writer=PillowWriter(fps=14), dpi=90)
print("wrote", out)
