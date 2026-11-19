import pcbnew,sys,math,heapq,collections
b=pcbnew.LoadBoard(sys.argv[1]); T=pcbnew.ToMM; net=sys.argv[2]; a_ref,a_pad,z_ref,z_pad=sys.argv[3:7]
# graph over track endpoints + vias + pads (same net); edge weight = length / width  (resistance proxy)
nodes={}
def key(x,y,l): return (round(x,2),round(y,2),l)
adj=collections.defaultdict(list)
def add(u,v,w,wd,desc): adj[u].append((v,w,wd,desc)); adj[v].append((u,w,wd,desc))
for t in b.GetTracks():
    if t.GetNetname()!=net: continue
    if t.GetClass()=='PCB_VIA':
        p=t.GetPosition(); x,y=T(p.x),T(p.y)
        ls=[pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu]
        for l1,l2 in zip(ls,ls[1:]): add(key(x,y,l1),key(x,y,l2),0.05,0.45,'via')
    else:
        s,e=t.GetStart(),t.GetEnd(); L=math.hypot(T(e.x-s.x),T(e.y-s.y)); wd=T(t.GetWidth()); l=t.GetLayer()
        add(key(T(s.x),T(s.y),l),key(T(e.x),T(e.y),l),L/wd,wd,(b.GetLayerName(l),round(L,1),round(wd,2)))
def padnodes(ref,num):
    f=b.FindFootprintByReference(ref); out=[]
    for p in f.Pads():
        if p.GetNumber()==num: 
            for l in (pcbnew.F_Cu,pcbnew.B_Cu):
                if p.GetLayerSet().Contains(l): out.append((T(p.GetPosition().x),T(p.GetPosition().y),l))
    return out
# connect each node to nearest pad within 0.6mm
def near(ref,num):
    res=[]
    for (x,y,l) in padnodes(ref,num):
        for k in list(adj.keys()):
            if k[2]==l and math.hypot(k[0]-x,k[1]-y)<0.8: res.append(k)
    return res
src=near(a_ref,a_pad); dst=set(near(z_ref,z_pad))
dist={k:0 for k in src}; prev={}; pq=[(0,k) for k in src]
while pq:
    d,u=heapq.heappop(pq)
    if d>dist.get(u,1e9): continue
    if u in dst: break
    for v,w,wd,desc in adj[u]:
        nd=d+w
        if nd<dist.get(v,1e9): dist[v]=nd; prev[v]=(u,desc); heapq.heappush(pq,(nd,v))
end=[k for k in dst if k in dist]
if not end: print('no path'); sys.exit()
u=min(end,key=lambda k:dist[k]); segs=[]
while u in prev: u2,desc=prev[u]; segs.append(desc); u=u2
segs.reverse(); 
print('path squares (len/width) %.1f  => %.1f mohm @1oz(0.5mOhm/sq*..)'%(dist[min(end,key=lambda k:dist[k])],dist[min(end,key=lambda k:dist[k])]*0.5))
print([s for s in segs if s!='via'])
