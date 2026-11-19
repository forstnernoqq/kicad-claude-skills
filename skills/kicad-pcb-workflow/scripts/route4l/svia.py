"""svia.py in out x0 y0 x1 y1 maxn cx cy [exclx0 excly0 exclx1 excly1] : GND vias in a region, nearest to (cx,cy) first; drops In2 OUT_CH1 links."""
import pcbnew, sys, math
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.FromMM; T = pcbnew.ToMM; V = pcbnew.VECTOR2I; KEEP = []
for t in list(b.GetTracks()):
    if t.GetNetname() == '/OUT_CH1' and t.GetClass() == 'PCB_TRACK' and t.GetLayer() == pcbnew.In2_Cu: b.RemoveNative(t)
x0, y0, x1, y1, maxn, cx, cy = [float(v) for v in sys.argv[3:10]]; ex = [float(v) for v in sys.argv[10:14]] if len(sys.argv) > 13 else None
COPPER = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
obs = []
for t in b.GetTracks():
    if t.GetNetname() == 'GND': continue
    obs.append((t.GetEffectiveShape(), None if t.GetClass() == 'PCB_VIA' else t.GetLayer(), t.GetNetClassName()))
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetNetname() == 'GND': continue
        for L in COPPER:
            if p.IsOnLayer(L) or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                ps = p.GetEffectivePolygon(L if p.IsOnLayer(L) else pcbnew.F_Cu); KEEP.append(ps)
                obs.append((ps, None, 'padpoly' if p.GetNetClassName() not in ('Analog_sensitive', 'Power_heater') else p.GetNetClassName())); break
for z in b.Zones():
    if z.GetIsRuleArea() or z.GetNetname() == 'GND': continue
    for L in COPPER:
        if z.IsOnLayer(L): obs.append((z.GetFilledPolysList(L), L, 'zone'))
holes = [(T(g.GetCenter().x), T(g.GetCenter().y), T(g.GetRadius())) for f in b.GetFootprints() for g in f.GraphicalItems() if g.GetLayer() == pcbnew.Edge_Cuts and g.GetShapeStr() == 'Circle']
placed = [(T(t.GetPosition().x), T(t.GetPosition().y)) for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
def ok(x, y):
    if any(math.hypot(x - a, y - c) < 0.75 for a, c in placed): return False
    if any(math.hypot(x - a, y - c) < r + 0.5 for a, c, r in holes): return False
    if ex and ex[0] - 0.25 <= x <= ex[2] + 0.25 and ex[1] - 0.25 <= y <= ex[3] + 0.25: return False
    P = V(mm(x), mm(y))
    for sh, L, cls in obs:
        lim = 0.225 + (0.2 if cls in ('Analog_sensitive', 'Power_heater', 'zone') else 0.17)
        if cls in ('zone', 'padpoly') or isinstance(sh, pcbnew.SHAPE_POLY_SET):
            if math.sqrt(sh.SquaredDistance(P)) / 1e6 < lim or sh.Contains(P): return False
            continue
        if math.sqrt(sh.SquaredDistance(P)) / 1e6 < lim: return False
    return True
cands = sorted(((math.hypot(x - cx, y - cy), x, y) for x in [x0 + 0.05 * i for i in range(int((x1 - x0) / 0.05) + 1)] for y in [y0 + 0.05 * j for j in range(int((y1 - y0) / 0.05) + 1)]))
n = 0
for d, x, y in cands:
    if n >= maxn: break
    if ok(x, y):
        v = pcbnew.PCB_VIA(b); KEEP.append(v); v.SetPosition(V(mm(x), mm(y))); v.SetWidth(mm(0.45)); v.SetDrill(mm(0.2)); v.SetNet(b.FindNet('GND')); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLocked(True); b.Add(v)
        placed.append((x, y)); n += 1; print('via', round(x, 2), round(y, 2))
pcbnew.ZONE_FILLER(b).Fill([z for z in b.Zones() if not z.GetIsRuleArea()]); b.Save(sys.argv[2]); print('added', n)
