"""sch_tool.py: read and lint a KiCad 8-10 .kicad_sch, with no KiCad needed (plain python3).

  python3 sch_tool.py pins  FILE [REF ...]      pin tips in schematic coordinates (ref, pin, name, type, x, y)
  python3 sch_tool.py check FILE                geometry (dangling wire ends, floating labels, unconnected pins, off-grid)
  python3 sch_tool.py lint  FILE [--near MM]    readability: label-only nets whose pins sit close together,
                                                power nets drawn as labels, pins wired only by a label stub
  python3 sch_tool.py blocks FILE [--gap MM]    group symbols into spatial clusters (what is drawn where)
  python3 sch_tool.py same A B                  identical connectivity? (nets as sets of ref.pin; exit 1 if not)

As a module (for scripts that edit a schematic as text): parse(), dump(), pin_tips(), and the emit helpers
wire(), junction(), label(), global_label(), no_connect() return S-expression strings with fresh UUIDs.
Coordinates are in mm, with y pointing down. KiCad's connection grid is 1.27 mm (50 mil).
"""
import math, re, sys, uuid, collections

# ---------- S-expression ----------
_tok = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))')

def parse(text):
    """Return the nested list for the first top-level expression. Strings are tagged as ('s', value)."""
    stack, cur, pos = [], [], 0
    while True:
        m = _tok.match(text, pos)
        if not m or m.end() == pos:
            break
        pos = m.end()
        if m.group(1):
            stack.append(cur); cur = []
        elif m.group(2):
            done = cur; cur = stack.pop(); cur.append(done)
        elif m.group(3) is not None:
            cur.append(('s', m.group(3).replace('\\"', '"').replace('\\\\', '\\')))
        else:
            cur.append(m.group(4))
    return cur[0]

def val(x):
    return x[1] if isinstance(x, tuple) else x

def kids(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]

def kid(node, name):
    k = kids(node, name)
    return k[0] if k else None

def prop(node, name):
    for p in kids(node, 'property'):
        if val(p[1]) == name:
            return val(p[2])
    return None

# ---------- geometry ----------
def xform(px, py, ang, mirror):
    """Library pin point (y up) -> offset in the schematic (y down) for a symbol at angle ang with an optional mirror."""
    x, y = px, -py
    a = math.radians(ang)
    c, s = round(math.cos(a)), round(math.sin(a))
    x, y = x * c + y * s, -x * s + y * c
    if mirror == 'x':
        y = -y
    elif mirror == 'y':
        x = -x
    return x, y

def lib_pins(lib, unit, style):
    """Pins of a lib_symbols entry (flattened by KiCad in the schematic) for one unit and body style."""
    out = []
    for sub in kids(lib, 'symbol'):
        m = re.search(r'_(\d+)_(\d+)$', val(sub[1]))
        u, st = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
        if u not in (0, unit) or st not in (0, style):
            continue
        for p in kids(sub, 'pin'):
            at = kid(p, 'at')
            name = kid(p, 'name'); num = kid(p, 'number')
            out.append(dict(type=p[1], x=float(at[1]), y=float(at[2]), ang=float(at[3]) if len(at) > 3 else 0,
                            name=val(name[1]) if name else '', num=val(num[1]) if num else ''))
    return out

def load(path):
    root = parse(open(path, encoding='utf-8').read())
    libs = {val(s[1]): s for s in kids(kid(root, 'lib_symbols') or [], 'symbol')}
    return root, libs

def symbols(root):
    return kids(root, 'symbol')

def pin_tips(root, libs):
    """Yield dicts: ref, lib_id, pin, name, type, x, y, power (True for #PWR/#FLG symbols)."""
    for s in symbols(root):
        lib_id = val(kid(s, 'lib_id')[1])
        at = kid(s, 'at'); sx, sy, ang = float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0
        mir = kid(s, 'mirror'); mir = mir[1] if mir else None
        unit = int(kid(s, 'unit')[1]) if kid(s, 'unit') else 1
        bs = kid(s, 'body_style') or kid(s, 'convert'); style = int(bs[1]) if bs else 1
        ref = prop(s, 'Reference') or '?'
        lib = libs.get(lib_id)
        if lib is None:
            continue
        for p in lib_pins(lib, unit, style):
            dx, dy = xform(p['x'], p['y'], ang, mir)
            yield dict(ref=ref, lib_id=lib_id, pin=p['num'], name=p['name'], type=p['type'],
                       x=round(sx + dx, 3), y=round(sy + dy, 3), power=ref.startswith('#'))

def items(root):
    wires = [((float(kid(w, 'pts')[1][1]), float(kid(w, 'pts')[1][2])),
              (float(kid(w, 'pts')[2][1]), float(kid(w, 'pts')[2][2]))) for w in kids(root, 'wire')]
    labels = []
    for kind in ('label', 'global_label', 'hierarchical_label'):
        for l in kids(root, kind):
            at = kid(l, 'at'); labels.append(dict(kind=kind, name=val(l[1]), x=float(at[1]), y=float(at[2])))
    junctions = [(float(kid(j, 'at')[1]), float(kid(j, 'at')[2])) for j in kids(root, 'junction')]
    ncs = [(float(kid(j, 'at')[1]), float(kid(j, 'at')[2])) for j in kids(root, 'no_connect')]
    return wires, labels, junctions, ncs

def key(x, y):
    return (round(x, 2), round(y, 2))

def on_seg(p, a, b, tol=0.01):
    (x, y), (x1, y1), (x2, y2) = p, a, b
    if abs((x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)) > tol * max(1, math.hypot(x2 - x1, y2 - y1)):
        return False
    return min(x1, x2) - tol <= x <= max(x1, x2) + tol and min(y1, y2) - tol <= y <= max(y1, y2) + tol

# ---------- commands ----------
def cmd_pins(path, refs):
    root, libs = load(path)
    for p in pin_tips(root, libs):
        if not refs or p['ref'] in refs:
            print(f"{p['ref']:8} {p['pin']:>4} {p['name'][:16]:16} {p['type'][:12]:12} {p['x']:9.2f} {p['y']:9.2f}")

def connectivity(root, libs):
    """Union-find over pins, wire ends and labels (same name joins). Returns (pins, net_of_pin, net_label_names)."""
    wires, labels, junctions, _ = items(root)
    pins = list(pin_tips(root, libs))
    parent = {}
    def f(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    def u(a, b):
        parent[f(a)] = f(b)
    pts = set()
    for a, b in wires:
        u(('p',) + key(*a), ('p',) + key(*b)); pts |= {key(*a), key(*b)}
    for p in pins:
        pts.add(key(p['x'], p['y']))
    for l in labels:
        pts.add(key(l['x'], l['y']))
    for pt in pts:                                       # a point on a wire's interior connects to it
        for a, b in wires:
            if on_seg(pt, a, b):
                u(('p',) + pt, ('p',) + key(*a))
    for l in labels:
        u(('p',) + key(l['x'], l['y']), ('n', l['name']))
    for p in pins:
        if p['power']:                                   # power symbols join by their value (net name)
            pass
    for s in symbols(root):
        ref = prop(s, 'Reference') or ''
        if ref.startswith('#PWR'):
            v = prop(s, 'Value')
            for p in pins:
                if p['ref'] == ref:
                    u(('p',) + key(p['x'], p['y']), ('n', v))
    net = {}
    names = collections.defaultdict(set)
    for p in pins:
        r = f(('p',) + key(p['x'], p['y'])); net[(p['ref'], p['pin'])] = r
    for k in list(parent):
        if k[0] == 'n':
            names[f(k)].add(k[1])
    return pins, net, names, wires, labels

def cmd_check(path):
    root, libs = load(path)
    wires, labels, junctions, ncs = items(root)
    pins = list(pin_tips(root, libs))
    pinpts = collections.Counter(key(p['x'], p['y']) for p in pins)
    ends = collections.Counter()
    for a, b in wires:
        ends[key(*a)] += 1; ends[key(*b)] += 1
    lab = {key(l['x'], l['y']) for l in labels}
    nc = {key(*n) for n in ncs}
    def touches_wire(pt, skip=None):
        return any(on_seg(pt, a, b) for i, (a, b) in enumerate(wires) if i != skip)
    bad = 0
    for i, (a, b) in enumerate(wires):
        for e in (a, b):
            k = key(*e)
            if ends[k] > 1 or k in pinpts or k in lab or touches_wire(e, i):
                continue
            print(f"dangling wire end  ({e[0]:.2f}, {e[1]:.2f})"); bad += 1
    for l in labels:
        k = key(l['x'], l['y'])
        if k not in pinpts and k not in ends and not touches_wire((l['x'], l['y'])):
            print(f"floating {l['kind']} '{l['name']}' at ({l['x']:.2f}, {l['y']:.2f})"); bad += 1
    for p in pins:
        k = key(p['x'], p['y'])
        if p['power'] or p['type'] == 'no_connect' or k in nc:
            continue
        if pinpts[k] < 2 and k not in ends and k not in lab and not touches_wire((p['x'], p['y'])):
            print(f"unconnected pin    {p['ref']}.{p['pin']} ({p['name']}) at ({p['x']:.2f}, {p['y']:.2f})"); bad += 1
    off = [p for p in pins if abs(p['x'] / 1.27 - round(p['x'] / 1.27)) > 0.01 or abs(p['y'] / 1.27 - round(p['y'] / 1.27)) > 0.01]
    for p in off[:20]:
        print(f"pin off 1.27 grid  {p['ref']}.{p['pin']} at ({p['x']:.3f}, {p['y']:.3f})")
    print(f"{len(pins)} pins, {len(wires)} wires, {len(labels)} labels, {len(junctions)} junctions: "
          f"{bad} geometry issues, {len(off)} pins off grid. (Electrical truth: run ERC.)")

def cmd_lint(path, near):
    root, libs = load(path)
    pins, net, names, wires, labels = connectivity(root, libs)
    by_net = collections.defaultdict(list)
    for p in pins:
        if not p['power']:
            by_net[net[(p['ref'], p['pin'])]].append(p)
    lab_count = collections.Counter(l['name'] for l in labels)
    power_like = re.compile(r'^(GND\w*|AGND|DGND|PGND|VCC\w*|VDD\w*|VSS\w*|VBUS|VIN|\+\d+V\d*\w*|\+?\d+V\d*\w*)$', re.I)
    print("== power nets drawn with labels (use power symbols instead)")
    for n, c in sorted(lab_count.items()):
        if power_like.match(n):
            print(f"  {n}: {c} labels")
    print(f"== label-only connections between pins closer than {near} mm (draw a wire instead)")
    hits = 0
    for r, ps in by_net.items():
        nm = ', '.join(sorted(names.get(r, []))) or '(unnamed)'
        if len(ps) < 2 or power_like.match(nm.split(', ')[0]):
            continue
        # pins of one net that are not joined by wires (each pin's own wire group)
        groups = collections.defaultdict(list)
        for p in ps:
            groups[wire_group(p, wires)].append(p)
        if len(groups) < 2:
            continue
        gl = list(groups.values())
        for i in range(len(gl)):
            for j in range(i + 1, len(gl)):
                d = min(math.hypot(a['x'] - b['x'], a['y'] - b['y']) for a in gl[i] for b in gl[j])
                if d <= near:
                    a = gl[i][0]; b = gl[j][0]
                    print(f"  {nm}: {a['ref']}.{a['pin']} - {b['ref']}.{b['pin']}  {d:.1f} mm apart"); hits += 1
    # pins whose wire group holds no other pin but a label: 'pin -> label' style (netlist look)
    lab_pts = [(l['x'], l['y']) for l in labels]
    grp_pins = collections.Counter(wire_group(p, wires) for p in pins)
    def grp_has_label(g, p):
        if g[0] == 'pt':
            return any(key(*q) == g[1:] for q in lab_pts)
        return any(wire_group(dict(x=q[0], y=q[1]), wires) == g for q in lab_pts)
    stubs = collections.defaultdict(list)
    signal = [p for p in pins if not p['power'] and p['type'] != 'no_connect']
    for p in signal:
        g = wire_group(p, wires)
        if grp_pins[g] == 1 and grp_has_label(g, p):
            stubs[p['ref']].append(p['pin'])
    n = sum(len(v) for v in stubs.values())
    print(f"== pins connected only through a label: {n} of {len(signal)} signal pins ({100 * n // max(1, len(signal))} %)")
    for ref, ps in sorted(stubs.items(), key=lambda kv: -len(kv[1]))[:15]:
        print(f"  {ref}: pins {' '.join(ps)}")
    print(f"== {hits} near label-only links; {len(labels)} labels, {len(wires)} wires in total")

_wg_cache = {}
def wire_group(p, wires):
    """Id of the wire-connected group of a pin (labels ignored)."""
    if not _wg_cache:
        parent = {}
        def f(a):
            parent.setdefault(a, a)
            while parent[a] != a:
                parent[a] = parent[parent[a]]; a = parent[a]
            return a
        for a, b in wires:
            parent[f(key(*a))] = f(key(*b))
        for a, b in wires:
            for c, d in wires:
                for e in (c, d):
                    if on_seg(e, a, b):
                        parent[f(key(*e))] = f(key(*a))
        _wg_cache['f'] = f
        _wg_cache['wires'] = wires
    f = _wg_cache['f']
    k = key(p['x'], p['y'])
    for a, b in _wg_cache['wires']:
        if on_seg((p['x'], p['y']), a, b):
            return f(key(*a))
    return ('pt',) + k                                   # pins touching each other share the point

def cmd_blocks(path, gap):
    root, libs = load(path)
    syms = []
    for s in symbols(root):
        ref = prop(s, 'Reference') or ''
        if ref.startswith('#'):
            continue
        at = kid(s, 'at'); syms.append((ref, float(at[1]), float(at[2]), prop(s, 'Value') or ''))
    parent = list(range(len(syms)))
    def f(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i in range(len(syms)):
        for j in range(i + 1, len(syms)):
            if math.hypot(syms[i][1] - syms[j][1], syms[i][2] - syms[j][2]) <= gap:
                parent[f(i)] = f(j)
    cl = collections.defaultdict(list)
    for i, s in enumerate(syms):
        cl[f(i)].append(s)
    for c in sorted(cl.values(), key=lambda c: (min(s[2] for s in c), min(s[1] for s in c))):
        xs = [s[1] for s in c]; ys = [s[2] for s in c]
        print(f"block x {min(xs):.0f}-{max(xs):.0f}  y {min(ys):.0f}-{max(ys):.0f}: " + ' '.join(f"{s[0]}({s[3][:10]})" for s in c))

def nets_of(path):
    root, libs = load(path)
    pins, net, names, _, _ = connectivity(root, libs)
    groups = collections.defaultdict(set)
    for (ref, pin), r in net.items():
        if not ref.startswith('#'):
            groups[r].add(f'{ref}.{pin}')
    named = {}
    for r, g in groups.items():
        named[frozenset(g)] = sorted(names.get(r, []))
    return named

def cmd_same(a, b):
    A, B = nets_of(a), nets_of(b)
    only_a = [s for s in A if s not in B]; only_b = [s for s in B if s not in A]
    renamed = [(A[s], B[s]) for s in A if s in B and A[s] != B[s]]
    for s in only_a[:20]:
        print('only in A:', A[s] or '(unnamed)', ' '.join(sorted(s)[:8]))
    for s in only_b[:20]:
        print('only in B:', B[s] or '(unnamed)', ' '.join(sorted(s)[:8]))
    for x, y in renamed[:20]:
        print('same pins, other name:', x, '->', y)
    ok = not only_a and not only_b
    print(f"{'IDENTICAL' if ok else 'DIFFERENT'} connectivity: {len(A)} vs {len(B)} nets, {len(renamed)} renamed")
    sys.exit(0 if ok else 1)

# ---------- emit helpers (strings to paste before the final ')' of the root expression) ----------
def _u():
    return str(uuid.uuid4())

def wire(x1, y1, x2, y2):
    return (f'\t(wire\n\t\t(pts\n\t\t\t(xy {x1:g} {y1:g}) (xy {x2:g} {y2:g})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n'
            f'\t\t\t(type default)\n\t\t)\n\t\t(uuid "{_u()}")\n\t)\n')

def junction(x, y):
    return (f'\t(junction\n\t\t(at {x:g} {y:g})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{_u()}")\n\t)\n')

def no_connect(x, y):
    return f'\t(no_connect\n\t\t(at {x:g} {y:g})\n\t\t(uuid "{_u()}")\n\t)\n'

def label(name, x, y, ang=0, justify='left'):
    return (f'\t(label "{name}"\n\t\t(at {x:g} {y:g} {ang:g})\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n'
            f'\t\t\t)\n\t\t\t(justify {justify} bottom)\n\t\t)\n\t\t(uuid "{_u()}")\n\t)\n')

def global_label(name, x, y, ang=0, shape='bidirectional', justify='left'):
    return (f'\t(global_label "{name}"\n\t\t(shape {shape})\n\t\t(at {x:g} {y:g} {ang:g})\n\t\t(fields_autoplaced yes)\n'
            f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify {justify})\n\t\t)\n'
            f'\t\t(uuid "{_u()}")\n\t)\n')

if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] not in ('pins', 'check', 'lint', 'blocks', 'same'):
        print(__doc__); sys.exit(1)
    opt = lambda n, d: float(a[a.index(n) + 1]) if n in a else d
    if a[0] == 'pins':
        cmd_pins(a[1], set(a[2:]))
    elif a[0] == 'check':
        cmd_check(a[1])
    elif a[0] == 'same':
        cmd_same(a[1], a[2])
    elif a[0] == 'lint':
        cmd_lint(a[1], opt('--near', 15.0))
    else:
        cmd_blocks(a[1], opt('--gap', 12.0))
