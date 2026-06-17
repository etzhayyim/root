#!/usr/bin/env python3
"""3D energy-landscape (grokking) comparing baien / maxwell-diffusion / oka.
Surface = oka (the sheaf manifold) · white ball = maxwell-diffusion (dynamics) ·
deep narrow well = baien (efficient minimum) · descent path = RSi drive."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa

R = 3.0
n = 120
xs = np.linspace(-R, R, n)
ys = np.linspace(-R, R, n)
X, Y = np.meshgrid(xs, ys)

def E(x, y):
    memo  = -1.05 * np.exp(-(((x + 1.6) ** 2 + (y + 1.6) ** 2) / 3.2))   # wide shallow = memorization
    gen   = -2.55 * np.exp(-(((x - 1.6) ** 2 + (y - 1.6) ** 2) / 0.45))  # narrow deep = generalization (baien)
    struct= -0.70 * np.exp(-(((x + 1.7) ** 2 + (y - 1.6) ** 2) / 4.0))   # broad structural region
    ripple = 0.10 * np.sin(1.8 * x) * np.cos(1.8 * y)                     # mesh texture
    bowl   = 0.045 * (x ** 2 + y ** 2)                                   # gentle rim lift
    return memo + gen + struct + ripple + bowl

Z = E(X, Y)

fig = plt.figure(figsize=(13, 8.6), facecolor="#08080e")
ax = fig.add_subplot(111, projection="3d")
ax.set_facecolor("#08080e")

# purple shaded mesh surface (oka = the manifold)
surf = ax.plot_surface(
    X, Y, Z, color="#7c54c9", rstride=2, cstride=2,
    edgecolor=(1, 1, 1, 0.16), linewidth=0.3, antialiased=True, shade=True, alpha=0.95,
)

# --- weight markers on the landscape ---
def z_at(x, y):
    return float(E(np.array(x), np.array(y)))

# baien — deep narrow generalization well
bx, by = 1.6, 1.6
ax.scatter([bx], [by], [z_at(bx, by) + 0.05], s=130, c="#39d353",
           edgecolors="white", linewidths=1.4, depthshade=False, zorder=10)
ax.text(bx + 0.15, by + 0.2, z_at(bx, by) + 0.55, "baien (BitNet 1.58b)\nefficient minimum",
        color="#39d353", fontsize=10.5, fontweight="bold")

# maxwell-diffusion — white ball mid-descent (the rolling particle)
mx, my = 0.15, 0.05
ax.scatter([mx], [my], [z_at(mx, my) + 0.07], s=180, c="white",
           edgecolors="#e08a4f", linewidths=2.0, depthshade=False, zorder=11)
ax.text(mx - 1.5, my - 0.1, z_at(mx, my) + 0.7, "maxwell-diffusion\n(rolling: denoise dynamics)",
        color="#f0a06a", fontsize=10.5, fontweight="bold")

# RSi descent trajectory: memorization basin → over barrier → generalization well
tt = np.linspace(0, 1, 60)
tx = -1.6 + tt * (1.6 - (-1.6))
ty = -1.6 + tt * (1.6 - (-1.6)) + 0.5 * np.sin(np.pi * tt)
tz = E(tx, ty) + 0.18
ax.plot(tx, ty, tz, color="#c08bf0", lw=2.2, ls=(0, (4, 3)), zorder=9)
ax.text(-1.9, -1.8, z_at(-1.6, -1.6) + 0.6, "memorization\n(wide, shallow)",
        color="#9aa0b4", fontsize=9.5)
ax.text(0.2, 1.0, 1.4, "RSi = continued-training drive\n(pushes over the barrier)",
        color="#c08bf0", fontsize=9.5)

# oka label — the surface itself
ax.text(-2.8, 2.6, 1.9, "oka (MMSheaf / sheaf diffusion)\n= the manifold itself — defines the terrain",
        color="#b39ddb", fontsize=10.5, fontweight="bold")

# axes styling (dark)
for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
    axis.set_pane_color((0, 0, 0, 0))
    axis.line.set_color((1, 1, 1, 0.25))
ax.grid(False)
ax.set_xlabel("Configuration Coordinate X", color="#8890a8", fontsize=10, labelpad=8)
ax.set_ylabel("Configuration Coordinate Y", color="#8890a8", fontsize=10, labelpad=8)
ax.set_zlabel("Energy", color="#8890a8", fontsize=10, labelpad=4)
ax.tick_params(colors="#555a6e", labelsize=7)
ax.view_init(elev=30, azim=-54)
ax.set_box_aspect((1, 1, 0.6))

fig.suptitle("etzhayyim weight-family on the grokking energy landscape (3D)",
             color="white", fontsize=18, fontweight="bold", y=0.96)
fig.text(0.5, 0.045,
         "oka = terrain (sheaf manifold)   ·   maxwell-diffusion = the rolling particle (dynamics)   ·   "
         "baien = the deep narrow well (efficient circuit)   ·   RSi = the descent drive",
         ha="center", color="#9aa0b4", fontsize=10.5)
fig.text(0.5, 0.018, 'ref: grokking energy-landscape / "temperature: learning vs exploration" (YouTube)',
         ha="center", color="#5a5f72", fontsize=8.5)

base = "/Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/90-docs/baien/weight-family-landscape-3d"
fig.savefig(base + ".png", dpi=200, facecolor=fig.get_facecolor())
fig.savefig(base + ".svg", facecolor=fig.get_facecolor())
print("wrote", base + ".png/.svg")
