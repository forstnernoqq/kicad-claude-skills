import pcbnew,sys,json,math
b=pcbnew.LoadBoard(sys.argv[1]); mm=pcbnew.FromMM; V=pcbnew.VECTOR2I; KEEP=[]
import os
X0,Y0,X1,Y1,R=65.0,54.0,115.0+float(os.environ.get('DL','5')),69.0+float(os.environ.get('DH','3')),2.0
# GND plane In1 + router keepouts
b.SetLayerType(pcbnew.In1_Cu,pcbnew.LT_POWER)
net=b.FindNet('GND'); m=mm(0.4)
z=pcbnew.ZONE(b); z.SetLayer(pcbnew.In1_Cu); z.SetNet(net); z.SetLocalClearance(mm(0.25)); z.SetMinThickness(mm(0.2)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
o=z.Outline(); o.NewOutline()
for x,y in ((X0+0.4,Y0+0.4),(X1-0.4,Y0+0.4),(X1-0.4,Y1-0.4),(X0+0.4,Y1-0.4)): o.Append(mm(x),mm(y))
b.Add(z); KEEP.append(z)
def keepout(pts):
    k=pcbnew.ZONE(b); k.SetIsRuleArea(True); k.SetDoNotAllowTracks(True); k.SetDoNotAllowVias(True); k.SetDoNotAllowZoneFills(False); k.SetDoNotAllowPads(False); k.SetDoNotAllowFootprints(False)
    ls=pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); ls.AddLayer(pcbnew.In1_Cu); ls.AddLayer(pcbnew.In2_Cu); k.SetLayerSet(ls)
    o=k.Outline(); o.NewOutline(); KEEP.append(o)
    for x,y in pts: o.Append(mm(x),mm(y))
    b.Add(k); KEEP.append(k); KEEP.append(ls)
print('STAGE W=0.35',flush=True)
W=0.35
# straight edge strips
keepout([(X0-1,Y0-1),(X1+1,Y0-1),(X1+1,Y0+W),(X0-1,Y0+W)]); keepout([(X0-1,Y1-W),(X1+1,Y1-W),(X1+1,Y1+1),(X0-1,Y1+1)])
keepout([(X0-1,Y0-1),(X0+W,Y0-1),(X0+W,Y1+1),(X0-1,Y1+1)]); keepout([(X1-W,Y0-1),(X1+1,Y0-1),(X1+1,Y1+1),(X1-W,Y1+1)])
# rounded corners: region outside the inset arc inside each corner square
for cx,cy,sx,sy in ((X0+R,Y0+R,-1,-1),(X1-R,Y0+R,1,-1),(X1-R,Y1-R,1,1),(X0+R,Y1-R,-1,1)):
    pts=[(cx+sx*(R+1),cy+sy*(R+1)),(cx+sx*(R+1),cy)]
    for a in range(0,91,10):
        ang=math.radians(a); pts.append((cx+sx*(R-W)*math.cos(ang) if False else cx+sx*(R-W)*math.cos(ang), cy+sy*(R-W)*math.sin(ang)))
    pts.append((cx,cy+sy*(R+1)))
    keepout(pts)
print('STAGE # J3 milled',flush=True)
# J3 milled holes
for f in b.GetFootprints():
    if f.GetReference()=='J3':
        for g in f.GraphicalItems():
            if g.GetLayer()==pcbnew.Edge_Cuts and g.GetShapeStr()=='Circle':
                c=g.GetCenter(); r=pcbnew.ToMM(g.GetRadius())+0.35
                keepout([(pcbnew.ToMM(c.x)+r*math.cos(math.radians(a)),pcbnew.ToMM(c.y)+r*math.sin(math.radians(a))) for a in range(0,360,30)])
print('STAGE pcbnew.ZONE_FILLER',flush=True)
pcbnew.ZONE_FILLER(b).Fill([x for x in b.Zones() if not x.GetIsRuleArea()])
b.Save(sys.argv[2])
# sanity: pad positions
for ref,pad in (('J1','A4'),('J3','T'),('SW2','1'),('C50','1'),('J5','1'),('U2','1')):
    f=b.FindFootprintByReference(ref)
    for p in f.Pads():
        if p.GetNumber()==pad: print(ref,pad,round(pcbnew.ToMM(p.GetPosition().x),2),round(pcbnew.ToMM(p.GetPosition().y),2),f.GetLayerName()); break
