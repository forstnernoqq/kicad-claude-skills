import json,math,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.patches as pa
exec(open('pack.py').read().split('# ---------- groups')[0].split("RES=0.1")[0])
d=json.load(open('fp.json'))
for i in range(1,10): d['TP%d'%i].update(cx0=-0.7,cx1=0.7,cy0=-0.7,cy1=0.7)
d['J4'].update(cx0=-1.6,cx1=1.6,cy0=-2.85,cy1=2.85)
for r in ('JP1','JP2'): d[r].update(cx0=-1.16,cx1=1.16,cy0=-0.52,cy1=0.52)
d['J5'].update(cx0=-6.2,cx1=6.2,cy0=-2.5,cy1=5.0)
P=json.load(open('placement14.json')); pl=P['place']; grp=P['grp']
def bbox(r,rot,side):
    x0,x1,y0,y1=d[r]['cx0'],d[r]['cx1'],d[r]['cy0'],d[r]['cy1']
    pts=[(x0,y0),(x0,y1),(x1,y0),(x1,y1)]
    if side=='B': pts=[(x,-y) for x,y in pts]
    t=math.radians(rot); c,s=round(math.cos(t),6),round(math.sin(t),6)
    pts=[(x*c+y*s,-x*s+y*c) for x,y in pts]
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; return min(xs),max(xs),min(ys),max(ys)
col=dict(A='#e41a1c',B='#377eb8',C='#4daf4a',D='#984ea3',E='#ff7f00',F='#a65628',G='#f781bf',H='#999999')
fig,ax=plt.subplots(2,1,figsize=(16,10))
for a,side in zip(ax,('T','B')):
    a.add_patch(pa.FancyBboxPatch((67,56),46,8,boxstyle='round,pad=0,rounding_size=0',fc='none',ec='k',lw=0))
    a.add_patch(pa.Rectangle((65,54),50,15,fc='#eef',ec='k',lw=1.5))
    for r,p in pl.items():
        if not p or (p['side']!=side and r!='J5'): continue
        if r=='J5' and side=='T': continue
        b=bbox(r,p['rot'],side); a.add_patch(pa.Rectangle((p['x']+b[0],p['y']+b[2]),b[1]-b[0],b[3]-b[2],fc=col[grp[r]],alpha=.6,ec='k',lw=.4))
        if (b[1]-b[0])>2.5 or r.startswith(('U','Q','J','SW','L')): a.text(p['x'],p['y'],r,fontsize=6,ha='center',va='center')
    if side=='T': a.add_patch(pa.Rectangle((97-7.2,68.7-11.5),14.4,11.5,fc='none',ec='m',lw=1.2,ls='--'))
    a.set_xlim(60,135); a.set_ylim(75,50); a.set_aspect('equal'); a.set_title({'T':'TOP','B':'BOTTOM'}[side])
plt.savefig('pl14.png',dpi=90,bbox_inches='tight')
