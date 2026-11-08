#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hydrasense_v3.py -- studies added in version 1.1.0 (responses to a pre-submission review).

Uses the extended engine of hydrasense_v2.py (new switchable mechanisms: common cause of the sensing layer, time-dependent operator response,
realistic detection of covered neighbors) and adds:

  eventtree    consequence-based assessment: undetected-error scenarios -> consequences -> expected annual loss (ILLUSTRATIVE, assumed probabilities and losses)
  sensingcc    common-cause failures of the sensing layer (gateway outage, historian failure, wrong identification, calibration error), fail-safe versus ignored outage
  timeresp     time-dependent operator response against the time available before a consequence develops
  bounds       boundaries: maximum bypass / common-cause rate, minimum response, maximum communication loss for a required risk-reduction factor
  threshold    sensitivity of the results to the 10 %-of-stroke defect threshold
  ci           sampling uncertainty (95 % interval) of the risk-reduction factor from independent replications
  psa2         probabilistic sensitivity analysis including the response and common-cause inputs
  fatigue      grid of response probability and fatigue coefficient
  coverage     coverage of neighbors with and without a realistic sensor (noise, availability)
  cluster      beta-binomial acceptance tests for a pilot whose validations are clustered by valve or by transfer
  slipcheck    closed-form miss probability including slip events (explains the 0.286 % versus 0.257 % of the first version)

Usage:  python hydrasense_v3.py --all | --quick | --figures
ALL INPUT PROBABILITIES, CONSEQUENCE PROBABILITIES AND LOSSES ARE ASSUMED, ILLUSTRATIVE VALUES.
"""
import argparse
import json
import math
import os
import time
from dataclasses import replace

import numpy as np
from scipy import stats
from scipy.integrate import quad

import HydraSense_MC as H
import hydrasense_v2 as V
from hydrasense_v2 import Params2, run2, p_of

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
FIG = os.path.join(HERE, "figures")
SEED3 = 2027


def pr(c, key="any_und"):
    return c[key] / c["n"]


def base_risk(P, n, seed):
    c = run2("transfer_14", "baseline", P, n, seed)
    return pr(c)


# ------------------------------------------------------------------------------------------------ closed form with slip
def miss_with_slip(e0=0.15, tol=0.08, ops=3, arch=None):
    arch = arch or H.ARCHS["stem"]
    sig = math.sqrt(arch.sigma_noise ** 2 + arch.sigma_cal ** 2 + ops * arch.sigma_drift ** 2)
    F = lambda x: H.Phi((tol - x) / sig) - H.Phi((-tol - x) / sig)
    ps = 1 - (1 - arch.p_slip) ** ops
    slip = quad(lambda s: 0.5 * (F(e0 + s) + F(e0 - s)) / 0.25, 0.05, 0.30)[0]
    return (1 - ps) * F(e0) + ps * slip, F(e0)


def study_slipcheck(n=3_000_000, seed=11):
    rng = np.random.default_rng(seed)
    err = H.sensor_error(rng, (n,), H.ARCHS["stem"], np.full(n, 3))
    k = int((np.abs(0.15 + err) <= 0.08).sum())
    lo, hi = H.wilson(k, n)
    wslip, wo = miss_with_slip()
    return dict(n=n, mc=k / n, lo=lo, hi=hi, closed_form_without_slip=wo, closed_form_with_slip=wslip)


# ------------------------------------------------------------------------------------------------ sampling uncertainty of the risk-reduction factor
def study_ci(reps=20, n=150_000):
    b, s, f = [], [], []
    for i in range(reps):
        seed = SEED3 * 10 + i
        b.append(pr(run2("transfer_14", "baseline", Params2(), n, seed)))
        s.append(pr(run2("transfer_14", "stem", Params2(), n, seed)))
        f.append(pr(run2("transfer_14", "full", Params2(), n, seed)))
    b, s, f = map(np.array, (b, s, f))
    rng = np.random.default_rng(5)
    idx = rng.integers(0, reps, (4000, reps))
    rrf = b[idx].mean(1) / f[idx].mean(1)
    rrf_s = b[idx].mean(1) / s[idx].mean(1)
    dif = (s[idx].mean(1) - f[idx].mean(1)) / f[idx].mean(1)
    q = lambda a: [float(np.percentile(a, 2.5)), float(np.percentile(a, 50)), float(np.percentile(a, 97.5))]
    return dict(reps=reps, n_per_rep=n, base=float(b.mean()), stem=float(s.mean()), full=float(f.mean()), rrf_full=q(rrf), rrf_stem=q(rrf_s), stem_minus_full_rel=q(dif),
                se_base=float(b.std(ddof=1) / math.sqrt(reps)), se_full=float(f.std(ddof=1) / math.sqrt(reps)))


# ------------------------------------------------------------------------------------------------ common cause of the sensing layer
def study_sensingcc(n=300_000):
    P0 = Params2()
    base = base_risk(P0, n, 21)
    qs = [1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1]
    scen = [("gateway outage, ignored", dict(q_gate=1.0)), ("gateway outage, fail-safe blocking", dict(q_gate=1.0, cc_bypass=0.0)),
            ("historian failure, ignored", dict(q_hist=1.0)), ("historian failure, fail-safe blocking", dict(q_hist=1.0, cc_bypass=0.0)),
            ("wrong valve identification", dict(q_id=1.0)), ("calibration procedure error", dict(q_cal=1.0)),
            ("all four, outages ignored", dict(q_gate=1.0, q_hist=1.0, q_id=1.0, q_cal=1.0)), ("all four, fail-safe blocking", dict(q_gate=1.0, q_hist=1.0, q_id=1.0, q_cal=1.0, cc_bypass=0.0))]
    out = {"base": base, "q": qs, "rows": []}
    f0 = run2("transfer_14", "full", P0, n, 21)
    out["nominal_full"] = p_of(f0)
    for name, kw in scen:
        row = dict(name=name, full=[], fa=[])
        for q in qs:
            P = replace(P0, **{k: (q if k.startswith("q_") else v) for k, v in kw.items()})
            c = run2("transfer_14", "full", P, n, 21)
            d = p_of(c); d["rrf"] = base / d["p"]
            row["full"].append(d); row["fa"].append(c["fa_count"] / c["n"])
        out["rows"].append(row)
    return out


# ------------------------------------------------------------------------------------------------ time-dependent response
def study_timeresp(n=200_000):
    P0 = Params2()
    base = base_risk(P0, n, 31)
    out = {"base": base, "grid": []}
    for kappa in (0.0, 0.3):
        for rt in (1.0, 2.0, 3.0, 5.0, 10.0, 20.0):
            for dev in (5.0, 10.0, 20.0, 40.0):
                c = run2("transfer_14", "full", Params2(rt_mean=rt, d_ev_med=dev, fatigue_k=kappa), n, 31)
                d = p_of(c)
                out["grid"].append(dict(kappa=kappa, rt=rt, d_ev=dev, full=d, rrf=base / d["p"], share_event=c["und_ev"] / max(c["any_und"], 1)))
    c = run2("transfer_14", "full", P0, n, 31)
    out["probability_model_full"] = p_of(c); out["probability_model_rrf"] = base / pr(c)
    return out


# ------------------------------------------------------------------------------------------------ boundaries
def crossing(xs, rrfs, target, increasing):
    """x at which the (monotone) risk-reduction factor crosses the target, by linear interpolation in log(rrf); None if not crossed."""
    pts = list(zip(xs, rrfs))
    for (x0, r0), (x1, r1) in zip(pts[:-1], pts[1:]):
        if (r0 - target) * (r1 - target) <= 0 and r0 != r1:
            t = (math.log(target) - math.log(r0)) / (math.log(r1) - math.log(r0))
            return x0 + t * (x1 - x0)
    return None


def study_bounds(n=200_000):
    P0 = Params2()
    base = base_risk(P0, n, 41)
    runs = {}

    def sweep(name, xs, mk):
        r = []
        for x in xs:
            c = run2("transfer_14", "full", mk(x), n, 41)
            r.append(base / pr(c))
        runs[name] = dict(x=list(xs), rrf=r)

    sweep("bypass", [0.0, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0], lambda x: replace(P0, bypass=x))
    sweep("response", [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0], lambda x: replace(P0, resp0=x))
    sweep("cc_all", [1e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1, 3e-1], lambda x: replace(P0, q_gate=x, q_hist=x, q_id=x, q_cal=x))
    sweep("comm", [0.0005, 0.003, 0.01, 0.02, 0.05, 0.1], lambda x: replace(P0, p_comm=x))
    sweep("tol", [0.04, 0.06, 0.08, 0.10, 0.12, 0.15], lambda x: replace(P0, tol=x))
    b = {}
    for tgt in (5.0, 10.0):
        b[str(int(tgt))] = dict(bypass_max=crossing(runs["bypass"]["x"], runs["bypass"]["rrf"], tgt, False), response_min=crossing(runs["response"]["x"], runs["response"]["rrf"], tgt, True),
                                cc_all_max=crossing(runs["cc_all"]["x"], runs["cc_all"]["rrf"], tgt, False), comm_max=crossing(runs["comm"]["x"], runs["comm"]["rrf"], tgt, False))
    return dict(base=base, sweeps=runs, bounds=b)


# ------------------------------------------------------------------------------------------------ defect threshold
def study_threshold(n=300_000):
    rows = []
    for dt in (0.05, 0.10, 0.15, 0.20):
        for label, tol in (("fixed 8%", 0.08), ("0.8 x threshold", 0.8 * dt)):
            P = Params2(d_true=dt, tol=tol)
            b = run2("transfer_14", "baseline", P, n, 51); f = run2("transfer_14", "full", P, n, 51)
            rows.append(dict(d_true=dt, tol_rule=label, tol=tol, base=p_of(b), full=p_of(f), rrf=pr(b) / pr(f), fa_per_validation=f["fa_count"] / f["n"], miss=1 - f["def_flagged"] / max(f["defects"], 1)))
    return rows


# ------------------------------------------------------------------------------------------------ fatigue grid and coverage
def study_fatigue(n=100_000):
    P0 = Params2()
    base = base_risk(P0, n, 61)
    rows = []
    for r0 in (0.7, 0.8, 0.9, 1.0):
        for k in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
            f = run2("transfer_14", "full", Params2(resp0=r0, fatigue_k=k), n, 61)
            rows.append(dict(resp0=r0, k=k, rrf=base / pr(f), full=pr(f)))
    return rows


def study_coverage(n=300_000):
    out = []
    for cov in (0.0, 0.25, 0.5, 0.75, 1.0):
        row = dict(coverage=cov)
        for key, real in (("realistic", True), ("ideal", False)):
            f = run2("transfer_14", "full", Params2(coverage=cov, cov_realistic=real), n, 19)
            row[key] = 1000 * f["coll_und"] / f["n"]
        b = run2("transfer_14", "baseline", Params2(coverage=cov), n, 19)
        row["baseline"] = 1000 * b["coll_und"] / b["n"]; row["events_full"] = 1000 * f["coll_def"] / f["n"]; row["events_baseline"] = 1000 * b["coll_def"] / b["n"]
        out.append(row)
    return out


# ------------------------------------------------------------------------------------------------ PSA 2
NAMES2 = V.PRIOR_NAMES + ["operator response to an isolated alarm", "alarm fatigue coefficient", "common-cause rate of the sensing layer (each of 4)"]


def study_psa2(ndraw=150, n=40_000):
    rng = np.random.default_rng(SEED3 + 3)
    X, base, stem, full = [], [], [], []
    for i in range(ndraw):
        f = V.sample_priors(rng)
        P2, archs = V.apply_priors(f)
        r0 = rng.uniform(0.7, 1.0); kk = rng.uniform(0.0, 1.0); q = 10 ** rng.uniform(-4, -1.5)
        P2 = replace(P2, resp0=r0, fatigue_k=kk, q_gate=q, q_hist=q, q_id=q, q_cal=q)
        seed = 7000 + i
        b = run2("transfer_14", "baseline", P2, n, seed)
        fu = run2("transfer_14", "full", P2, n, seed, arch_obj=archs["full"])
        X.append([f["op"], f["miss"], f["seq"], f["unauth"], f["noise"], f["cal"], f["drift"], f["slip"], f["assign"], f["unav"], f["bypass"], f["comp"], f["hs"], r0, kk, math.log10(q)])
        base.append(pr(b)); full.append(pr(fu))
    X = np.array(X); base = np.array(base); full = np.array(full)
    rrf = base / np.maximum(full, 1e-6)

    def prcc(y):
        R = np.apply_along_axis(stats.rankdata, 0, X); ry = stats.rankdata(y); out = []
        for j in range(X.shape[1]):
            A = np.column_stack([np.ones(len(ry)), np.delete(R, j, axis=1)])
            r1 = R[:, j] - A @ np.linalg.lstsq(A, R[:, j], rcond=None)[0]
            r2 = ry - A @ np.linalg.lstsq(A, ry, rcond=None)[0]
            out.append(float(np.corrcoef(r1, r2)[0, 1]))
        return out
    q = lambda a: [float(np.percentile(a, 5)), float(np.percentile(a, 50)), float(np.percentile(a, 95))]
    return dict(ndraw=ndraw, n=n, names=NAMES2, baseline=q(base), full=q(full), rrf=q(rrf), P_rrf_gt2=float((rrf > 2).mean()), P_rrf_gt5=float((rrf > 5).mean()), P_rrf_gt10=float((rrf > 10).mean()),
                prcc_rrf=prcc(np.log(rrf)), arrays=dict(baseline=base.tolist(), full=full.tolist(), rrf=rrf.tolist()))


# ------------------------------------------------------------------------------------------------ event tree
SCEN = ["required-open valve left closed or partly closed", "required-closed valve left open or partly open", "out-of-sequence step", "movement after validation", "collateral movement of a neighbor"]
CONS = ["benign or recoverable", "product contamination or misrouting", "tank overflow or release", "blocked-in or overpressure"]
PCOND = np.array([[0.90, 0.02, 0.00, 0.08],
                  [0.55, 0.30, 0.15, 0.00],
                  [0.85, 0.05, 0.03, 0.07],
                  [0.60, 0.20, 0.10, 0.10],
                  [0.70, 0.15, 0.10, 0.05]])          # P(consequence | undetected scenario); ASSUMED, illustrative
LOSS = np.array([0.0, 150_000.0, 2_000_000.0, 800_000.0])    # loss per consequence (illustrative currency units)
NT = 1000                                                    # transfers per year (illustrative)


def study_eventtree(n=300_000, ndraw=4000):
    P = Params2(coverage=0.5)
    res = {}
    for arch in ("baseline", "stem", "full"):
        c = run2("transfer_14", arch, P, n, 71)
        e = np.array([c["ui_lo"], c["ui_hi"], c["und_seq"], c["und_ev"], c["coll_und"]], float) / c["n"]
        res[arch] = dict(scenario_per_transfer=e.tolist(), cons_per_transfer=(e @ PCOND).tolist())
        res[arch]["eal"] = float(NT * (e @ PCOND) @ LOSS)
    for a in ("stem", "full"):
        res[a]["rrf_cons"] = [res["baseline"]["cons_per_transfer"][j] / res[a]["cons_per_transfer"][j] if res[a]["cons_per_transfer"][j] > 0 else None for j in range(4)]
        res[a]["rrf_eal"] = res["baseline"]["eal"] / res[a]["eal"]
    # uncertainty of the assumed conditional probabilities and losses
    rng = np.random.default_rng(SEED3 + 5)
    eb = np.array(res["baseline"]["scenario_per_transfer"]); ef = np.array(res["full"]["scenario_per_transfer"])
    ratios, eals_b, eals_f = [], [], []
    for _ in range(ndraw):
        m = np.exp(rng.normal(0, math.log(3.0) / 1.645, (5, 3)))
        Pc = PCOND.copy(); Pc[:, 1:] = np.minimum(PCOND[:, 1:] * m, 1.0)
        s = Pc[:, 1:].sum(1)
        Pc[:, 1:] = Pc[:, 1:] / np.maximum(s, 1.0)[:, None]; Pc[:, 0] = 1 - Pc[:, 1:].sum(1)
        L = LOSS * np.exp(np.r_[0.0, rng.normal(0, math.log(3.0) / 1.645, 3)])
        b_ = NT * (eb @ Pc) @ L; f_ = NT * (ef @ Pc) @ L
        eals_b.append(b_); eals_f.append(f_); ratios.append(b_ / f_)
    q = lambda a: [float(np.percentile(a, 5)), float(np.percentile(a, 50)), float(np.percentile(a, 95))]
    res["uncertainty"] = dict(draws=ndraw, rrf_eal=q(ratios), eal_baseline=q(eals_b), eal_full=q(eals_f))
    res["assumptions"] = dict(scenarios=SCEN, consequences=CONS, pcond=PCOND.tolist(), loss=LOSS.tolist(), transfers_per_year=NT, coverage=0.5)
    return res


# ------------------------------------------------------------------------------------------------ clustered pilot
def betabinom_sum_pmf(K, m, p, rho):
    """pmf of the total number of events among K clusters of m validations, each cluster with its own rate ~ Beta of mean p and intraclass correlation rho"""
    if rho <= 0:
        return stats.binom.pmf(np.arange(K * m + 1), K * m, p)
    s = 1 / rho - 1
    a, b = p * s, (1 - p) * s
    one = stats.betabinom.pmf(np.arange(m + 1), m, a, b)
    out = np.array([1.0])
    for _ in range(K):
        out = np.convolve(out, one)
    return out


def study_cluster():
    designs = [("12 valves x 83 validations (clusters = valves)", 12, 83), ("30 valves x 33 validations (clusters = valves)", 30, 33), ("71 transfers x 14 valves (clusters = transfers)", 71, 14)]
    rows = []
    for name, K, m in designs:
        for rho in (0.0, 0.01, 0.02, 0.05, 0.10):
            pm3 = betabinom_sum_pmf(K, m, 0.03, rho); pm14 = betabinom_sum_pmf(K, m, 0.014, rho)
            cdf3 = np.cumsum(pm3); cdf14 = np.cumsum(pm14)
            c = -1
            while c + 1 < len(cdf3) and cdf3[c + 1] <= 0.05:
                c += 1
            rows.append(dict(design=name, K=K, m=m, N=K * m, rho=rho, deff=1 + (m - 1) * rho, n_eff=K * m / (1 + (m - 1) * rho), accept_max=c,
                             power_at_1p4=float(cdf14[c]) if c >= 0 else 0.0, risk_at_3=float(cdf3[c]) if c >= 0 else 0.0))
    return rows


# ------------------------------------------------------------------------------------------------ driver
def make_figures(R):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False})
    C1, C2, C3, C4 = "#1f4e9c", "#d1495b", "#2a9d8f", "#e9a23b"
    # Fig 11: event tree and sensing common cause
    fig, ax = plt.subplots(1, 3, figsize=(7.8, 2.9))
    E = R["eventtree"]; short = ["benign", "contamination", "overflow", "overpressure"]
    x = np.arange(4); w = 0.27
    for k, (a, lab, col) in enumerate((("baseline", "existing checks", C2), ("stem", "direct sensing", C4), ("full", "direct + NFC", C3))):
        ax[0].bar(x + (k - 1) * w, [1000 * v for v in E[a]["cons_per_transfer"]], w, color=col, label=lab)
    ax[0].set_xticks(x); ax[0].set_xticklabels(short, fontsize=6.5, rotation=15); ax[0].set_yscale("log"); ax[0].set_ylabel("Undetected-error consequences per 1000 transfers"); ax[0].legend(frameon=False, fontsize=6.5); ax[0].set_title("(a) consequences", fontsize=8.5)
    S = R["sensingcc"]; qs = S["q"]
    for row, col, ls in zip(S["rows"], [C2, C2, C4, C4, C1, C3, "k", "k"], ["-", "--", "-", "--", "-", "-", "-", "--"]):
        ax[1].plot(qs, [d["rrf"] for d in row["full"]], ls, color=col, lw=1.2, label=row["name"])
    ax[1].set_xscale("log"); ax[1].set_yscale("log"); ax[1].axhline(5, color="0.6", lw=0.6, ls=":"); ax[1].set_xlabel("Common-cause probability per validation"); ax[1].set_ylabel("Risk-reduction factor"); ax[1].set_title("(b) sensing-layer common cause", fontsize=8.5)
    ax[1].legend(frameon=False, fontsize=4.8, loc="lower left")
    T = R["timeresp"]["grid"]
    for dev, col in ((5.0, C2), (10.0, C4), (20.0, C1), (40.0, C3)):
        rows = [r for r in T if r["kappa"] == 0.0 and r["d_ev"] == dev]
        ax[2].plot([r["rt"] for r in rows], [r["rrf"] for r in rows], "o-", ms=3, color=col, label="%d min available" % dev)
    ax[2].set_xscale("log"); ax[2].set_xlabel("Mean response time (min)"); ax[2].set_ylabel("Risk-reduction factor"); ax[2].legend(frameon=False, fontsize=6.5); ax[2].set_title("(c) time-dependent response", fontsize=8.5)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "Fig12_eventtree_cc_time.png"), dpi=200, bbox_inches="tight"); plt.close(fig)
    # Fig 13: boundaries and psa2
    fig, ax = plt.subplots(1, 3, figsize=(7.8, 2.9))
    B = R["bounds"]["sweeps"]
    for key, col, lab, xl in (("bypass", C2, "bypass probability", None), ("response", C1, "response to an alarm", None)):
        ax[0].plot(B[key]["x"], B[key]["rrf"], "o-", ms=3, color=col, label=lab)
    ax[0].axhline(5, color="0.6", ls=":", lw=0.6); ax[0].axhline(10, color="0.6", ls=":", lw=0.6); ax[0].set_xlabel("Probability"); ax[0].set_ylabel("Risk-reduction factor"); ax[0].legend(frameon=False, fontsize=6.5); ax[0].set_title("(a) boundaries", fontsize=8.5)
    P2 = R["psa2"]; rrf = np.array(P2["arrays"]["rrf"]); ax[1].hist(np.log10(rrf), bins=22, color=C1, alpha=0.85); ax[1].axvline(math.log10(P2["rrf"][1]), color="k", ls=":")
    ax[1].set_xlabel("log$_{10}$ risk-reduction factor"); ax[1].set_ylabel("Prior draws"); ax[1].set_title("(b) with response and common cause", fontsize=8.5)
    C = R["cluster"]
    for name, col in (("12 valves x 83 validations (clusters = valves)", C2), ("30 valves x 33 validations (clusters = valves)", C4), ("71 transfers x 14 valves (clusters = transfers)", C3)):
        rows = [r for r in C if r["design"] == name]
        ax[2].plot([r["rho"] for r in rows], [r["power_at_1p4"] for r in rows], "o-", ms=3, color=col, label=name.split(" (")[0])
    ax[2].set_xlabel("Intraclass correlation"); ax[2].set_ylabel("Power at a true 1.4% (consumer risk 5%)"); ax[2].legend(frameon=False, fontsize=5.8); ax[2].set_title("(c) clustered pilot", fontsize=8.5)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "Fig13_bounds_psa2_cluster.png"), dpi=200, bbox_inches="tight"); plt.close(fig)


def run_all(quick=False):
    os.makedirs(RES, exist_ok=True)
    k = 0.1 if quick else 1.0
    t0 = time.time(); R = dict(seed=SEED3)
    nn = lambda x: max(int(x * k), 10_000)

    def step(name, fn, *a, **kw):
        R[name] = fn(*a, **kw); print(name, round(time.time() - t0, 1), flush=True)
    step("slipcheck", study_slipcheck, nn(3_000_000))
    step("ci", study_ci, 20 if not quick else 6, nn(150_000))
    step("sensingcc", study_sensingcc, nn(300_000))
    step("timeresp", study_timeresp, nn(200_000))
    step("bounds", study_bounds, nn(200_000))
    step("threshold", study_threshold, nn(300_000))
    step("fatigue", study_fatigue, nn(100_000))
    step("coverage", study_coverage, nn(300_000))
    step("eventtree", study_eventtree, nn(300_000), 4000)
    step("cluster", study_cluster)
    step("psa2", study_psa2, 150 if not quick else 12, nn(40_000))
    R["runtime_s"] = round(time.time() - t0, 1)
    if not quick:
        make_figures(R)
    json.dump(R, open(os.path.join(RES, "results_quick_v3.json" if quick else "results_v3.json"), "w"), indent=1, default=float)
    return R


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--all", action="store_true"); ap.add_argument("--quick", action="store_true"); ap.add_argument("--figures", action="store_true")
    a = ap.parse_args()
    if a.figures:
        make_figures(json.load(open(os.path.join(RES, "results_v3.json"))))
        print("figures")
    else:
        R = run_all(quick=a.quick); print("done", R["runtime_s"], "s")
