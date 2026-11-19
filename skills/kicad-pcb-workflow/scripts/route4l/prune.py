"""prune.py in.kicad_pcb out.kicad_pcb drc.json : delete GND vias that take part in a DRC error/warning, refill zones."""
import pcbnew,sys,json,math
b=pcbnew.LoadBoard(sys.argv[1]); d=json.load(open(sys.argv[3])); T=pcbnew.ToMM; mm=pcbnew.FromMM
bad=[]
for v in d['violations']:
    if v['severity']!='error' and v['type'] not in ('hole_to_hole','holes_co_located'): continue
    if v['type'] in ('npth_inside_courtyard',): continue
    for it in v['items']:
        if it['description'].startswith('Via [GND]'): bad.append((it['pos']['x'],it['pos']['y']))
n=0
for t in list(b.GetTracks()):
    if t.GetClass()=='PCB_VIA' and t.GetNetname()=='GND':
        q=t.GetPosition()
        if any(math.hypot(T(q.x)-x,T(q.y)-y)<0.05 for x,y in bad): b.RemoveNative(t); n+=1
print('removed vias',n,'of',len(bad))
pcbnew.ZONE_FILLER(b).Fill([z for z in b.Zones() if not z.GetIsRuleArea()])
b.Save(sys.argv[2])
