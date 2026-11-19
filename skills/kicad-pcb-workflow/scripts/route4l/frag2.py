import pcbnew,math,sys
b=pcbnew.LoadBoard(sys.argv[1]); T=pcbnew.ToMM; V=pcbnew.VECTOR2I; mm=pcbnew.FromMM; KEEP=[]
COPPER=(pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu)
obs=[]
for t in b.GetTracks():
    if t.GetNetname()=='GND': continue
    bx=t.GetBoundingBox(); obs.append((t.GetEffectiveShape(),T(bx.GetLeft()),T(bx.GetTop()),T(bx.GetRight()),T(bx.GetBottom())))
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname()=='GND': continue
        bx=p.GetBoundingBox(); ls=[l for l in COPPER if p.GetLayerSet().Contains(l)] or [pcbnew.F_Cu]
        obs.append((p.GetEffectiveShape(ls[0]),T(bx.GetLeft()),T(bx.GetTop()),T(bx.GetRight()),T(bx.GetBottom())))
def margin(x,y):
    P=V(mm(x),mm(y)); m=9
    for sh,x0,y0,x1,y1 in obs:
        if x<x0-1 or x>x1+1 or y<y0-1 or y>y1+1: continue
        m=min(m,math.sqrt(sh.SquaredDistance(P))/1e6)
    return m-0.225
gv=[(T(t.GetPosition().x),T(t.GetPosition().y)) for t in b.GetTracks() if t.GetClass()=='PCB_VIA' and t.GetNetname()=='GND']
added=0
for z in b.Zones():
    if z.GetIsRuleArea() or z.GetNetname()!='GND': continue
    L=z.GetFirstLayer()
    if L==pcbnew.In1_Cu: continue
    poly=z.GetFilledPolysList(L)
    for i in range(poly.OutlineCount()):
        if any(poly.Contains(V(mm(x),mm(y)),i,0) for x,y in gv): continue
        bx=poly.Outline(i).BBox(); x0,x1,y0,y1=[T(v) for v in (bx.GetLeft(),bx.GetRight(),bx.GetTop(),bx.GetBottom())]
        best=None; y=y0
        while y<=y1:
            x=x0
            while x<=x1:
                if poly.Contains(V(mm(x),mm(y)),i,0) and all(math.hypot(x-a,y-c)>0.8 for a,c in gv):
                    m=margin(x,y)
                    if best is None or m>best[0]: best=(m,x,y)
                x+=0.1
            y+=0.1
        if best and best[0]>=0.12:
            v=pcbnew.PCB_VIA(b); KEEP.append(v); v.SetPosition(V(mm(best[1]),mm(best[2]))); v.SetWidth(mm(0.45)); v.SetDrill(mm(0.2)); v.SetNet(b.FindNet('GND')); v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v); gv.append((best[1],best[2])); added+=1
        else: print('fragment without room',b.GetLayerName(L),round(x0,1),round(y0,1),round(x1,1),round(y1,1),'area',round(abs(poly.Outline(i).Area())/1e12,2))
print('fragment vias added',added)
pcbnew.ZONE_FILLER(b).Fill([z for z in b.Zones() if not z.GetIsRuleArea()]); b.Save(sys.argv[2])
