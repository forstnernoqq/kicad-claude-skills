import pcbnew, math, sys
b = pcbnew.LoadBoard(sys.argv[1])
n = odd = 0; oddlen = 0.0; tot = 0.0
for t in b.GetTracks():
    if t.GetClass() != "PCB_TRACK": continue
    s, e = t.GetStart(), t.GetEnd()
    dx, dy = (e.x - s.x)/1e6, (e.y - s.y)/1e6
    L = math.hypot(dx, dy)
    if L < 0.05: continue
    n += 1; tot += L
    a = math.degrees(math.atan2(dy, dx)) % 45
    if min(a, 45 - a) > 1.0:
        odd += 1; oddlen += L
print(f"segments {n}, non-45deg {odd} ({100*odd/n:.0f}%), length {oddlen:.0f} of {tot:.0f} mm")
