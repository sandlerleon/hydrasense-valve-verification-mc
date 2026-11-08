# -*- coding: utf-8 -*-
"""Shared helpers for the manuscript builders: results, number formatting, block lists."""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
FIG = os.path.join(ROOT, "figures")
OUT = os.path.join(ROOT, "manuscript")
R = json.load(open(os.path.join(ROOT, "results", "original_results.json"), encoding="utf-8"))      # first suite (HydraSense_MC.py), unchanged
X = json.load(open(os.path.join(ROOT, "results", "results_v2.json"), encoding="utf-8"))            # extended studies (hydrasense_v2.py)
W = json.load(open(os.path.join(ROOT, "results", "results_v3.json"), encoding="utf-8"))            # studies added in version 1.1.0 (hydrasense_v3.py)
DOIS = json.load(open(os.path.join(HERE, "dois.json"), encoding="utf-8"))
GITHUB = "https://github.com/sandlerleon/hydrasense-valve-verification-mc"
VERSION = "1.1.0"
EMAIL = "sandler.leon@gmail.com"
TITLE = "Quantifying the Effectiveness of Independent Manual-Valve Verification in Preventing Product-Transfer Risks: A Monte Carlo Process-Safety Assessment"


def n(x, d=0):
    s = "{:,.{d}f}".format(x, d=d)
    if set(s) <= set("-0.,"):
        return s.lstrip("-")
    return s.replace("-", "−")


def pc(x, d=0):
    """probability (0-1) as a percentage string"""
    return n(100.0 * x, d) + "%"


def ci(lo, hi, d=1):
    return "%s–%s%%" % (n(100 * lo, d), n(100 * hi, d))


FIGNUM = {"arch": 1, "resid": 2, "tol": 3, "age": 4, "avail": 5, "compl": 6, "sens": 7, "psa": 8, "resp": 9, "rez": 10, "cc3": 11, "bnd": 12}
TABNUM = {"arch": 1, "resid": 2, "prior": 3, "psa": 4, "pilot": 5, "miss": 6, "bnd": 7, "cons": 8, "clu": 9, "thr": 10, "claims": 11}
_TOK = re.compile(r"@([FT]):(\w+)@")


def _sub(x):
    """replace the symbolic figure and table numbers (@F:key@, @T:key@) in a block"""
    if isinstance(x, str):
        return _TOK.sub(lambda m: str({"F": FIGNUM, "T": TABNUM}[m.group(1)][m.group(2)]), x)
    if isinstance(x, tuple):
        return tuple(_sub(i) for i in x)
    if isinstance(x, list):
        return [_sub(i) for i in x]
    return x


B = []      # manuscript blocks
BS = []     # supplementary blocks


def add(b):
    B.append(_sub(b))


def adds(b):
    BS.append(_sub(b))


def fmt(_text, **kw):
    """replace <<key>> tokens (so that % and { } in the text are never interpreted)"""
    for k, v in kw.items():
        _text = _text.replace("<<%s>>" % k, str(v))
    assert "<<" not in _text, _text[_text.index("<<"):_text.index("<<") + 30]
    return _text


# ---- first suite (14-valve transfer route unless stated)
AR = R["archs"]
T14 = AR["transfer_14"]
P_ = lambda route, arch, key="any_und": AR[route][arch][key]["p"]
BASE, TURN, STEM, FULL = (P_("transfer_14", a) for a in ("baseline", "turns", "stem", "full"))
RRF0 = BASE / FULL
TOLS = {k: {round(r[0], 2): r for r in R["tolerance"][k]} for k in R["tolerance"]}        # [tol, false alarms per valve, missed-defect share]
OPS = {k: {r[0]: r for r in R["ops"][k]} for k in R["ops"]}                                 # [ops, false alarms per valve, missed share]
COMM = {k: {round(r[0], 4): r for r in R["comm"][k]} for k in R["comm"]}                    # [p_comm, blocked share, residual risk]
COMP = {round(r[0], 2): r[1] for r in R["complacency"]}
NFC = {round(r[0], 2): r[1] for r in R["nfc"]}
TOR = {r[0]: r[1:] for r in R["tornado"]["rows"]}
BAT = R["battery"]

# ---- extended studies
PSA = X["psa"]; CC = X["cc"]; RESP = X["response"]; TYP = X["types"]; REZ = X["rezero"]; COL = X["collateral"]; PIL = X["pilot"]
PRIOR_IDX = {nm: i for i, nm in enumerate(PSA["names"])}
