import numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from matplotlib.animation import FuncAnimation, PillowWriter
rng=np.random.default_rng(5); plt.rcParams.update({"font.family":["Hiragino Sans","DejaVu Sans"]})
L,K,dx,R=42,26,0.6,1.0
pos=np.zeros((L,K,3))
for l in range(L):
    th=np.linspace(0,2*np.pi,K,endpoint=False)+0.06*l; r=R+0.05*rng.standard_normal(K)
    pos[l,:,0]=l*dx; pos[l,:,1]=r*np.cos(th)+0.04*rng.standard_normal(K); pos[l,:,2]=r*np.sin(th)+0.04*rng.standard_normal(K)
segs=[[pos[l,k],pos[l+1,(k+o)%K]] for l in range(L-1) for k in range(K) for o in (-2,0,1,K//2)]
fig=plt.figure(figsize=(11,8),facecolor="#05050a"); ax=fig.add_subplot(111,projection="3d")
ax.set_facecolor("#05050a"); ax.set_axis_off()
ax.add_collection3d(Line3DCollection(segs,colors=(1,1,1,0.09),linewidths=0.3))
P=pos.reshape(-1,3); ax.scatter(P[:,0],P[:,1],P[:,2],s=7,c=plt.cm.plasma(np.repeat(np.linspace(0,1,L),K)),alpha=0.85)
ax.set_xlim(-1,(L-1)*dx+1); ax.set_ylim(-1.6,1.6); ax.set_zlim(-1.6,1.6); ax.set_box_aspect(((L-1)*dx+2,3.2,3.2))
fig.suptitle("maxwell-1 (Gemma 4 E4B) — 42 層 3D 接続構造（回転）",color="white",fontsize=15,fontweight="bold",y=0.9)
fig.text(0.5,0.12,"42 layers · hidden 2560 · GQA 8/2 · FFN 10240 · 入力(青)→LM head(黄)",ha="center",color="#9aa0b4",fontsize=10)
def upd(f): ax.view_init(elev=10+6*np.sin(f/72*2*np.pi), azim=f*5); return []
FuncAnimation(fig,upd,frames=72,interval=80).save("/Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/90-docs/baien/maxwell1-layers-3d.gif",writer=PillowWriter(fps=14),dpi=85)
print("wrote layers gif")
