#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Schematic of the sensing-layer architecture (Fig. 1 of the manuscript).   python make_schematic.py -> figures/Fig1_architecture.png"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Polygon, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
BLUE, RED, GREEN, GREY, AMBER = "#1f4e9c", "#d1495b", "#2a9d8f", "0.35", "#e9a23b"


def box(ax, x, y, w, h, text, fc="#eef3fb", ec=BLUE, fs=7.2, lw=1.0):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)


def arrow(ax, p, q, col=GREY, lw=1.2, ls="-", both=False):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="<|-|>" if both else "-|>", mutation_scale=9, color=col, lw=lw, ls=ls))


fig, ax = plt.subplots(figsize=(8.8, 4.4))
ax.set_xlim(0, 14.6); ax.set_ylim(0, 6.8); ax.axis("off")

# field zone: the valve with a clamp-on device and an NFC tag
ax.add_patch(Rectangle((0.1, 0.3), 4.5, 6.2, fc="#f8f6ef", ec="0.7", lw=0.8, ls="--"))
ax.text(0.3, 6.25, "Field (classified area)", fontsize=7.5, fontweight="bold", color=GREY, va="top")
ax.add_patch(Rectangle((0.6, 1.45), 3.6, 0.34, fc="0.75", ec="0.4"))                      # pipe
ax.add_patch(Polygon([(1.9, 1.62), (2.9, 1.62), (1.9, 2.52), (2.9, 2.52)], fc="#c9ced6", ec="0.3"))   # valve body
ax.add_patch(Rectangle((2.35, 2.52), 0.1, 0.7, fc="0.4"))                                 # stem
ax.add_patch(Rectangle((1.9, 3.22), 1.0, 0.14, fc="0.4"))                                 # handwheel
ax.add_patch(FancyBboxPatch((2.5, 2.65), 0.62, 0.42, boxstyle="round,pad=0.02,rounding_size=0.05", fc=GREEN, ec="k", lw=0.8))
ax.text(2.81, 2.86, "S", fontsize=7.5, ha="center", va="center", color="white", fontweight="bold")
ax.add_patch(Rectangle((1.45, 1.1), 0.45, 0.22, fc=AMBER, ec="k", lw=0.6))                # NFC tag
ax.text(1.68, 0.88, "NFC tag", fontsize=6.3, ha="center")
ax.text(3.0, 5.0, "clamp-on stem or\nindicator sensor", fontsize=6.5, ha="left", va="center")
ax.plot([3.15, 3.2], [4.75, 3.1], color=GREY, lw=0.6)
ax.text(0.3, 5.0, "reads the actual\nposition, not the\noperator's report", fontsize=6.5, color=GREEN, va="center")
ax.add_patch(Circle((0.95, 3.0), 0.17, fc="#f1c27d", ec="k", lw=0.7))                     # operator
ax.add_patch(Rectangle((0.8, 2.25), 0.3, 0.6, fc=BLUE, ec="k", lw=0.7))
ax.text(0.45, 2.0, "badge", fontsize=6.3, ha="left")
arrow(ax, (1.1, 2.55), (1.6, 1.35), AMBER, 1.0, "--", both=True)
ax.text(0.3, 0.5, "tap tag: assign + calibrate; tap badge: identity", fontsize=5.8, color=GREY)

# communication and data
box(ax, 5.2, 2.4, 1.9, 1.0, "WirelessHART\ngateway", fc="#eaf6f4", ec=GREEN, fs=6.8)
box(ax, 7.6, 2.4, 2.0, 1.0, "plant historian\n(position, identity,\ntime, step)", fc="#eaf6f4", ec=GREEN, fs=6.5)
box(ax, 10.1, 2.4, 1.9, 1.0, "route-validation\nservice", fc="#eaf6f4", ec=GREEN, fs=6.8)
box(ax, 12.5, 2.4, 1.9, 1.0, "control room:\nalignment status\nand alarms", fc="#fdf1f1", ec=RED, fs=6.5)
arrow(ax, (3.14, 2.86), (5.2, 2.9), GREEN, 1.6)
ax.text(4.15, 3.25, "wireless link,\nlocal buffer", fontsize=6.0, color=GREEN, ha="center", va="bottom")
for a, b in ((7.1, 7.6), (9.6, 10.1), (12.0, 12.5)):
    arrow(ax, (a, 2.9), (b, 2.9), GREEN, 1.6)
ax.text(11.05, 4.5, "procedure: required position\nfor each valve and step", fontsize=6.4, ha="center", va="center", color=GREY)
arrow(ax, (11.05, 4.05), (11.05, 3.4), GREY, 1.0)
ax.text(5.2, 4.3, "advisory protection layer: no pump interlock,\nnot a safety instrumented function", fontsize=6.6, ha="left", va="center", color=RED)

# existing barriers in parallel
box(ax, 5.2, 0.45, 9.2, 0.9, "existing barriers (unchanged): operator rounds, radio confirmation, paper checklist\nthey record what the operator reports, not what the valve does", fc="#f4f4f4", ec="0.55", fs=6.6)
arrow(ax, (13.45, 1.35), (13.45, 2.4), "0.55", 1.0, "--")
ax.text(13.6, 1.88, "independent\nsecond opinion", fontsize=6.0, color="0.4", va="center")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "Fig1_architecture.png"), dpi=220, bbox_inches="tight")
print("written")
