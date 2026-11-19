"""checks.py board.kicad_pcb [--power NET,NET] [--sensitive REGEX] [--decap MM] [--far MM]
Run with KiCad's python (scripts/run.sh). Placement/routing heuristics that found real problems before:
  1 supply pins without a nearby decoupling cap      2 passives far from the IC they serve
  3 long sensitive nets, length on inner layers      4 power nets: widths, inner-layer use, vias
  5 vias inside SMD pads                             6 traces that only lead to DNP parts (antennas)
  7 assembly flags (B-side / DNP / pos / BOM)
Distances are pad-centre to pad-centre in mm. Output is a worklist to inspect, not a verdict."""
import pcbnew, sys, re, math, argparse, collections
ap = argparse.ArgumentParser(); ap.add_argument("board")
ap.add_argument("--power", default="", help="comma list of high-current nets (default: netclass/width heuristic)")
ap.add_argument("--sensitive", default=r"FB|SENSE|IREF|VCOM|SS\b|RT\b|-\)|\+\)|IN_|T_CH|NTC|CMP|ADC|SW\)|-G\)|GATE", help="regex for sensitive net names")
ap.add_argument("--decap", type=float, default=3.0); ap.add_argument("--far", type=float, default=5.0)
a = ap.parse_args()
b = pcbnew.LoadBoard(a.board); mm = pcbnew.ToMM
cu = list(b.GetEnabledLayers().CuStack()); inner = {l for l in cu if l not in (pcbnew.F_Cu, pcbnew.B_Cu)}
fps = list(b.GetFootprints())
is_gnd = lambda n: bool(re.search(r"GND|VSS", n, re.I))
is_passive = lambda f: re.match(r"^(R|C|L|FB|D|TP|JP)\d", f.GetReference()) is not None
pos = lambda x: (mm(x.GetPosition().x), mm(x.GetPosition().y))
dist = lambda p, q: math.hypot(p[0]-q[0], p[1]-q[1])
padsby = collections.defaultdict(list)
for f in fps:
    for p in f.Pads():
        if p.GetNetname() and p.IsOnCopperLayer(): padsby[p.GetNetname()].append((f, p))
def ncls(n):
    try: return b.FindNet(n).GetNetClassName()
    except Exception: return ""
tracks = collections.defaultdict(lambda: [0.0, 0.0, 9e9, 0])  # total, inner, minw, vias
for t in b.GetTracks():
    s = tracks[t.GetNetname()]
    if t.GetClass() == "PCB_VIA": s[3] += 1; continue
    L = mm(t.GetLength()); s[0] += L; s[2] = min(s[2], mm(t.GetWidth()))
    if t.GetLayer() in inner: s[1] += L
rails = {n for n, v in padsby.items() if len(v) > 8 or is_gnd(n)}

print(f"== 1 supply pins: nearest decoupling cap (flag > {a.decap} mm)")
for f in fps:
    if is_passive(f) or f.GetReference().startswith(("J", "SW", "Q")): continue
    for p in f.Pads():
        n = p.GetNetname()
        try: pt = p.GetPinType()
        except Exception: pt = ""
        if not n or is_gnd(n) or not (pt.startswith("power_in") or re.search(r"^\+|VCC|VDD|VIN|3V3|5V|VBUS", n, re.I)): continue
        best = (9e9, "-")
        for g, q in padsby[n]:
            if g.GetReference().startswith("C") and any(is_gnd(r.GetNetname()) for r in g.Pads()):
                best = min(best, (dist(pos(p), pos(q)), g.GetReference() + (" DNP" if g.IsDNP() else "")))
        flag = "  <-- FAR" if best[0] > a.decap else ""
        print(f"  {f.GetReference()}.{p.GetNumber()} {n:14} {pt:10} nearest cap {best[1]:8} {best[0]:6.1f}{flag}")

print(f"\n== 2 passives far from the active part on their net (flag > {a.far} mm; rails/GND skipped)")
rows = []
for f in fps:
    if not re.match(r"^(R|C|L)\d", f.GetReference()): continue
    for p in f.Pads():
        n = p.GetNetname()
        if not n or n in rails: continue
        act = [(dist(pos(p), pos(q)), g.GetReference() + "." + q.GetNumber()) for g, q in padsby[n] if not is_passive(g)]
        if act:
            d0, who = min(act)
            if d0 > a.far: rows.append((d0, f.GetReference(), f.GetValue(), n, who, f.IsDNP()))
for d0, r, v, n, who, dnp in sorted(rows, reverse=True):
    print(f"  {r:5} {v[:10]:10} net {n:22} nearest active pad {who:10} {d0:5.1f} mm{'  (DNP)' if dnp else ''}")

print("\n== 3 sensitive / long nets: routed length (inner part)  [sensitive by --sensitive regex or class name]")
sens = re.compile(a.sensitive, re.I)
for n, (tot, inn, mw, nv) in sorted(tracks.items(), key=lambda kv: -kv[1][0]):
    c = ncls(n); s = bool(sens.search(n)) or bool(re.search(r"analog|sw|gate|sens", c, re.I))
    if n in rails and not s: continue
    if tot > 15 or (s and tot > 8):
        print(f"  {'!' if s else ' '} {n:24} [{c[:14]:14}] {tot:6.1f} mm, inner {inn:5.1f}, vias {nv}")

pw = [x for x in a.power.split(",") if x] or [n for n in tracks if re.search(r"power|heater|high", ncls(n), re.I)]
print("\n== 4 power nets:", ", ".join(pw) or "(none found: pass --power)")
for n in pw:
    tot, inn, mw, nv = tracks.get(n, [0, 0, 0, 0])
    vs = collections.Counter(round(mm(t.GetDrillValue()), 2) for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == n)
    print(f"  {n:14} routed {tot:5.1f} mm, min width {mw:.2f}, on inner layers {inn:5.1f} mm, vias {dict(vs)}")
    for f, p in padsby[n]:
        near = sum(1 for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == n and dist(pos(t), pos(p)) < 2.0)
        print(f"     pad {f.GetReference()}.{p.GetNumber():3} {'B' if f.IsFlipped() else 'F'} vias within 2 mm: {near}")

print("\n== 5 vias inside SMD pads")
for t in b.GetTracks():
    if t.GetClass() != "PCB_VIA": continue
    for f in fps:
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and p.IsOnCopperLayer() and p.HitTest(t.GetPosition()):
                print(f"  via {t.GetNetname():12} ({mm(t.GetPosition().x):.2f},{mm(t.GetPosition().y):.2f}) drill {mm(t.GetDrillValue()):.2f} in {f.GetReference()}.{p.GetNumber()}"
                      f"{' (DNP/hand-fit?)' if f.IsDNP() or f.IsExcludedFromPosFiles() else ''}")

print("\n== 6 nets whose only other pads are DNP (trace = antenna)")
for n, lst in padsby.items():
    live = [f for f, p in lst if not f.IsDNP()]
    if n not in rails and len(live) == 1 and len(lst) > 1 and tracks[n][0] > 3:
        print(f"  {n:22} {tracks[n][0]:5.1f} mm to DNP {sorted({f.GetReference() for f, p in lst if f.IsDNP()})} from {live[0].GetReference()}")

print("\n== 7 assembly flags")
bs = [f for f in fps if f.IsFlipped()]
print("  B side:", ", ".join(f"{f.GetReference()}{'' if f.IsExcludedFromPosFiles() else '(in pos!)'}" for f in sorted(bs, key=lambda f: f.GetReference())))
print("  DNP:", ", ".join(sorted(f.GetReference() for f in fps if f.IsDNP())))
print("  excluded from pos:", ", ".join(sorted(f.GetReference() for f in fps if f.IsExcludedFromPosFiles())) or "none")
