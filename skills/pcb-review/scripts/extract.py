"""extract.py board.kicad_pcb outdir  -- run with KiCad's python (scripts/run.sh).
Writes outdir/report.txt (footprints, pad nets, per-net track length by layer/width, vias per net,
zones, copper stackup) and outdir/geom.json (geometry for plot_netmap.py).
Board must sit next to its .kicad_pro, otherwise net classes and rules are defaults."""
import pcbnew, sys, os, json, collections
b = pcbnew.LoadBoard(sys.argv[1]); out = sys.argv[2]; mm = pcbnew.ToMM
cu = [l for l in b.GetEnabledLayers().CuStack()]
LN = {l: b.GetLayerName(l) for l in cu}
R = open(os.path.join(out, "report.txt"), "w")
def p(*a): print(*a, file=R)
bb = b.GetBoardEdgesBoundingBox()
p(f"copper layers {b.GetCopperLayerCount()}  outline {mm(bb.GetWidth()):.2f} x {mm(bb.GetHeight()):.2f} mm at ({mm(bb.GetX()):.2f},{mm(bb.GetY()):.2f})")
# stackup copper thickness: parse file text (python stackup API is not exposed in KiCad 10)
txt = open(sys.argv[1]).read()
import re
for m in re.finditer(r'\(layer "([^"]+\.Cu)"\s*\(type "copper"\)\s*\(thickness ([0-9.]+)\)', txt):
    p(f"  stackup {m.group(1)} copper {float(m.group(2))*1000:.1f} um")
def ncls(n):
    try: return n.GetNetClassName()
    except Exception: return "?"
nets = b.GetNetInfo().NetsByName()
NC = {str(k): ncls(v) for k, v in nets.items()}
p("\n== footprints: ref value fpid x y rot side dnp in_pos in_bom")
for f in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
    q = f.GetPosition()
    p(f"{f.GetReference():6} {f.GetValue()[:24]:24} {f.GetFPIDAsString()[:55]:55} {mm(q.x):7.2f} {mm(q.y):7.2f} r{f.GetOrientationDegrees():4.0f} "
      f"{'B' if f.IsFlipped() else 'F'} dnp={int(f.IsDNP())} pos={int(not f.IsExcludedFromPosFiles())} bom={int(not f.IsExcludedFromBOM())}")
p("\n== pads: ref | num:net@(x,y)  (paste-only pads skipped)")
for f in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
    ps = [x for x in f.Pads() if x.GetNumber() != "" or x.IsOnCopperLayer()]
    p(f.GetReference(), " | ".join(f"{x.GetNumber()}:{x.GetNetname()}@({mm(x.GetPosition().x):.2f},{mm(x.GetPosition().y):.2f})" for x in ps if x.IsOnCopperLayer()))
p("\n== tracks per net: total length, then layer/width:length (mm)")
d = collections.defaultdict(lambda: collections.defaultdict(float)); vias = collections.Counter()
G = {"tracks": [], "vias": [], "pads": [], "zones": [], "fps": [], "netclass": NC, "layers": [LN[l] for l in cu]}
for t in b.GetTracks():
    n = t.GetNetname()
    if t.GetClass() == "PCB_VIA":
        vias[(n, round(mm(t.GetWidth(pcbnew.F_Cu)), 2), round(mm(t.GetDrillValue()), 2))] += 1
        G["vias"].append([mm(t.GetPosition().x), mm(t.GetPosition().y), mm(t.GetWidth(pcbnew.F_Cu)), n])
    else:
        ln = LN.get(t.GetLayer(), "?")
        d[n][(ln, round(mm(t.GetWidth()), 3))] += mm(t.GetLength())
        G["tracks"].append([mm(t.GetStart().x), mm(t.GetStart().y), mm(t.GetEnd().x), mm(t.GetEnd().y), mm(t.GetWidth()), ln, n])
for n in sorted(d, key=lambda n: -sum(d[n].values())):
    p(f"{n:24} [{NC.get(n,'?')[:14]:14}] {sum(d[n].values()):6.1f}  " + "  ".join(f"{l}/{w}:{v:.1f}" for (l, w), v in sorted(d[n].items())))
p("\n== vias: (net, pad, drill) count")
for k, v in sorted(vias.items()): p(k, v)
p("\n== zones: net layers priority rule_area filled_mm2")
for z in b.Zones():
    lay = ",".join(b.GetLayerName(l) for l in z.GetLayerSet().Seq())
    p(f"{z.GetNetname() or '-':16} {lay:28} prio{z.GetAssignedPriority()} rule={int(z.GetIsRuleArea())} filled={z.GetFilledArea()/1e12 if z.IsFilled() else 0:.1f}")
    if z.GetIsRuleArea(): continue
    for l in cu:
        if z.IsOnLayer(l):
            fp = z.GetFilledPolysList(l)
            for i in range(fp.OutlineCount()):
                o = fp.Outline(i); G["zones"].append([LN[l], z.GetNetname(), [[mm(o.CPoint(k).x), mm(o.CPoint(k).y)] for k in range(o.PointCount())]])
for f in b.GetFootprints():
    G["fps"].append([f.GetReference(), mm(f.GetPosition().x), mm(f.GetPosition().y), "B" if f.IsFlipped() else "F"])
    for x in f.Pads():
        for l in cu:
            if x.IsOnLayer(l):
                poly = x.GetEffectivePolygon(l)
                for i in range(poly.OutlineCount()):
                    o = poly.Outline(i); G["pads"].append([LN[l], x.GetNetname(), [[mm(o.CPoint(k).x), mm(o.CPoint(k).y)] for k in range(o.PointCount())]])
G["bbox"] = [mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetWidth()), mm(bb.GetHeight())]
json.dump(G, open(os.path.join(out, "geom.json"), "w"))
R.close(); print("wrote report.txt, geom.json")
