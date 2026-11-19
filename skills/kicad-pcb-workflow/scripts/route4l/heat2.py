"""heat.py in out [W=3.0] : copper pours that follow the heater-net routes (VBUS, /VH, /OUT_CH1) on F.Cu, In2.Cu and B.Cu."""
import pcbnew,sys,math
b=pcbnew.LoadBoard(sys.argv[1]); W=float(sys.argv[3]) if len(sys.argv)>3 else 3.0
mm=pcbnew.FromMM; T=pcbnew.ToMM; V=pcbnew.VECTOR2I; KEEP=[]
NETS=('VBUS','/VH','/OUT_CH1'); LAYERS=(pcbnew.F_Cu,pcbnew.In2_Cu,pcbnew.B_Cu)
def rect(x0,y0,x1,y1,w):
    dx,dy=x1-x0,y1-y0; L=math.hypot(dx,dy)
    if L<1e-6: nx,ny=0,w/2; ux,uy=1,0
    else: ux,uy=dx/L,dy/L; nx,ny=-uy*w/2,ux*w/2
    e=w/2*0.0
    return [(x0-ux*e+nx,y0-uy*e+ny),(x1+ux*e+nx,y1+uy*e+ny),(x1+ux*e-nx,y1+uy*e-ny),(x0-ux*e-nx,y0-uy*e-ny)]
made=0
for net in NETS:
    ni=b.FindNet(net)
    for layer in LAYERS:
        polys=[]
        for t in b.GetTracks():
            if t.GetNetname()!=net: continue
            if t.GetClass()=='PCB_TRACK' and t.GetLayer()==layer:
                s,e=t.GetStart(),t.GetEnd(); polys.append(rect(T(s.x),T(s.y),T(e.x),T(e.y),W))
            elif t.GetClass()=='PCB_VIA':
                p=t.GetPosition(); c=(T(p.x),T(p.y)); polys.append([(c[0]-W/2,c[1]-W/2),(c[0]+W/2,c[1]-W/2),(c[0]+W/2,c[1]+W/2),(c[0]-W/2,c[1]+W/2)])
        for f in b.GetFootprints():
            for p in f.Pads():
                if p.GetNetname()==net and p.GetLayerSet().Contains(layer):
                    bx=p.GetBoundingBox(); polys.append([(T(bx.GetLeft())-0.6,T(bx.GetTop())-0.6),(T(bx.GetRight())+0.6,T(bx.GetTop())-0.6),(T(bx.GetRight())+0.6,T(bx.GetBottom())+0.6),(T(bx.GetLeft())-0.6,T(bx.GetBottom())+0.6)])
        if net=='/VH' and layer==pcbnew.B_Cu:
            polys.append([(102.0,55.9),(109.9,55.9),(109.9,70.9),(102.0,70.9)])   # bank pocket + bus end
        if not polys: continue
        z=pcbnew.ZONE(b); KEEP.append(z); z.SetLayer(layer); z.SetNet(ni)
        z.SetAssignedPriority(2); z.SetLocalClearance(mm(0.2)); z.SetMinThickness(mm(0.25)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        o=z.Outline(); first=True
        for pl in polys:
            o.NewOutline()
            for x,y in pl: o.Append(mm(x),mm(y))
        b.Add(z); made+=1
print('heater zones',made,flush=True)
pcbnew.ZONE_FILLER(b).Fill([z for z in b.Zones() if not z.GetIsRuleArea()])
b.Save(sys.argv[2]); print('saved')
