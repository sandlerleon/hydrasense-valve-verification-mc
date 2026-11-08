#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hydrasense_v2.py -- extended studies for the HydraSense valve-position verification model.

The original single-file model (HydraSense_MC.py, unchanged) is imported and its engine is extended with five mechanisms that can each be switched off; with all of them off
the extended engine reproduces the original counts exactly (tests/test_all.py):

  cc_sigma     common cause: a per-transfer lognormal multiplier (mean 1) on the three operator error rates (fatigue, poor lighting, a mislabeled valve group)
  resp0, fatigue_k   operator response: probability of acting correctly on a true alarm, falling with the number of nuisance alarms in the same validation
  tol_mid      separate alarm tolerance for intermediate (throttled) valves
  rezero       end-stop re-zeroing of binary valves (one operation since the last zero)
  coverage, d_coll   collateral movement: a wrong-valve action disturbs a neighbouring valve that carries no route device; coverage = fraction of neighbours with a device

Studies: psa (probabilistic sensitivity analysis over the assumed priors), cc, response, valve types and tolerances, rezero, pilot sizing, collateral coverage.
ALL INPUT PROBABILITIES REMAIN ASSUMED PRIORS (not plant data).

Usage:  python hydrasense_v2.py --all | --quick
"""
import argparse
import json
import math
import os
import time
from dataclasses import dataclass, replace

import numpy as np
from scipy import stats

import HydraSense_MC as H

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
FIG = os.path.join(HERE, "figures")
SEED = 2026


@dataclass(frozen=True)
class Params2(H.Params):
    cc_sigma: float = 0.0
    resp0: float = 1.0
    fatigue_k: float = 0.0
    tol_mid: float = -1.0            # negative: same tolerance as the binary valves
    rezero: bool = False
    coverage: float = 0.0
    d_coll: float = 0.5
    cov_realistic: bool = True       # a covered neighbor is detected with the sensor's noise, bias, availability (False: detected with certainty)
    q_gate: float = 0.0              # common cause of the sensing layer, per validation: gateway outage (all devices unavailable)
    q_hist: float = 0.0              #   historian / route-validation service failure (validation lost)
    q_id: float = 0.0                #   systematic wrong valve identification (all assignments shifted by one valve)
    q_cal: float = 0.0               #   calibration procedure error (shared systematic bias of all devices of the transfer)
    cal_shared: float = 0.06         #   standard deviation of that shared bias (stroke fraction)
    cc_bypass: float = -1.0          #   probability that the operator proceeds after such an outage; negative: same as the device bypass probability, 0: fail-safe blocking
    rt_mean: float = 0.0             # time-dependent response: mean response time to an isolated alarm (min); 0: probability model
    d_pre: float = 10.0              #   time available before pump start for the pre-transfer alarms (min)
    d_ev_med: float = 20.0           #   median time available before a consequence develops after a movement during the transfer (min)
    d_ev_sig: float = 0.7            #   log-standard deviation of that time


EXTRA_KEYS = ["fa_mid", "fa_bin", "coll_def", "coll_und", "acted_fail", "ui_lo", "ui_hi"]


def run_chunk2(rng, rng2, n, route, arch, P, nominal=False):
    """The original engine (H.run_chunk) with the extensions above.  Original random numbers are drawn in the original order from rng; the extra ones from rng2."""
    req = np.array(H.ROUTES[route], float); V = len(req)
    sd_d = 0.0 if nominal else P.d_logit_sd
    opsig = 0.0 if nominal else P.op_sigma_mid
    sensing = arch.mode != "none"
    init = (rng.random((n, V)) < 0.5).astype(float)
    u = rng.random((n, V))
    mult = np.exp(P.cc_sigma * rng2.standard_normal((n, 1)) - 0.5 * P.cc_sigma ** 2) if P.cc_sigma > 0 else 1.0
    p_wrong = P.p_wrong * (1 - (P.tap_comp * P.heed if arch.nfc else 0.0))
    ps, pw, pi_ = P.p_skip * mult, p_wrong * mult, P.p_inc * mult
    skip = u < ps
    wrong = (u >= ps) & (u < ps + pw)
    inc = (u >= ps + pw) & (u < ps + pw + pi_)
    mid = (req == 0.5)[None, :]
    actual = np.broadcast_to(req, (n, V)) + np.where(mid, rng.normal(0, opsig, (n, V)), 0.0)
    frac = rng.uniform(0.6, 0.97, (n, V))
    actual = np.where(inc, init + (req - init) * frac, actual)
    actual = np.where(skip | wrong, init, actual)
    true_def = np.abs(actual - req) > P.d_true
    typ = np.where(skip, 0, np.where(wrong, 1, np.where(inc, 2, 3)))
    dvals = np.array([P.d_skip, P.d_wrong, P.d_inc, P.d_mid])
    comp = P.complacency if sensing else 0.0
    z = rng.standard_normal((n, 1))
    det_ex = rng.random((n, V)) < H._det(dvals[typ], P.d_scale, z, sd_d, comp)

    p_unav = 1 - (1 - P.p_comm) * (1 - P.p_batt) * (1 - P.p_hw)
    dev_bad = rng.random((n, V)) < p_unav
    ops = rng.poisson(P.ops_mean, (n, V))
    if P.rezero:
        ops = np.where(mid, ops, np.minimum(ops, 1))
    err = H.sensor_error(rng, (n, V), arch, ops)
    mis = rng.random((n, V)) < arch.p_assign
    bypass_u = rng.random(n)
    if sensing and P.q_cal > 0:
        err = err + np.where(rng2.random(n) < P.q_cal, rng2.normal(0, P.cal_shared, n), 0.0)[:, None]
    if sensing and P.q_id > 0:
        mis = mis | (rng2.random(n) < P.q_id)[:, None]
    tol_v = np.where(mid, P.tol if P.tol_mid < 0 else P.tol_mid, P.tol)
    if sensing:
        blocked = dev_bad.any(1)
        bypass = blocked & (bypass_u < P.bypass)
        if P.q_gate > 0 or P.q_hist > 0:
            outage = np.zeros(n, bool)
            if P.q_gate > 0:
                outage |= rng2.random(n) < P.q_gate
            if P.q_hist > 0:
                outage |= rng2.random(n) < P.q_hist
            ccb = P.bypass if P.cc_bypass < 0 else P.cc_bypass
            bypass = bypass | (outage & (rng2.random(n) < ccb))
            blocked = blocked | outage
        meas = np.where(mis, np.roll(actual, 1, axis=1), actual) + err
        flagged = (np.abs(meas - req) > tol_v) & ~bypass[:, None]
    else:
        blocked = np.zeros(n, bool); bypass = np.zeros(n, bool); flagged = np.zeros((n, V), bool)
    fa = flagged & ~true_def
    # operator response to alarms (extra random numbers only when the mechanism is on)
    if P.rt_mean > 0.0:
        m_eff = P.rt_mean * np.exp(P.fatigue_k * fa.sum(1))
        resp = P.resp0 * (1 - np.exp(-P.d_pre / m_eff))
        acted = rng2.random((n, V)) < resp[:, None]
        acted_seq = rng2.random(n) < resp
        acted_ev = (rng2.exponential(1.0, n) * m_eff < rng2.lognormal(math.log(P.d_ev_med), P.d_ev_sig, n)) & (rng2.random(n) < P.resp0)
    elif P.resp0 < 1.0 or P.fatigue_k > 0.0:
        resp = P.resp0 * np.exp(-P.fatigue_k * fa.sum(1))
        acted = rng2.random((n, V)) < resp[:, None]
        acted_seq = rng2.random(n) < resp
        acted_ev = rng2.random(n) < resp
    else:
        resp = np.ones(n); acted = np.ones((n, V), bool); acted_seq = np.ones(n, bool); acted_ev = np.ones(n, bool)
    und_state = true_def & ~det_ex & ~(flagged & acted)

    seq = rng.random(n) < P.p_seq
    ex_seq = rng.random(n) < H._det(np.full(n, P.d_seq), P.d_scale, z[:, 0], sd_d, comp)
    hs_seq = (rng.random(n) < P.hs_seq_det) & ~bypass & sensing
    und_seq = seq & ~ex_seq & ~(hs_seq & acted_seq)

    T = rng.lognormal(math.log(P.dur_median_h), P.dur_sigma, n)
    has = rng.poisson(P.lam_unauth * V * T) > 0
    delta = rng.uniform(0.10, 1.0, n)
    idx = rng.integers(0, V, n)
    e_ev = err[np.arange(n), idx] if sensing else np.zeros(n)
    tol_ev = tol_v[0, idx] if tol_v.ndim == 2 else tol_v
    flag_ev = np.abs(delta + e_ev) > tol_ev
    online = rng.random(n) > P.p_out_time
    ex_ev = rng.random(n) < H._det(np.full(n, P.d_event), P.d_scale, z[:, 0], sd_d, comp)
    hs_any = has & flag_ev & (online | P.store_forward) & ~bypass & sensing
    hs_60 = has & flag_ev & online & ~bypass & sensing
    und_ev = has & ~ex_ev & ~(hs_any & acted_ev)
    any_und = und_state.any(1) | und_seq | und_ev
    # collateral movement of a neighbouring valve that carries no route device
    cdef = wrong & (rng2.random((n, V)) < 0.5)
    ex_c = rng2.random((n, V)) < H._det(P.d_coll, P.d_scale, z, sd_d, comp)
    covered = rng2.random((n, V)) < P.coverage
    sensed = covered & sensing & ~bypass[:, None]
    if P.cov_realistic and P.coverage > 0 and sensing:
        dcol = rng2.uniform(0.10, 1.0, (n, V))
        errc = H.sensor_error(rng2, (n, V), arch, ops)
        sensed = sensed & ~(rng2.random((n, V)) < p_unav) & (np.abs(dcol + errc) > P.tol)
    ac_c = rng2.random((n, V)) < resp[:, None]
    cund = cdef & ~ex_c & ~(sensed & ac_c)
    lo = actual < req[None, :]
    c = dict(n=n, valves=n * V, pre_def=int(true_def.any(1).sum()), defects=int(true_def.sum()),
             def_flagged=int((true_def & flagged).sum()), und_state_trials=int(und_state.any(1).sum()),
             und_seq=int(und_seq.sum()), und_ev=int(und_ev.sum()), any_und=int(any_und.sum()),
             fa_trials=int(fa.any(1).sum()), fa_count=int(fa.sum()), blocked=int(blocked.sum()),
             bypass=int(bypass.sum()), collateral=int(wrong.any(1).sum()), events=int(has.sum()),
             ev_any=int(hs_any.sum()), ev_60=int(hs_60.sum()),
             fa_mid=int((fa & mid).sum()), fa_bin=int((fa & ~mid).sum()), coll_def=int(cdef.any(1).sum()), coll_und=int(cund.any(1).sum()),
             acted_fail=int((flagged & true_def & ~acted).sum()), ui_lo=int((und_state & lo).sum()), ui_hi=int((und_state & ~lo).sum()))
    return c, any_und


def run2(route="transfer_14", arch="full", P=Params2(), n=300_000, seed=1, nominal=False, chunk=50_000, arch_obj=None):
    A = arch_obj or H.ARCHS[arch]
    tot = {k: 0 for k in H.COUNT_KEYS + EXTRA_KEYS}
    for i, start in enumerate(range(0, n, chunk)):
        m = min(chunk, n - start)
        c, _ = run_chunk2(np.random.default_rng([seed, i]), np.random.default_rng([seed, i, 7]), m, route, A, P, nominal)
        for k in tot:
            tot[k] += c[k]
    tot["route"] = route; tot["arch"] = A.name
    return tot


def p_of(c, key="any_und", of="n"):
    k, n = c[key], c[of]; lo, hi = H.wilson(k, n)
    return dict(p=k / n, lo=lo, hi=hi)


# ------------------------------------------------------------------------------------------------ probabilistic sensitivity analysis over the assumed priors
PRIOR_NAMES = ["operator error rates (x)", "existing-barrier miss rate (x)", "out-of-sequence rate (x)", "unauthorized-movement rate (x)", "sensor noise (x)", "sensor calibration bias (x)",
               "sensor drift (x)", "slip rate (x)", "wrong-device assignment (x)", "device unavailability (x)", "bypass probability", "operator complacency", "time-stamp sequence detection"]


def sample_priors(rng):
    ln = lambda factor90: rng.normal(0.0, math.log(factor90) / 1.645)
    f = dict(op=math.exp(ln(4.0)), miss=math.exp(ln(3.0)), seq=math.exp(ln(3.0)), unauth=math.exp(ln(3.0)), noise=math.exp(ln(2.0)), cal=math.exp(ln(2.0)), drift=math.exp(ln(3.0)),
             slip=math.exp(ln(3.0)), assign=math.exp(ln(3.0)), unav=math.exp(ln(4.0)), bypass=rng.uniform(0.0, 0.5), comp=rng.uniform(0.0, 0.6), hs=rng.uniform(0.7, 1.0))
    return f


def apply_priors(f, P=None):
    P = P or Params2()
    P2 = replace(P, p_skip=P.p_skip * f["op"], p_wrong=P.p_wrong * f["op"], p_inc=P.p_inc * f["op"], d_scale=f["miss"], p_seq=min(P.p_seq * f["seq"], 0.5), lam_unauth=P.lam_unauth * f["unauth"],
                 p_comm=min(P.p_comm * f["unav"], 0.5), p_batt=min(P.p_batt * f["unav"], 0.5), p_hw=min(P.p_hw * f["unav"], 0.5), bypass=f["bypass"], complacency=f["comp"], hs_seq_det=f["hs"])
    archs = {}
    for k in ("stem", "full"):
        a = H.ARCHS[k]
        archs[k] = replace(a, sigma_noise=a.sigma_noise * f["noise"], sigma_cal=a.sigma_cal * f["cal"], sigma_drift=a.sigma_drift * f["drift"], p_slip=min(a.p_slip * f["slip"], 0.5), p_assign=min(a.p_assign * f["assign"], 0.5))
    return P2, archs


def study_psa(ndraw=200, n=40_000):
    rng = np.random.default_rng(SEED + 11)
    X = []; base = []; stem = []; full = []; fa = []
    for i in range(ndraw):
        f = sample_priors(rng)
        P2, archs = apply_priors(f)
        seed = 5000 + i
        b = run2("transfer_14", "baseline", P2, n, seed)
        s = run2("transfer_14", "stem", P2, n, seed, arch_obj=archs["stem"])
        fu = run2("transfer_14", "full", P2, n, seed, arch_obj=archs["full"])
        X.append([f["op"], f["miss"], f["seq"], f["unauth"], f["noise"], f["cal"], f["drift"], f["slip"], f["assign"], f["unav"], f["bypass"], f["comp"], f["hs"]])
        base.append(b["any_und"] / n); stem.append(s["any_und"] / n); full.append(fu["any_und"] / n); fa.append(fu["fa_count"] / fu["valves"])
    X = np.array(X); base = np.array(base); full = np.array(full); stem = np.array(stem); fa = np.array(fa)
    rrf = base / np.maximum(full, 1e-6)

    def prcc(y):
        R = np.apply_along_axis(stats.rankdata, 0, X); ry = stats.rankdata(y)
        out = []
        for j in range(X.shape[1]):
            others = np.delete(R, j, axis=1)
            A = np.column_stack([np.ones(len(ry)), others])
            r1 = R[:, j] - A @ np.linalg.lstsq(A, R[:, j], rcond=None)[0]
            r2 = ry - A @ np.linalg.lstsq(A, ry, rcond=None)[0]
            out.append(float(np.corrcoef(r1, r2)[0, 1]))
        return out
    q = lambda a: [float(np.percentile(a, 5)), float(np.percentile(a, 50)), float(np.percentile(a, 95))]
    return dict(ndraw=ndraw, n=n, names=PRIOR_NAMES, baseline=q(base), stem=q(stem), full=q(full), rrf=q(rrf), fa_per_valve=q(fa), P_rrf_gt5=float((rrf > 5).mean()), P_rrf_gt10=float((rrf > 10).mean()),
                P_rrf_gt2=float((rrf > 2).mean()), prcc_rrf=prcc(np.log(rrf)), prcc_full=prcc(np.log(np.maximum(full, 1e-6))), prcc_baseline=prcc(np.log(base)),
                arrays=dict(baseline=base.tolist(), full=full.tolist(), rrf=rrf.tolist()))


# ------------------------------------------------------------------------------------------------ other studies
def study_cc(n):
    rows = []
    for s in (0.0, 0.5, 1.0, 1.5):
        P = Params2(cc_sigma=s)
        b = run2("transfer_14", "baseline", P, n, 7); f = run2("transfer_14", "full", P, n, 7)
        rows.append(dict(sigma=s, baseline=p_of(b), full=p_of(f), rrf=(b["any_und"] / f["any_und"])))
    return rows


def study_response(n):
    out = {"grid": [], "tol": []}
    for r0 in (1.0, 0.9, 0.8):
        for k in (0.0, 0.3, 0.6):
            P = Params2(resp0=r0, fatigue_k=k)
            b = run2("transfer_14", "baseline", P, n, 9); f = run2("transfer_14", "full", P, n, 9)
            out["grid"].append(dict(resp0=r0, k=k, full=p_of(f), rrf=b["any_und"] / f["any_und"]))
    for r0, k in ((1.0, 0.0), (0.95, 0.3), (0.95, 0.6)):
        for tol in (0.04, 0.05, 0.06, 0.07, 0.08, 0.10, 0.12, 0.15):
            P = Params2(resp0=r0, fatigue_k=k, tol=tol)
            f = run2("transfer_14", "full", P, n, 9)
            out["tol"].append(dict(resp0=r0, k=k, tol=tol, full=p_of(f), fa_per_validation=f["fa_count"] / f["n"], fa_per_valve=f["fa_count"] / f["valves"]))
    return out


def study_types(n):
    out = {"grid": []}
    for tb in (0.05, 0.06, 0.08):
        for tm in (0.08, 0.12, 0.15):
            P = Params2(tol=tb, tol_mid=tm)
            c = run2("transfer_14", "stem", P, n, 13)
            nb = 12 * c["n"]; nm_ = 2 * c["n"]
            out["grid"].append(dict(tol_bin=tb, tol_mid=tm, fa_bin_per_valve=c["fa_bin"] / nb, fa_mid_per_valve=c["fa_mid"] / nm_, fa_per_validation=c["fa_count"] / c["n"],
                                    miss=1 - c["def_flagged"] / c["defects"], risk=p_of(c)))
    P0 = Params2()
    c = run2("transfer_14", "stem", P0, n, 13)
    out["base"] = dict(fa_bin_per_valve=c["fa_bin"] / (12 * c["n"]), fa_mid_per_valve=c["fa_mid"] / (2 * c["n"]), fa_share_mid=c["fa_mid"] / max(c["fa_count"], 1))
    return out


def study_rezero(n):
    out = []
    for k in (1, 3, 10, 30, 100, 300):
        for rz in (False, True):
            c = run2("transfer_14", "stem", Params2(ops_mean=float(k), rezero=rz), n, 17)
            out.append(dict(ops=k, rezero=rz, fa_per_valve=c["fa_count"] / c["valves"], miss=1 - c["def_flagged"] / c["defects"]))
    return out


def study_collateral(n):
    out = []
    for cov in (0.0, 0.25, 0.5, 0.75, 1.0):
        P = Params2(coverage=cov)
        f = run2("transfer_14", "full", P, n, 19); b = run2("transfer_14", "baseline", P, n, 19)
        out.append(dict(coverage=cov, full_per_1000=1000 * f["coll_und"] / f["n"], baseline_per_1000=1000 * b["coll_und"] / b["n"], events_per_1000=1000 * f["coll_def"] / f["n"], baseline_events_per_1000=1000 * b["coll_def"] / b["n"]))
    return out


def study_pilot():
    """Pilot sizing: exact binomial acceptance tests for the nuisance-alarm rate, and the number of injected defects needed to demonstrate a miss rate; accuracy from the chi-square interval."""
    out = {"fa": [], "miss": [], "accuracy": []}
    p_good, p_bad, p_limit = 0.014, 0.03, 0.03
    for N in (100, 200, 500, 1000, 2000, 5000):
        # acceptance number c: largest count with P(X <= c | p_bad) <= 0.05 (consumer risk 5 %)
        c = int(stats.binom.ppf(0.05, N, p_bad))
        while stats.binom.cdf(c, N, p_bad) > 0.05:
            c -= 1
        c = max(c, 0)
        out["fa"].append(dict(N=N, accept_max=c, power_at_1p4=float(stats.binom.cdf(c, N, p_good)), consumer_risk_at_3=float(stats.binom.cdf(c, N, p_bad)), upper95_at_expected=float(stats.beta.ppf(0.975, int(round(N * p_good)) + 1, N - int(round(N * p_good))))))
    for m in (20, 40, 80, 150, 300):
        # demonstrate a miss rate of at most 15 % given a true rate of 6 %: accept if misses <= c with consumer risk 5 % at 15 %
        c = int(stats.binom.ppf(0.05, m, 0.15))
        while c >= 0 and stats.binom.cdf(c, m, 0.15) > 0.05:
            c -= 1
        c = max(c, -1)
        out["miss"].append(dict(injected=m, accept_max=c, power_at_6=float(stats.binom.cdf(c, m, 0.06)) if c >= 0 else 0.0))
    for nread in (30, 50, 100, 200, 500):
        lo = math.sqrt((nread - 1) / stats.chi2.ppf(0.975, nread - 1)); hi = math.sqrt((nread - 1) / stats.chi2.ppf(0.025, nread - 1))
        out["accuracy"].append(dict(readings=nread, sd_ratio_lo=lo, sd_ratio_hi=hi))
    return out


# ------------------------------------------------------------------------------------------------ figures
def make_figures(R):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False})
    C1, C2, C3, C4 = "#1f4e9c", "#d1495b", "#2a9d8f", "#e9a23b"
    P = R["psa"]
    fig, ax = plt.subplots(1, 3, figsize=(7.6, 2.9))
    rrf = np.array(P["arrays"]["rrf"]); full = np.array(P["arrays"]["full"]) * 100; base = np.array(P["arrays"]["baseline"]) * 100
    ax[0].hist(np.log10(rrf), bins=24, color=C1, alpha=0.85); ax[0].set_xlabel("log$_{10}$ risk-reduction factor"); ax[0].set_ylabel("Prior draws"); ax[0].axvline(math.log10(P["rrf"][1]), color="k", ls=":")
    ax[0].set_title("(a) risk-reduction factor", fontsize=8.5)
    ax[1].scatter(base, full, s=6, color=C3, alpha=0.6); ax[1].set_xscale("log"); ax[1].set_yscale("log"); ax[1].plot([0.3, 40], [0.3, 40], "k-", lw=0.6)
    ax[1].set_xlabel("Existing checks only (%)"); ax[1].set_ylabel("With sensing layer (%)"); ax[1].set_title("(b) residual risk per draw", fontsize=8.5)
    o = np.argsort(np.abs(P["prcc_rrf"]))
    ax[2].barh(range(len(o)), [P["prcc_rrf"][i] for i in o], color=[C2 if P["prcc_rrf"][i] < 0 else C1 for i in o]); ax[2].set_yticks(range(len(o))); ax[2].set_yticklabels([P["names"][i] for i in o], fontsize=6)
    ax[2].set_xlabel("PRCC with log RRF"); ax[2].set_title("(c) drivers", fontsize=8.5)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "Fig9_psa.png"), dpi=200, bbox_inches="tight"); plt.close(fig)

    fig, ax = plt.subplots(1, 3, figsize=(7.6, 2.8))
    cc = R["cc"]
    ax[0].bar(np.arange(len(cc)) - 0.2, [r["baseline"]["p"] * 100 for r in cc], 0.4, color=C2, label="existing checks only"); ax[0].set_ylabel("Undetected-error probability (%)")
    a2 = ax[0].twinx(); a2.bar(np.arange(len(cc)) + 0.2, [r["full"]["p"] * 100 for r in cc], 0.4, color=C3, label="with sensing layer"); a2.set_ylabel("with sensing (%)", color=C3)
    ax[0].set_xticks(range(len(cc))); ax[0].set_xticklabels([str(r["sigma"]) for r in cc]); ax[0].set_xlabel("Common-cause spread σ"); ax[0].set_title("(a) common cause", fontsize=8.5)
    T = [r for r in R["response"]["tol"]]
    for (r0, k), col in (((1.0, 0.0), C1), ((0.95, 0.3), C4), ((0.95, 0.6), C2)):
        rows = [r for r in T if r["resp0"] == r0 and r["k"] == k]
        ax[1].plot([r["tol"] * 100 for r in rows], [r["full"]["p"] * 100 for r in rows], "o-", ms=3, color=col, label="response %.2f, fatigue %.1f" % (r0, k))
    ax[1].set_yscale("log"); ax[1].set_xlabel("Alarm tolerance (% of stroke)"); ax[1].set_ylabel("Undetected-error probability (%)"); ax[1].legend(frameon=False, fontsize=6.5); ax[1].set_title("(b) optimal tolerance", fontsize=8.5)
    g = R["types"]["grid"]
    tb = sorted({r["tol_bin"] for r in g}); tm = sorted({r["tol_mid"] for r in g})
    M = np.array([[next(r["fa_per_validation"] for r in g if r["tol_bin"] == a and r["tol_mid"] == b) for b in tm] for a in tb])
    im = ax[2].imshow(M, origin="lower", cmap="YlOrRd", aspect="auto"); ax[2].set_xticks(range(len(tm))); ax[2].set_xticklabels([int(x * 100) for x in tm]); ax[2].set_yticks(range(len(tb))); ax[2].set_yticklabels([int(x * 100) for x in tb])
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax[2].text(j, i, "%.2f" % M[i, j], ha="center", va="center", fontsize=7)
    ax[2].set_xlabel("Tolerance, intermediate valves (%)"); ax[2].set_ylabel("Tolerance, binary valves (%)"); ax[2].set_title("(c) false alarms / validation", fontsize=8.5)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "Fig10_cc_tolerance.png"), dpi=200, bbox_inches="tight"); plt.close(fig)

    fig, ax = plt.subplots(1, 3, figsize=(7.6, 2.8))
    rz = R["rezero"]
    for flag, col, ls in ((False, C2, "--s"), (True, C3, "-o")):
        rows = [r for r in rz if r["rezero"] == flag]
        ax[0].semilogx([r["ops"] for r in rows], [r["fa_per_valve"] * 100 for r in rows], ls, color=col, ms=3, label="re-zero at end stops" if flag else "calibration at assignment only")
    ax[0].set_xlabel("Operations since calibration"); ax[0].set_ylabel("False alarms per valve (%)"); ax[0].legend(frameon=False, fontsize=6.5); ax[0].set_title("(a) end-stop re-zeroing", fontsize=8.5)
    pl = R["pilot"]
    ax[1].semilogx([r["N"] for r in pl["fa"]], [r["power_at_1p4"] for r in pl["fa"]], "o-", color=C1, label="power at true 1.4%"); ax[1].semilogx([r["N"] for r in pl["fa"]], [r["consumer_risk_at_3"] for r in pl["fa"]], "s--", color=C2, label="risk of accepting true 3%")
    ax[1].set_xlabel("Validated valves in the pilot"); ax[1].set_ylabel("Probability"); ax[1].legend(frameon=False, fontsize=6.5); ax[1].set_title("(b) pilot sizing, nuisance alarms", fontsize=8.5)
    col = R["collateral"]
    ax[2].plot([r["coverage"] * 100 for r in col], [r["full_per_1000"] for r in col], "o-", color=C3, label="with sensing layer"); ax[2].axhline(col[0]["baseline_per_1000"], color=C2, ls=":", label="existing checks only")
    ax[2].set_xlabel("Neighboring valves with a device (%)"); ax[2].set_ylabel("Undetected collateral events\nper 1000 transfers"); ax[2].legend(frameon=False, fontsize=6.5); ax[2].set_title("(c) collateral coverage", fontsize=8.5)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "Fig11_rezero_pilot_collateral.png"), dpi=200, bbox_inches="tight"); plt.close(fig)


def run_all(quick=False):
    os.makedirs(RES, exist_ok=True); os.makedirs(FIG, exist_ok=True)
    n = 20_000 if quick else 300_000
    t0 = time.time(); R = dict(seed=SEED, n=n)
    R["psa"] = study_psa(20 if quick else 200, 10_000 if quick else 40_000); print("psa", round(time.time() - t0, 1), flush=True)
    R["cc"] = study_cc(n); R["response"] = study_response(n // 2 if not quick else n); print("response", round(time.time() - t0, 1), flush=True)
    R["types"] = study_types(n // 1); R["rezero"] = study_rezero(n // 2 if not quick else n); R["collateral"] = study_collateral(n); R["pilot"] = study_pilot()
    R["runtime_s"] = round(time.time() - t0, 1)
    if not quick:
        make_figures(R)
    json.dump(R, open(os.path.join(RES, "results_quick.json" if quick else "results_v2.json"), "w"), indent=1, default=float)
    return R


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--all", action="store_true"); ap.add_argument("--quick", action="store_true"); ap.add_argument("--figures", action="store_true")
    a = ap.parse_args()
    if a.figures:
        R = json.load(open(os.path.join(RES, "results_v2.json"))); make_figures(R); print("figures")
    else:
        R = run_all(quick=a.quick); print("done", R["runtime_s"], "s")
