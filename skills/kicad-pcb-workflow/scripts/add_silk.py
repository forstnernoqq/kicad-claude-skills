"""add_silk.py in.kicad_pcb labels.json out.kicad_pcb
labels.json: [{"text":"UART","x":129.2,"y":52.3,"h":0.8,"layer":"F","just":"c|l|r","mirror":false}, ...]
Coordinates are absolute board mm. Keep h >= the board's min_text_height (0.8)."""
import pcbnew, sys, json
b = pcbnew.LoadBoard(sys.argv[1])
J = {'c': pcbnew.GR_TEXT_H_ALIGN_CENTER, 'l': pcbnew.GR_TEXT_H_ALIGN_LEFT, 'r': pcbnew.GR_TEXT_H_ALIGN_RIGHT}
for d in json.load(open(sys.argv[2])):
    back = d.get('layer', 'F') == 'B'
    t = pcbnew.PCB_TEXT(b)
    t.SetText(d['text']); t.SetLayer(pcbnew.B_SilkS if back else pcbnew.F_SilkS)
    t.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(d['x']), pcbnew.FromMM(d['y'])))
    h = d.get('h', 0.8)
    t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(h), pcbnew.FromMM(h)))
    t.SetTextThickness(pcbnew.FromMM(0.15))
    t.SetHorizJustify(J[d.get('just', 'c')])
    if back or d.get('mirror'): t.SetMirrored(True)
    b.Add(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[3])
