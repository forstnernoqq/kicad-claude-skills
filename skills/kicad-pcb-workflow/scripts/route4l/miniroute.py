"""miniroute.py in.kicad_pcb out.kicad_pcb jobs.json
jobs: [{"net": "/CMP_TH", "a": ["U2","4"] | [x,y,"F"], "b": ["R41","2"] | [x,y,"F"], "w": 0.127, "win": [x0,y0,x1,y1]}]
Grid A* (0.05 mm) on F/In2/B with vias; obstacles = other-net pads/tracks/vias (+ zones of other nets), class-aware clearance."""
import pcbnew, sys, json, math, heapq
import numpy as np
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.FromMM; T = pcbnew.ToMM; VEC = pcbnew.VECTOR2I; KEEP = []
jobs = json.load(open(sys.argv[3])); LOCK = len(sys.argv) > 4 and sys.argv[4] == 'lock'

class Path:
    def __init__(self, pts): self.p = np.array(pts, float)
    def contains_points(self, P):
        x = P[:, 0]; y = P[:, 1]; inside = np.zeros(len(P), bool); p = self.p; n = len(p)
        for k in range(n):
            x0, y0 = p[k]; x1, y1 = p[(k + 1) % n]
            cond = ((y0 > y) != (y1 > y))
            with np.errstate(divide='ignore', invalid='ignore'):
                xin = (x1 - x0) * (y - y0) / (y1 - y0 + 1e-30) + x0
            inside ^= cond & (x < xin)
        return inside
LAY = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]; RES = 0.05
ANALOG = 'Analog_sensitive'; NOISY = ('PWM_gate', 'Buck_SW', 'Power_heater')
def ncls(item):
    try: return item.GetEffectiveNetClass().GetName()
    except Exception: return item.GetNetClassName()
def clr(tnet_cls, ocls):
    c = 0.135
    if ocls in ('Power_heater', 'Buck_SW', 'PWM_gate') or tnet_cls in ('Power_heater', 'Buck_SW', 'PWM_gate'): c = 0.165
    if ocls == ANALOG or tnet_cls == ANALOG: c = max(c, 0.155)
    if (tnet_cls == ANALOG and ocls in NOISY) or (ocls == ANALOG and tnet_cls in NOISY): c = 0.51
    return c
def run(job):
    net = job['net']; ni = b.FindNet(net); tcls = None
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() == net: tcls = ncls(p); break
        if tcls: break
    w = job.get('w', 0.127); vd = 0.45; vdr = 0.2
    X0, Y0, X1, Y1 = job['win']; nx = int((X1 - X0) / RES) + 1; ny = int((Y1 - Y0) / RES) + 1
    gx = X0 + np.arange(nx) * RES; gy = Y0 + np.arange(ny) * RES; GX, GY = np.meshgrid(gx, gy)
    blockT = {L: np.zeros((ny, nx), bool) for L in LAY}     # track centre forbidden
    blockV = np.zeros((ny, nx), bool)                        # via centre forbidden
    def mark_dist(L, dist, lim_t, lim_v):
        if L in blockT: blockT[L] |= dist < lim_t
        blockV[:] |= dist < lim_v
    def seg_dist(ax, ay, bx_, by_, sl):
        px, py = GX[sl], GY[sl]; dx, dy = bx_ - ax, by_ - ay; L2 = dx * dx + dy * dy
        t = np.clip(((px - ax) * dx + (py - ay) * dy) / L2, 0, 1) if L2 > 0 else 0
        return np.hypot(px - (ax + t * dx), py - (ay + t * dy))
    def sl_for(bx0, by0, bx1, by1, m):
        i0 = max(0, int((bx0 - m - X0) / RES)); i1 = min(nx, int((bx1 + m - X0) / RES) + 2)
        j0 = max(0, int((by0 - m - Y0) / RES)); j1 = min(ny, int((by1 + m - Y0) / RES) + 2)
        if i0 >= i1 or j0 >= j1: return None
        return (slice(j0, j1), slice(i0, i1))
    def apply_shape(layers, poly_pts, ocls, is_round=None, hole=False):
        c = clr(tcls, ocls)
        if hole: c = max(c, 0.22)
        lt = c + w / 2; lv = c + vd / 2
        if is_round:
            cx, cy, r = is_round; sl = sl_for(cx - r, cy - r, cx + r, cy + r, lv)
            if sl is None: return
            d = np.hypot(GX[sl] - cx, GY[sl] - cy) - r
        else:
            xs = [p[0] for p in poly_pts]; ys = [p[1] for p in poly_pts]
            sl = sl_for(min(xs), min(ys), max(xs), max(ys), lv)
            if sl is None: return
            inside = Path(poly_pts).contains_points(np.c_[GX[sl].ravel(), GY[sl].ravel()]).reshape(GX[sl].shape)
            d = np.full(GX[sl].shape, 1e9)
            for (ax, ay), (bx_, by_) in zip(poly_pts, poly_pts[1:] + poly_pts[:1]): d = np.minimum(d, seg_dist(ax, ay, bx_, by_, sl))
            d[inside] = -1
        for L in layers:
            if L in blockT: blockT[L][sl] |= d < lt
        blockV[sl] |= d < lv
    for t in b.GetTracks():
        if t.GetNetCode() == ni.GetNetCode(): continue
        oc = ncls(t)
        if t.GetClass() == 'PCB_VIA':
            p = t.GetPosition(); apply_shape(LAY, None, oc, (T(p.x), T(p.y), T(t.GetWidth(pcbnew.F_Cu)) / 2))
        else:
            s, e = t.GetStart(), t.GetEnd(); hw = T(t.GetWidth()) / 2; L = t.GetLayer()
            if L not in LAY: continue
            c = clr(tcls, oc); sl = sl_for(min(T(s.x), T(e.x)), min(T(s.y), T(e.y)), max(T(s.x), T(e.x)), max(T(s.y), T(e.y)), hw + c + vd)
            if sl is None: continue
            d = seg_dist(T(s.x), T(s.y), T(e.x), T(e.y), sl) - hw
            blockT[L][sl] |= d < c + w / 2; blockV[sl] |= d < c + vd / 2
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetCode() == ni.GetNetCode() and p.GetNetCode() != 0:
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:   # no via inside own SMD pads
                    L0 = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu; o = p.GetEffectivePolygon(L0).Outline(0)
                    pts = [(T(o.CPoint(k).x), T(o.CPoint(k).y)) for k in range(o.PointCount())]
                    xs = [q[0] for q in pts]; ys = [q[1] for q in pts]; sl = sl_for(min(xs), min(ys), max(xs), max(ys), 0.3)
                    if sl is not None:
                        d = np.full(GX[sl].shape, 1e9)
                        for (ax, ay), (bx_, by_) in zip(pts, pts[1:] + pts[:1]): d = np.minimum(d, seg_dist(ax, ay, bx_, by_, sl))
                        inside = Path(pts).contains_points(np.c_[GX[sl].ravel(), GY[sl].ravel()]).reshape(GX[sl].shape)
                        blockV[sl] |= inside | (d < vd / 2)
                continue
            oc = ncls(p) if p.GetNetCode() else 'Default'
            ls = [L for L in LAY if p.IsOnLayer(L)]
            npth = p.GetAttribute() in (pcbnew.PAD_ATTRIB_NPTH, pcbnew.PAD_ATTRIB_PTH)
            if npth: ls = LAY
            if not ls: continue
            ps = p.GetEffectivePolygon(ls[0] if ls[0] != pcbnew.In2_Cu else pcbnew.F_Cu) if not npth else p.GetEffectivePolygon(pcbnew.F_Cu)
            o = ps.Outline(0); pts = [(T(o.CPoint(k).x), T(o.CPoint(k).y)) for k in range(o.PointCount())]
            if npth:
                hs = T(p.GetDrillSize().x) / 2; q = p.GetPosition()
                apply_shape(LAY, None, oc, (T(q.x), T(q.y), max(hs, max(T(p.GetSize().x), T(p.GetSize().y)) / 2)), hole=True)
            else: apply_shape(ls, pts, oc)
        for g in f.GraphicalItems():
            if g.GetLayer() == pcbnew.Edge_Cuts and g.GetShapeStr() == 'Circle':
                c_ = g.GetCenter(); apply_shape(LAY, None, 'Default', (T(c_.x), T(c_.y), T(g.GetRadius()) + 0.17))
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetCode() == ni.GetNetCode() or z.GetNetname() == 'GND': continue
        for L in LAY:
            if not z.IsOnLayer(L): continue
            fp = z.GetFilledPolysList(L)
            for i in range(fp.OutlineCount()):
                o = fp.Outline(i); pts = [(T(o.CPoint(k).x), T(o.CPoint(k).y)) for k in range(o.PointCount())]
                c = clr(tcls, ncls(z)); lt = c + w / 2
                xs = [p_[0] for p_ in pts]; ys = [p_[1] for p_ in pts]; sl = sl_for(min(xs), min(ys), max(xs), max(ys), c + vd)
                if sl is None: continue
                inside = Path(pts).contains_points(np.c_[GX[sl].ravel(), GY[sl].ravel()]).reshape(GX[sl].shape)
                blockT[L][sl] |= inside; blockV[sl] |= inside
    # edge keep
    bb = b.GetBoardEdgesBoundingBox(); EX0, EY0, EX1, EY1 = T(bb.GetLeft()), T(bb.GetTop()), T(bb.GetRight()), T(bb.GetBottom())
    edge = (GX < EX0 + 0.4) | (GX > EX1 - 0.4) | (GY < EY0 + 0.4) | (GY > EY1 - 0.4)
    for L in LAY: blockT[L] |= edge
    blockV |= (GX < EX0 + 0.6) | (GX > EX1 - 0.6) | (GY < EY0 + 0.6) | (GY > EY1 - 0.6)
    def endpoint(spec):
        if isinstance(spec[0], str):
            p = [q for q in b.FindFootprintByReference(spec[0]).Pads() if q.GetNumber() == spec[1] and q.GetNetname() == net][0]
            ps = p.GetEffectivePolygon(pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu); o = ps.Outline(0)
            pts = [(T(o.CPoint(k).x), T(o.CPoint(k).y)) for k in range(o.PointCount())]
            inside = Path(pts).contains_points(np.c_[GX.ravel(), GY.ravel()]).reshape(GX.shape)
            L = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
            q = p.GetPosition(); return [(L, j, i) for j, i in zip(*np.nonzero(inside))], (T(q.x), T(q.y), L)
        x, y, ln = spec; L = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu, 'In2': pcbnew.In2_Cu}[ln]
        i = int(round((x - X0) / RES)); j = int(round((y - Y0) / RES))
        return [(L, jj, ii) for jj in range(j - 1, j + 2) for ii in range(i - 1, i + 2)], (x, y, L)
    allowed = [{'F': pcbnew.F_Cu, 'In2': pcbnew.In2_Cu, 'B': pcbnew.B_Cu}[x] for x in job.get('layers', ['F', 'In2', 'B'])]
    A, pa = endpoint(job['a'])
    if job['b'] == 'net':
        aset = set(A); B = []
        b.BuildConnectivity(); conn = b.GetConnectivity(); apad = None
        for f in b.GetFootprints():
            for p in f.Pads():
                if p.GetNetCode() != ni.GetNetCode(): continue
                if isinstance(job['a'][0], str):
                    if f.GetReference() == job['a'][0] and p.GetNumber() == job['a'][1]: apad = p
                else:
                    q = p.GetPosition()
                    if abs(T(q.x) - job['a'][0]) < 0.05 and abs(T(q.y) - job['a'][1]) < 0.05: apad = p
        ex = set()
        if apad is None and not isinstance(job['a'][0], str):
            P0 = VEC(mm(job['a'][0]), mm(job['a'][1])); best = None
            for t in b.GetTracks():
                if t.GetNetCode() != ni.GetNetCode(): continue
                dd = t.GetEffectiveShape().SquaredDistance(P0)
                if best is None or dd < best[0]: best = (dd, t)
            if best is not None and best[0] < mm(0.15) ** 2: apad = best[1]
        if apad is not None:
            ex = {x.m_Uuid.AsString() for x in conn.GetConnectedItems(apad)} | {apad.m_Uuid.AsString()}
        for t in b.GetTracks():
            if t.GetNetCode() != ni.GetNetCode() or t.m_Uuid.AsString() in ex: continue
            if t.GetClass() == 'PCB_VIA':
                p = t.GetPosition(); i = int(round((T(p.x) - X0) / RES)); j = int(round((T(p.y) - Y0) / RES))
                if 0 <= i < nx and 0 <= j < ny: B += [(L, j, i) for L in LAY]
            elif t.GetLayer() in LAY:
                s_, e_ = t.GetStart(), t.GetEnd(); n_ = int(T(t.GetLength()) / RES) + 2
                for k in range(n_ + 1):
                    x = T(s_.x) + (T(e_.x) - T(s_.x)) * k / n_; y = T(s_.y) + (T(e_.y) - T(s_.y)) * k / n_
                    i = int(round((x - X0) / RES)); j = int(round((y - Y0) / RES))
                    if 0 <= i < nx and 0 <= j < ny: B.append((t.GetLayer(), j, i))
        for f in b.GetFootprints():
            for p in f.Pads():
                if p.GetNetCode() != ni.GetNetCode(): continue
                if p.m_Uuid.AsString() in ex: continue
                for L in LAY:
                    if not p.IsOnLayer(L): continue
                    o = p.GetEffectivePolygon(L).Outline(0); pts = [(T(o.CPoint(k).x), T(o.CPoint(k).y)) for k in range(o.PointCount())]
                    inside = Path(pts).contains_points(np.c_[GX.ravel(), GY.ravel()]).reshape(GX.shape)
                    B += [(L, j, i) for j, i in zip(*np.nonzero(inside))]
        B = [c for c in B if c not in aset]
        if not B: print('no goal copper in window', net); return False
    else: B, pb = endpoint(job['b'])
    for L, j, i in A + B: blockT[L][j, i] = False
    for L in LAY:
        if L not in allowed:
            keep = np.zeros_like(blockT[L])
            for L2, j, i in A + B:
                if L2 == L: keep[j, i] = True
            blockT[L] = ~keep
    inpref = job.get('in2_bonus', 0.0)
    goal = set(B); gi = np.mean([c[2] for c in B]); gj = np.mean([c[1] for c in B])
    def h(j, i): return math.hypot(i - gi, j - gj) * 0.9
    LI = {L: k for k, L in enumerate(LAY)}
    dist = {}; prev = {}; pq = []
    for s in A: dist[s] = 0; heapq.heappush(pq, (h(s[1], s[2]), 0, s))
    VIA_COST = 25; found = None
    moves = [(0, 1, 1), (1, 0, 1), (0, -1, 1), (-1, 0, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    while pq:
        _, d, u = heapq.heappop(pq)
        if d > dist.get(u, 1e18): continue
        if u in goal: found = u; break
        L, j, i = u
        for dj, di, c in moves:
            jj, ii = j + dj, i + di
            if 0 <= jj < ny and 0 <= ii < nx and not blockT[L][jj, ii]:
                v = (L, jj, ii); nd = d + c * (1.0 - inpref if L == pcbnew.In2_Cu else 1.0) + (0.3 if L == pcbnew.In2_Cu and not inpref else 0)
                if nd < dist.get(v, 1e18): dist[v] = nd; prev[v] = u; heapq.heappush(pq, (nd + h(jj, ii), nd, v))
        if not blockV[j, i]:
            for L2 in LAY:
                if L2 == L or blockT[L2][j, i]: continue
                v = (L2, j, i); nd = d + VIA_COST
                if nd < dist.get(v, 1e18): dist[v] = nd; prev[v] = u; heapq.heappush(pq, (nd + h(j, i), nd, v))
    if not found:
        reach = set(k for k in dist)
        print('NO PATH', net, 'reached', len(reach), 'freeT', {b.GetLayerName(L): int((~blockT[L]).sum()) for L in LAY}, 'freeV', int((~blockV).sum()), 'cells', nx*ny)
        import collections; print('   reached per layer', collections.Counter(b.GetLayerName(k[0]) for k in reach))
        return False
    path = [found]
    while path[-1] in prev: path.append(prev[path[-1]])
    path.reverse()
    # emit: split into same-layer runs, simplify collinear points
    pts = [(L, float(X0 + i * RES), float(Y0 + j * RES)) for L, j, i in path]
    runs = []; cur = [pts[0]]
    for p in pts[1:]:
        if p[0] != cur[-1][0]: runs.append(cur); cur = [p]
        else: cur.append(p)
    runs.append(cur)
    def clear_line(L, xa, ya, xb, yb):
        n = int(max(abs(xb - xa), abs(yb - ya)) / (RES * 0.5)) + 1
        for k in range(n + 1):
            x = xa + (xb - xa) * k / n; y = ya + (yb - ya) * k / n
            i = int(round((x - X0) / RES)); j = int(round((y - Y0) / RES))
            if blockT[L][j, i] and (L, j, i) not in endset: return False
        return True
    endset = set(A) | set(B)
    def simplify(r):
        out = [r[0]]; k = 0
        while k < len(r) - 1:
            best = k + 1
            for m in range(len(r) - 1, k + 1, -1):
                if clear_line(r[k][0], r[k][1], r[k][2], r[m][1], r[m][2]): best = m; break
            out.append(r[best]); k = best
        return out
    added = []
    for r in runs:
        r = simplify(r)
        for (L, x0, y0), (_, x1, y1) in zip(r, r[1:]):
            s = pcbnew.PCB_TRACK(b); KEEP.append(s); s.SetLayer(L); s.SetNet(ni); s.SetWidth(mm(w)); s.SetStart(VEC(mm(x0), mm(y0))); s.SetEnd(VEC(mm(x1), mm(y1))); s.SetLocked(LOCK); b.Add(s); added.append(('t', b.GetLayerName(L), round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)))
    for r0, r1 in zip(runs, runs[1:]):
        x, y = r0[-1][1], r0[-1][2]
        vi = pcbnew.PCB_VIA(b); KEEP.append(vi); vi.SetPosition(VEC(mm(x), mm(y))); vi.SetWidth(mm(vd)); vi.SetDrill(mm(vdr)); vi.SetNet(ni); vi.SetViaType(pcbnew.VIATYPE_THROUGH); vi.SetLocked(LOCK); b.Add(vi); added.append(('v', round(x, 2), round(y, 2)))
    # stubs from grid start/end to pad centres if endpoints are pads/points
    print('routed', net, len(added), added[:12]); return True
ok = [run(j) for j in jobs]
b.Save(sys.argv[2]); print('done', ok)
