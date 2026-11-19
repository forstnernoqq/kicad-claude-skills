"""post12.py routed.kicad_pcb out.kicad_pcb [drc.json]
GND pours F/B (+existing In1 plane), exact-shape clearance-checked stitching vias, QFN EP vias, fragment vias, isolated-pad stubs, widen thin tracks, solid connection for starved pads."""
import pcbnew,sys,math,json,re
b=pcbnew.LoadBoard(sys.argv[1]); mm=pcbnew.FromMM; V=pcbnew.VECTOR2I; T=pcbnew.ToMM; KEEP=[]
drc=json.load(open(sys.argv[3])) if len(sys.argv)>3 else None
gnd=b.FindNet('GND'); bb=b.GetBoardEdgesBoundingBox(); m=mm(0.45)
for t in b.GetTracks():
    if t.GetClass()=='PCB_TRACK' and t.GetWidth()<mm(0.1): t.SetWidth(mm(0.1))
if drc:
    for v in drc['violations']:
        if v['type']=='starved_thermal':
            for it in v['items']:
                mt=re.match(r'Pad (\S+) \[GND\] of (\S+) on',it['description'])
                if mt:
                    f=b.FindFootprintByReference(mt.group(2))
                    for p in f.Pads():
                        if p.GetNumber()==mt.group(1) and p.GetNetname()=='GND': p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
zones={}
for layer in (pcbnew.F_Cu,pcbnew.B_Cu):
    z=pcbnew.ZONE(b); KEEP.append(z); z.SetLayer(layer); z.SetNet(gnd)
    z.SetLocalClearance(mm(0.2)); z.SetMinThickness(mm(0.2)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS); z.SetThermalReliefGap(mm(0.2)); z.SetThermalReliefSpokeWidth(mm(0.25))
    o=z.Outline(); o.NewOutline()
    for x,y in ((bb.GetLeft()+m,bb.GetTop()+m),(bb.GetRight()-m,bb.GetTop()+m),(bb.GetRight()-m,bb.GetBottom()-m),(bb.GetLeft()+m,bb.GetBottom()-m)): o.Append(x,y)
    b.Add(z); zones[layer]=z
allz=[z for z in b.Zones() if not z.GetIsRuleArea()]
pcbnew.ZONE_FILLER(b).Fill(allz)
# obstacle list: (shape, layerset-as-set-of-layer-ids, x0,y0,x1,y1)
obs=[]
def add_obs(item,layers):
    if item.GetClass()=='PAD':
        lay=sorted(layers)[0] if layers else pcbnew.F_Cu
        sh=item.GetEffectiveShape(lay)
    else: sh=item.GetEffectiveShape()
    bx=item.GetBoundingBox()
    obs.append((sh,layers,T(bx.GetLeft()),T(bx.GetTop()),T(bx.GetRight()),T(bx.GetBottom())))
COPPER=(pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu)
def build():
    obs.clear()
    for t in b.GetTracks():
        if t.GetNetname()=='GND': continue
        if t.GetClass()=='PCB_VIA': add_obs(t,set(COPPER))
        else: add_obs(t,{t.GetLayer()})
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname()=='GND': continue
            ls=set(l for l in COPPER if p.GetLayerSet().Contains(l))
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_NPTH,): ls=set(COPPER)
            add_obs(p,ls)
build()
def free(x,y,r,layers,mg):
    if r>0.2 and (not board_ok(x,y,0.95) or any(math.hypot(x-a,y-c)<rr+1.0 for a,c,rr in J3H) or any(math.hypot(x-a,y-c)<0.95 for a,c in placed)): return False
    return free0(x,y,r,layers,mg)
def free0(x,y,r,layers,mg):
    """circle of radius r at (x,y) keeps mg clearance from non-GND copper on `layers`"""
    P=V(mm(x),mm(y)); lim=r+mg
    for sh,ls,x0,y0,x1,y1 in obs:
        if x<x0-lim-0.3 or x>x1+lim+0.3 or y<y0-lim-0.3 or y>y1+lim+0.3: continue
        if not (ls & layers): continue
        if math.sqrt(sh.SquaredDistance(P))/1e6 < lim: return False
    return True
ALL=set(COPPER)
X0,Y0,X1,Y1,RC=T(bb.GetLeft()),T(bb.GetTop()),T(bb.GetRight()),T(bb.GetBottom()),2.0
def board_ok(x,y,mg):
    # distance to the rounded-rectangle outline must be >= mg (inside)
    cx=min(max(x,X0+RC),X1-RC); cy=min(max(y,Y0+RC),Y1-RC)
    d=RC-math.hypot(x-cx,y-cy) if (x<X0+RC or x>X1-RC) and (y<Y0+RC or y>Y1-RC) else min(x-X0,X1-x,y-Y0,Y1-y)
    return d>=mg
J3H=[]
for f in b.GetFootprints():
    if f.GetReference()=='J3':
        for g in f.GraphicalItems():
            if g.GetLayer()==pcbnew.Edge_Cuts and g.GetShapeStr()=='Circle': J3H.append((T(g.GetCenter().x),T(g.GetCenter().y),T(g.GetRadius())))
placed=[(T(t.GetPosition().x),T(t.GetPosition().y)) for t in b.GetTracks() if t.GetClass()=='PCB_VIA']
_free0=None
def addvia(x,y):
    placed.append((x,y))
    v=pcbnew.PCB_VIA(b); KEEP.append(v); v.SetPosition(V(mm(x),mm(y))); v.SetWidth(mm(0.45)); v.SetDrill(mm(0.2)); v.SetNet(gnd); v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
nv=0
def inside(layer,x,y): return zones[layer].HitTestFilledArea(layer,V(mm(x),mm(y)),0)
# exposed pad vias
u2=b.FindFootprintByReference('U2')
for p in u2.Pads():
    if p.GetNumber()=='29':
        c=p.GetPosition(); cx,cy=T(c.x),T(c.y); n=0
        for dx,dy in ((-0.7,-0.7),(0.7,-0.7),(-0.7,0.7),(0.7,0.7),(0,0)):
            if n<4 and free(cx+dx,cy+dy,0.225,ALL,0.14): addvia(cx+dx,cy+dy); n+=1; nv+=1
        print('EP vias',n)
build_pending=True
STEP=1.2
y=T(bb.GetTop())+1.2
vs=[]
while y<T(bb.GetBottom())-1.0:
    x=T(bb.GetLeft())+1.2
    while x<T(bb.GetRight())-1.0:
        if inside(pcbnew.F_Cu,x,y) and inside(pcbnew.B_Cu,x,y) and free(x,y,0.225,ALL,0.17) and all(math.hypot(x-a,y-c)>0.9 for a,c in vs):
            addvia(x,y); vs.append((x,y)); nv+=1
        x+=STEP
    y+=STEP
print('grid vias',nv,flush=True)
pcbnew.ZONE_FILLER(b).Fill(allz)
allv=[(T(t.GetPosition().x),T(t.GetPosition().y)) for t in b.GetTracks() if t.GetClass()=='PCB_VIA' and t.GetNetname()=='GND']
nf=0
for layer in (pcbnew.F_Cu,pcbnew.B_Cu):
    poly=zones[layer].GetFilledPolysList(layer)
    for i in range(poly.OutlineCount()):
        if any(poly.Contains(V(mm(x),mm(y)),i,0) for x,y in allv): continue
        bx=poly.Outline(i).BBox(); x0,x1,y0,y1=[T(v) for v in (bx.GetLeft(),bx.GetRight(),bx.GetTop(),bx.GetBottom())]
        done=False; yy=y0
        while yy<=y1 and not done:
            xx=x0
            while xx<=x1 and not done:
                if poly.Contains(V(mm(xx),mm(yy)),i,0) and free(xx,yy,0.225,ALL,0.17): addvia(xx,yy); allv.append((xx,yy)); nf+=1; done=True
                xx+=0.15
            yy+=0.15
print('fragment vias',nf)
added=0
if drc:
    for u in drc['unconnected_items']:
        for it in u['items']:
            mt=re.match(r'Pad (\S+) \[GND\] of (\S+) on (\S+)',it['description'])
            if not mt: continue
            f=b.FindFootprintByReference(mt.group(2)); pad=[p for p in f.Pads() if p.GetNumber()==mt.group(1)][0]
            c=pad.GetPosition(); cx,cy=T(c.x),T(c.y); layer=pcbnew.F_Cu if mt.group(3)=='F.Cu' else pcbnew.B_Cu; LS={layer}
            best=None
            for r in (0.8,1.0,1.2,1.5,1.9,2.4,3.0):
                for a in range(0,360,15):
                    px,py=cx+r*math.cos(math.radians(a)),cy+r*math.sin(math.radians(a))
                    if not free(px,py,0.225,ALL,0.17): continue
                    if all(free(cx+(px-cx)*t,cy+(py-cy)*t,0.075,LS,0.15) for t in [k/10 for k in range(3,10)]): best=(px,py); break
                if best: break
            if best:
                addvia(*best); tr=pcbnew.PCB_TRACK(b); KEEP.append(tr); tr.SetLayer(layer); tr.SetNet(gnd); tr.SetStart(c); tr.SetEnd(V(mm(best[0]),mm(best[1]))); tr.SetWidth(mm(0.15)); b.Add(tr); added+=1
            else: print('no stub for',mt.group(2),mt.group(1))
print('pad stubs',added)
pcbnew.ZONE_FILLER(b).Fill(allz)
b.Save(sys.argv[2]); print('saved')
