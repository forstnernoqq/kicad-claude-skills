import pcbnew, sys, math, collections
b = pcbnew.LoadBoard(sys.argv[1]); T = pcbnew.ToMM
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}
L = collections.defaultdict(lambda: collections.defaultdict(float)); NV = collections.Counter(); VD = collections.defaultdict(list)
for t in b.GetTracks():
    n = t.GetNetname()
    if t.GetClass() == 'PCB_VIA': NV[n] += 1; VD[n].append((round(T(t.GetPosition().x), 2), round(T(t.GetPosition().y), 2), T(t.GetDrill())))
    else: L[n][LN.get(t.GetLayer(), '?')] += T(t.GetLength())
key = ['Net-(U3-SW)', 'Net-(U3-FB)', 'Net-(U3-SS)', 'Net-(U3-RT)', 'Net-(U3-BST)', 'Net-(U5--)', 'Net-(U5-+)', '/IN_CH1', '/T_CH1', '/VH_SENSE', '/OUT_SENSE', '/NTC_SENSE',
       '/CMP_TH', 'Net-(Q3-G)', '/Q3_EN', '/OLED_VCOMH', '/OLED_VCC', '/OLED_IREF', '/USB_DP_MCU', '/USB_DP', '/USB_DM', '/FET_PWM', 'Net-(Q1-D)', 'Net-(Q1-G)', 'VBUS', '/VH', '/OUT_CH1', '+3V3']
for k in key:
    d = L[k]; print('%-14s total %5.1f mm  %s  vias %d' % (k.replace('Net-(', '').replace(')', ''), sum(d.values()), {a: round(v, 1) for a, v in d.items()}, NV[k]))
print('GND vias', NV['GND'])
# heater copper area per layer (zones + tracks approx)
for net in ('VBUS', '/VH', '/OUT_CH1'):
    area = collections.defaultdict(float)
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != net: continue
        for Lr in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
            if z.IsOnLayer(Lr):
                ps = z.GetFilledPolysList(Lr); area[LN[Lr]] += ps.Area() / 1e12
    print(net, 'zone fill mm2', {k: round(v, 1) for k, v in area.items()}, 'via drills', collections.Counter(d for _, _, d in VD[net]))
# heater nets on inner layers?
inner = [(t.GetNetname(), LN[t.GetLayer()]) for t in b.GetTracks() if t.GetClass() != 'PCB_VIA' and t.GetLayer() in (pcbnew.In1_Cu, pcbnew.In2_Cu) and t.GetNetname() in ('VBUS', '/VH', '/OUT_CH1', 'Net-(U3-SW)')]
print('heater/SW tracks on inner layers:', inner)
zin = [(z.GetNetname(), LN[z.GetFirstLayer()]) for z in b.Zones() if not z.GetIsRuleArea() and z.GetFirstLayer() in (pcbnew.In1_Cu, pcbnew.In2_Cu)]
print('inner-layer zones:', zin)
# vias near transitions
def count(net, x0, y0, x1, y1): return sum(1 for x, y, d in VD[net] if x0 <= x <= x1 and y0 <= y <= y1)
print('VBUS vias at Q3', count('VBUS', 83.5, 58.8, 87.0, 61.0), '| VH vias at Q3', count('/VH', 84.0, 54.0, 89.0, 57.5), '| VH vias at Q2', count('/VH', 109.0, 54.0, 111.5, 57.8), '| OUT vias', count('/OUT_CH1', 111.5, 54.0, 115.5, 61.0))
print('GND vias around S pads: upper', count('GND', 118.0, 57.4, 121.0, 61.3), 'lower', count('GND', 117.8, 64.8, 121.0, 68.6), '| U2 EP', count('GND', 80.0, 62.4, 82.4, 64.8))
