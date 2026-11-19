"""gndfix2.py in out drc.json : connect still-floating GND pads (and the QFN EP) with vias in the pad (hand-fitted/large pads) or short stubs."""
import pcbnew,sys,math,json,re
b=pcbnew.LoadBoard(sys.argv[1]); d=json.load(open(sys.argv[3])); mm=pcbnew.FromMM; T=pcbnew.ToMM; V=pcbnew.VECTOR2I; KEEP=[]
gnd=b.FindNet('GND'); COPPER=(pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu); ALL=set(COPPER)
hz=[z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() not in ('GND','')]
def hz_hit(x,y,layers,acc=0.3):
    for z in hz:
        L=z.GetFirstLayer()
        if L in layers and z.HitTestFilledArea(L,V(mm(x),mm(y)),mm(acc)): return True
    return False
obs=[]
for t in b.GetTracks():
    if t.GetNetname()=='GND': continue
    obs.append((t.GetEffectiveShape(),set(COPPER) if t.GetClass()=='PCB_VIA' else {t.GetLayer()},T(t.GetBoundingBox().GetLeft()),T(t.GetBoundingBox().GetTop()),T(t.GetBoundingBox().GetRight()),T(t.GetBoundingBox().GetBottom())))
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetNetname()=='GND': continue
        ls=set(l for l in COPPER if p.GetLayerSet().Contains(l)) or {pcbnew.F_Cu}
        if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH: ls=set(COPPER)
        bx=p.GetBoundingBox(); obs.append((p.GetEffectiveShape(sorted(ls)[0]),ls,T(bx.GetLeft()),T(bx.GetTop()),T(bx.GetRight()),T(bx.GetBottom())))
placed=[(T(t.GetPosition().x),T(t.GetPosition().y)) for t in b.GetTracks() if t.GetClass()=='PCB_VIA']
def free(x,y,r,layers,mg):
    P=V(mm(x),mm(y)); lim=r+mg
    for sh,ls,x0,y0,x1,y1 in obs:
        if x<x0-lim-0.3 or x>x1+lim+0.3 or y<y0-lim-0.3 or y>y1+lim+0.3: continue
        if not (ls&layers): continue
        if math.sqrt(sh.SquaredDistance(P))/1e6<lim: return False
    return True
def addvia(x,y):
    v=pcbnew.PCB_VIA(b); KEEP.append(v); v.SetPosition(V(mm(x),mm(y))); v.SetWidth(mm(0.45)); v.SetDrill(mm(0.2)); v.SetNet(gnd); v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v); placed.append((x,y))
targets=set()
for u in d['unconnected_items']:
    for it in u['items']:
        mt=re.match(r'Pad (\S+) \[GND\] of (\S+) on (\S+)',it['description'])
        if mt: targets.add((mt.group(2),mt.group(1),mt.group(3)))
for v in d['violations']:
    if v['type']=='starved_thermal':
        for it in v['items']:
            mt=re.match(r'Pad (\S+) \[GND\] of (\S+) on (\S+)',it['description'])
            if mt:
                f=b.FindFootprintByReference(mt.group(2))
                for p in f.Pads():
                    if p.GetNumber()==mt.group(1) and p.GetNetname()=='GND': p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
done=[];fail=[]
for ref,num,lay in sorted(targets):
    f=b.FindFootprintByReference(ref); pad=[p for p in f.Pads() if p.GetNumber()==num][0]
    c=pad.GetPosition(); cx,cy=T(c.x),T(c.y); sz=(T(pad.GetSize().x),T(pad.GetSize().y)); ang=pad.GetOrientationDegrees()
    # pad extents in board frame
    bx=pad.GetBoundingBox(); w,h=T(bx.GetWidth()),T(bx.GetHeight())
    layer=pcbnew.F_Cu if lay=='F.Cu' else pcbnew.B_Cu; LS={layer}
    ok=False
    if min(w,h)>=0.7 or ref=='U2':
        offs=[(0,0)]
        if ref=='U2': offs=[(-0.7,-0.7),(0.7,-0.7),(-0.7,0.7),(0.7,0.7)]
        else:
            if w>=h:
                for k in (0.3,0.6,0.9,-0.3,-0.6,-0.9):
                    if abs(k)<=w/2-0.3: offs.append((k,0))
            else:
                for k in (0.3,0.6,0.9,-0.3,-0.6,-0.9):
                    if abs(k)<=h/2-0.3: offs.append((0,k))
        n=0
        for dx,dy in offs:
            if any(math.hypot(cx+dx-a,cy+dy-bb)<0.8 for a,bb in placed): continue
            if free(cx+dx,cy+dy,0.225,ALL,0.14): addvia(cx+dx,cy+dy); n+=1; ok=True
            if ref!='U2' and n>=1: break
            if ref=='U2' and n>=4: break
    if not ok:
        best=None
        for r in (0.7,0.9,1.1,1.4,1.8,2.3,3.0):
            for a in range(0,360,12):
                px,py=cx+r*math.cos(math.radians(a)),cy+r*math.sin(math.radians(a))
                if any(math.hypot(px-q,py-s)<0.8 for q,s in placed): continue
                if not free(px,py,0.225,ALL,0.15): continue
                if all(free(cx+(px-cx)*t,cy+(py-cy)*t,0.075,LS,0.14) for t in [k/12 for k in range(2,12)]): best=(px,py); break
            if best: break
        if best:
            addvia(*best); tr=pcbnew.PCB_TRACK(b); KEEP.append(tr); tr.SetLayer(layer); tr.SetNet(gnd); tr.SetStart(c); tr.SetEnd(V(mm(best[0]),mm(best[1]))); tr.SetWidth(mm(0.15)); b.Add(tr); ok=True
    (done if ok else fail).append(ref+'-'+num)
print('fixed',done); print('could not fix',fail)
pcbnew.ZONE_FILLER(b).Fill([z for z in b.Zones() if not z.GetIsRuleArea()])
b.Save(sys.argv[2])
