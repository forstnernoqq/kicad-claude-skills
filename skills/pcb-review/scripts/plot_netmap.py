"""plot_netmap.py geom.json out.png [--map net=color,...]  -- run with a normal python that has matplotlib (KiCad's bundled python usually lacks it).
One panel per copper layer; nets colored by function so heater paths, analog runs and switch nodes stand out.
Coloring: --map overrides, then net class name keywords, then net name keywords."""
import json, sys, re, argparse, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
ap = argparse.ArgumentParser(); ap.add_argument("geom"); ap.add_argument("out"); ap.add_argument("--map", default="")
a = ap.parse_args(); g = json.load(open(a.geom)); NC = g.get("netclass", {})
OVR = dict(x.split("=") for x in a.map.split(",") if x)
POWER_COLS = ["#d62728", "#ff7f0e", "#9467bd", "#e6ab02", "#a6761d"]; pcol = {}
def col(n):
    if n in OVR: return OVR[n]
    c = NC.get(n, "").lower()
    if re.search(r"gnd|vss", n, re.I): return "#c8c8c8"
    if re.search(r"power|heater|high", c) or re.search(r"VBUS|VIN|VH\b|OUT_CH", n):
        return pcol.setdefault(n, POWER_COLS[len(pcol) % len(POWER_COLS)])
    if re.search(r"analog|sens", c) or re.search(r"SENSE|NTC|T_CH|IN_CH|CMP|U\d+-[-+]", n): return "#2ca02c"
    if re.search(r"sw|buck", c) or re.search(r"-(SW|FB|SS|RT|BST)\)", n): return "#e377c2"
    if re.search(r"gate|pwm", c) or re.search(r"PWM|-G\)|-D\)", n): return "#8c564b"
    if re.search(r"supply|3v3|^\+", c + " " + n, re.I): return "#17becf"
    return "#1f3b73"
x0, y0, w, h = g["bbox"]; L = g["layers"]
FW = max(10, w * 0.4); PT_PER_MM = FW * 72 / (w + 0.4) * 0.9
fig, axs = plt.subplots(len(L), 1, figsize=(FW, len(L) * (h * 0.4 + 1.2)))
axs = axs if len(L) > 1 else [axs]
for ax, ly in zip(axs, L):
    for l, n, pts in g["zones"]:
        if l == ly: ax.add_patch(Polygon(pts, closed=True, fc=col(n), ec="none", alpha=0.45 if col(n) == "#c8c8c8" else 0.8))
    for x1, y1, x2, y2, tw, l, n in g["tracks"]:
        if l == ly: ax.plot([x1, x2], [y1, y2], color=col(n), lw=max(0.6, tw * PT_PER_MM), solid_capstyle="round")
    for l, n, pts in g["pads"]:
        if l == ly: ax.add_patch(Polygon(pts, closed=True, fc=col(n), ec="k", lw=0.3))
    for x, y, d, n in g["vias"]: ax.add_patch(Circle((x, y), d / 2, fc=col(n), ec="k", lw=0.5))
    side = "F" if ly == L[0] else ("B" if ly == L[-1] else None)
    for r, x, y, s in g["fps"]:
        if s == side: ax.text(x, y, r, fontsize=7, ha="center", va="center", weight="bold", bbox=dict(fc="white", alpha=0.6, pad=0.4, lw=0))
    ax.set_xlim(x0 - .2, x0 + w + .2); ax.set_ylim(y0 + h + .2, y0 - .2); ax.set_aspect("equal")
    ax.set_xticks(range(int(x0), int(x0 + w) + 2, 2)); ax.grid(alpha=0.2)
    ax.set_title(f"{ly}  (power nets red/orange/purple, analog green, buck pink, gate brown, supply cyan, GND grey, other navy)", fontsize=10)
plt.tight_layout(); plt.savefig(a.out, dpi=80); print("wrote", a.out); print("power-net colors:", pcol)
