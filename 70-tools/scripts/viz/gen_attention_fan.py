import numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
rng=np.random.default_rng(8); plt.rcParams.update({"font.family":["Hiragino Sans","DejaVu Sans"]})
fig=plt.figure(figsize=(10.5,9),facecolor="#05050a"); ax=fig.add_subplot(111,projection="3d")
ax.set_facecolor("#05050a"); ax.set_axis_off()
H=8  # GQA query heads -> 8 petals
for h in range(H):
    base=2*np.pi*h/H
    for f in range(60):
        r=np.linspace(0.08,2.7,70)
        ang=base+(f/60-0.5)*0.52
        x=r*np.cos(ang)+0.12*np.sin(4*r)*(f/60-0.5)
        y=r*np.sin(ang)+0.12*np.cos(4*r)*(f/60-0.5)
        z=0.35*np.sin(1.7*r+base)*(r/2.7)
        ax.plot(x,y,z,color="white",lw=0.32,alpha=0.14)
# inter-token causal chords (faint, the all-to-all)
N=44; th=np.linspace(0,2*np.pi,N,endpoint=False); ring=np.c_[2.5*np.cos(th),2.5*np.sin(th),np.zeros(N)]
for i in range(N):
    for j in range(0,i,3):
        ax.plot([ring[i,0],ring[j,0]],[ring[i,1],ring[j,1]],[0.05,0.05],color="#cbd6ff",lw=0.2,alpha=0.07)
# colored 8-point core (the attention 'star')
cc=rng.standard_normal((300,3))*0.20; cc[:,2]*=0.4
ax.scatter(cc[:,0],cc[:,1],cc[:,2],s=7,c=np.linspace(0,1,300),cmap="cool",alpha=0.9)
for h in range(H):
    a=2*np.pi*h/H; ax.plot([0,0.9*np.cos(a)],[0,0.9*np.sin(a)],[0,0],color=plt.cm.rainbow(h/H),lw=2,alpha=0.8)
ax.view_init(elev=74,azim=20); ax.set_xlim(-2.7,2.7); ax.set_ylim(-2.7,2.7); ax.set_zlim(-1.6,1.6); ax.set_box_aspect((1,1,0.6))
fig.suptitle("self-attention（1 層）= all-to-all causal fan / GQA 8 query heads",color="white",fontsize=15,fontweight="bold",y=0.9)
fig.text(0.5,0.10,"8 本の petal = 8 query heads（中心=softmax(QKᵀ/√d)V の集約コア / 外周=token / fiber=注意の重み）",ha="center",color="#9aa0b4",fontsize=10.5)
fig.subplots_adjust(left=0,right=1,top=0.97,bottom=0.06)
fig.savefig("/Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/90-docs/baien/maxwell1-attention-fan.png",dpi=190,facecolor=fig.get_facecolor())
print("wrote attention fan")
