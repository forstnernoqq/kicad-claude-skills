"""import_ses_finish.py in.kicad_pcb routes.ses out.kicad_pcb [min_width_mm=0.15] [hide_refs=1]
Imports the Freerouting SES, adds GND pours on F.Cu and B.Cu (inset 0.3 mm from the outline),
widens tracks thinner than min_width, refills zones, optionally hides reference designators."""
import pcbnew, sys
src, ses, dst = sys.argv[1:4]
minw = float(sys.argv[4]) if len(sys.argv) > 4 else 0.15
hide = (sys.argv[5] != '0') if len(sys.argv) > 5 else True
b = pcbnew.LoadBoard(src)
print('import ses', pcbnew.ImportSpecctraSES(b, ses))
net = b.FindNet('GND')
bb = b.GetBoardEdgesBoundingBox(); m = pcbnew.FromMM(0.3)
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer); z.SetNet(net)
    z.SetLocalClearance(pcbnew.FromMM(0.2)); z.SetMinThickness(pcbnew.FromMM(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(pcbnew.FromMM(0.25)); z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.3))
    o = z.Outline(); o.NewOutline()
    for x, y in ((bb.GetLeft()+m, bb.GetTop()+m), (bb.GetRight()-m, bb.GetTop()+m),
                 (bb.GetRight()-m, bb.GetBottom()-m), (bb.GetLeft()+m, bb.GetBottom()-m)):
        o.Append(x, y)
    b.Add(z)
for t in b.GetTracks():
    if t.GetClass() == 'PCB_TRACK' and t.GetWidth() < pcbnew.FromMM(minw):
        t.SetWidth(pcbnew.FromMM(minw))
if hide:
    for fp in b.GetFootprints(): fp.Reference().SetVisible(False)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(dst)
print('tracks', len([t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']),
      'vias', len([t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']))
