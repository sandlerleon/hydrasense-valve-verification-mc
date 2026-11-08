#!/usr/bin/env python3
"""
HydraSense_MC.py - Monte Carlo barrier-effectiveness model for independent, real-time
verification of manual valve position during product transfers.

One self-contained file (numpy + matplotlib), MyUncle-style:
  * route presets and sensing-architecture presets sharing one engine
  * closed-form checks that cross-validate the simulation
  * one-call figure suite + Markdown results + SQLite run log

Question answered:
    For a transfer route of V manual valves, with operator errors (skipped valve, wrong valve,
    incomplete movement, imprecise throttling, out-of-sequence steps) and post-validation
    unauthorized movement, how much does an independent position-sensing layer reduce the
    probability that an error goes undetected, at what false-alarm cost, and which design
    parameters (alarm tolerance, recalibration interval, availability, bypass, operator
    complacency) control that benefit?

Every probability below is an ASSUMED PRIOR (order-of-magnitude, informed by human-reliability
practice). Nothing here is measured plant data; absolute risks are illustrative and the
relative comparisons and sensitivities are the intended output.

Usage:
    python HydraSense_MC.py --demo                      # self-test (closed-form cross-checks)
    python HydraSense_MC.py --reproduce                 # full figure suite + results.md + results.json
    python HydraSense_MC.py --route transfer_14 --arch full --n 500000
"""
import argparse, json, math, os, sqlite3, time
from dataclasses import dataclass, replace
import numpy as np

# ----------------------------------------------------------------------------- presets
@dataclass(frozen=True)
class Params:
    # operator error model (per valve action) - assumed priors
    p_skip: float = 0.002          # valve action omitted (also covers false "done" report)
    p_wrong: float = 0.0015        # adjacent/wrong valve operated; intended valve left unchanged
    p_inc: float = 0.006           # movement stopped short (fraction 0.60-0.97 of required travel)
    op_sigma_mid: float = 0.04     # operator setting accuracy on intermediate (throttled) valves
    p_seq: float = 0.004           # per-transfer probability of an out-of-sequence step
    lam_unauth: float = 5e-5       # unauthorized/accidental movement rate, per valve-hour
    dur_median_h: float = 8.0      # transfer duration (lognormal)
    dur_sigma: float = 0.5
    d_true: float = 0.10           # |position - required| above this is a true defect (stroke fraction)
    # detection by EXISTING barriers (rounds, radio, paper checklist), per defect
    d_skip: float = 0.80; d_wrong: float = 0.80; d_inc: float = 0.60; d_mid: float = 0.50
    d_seq: float = 0.10; d_event: float = 0.20
    d_logit_sd: float = 0.5        # per-trial uncertainty on existing detection probabilities
    d_scale: float = 1.0           # multiplies the existing-barrier MISS probability
    complacency: float = 0.20      # relative loss of existing-barrier effectiveness when a sensor layer is present
    # sensing-layer behaviour
    tol: float = 0.08              # alarm tolerance (stroke fraction); 0.05 gives too many false alarms (see study_tolerance)
    ops_mean: float = 3.0          # operations since last calibration (temporary deployment: calibrated on assignment)
    p_comm: float = 0.003          # device not communicating at validation time
    p_batt: float = 0.001          # battery fault not yet alarmed
    p_hw: float = 0.002            # hardware fault
    bypass: float = 0.20           # prob. an operator proceeds without sensor validation when a device is unavailable
    p_out_time: float = 0.005      # fraction of time a device is out of communication during transfer
    store_forward: bool = True     # events buffered on device and reported after reconnection
    tap_comp: float = 0.90         # operator taps NFC tag before touching a valve
    heed: float = 0.95             # operator heeds a wrong-valve alarm
    hs_seq_det: float = 0.95       # time-stamped event logic catches an out-of-sequence step

@dataclass(frozen=True)
class Arch:
    name: str
    mode: str                      # none | turns | stem
    sigma_noise: float             # measurement noise (stroke fraction, 1 sd)
    sigma_cal: float               # calibration bias (1 sd)
    sigma_drift: float             # drift per sqrt(operation)
    p_slip: float                  # probability per operation of losing counts / slipping
    nfc: bool                      # NFC tag assignment + operator ID
    p_assign: float                # probability the device is linked to the wrong valve

ARCHS = {
    "baseline": Arch("Existing checks only", "none", 0, 0, 0, 0, False, 0),
    "turns":    Arch("Handwheel turn-count collar", "turns", 0.02, 0.03, 0.004, 0.004, False, 0.005),
    "stem":     Arch("Direct stem/indicator sensing", "stem", 0.015, 0.02, 0.0005, 0.0003, False, 0.005),
    "full":     Arch("Direct sensing + NFC identity (HydraSense)", "stem", 0.015, 0.02, 0.0005, 0.0003, True, 0.0002),
}
# required positions (stroke fraction); 0.5 = intermediate (throttled)
ROUTES = {
    "short_6":    [1, 1, 1, 0, 0, 0.5],
    "transfer_14": [1] * 8 + [0] * 4 + [0.5] * 2,
    "long_24":    [1] * 14 + [0] * 7 + [0.5] * 3,
    "binary_14":  [1] * 9 + [0] * 5,           # used for the closed-form cross-check
}

# ----------------------------------------------------------------------------- helpers
def Phi(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def wilson(k, n, z=1.96):
    if n == 0: return 0.0, 0.0
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)

def _det(d, scale, z, sd, comp):
    d = 1 - (1 - d) * scale
    d = np.clip(d * (1 - comp), 1e-6, 1 - 1e-6)
    return 1 / (1 + np.exp(-(np.log(d / (1 - d)) + sd * z)))

def sensor_error(rng, shape, arch, ops):
    """Measurement error (stroke fraction): calibration bias + noise + drift + slip events."""
    bias = rng.normal(0, arch.sigma_cal, shape)
    noise = rng.normal(0, arch.sigma_noise, shape)
    drift = rng.normal(0, arch.sigma_drift, shape) * np.sqrt(ops)
    p_any_slip = 1 - (1 - arch.p_slip) ** ops
    slip = np.where(rng.random(shape) < p_any_slip, rng.choice([-1.0, 1.0], shape) * rng.uniform(0.05, 0.30, shape), 0.0)
    return bias + noise + drift + slip

# ----------------------------------------------------------------------------- engine
COUNT_KEYS = ["n", "valves", "pre_def", "defects", "def_flagged", "und_state_trials", "und_seq", "und_ev",
              "any_und", "fa_trials", "fa_count", "blocked", "bypass", "collateral", "events", "ev_any", "ev_60"]

def run_chunk(rng, n, route, arch, P, nominal=False):
    req = np.array(ROUTES[route], float); V = len(req)
    sd_d = 0.0 if nominal else P.d_logit_sd
    opsig = 0.0 if nominal else P.op_sigma_mid
    sensing = arch.mode != "none"
    init = (rng.random((n, V)) < 0.5).astype(float)
    u = rng.random((n, V))
    p_wrong = P.p_wrong * (1 - (P.tap_comp * P.heed if arch.nfc else 0.0))
    skip = u < P.p_skip
    wrong = (u >= P.p_skip) & (u < P.p_skip + p_wrong)
    inc = (u >= P.p_skip + p_wrong) & (u < P.p_skip + p_wrong + P.p_inc)
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
    det_ex = rng.random((n, V)) < _det(dvals[typ], P.d_scale, z, sd_d, comp)

    # sensing layer (random numbers always drawn so architectures share a common random stream)
    p_unav = 1 - (1 - P.p_comm) * (1 - P.p_batt) * (1 - P.p_hw)
    dev_bad = rng.random((n, V)) < p_unav
    ops = rng.poisson(P.ops_mean, (n, V))
    err = sensor_error(rng, (n, V), arch, ops)
    mis = rng.random((n, V)) < arch.p_assign
    bypass_u = rng.random(n)
    if sensing:
        blocked = dev_bad.any(1)
        bypass = blocked & (bypass_u < P.bypass)
        meas = np.where(mis, np.roll(actual, 1, axis=1), actual) + err
        flagged = (np.abs(meas - req) > P.tol) & ~bypass[:, None]
    else:
        blocked = np.zeros(n, bool); bypass = np.zeros(n, bool); flagged = np.zeros((n, V), bool)

    und_state = true_def & ~det_ex & ~flagged
    fa = flagged & ~true_def

    seq = rng.random(n) < P.p_seq
    ex_seq = rng.random(n) < _det(np.full(n, P.d_seq), P.d_scale, z[:, 0], sd_d, comp)
    hs_seq = (rng.random(n) < P.hs_seq_det) & ~bypass & sensing
    und_seq = seq & ~ex_seq & ~hs_seq

    T = rng.lognormal(math.log(P.dur_median_h), P.dur_sigma, n)
    has = rng.poisson(P.lam_unauth * V * T) > 0
    delta = rng.uniform(0.10, 1.0, n)
    idx = rng.integers(0, V, n)
    e_ev = err[np.arange(n), idx] if sensing else np.zeros(n)
    flag_ev = np.abs(delta + e_ev) > P.tol
    online = rng.random(n) > P.p_out_time
    ex_ev = rng.random(n) < _det(np.full(n, P.d_event), P.d_scale, z[:, 0], sd_d, comp)
    hs_any = has & flag_ev & (online | P.store_forward) & ~bypass & sensing
    hs_60 = has & flag_ev & online & ~bypass & sensing
    und_ev = has & ~ex_ev & ~hs_any
    any_und = und_state.any(1) | und_seq | und_ev
    c = dict(n=n, valves=n * V, pre_def=int(true_def.any(1).sum()), defects=int(true_def.sum()),
             def_flagged=int((true_def & flagged).sum()), und_state_trials=int(und_state.any(1).sum()),
             und_seq=int(und_seq.sum()), und_ev=int(und_ev.sum()), any_und=int(any_und.sum()),
             fa_trials=int(fa.any(1).sum()), fa_count=int(fa.sum()), blocked=int(blocked.sum()),
             bypass=int(bypass.sum()), collateral=int(wrong.any(1).sum()), events=int(has.sum()),
             ev_any=int(hs_any.sum()), ev_60=int(hs_60.sum()))
    return c, any_und

def run(route="transfer_14", arch="full", P=Params(), n=300_000, seed=1, nominal=False, chunk=50_000, keep=False, arch_obj=None):
    A = arch_obj or ARCHS[arch]
    tot = {k: 0 for k in COUNT_KEYS}; trials = []
    for i, start in enumerate(range(0, n, chunk)):
        m = min(chunk, n - start)
        c, a = run_chunk(np.random.default_rng([seed, i]), m, route, A, P, nominal)
        for k in COUNT_KEYS: tot[k] += c[k]
        if keep: trials.append(a)
    tot["route"] = route; tot["arch"] = A.name
    if keep: tot["trials"] = np.concatenate(trials)
    return tot

def prob(c, key, of="n"):
    k, n = c[key], c[of]; lo, hi = wilson(k, n)
    return dict(p=k / n if n else 0.0, lo=lo, hi=hi)

def summarize(c):
    s = {k: prob(c, k) for k in ("any_und", "und_state_trials", "und_seq", "und_ev", "fa_trials", "blocked", "bypass", "pre_def")}
    s["fa_per_valve"] = c["fa_count"] / c["valves"]
    s["fa_per_validation"] = c["fa_count"] / c["n"]
    s["sensor_miss_rate"] = (1 - c["def_flagged"] / c["defects"]) if c["defects"] else None
    s["collateral_per_1000"] = 1000 * c["collateral"] / c["n"]
    s["ev_detect_60s"] = c["ev_60"] / c["events"] if c["events"] else None
    s["ev_detect_any"] = c["ev_any"] / c["events"] if c["events"] else None
    return s

# ----------------------------------------------------------------------------- analytics
def fa_ideal(sigma, tol): return 2 * (1 - Phi(tol / sigma))
def miss_offset(e, sigma, tol): return Phi((tol - e) / sigma) - Phi((-tol - e) / sigma)

def baseline_residual_binary(P, route="binary_14"):
    """Closed form: independent skip/wrong/incomplete defects on binary valves, existing barriers only."""
    V = len(ROUTES[route])
    p_inc_true = (0.40 - P.d_true) / 0.37        # (1 - frac) ~ U(0.03, 0.40)
    u = 0.5 * (P.p_skip * (1 - P.d_skip) + P.p_wrong * (1 - P.d_wrong) + P.p_inc * p_inc_true * (1 - P.d_inc))
    return 1 - (1 - u) ** V

def selftest(P=Params(), n=300_000, seed=11):
    out = {}
    # (a) false-alarm probability with ideal Gaussian sensor
    ideal = Arch("ideal", "stem", 0.03, 0, 0, 0, False, 0)
    P0 = replace(P, p_skip=0, p_wrong=0, p_inc=0, op_sigma_mid=0, p_comm=0, p_batt=0, p_hw=0, p_seq=0, lam_unauth=0)
    c = run("binary_14", arch_obj=ideal, P=P0, n=n, seed=seed, nominal=True)
    mc, an = c["fa_count"] / c["valves"], fa_ideal(0.03, P.tol)
    out["false_alarm"] = (mc, an)
    assert abs(mc - an) < 4 * math.sqrt(an * (1 - an) / c["valves"]) + 1e-4, f"FA mismatch {mc} vs {an}"
    # (b) miss probability for a fixed offset defect
    rng = np.random.default_rng(seed); e0 = 0.15
    err = sensor_error(rng, (n,), ARCHS["stem"], np.full(n, 3))
    sig = math.sqrt(0.015 ** 2 + 0.02 ** 2 + 3 * 0.0005 ** 2)
    mc_m = float((np.abs(e0 + err) <= P.tol).mean())
    an_m = miss_offset(e0, sig, P.tol)
    out["miss_offset"] = (mc_m, an_m)
    assert abs(mc_m - an_m) < 0.003, f"miss mismatch {mc_m} vs {an_m}"
    # (c) baseline residual risk, binary route, no randomness on detection probabilities
    c = run("binary_14", arch="baseline", P=P, n=n, seed=seed, nominal=True)
    mc_r = c["und_state_trials"] / c["n"]; an_r = baseline_residual_binary(P)
    out["baseline_residual"] = (mc_r, an_r)
    assert abs(mc_r - an_r) < 4 * math.sqrt(an_r * (1 - an_r) / n) + 1e-4, f"residual mismatch {mc_r} vs {an_r}"
    return out

# ----------------------------------------------------------------------------- studies
def study_archs(P, n, seed):
    res = {}
    for route in ("short_6", "transfer_14", "long_24"):
        res[route] = {a: summarize(run(route, a, P, n, seed)) for a in ARCHS}
    return res

def study_tolerance(P, n, seed, tols=(0.03, 0.05, 0.06, 0.08, 0.10, 0.12, 0.15), aged_ops=60):
    out = {}
    for label, a, ops in (("stem", "stem", P.ops_mean), ("turns", "turns", P.ops_mean), ("turns_aged", "turns", aged_ops), ("stem_aged", "stem", aged_ops)):
        rows = []
        for t in tols:
            c = run("transfer_14", a, replace(P, tol=t, ops_mean=ops), n, seed)
            rows.append((t, c["fa_count"] / c["valves"], 1 - c["def_flagged"] / c["defects"]))
        out[label] = rows
    return out

def study_ops(P, n, seed, ops_list=(1, 3, 10, 30, 100, 300)):
    out = {}
    for a in ("turns", "stem"):
        rows = []
        for k in ops_list:
            c = run("transfer_14", a, replace(P, ops_mean=float(k)), n, seed)
            rows.append((k, c["fa_count"] / c["valves"], 1 - c["def_flagged"] / c["defects"]))
        out[a] = rows
    return out

def study_comm(P, n, seed, comms=(0.0005, 0.001, 0.003, 0.01, 0.02, 0.05)):
    out = {}
    for label, byp in (("bypass_20", 0.2), ("bypass_0", 0.0)):
        rows = []
        for pc in comms:
            c = run("transfer_14", "full", replace(P, p_comm=pc, bypass=byp), n, seed)
            rows.append((pc, c["blocked"] / c["n"], c["any_und"] / c["n"]))
        out[label] = rows
    return out

def study_complacency(P, n, seed, comps=(0.0, 0.1, 0.2, 0.4, 0.6, 0.8)):
    return [(cp, run("transfer_14", "full", replace(P, complacency=cp), n, seed)["any_und"] / n) for cp in comps]

def study_nfc(P, n, seed, taps=(0.0, 0.25, 0.5, 0.75, 0.9, 1.0)):
    rows = []
    for tc in taps:
        c = run("transfer_14", "full", replace(P, tap_comp=tc), n, seed)
        rows.append((tc, 1000 * c["collateral"] / c["n"]))
    return rows

def study_battery(n=200_000, seed=5):
    rng = np.random.default_rng(seed)
    cap = rng.normal(2.6, 0.1, n)                      # Ah, primary lithium cell(s)
    derate = rng.uniform(0.60, 0.95, n)                # temperature / usable-capacity derating
    sleep = rng.normal(15e-6, 3e-6, n).clip(5e-6)      # A
    hb_s = rng.choice([8.0, 16.0, 32.0, 60.0], n, p=[.1, .5, .3, .1])   # heartbeat interval
    msg_mAs = rng.normal(0.4, 0.08, n).clip(0.1)       # tx+rx charge per message
    mot_per_day = rng.poisson(6, n)                    # motion events per day, each awake 60 s at 3 mA
    mAh_day = sleep * 24 * 1000 + (86400 / hb_s) * msg_mAs / 3600 + mot_per_day * 60 * 3 / 3600
    life_y = cap * 1000 * derate / mAh_day / 365
    an = 2.6 * 1000 * 0.775 / (15e-6 * 24 * 1000 + np.mean(86400 / hb_s) * 0.4 / 3600 + 6 * 60 * 3 / 3600) / 365
    return life_y, float(an)

def study_tornado(P, n, seed):
    A0 = ARCHS["full"]
    base = run("transfer_14", "full", P, n, seed)["any_und"] / n
    items = [
        ("existing-barrier miss rate", lambda f: (replace(P, d_scale=f), A0)),
        ("skip rate", lambda f: (replace(P, p_skip=P.p_skip * f), A0)),
        ("incomplete-movement rate", lambda f: (replace(P, p_inc=P.p_inc * f), A0)),
        ("out-of-sequence rate", lambda f: (replace(P, p_seq=P.p_seq * f), A0)),
        ("unauthorized-movement rate", lambda f: (replace(P, lam_unauth=P.lam_unauth * f), A0)),
        ("sensor noise", lambda f: (P, replace(A0, sigma_noise=A0.sigma_noise * f))),
        ("calibration bias", lambda f: (P, replace(A0, sigma_cal=A0.sigma_cal * f))),
        ("alarm tolerance", lambda f: (replace(P, tol=P.tol * f), A0)),
        ("device unavailability", lambda f: (replace(P, p_comm=P.p_comm * f, p_batt=P.p_batt * f, p_hw=P.p_hw * f), A0)),
        ("bypass probability", lambda f: (replace(P, bypass=min(1.0, P.bypass * f)), A0)),
        ("operator complacency", lambda f: (replace(P, complacency=min(0.95, P.complacency * f)), A0)),
        ("wrong-device assignment", lambda f: (P, replace(A0, p_assign=A0.p_assign * f))),
    ]
    rows = []
    for name, fn in items:
        v = []
        for f in (0.5, 2.0):
            Pm, Am = fn(f); v.append(run("transfer_14", "full", Pm, n, seed, arch_obj=Am)["any_und"] / n)
        rows.append((name, v[0], v[1]))
    return base, rows

# ----------------------------------------------------------------------------- figures + report
def reproduce_paper(outdir="hydrasense_mc_out", n=300_000, n_sweep=120_000, seed=2026, P=Params()):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(outdir, exist_ok=True); t0 = time.time()
    chk = selftest(P)
    arch_res = study_archs(P, n, seed)
    tol = study_tolerance(P, n_sweep, seed); ops = study_ops(P, n_sweep, seed)
    comm = study_comm(P, n_sweep, seed); comp = study_complacency(P, n_sweep, seed); nfc = study_nfc(P, n_sweep, seed)
    life, life_an = study_battery(); torn_base, torn = study_tornado(P, n_sweep, seed)
    conv = run("transfer_14", "full", P, n, seed, keep=True)
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    figs = {}
    names = ["baseline", "turns", "stem", "full"]; lab = ["Existing\nchecks", "Handwheel\ncollar", "Direct\nstem", "Direct +\nNFC"]

    f, ax = plt.subplots(figsize=(6.6, 3.5)); w = 0.26
    for j, route in enumerate(("short_6", "transfer_14", "long_24")):
        ax.bar(np.arange(4) + (j - 1) * w, [arch_res[route][a]["any_und"]["p"] * 100 for a in names], w, label=f"{route.replace('_', ' ')} ({len(ROUTES[route])} valves)")
    ax.set_xticks(range(4)); ax.set_xticklabels(lab); ax.set_yscale("log"); ax.set_ylabel("Undetected-error probability per transfer (%)")
    ax.legend(frameon=False, fontsize=8); ax.set_title("Residual risk by architecture and route"); f.tight_layout()
    figs["fig1_architectures.png"] = f

    f, ax = plt.subplots(figsize=(5.8, 3.6))
    for k, ls in (("stem", "-o"), ("turns", "--s"), ("stem_aged", "-^"), ("turns_aged", "--v")):
        ax.plot([r[1] * 100 for r in tol[k]], [r[2] * 100 for r in tol[k]], ls, ms=4, label=k.replace("_", " "))
    ax.set_xscale("log"); ax.set_xlabel("False alarms per valve validation (%)"); ax.set_ylabel("Missed true defects (%)")
    ax.set_title("Alarm-tolerance trade-off (aged = 60 operations since calibration)"); ax.legend(frameon=False, fontsize=8); f.tight_layout()
    figs["fig2_tolerance_tradeoff.png"] = f

    f, axs = plt.subplots(1, 2, figsize=(7.0, 3.3))
    for a, ls in (("turns", "--s"), ("stem", "-o")):
        axs[0].semilogx([r[0] for r in ops[a]], [r[1] * 100 for r in ops[a]], ls, ms=4, label=a)
        axs[1].semilogx([r[0] for r in ops[a]], [r[2] * 100 for r in ops[a]], ls, ms=4, label=a)
    axs[0].set_ylabel("False alarms per valve (%)"); axs[1].set_ylabel("Missed true defects (%)")
    for x in axs: x.set_xlabel("Operations since calibration"); x.legend(frameon=False)
    f.suptitle("Measurement quality vs calibration age", fontsize=9); f.tight_layout()
    figs["fig3_calibration_age.png"] = f

    f, axs = plt.subplots(1, 2, figsize=(7.0, 3.3))
    for k, ls in (("bypass_20", "-o"), ("bypass_0", "--s")):
        axs[0].semilogx([r[0] for r in comm[k]], [r[1] * 100 for r in comm[k]], ls, ms=4, label=k.replace("_", " "))
        axs[1].loglog([r[0] for r in comm[k]], [max(r[2] * 100, 1e-4) for r in comm[k]], ls, ms=4, label=k.replace("_", " "))
    axs[0].set_ylabel("Validation blocked (%)"); axs[1].set_ylabel("Undetected-error probability (%)")
    for x in axs: x.set_xlabel("Per-device communication-loss probability"); x.legend(frameon=False, fontsize=8)
    f.suptitle("Availability and bypass", fontsize=9); f.tight_layout()
    figs["fig4_availability_bypass.png"] = f

    f, axs = plt.subplots(1, 2, figsize=(7.0, 3.3))
    axs[0].plot([r[0] for r in comp], [r[1] * 100 for r in comp], "-o", ms=4)
    axs[0].axhline(arch_res["transfer_14"]["baseline"]["any_und"]["p"] * 100, color="r", ls=":", label="Existing checks only")
    axs[0].set_xlabel("Operator complacency (loss of existing-barrier effectiveness)"); axs[0].set_ylabel("Undetected-error probability (%)"); axs[0].legend(frameon=False, fontsize=8)
    axs[1].plot([r[0] for r in nfc], [r[1] for r in nfc], "-o", ms=4)
    axs[1].set_xlabel("NFC tap compliance"); axs[1].set_ylabel("Wrong-valve events per 1000 transfers")
    f.tight_layout(); figs["fig5_complacency_nfc.png"] = f

    f, ax = plt.subplots(figsize=(5.4, 3.2))
    ax.hist(life, 60, density=True); ax.axvline(float(np.median(life)), color="k", ls=":")
    ax.set_xlabel("Battery life (years)"); ax.set_ylabel("Density"); ax.set_title("Battery-life distribution (design estimate)"); f.tight_layout()
    figs["fig6_battery.png"] = f

    f, ax = plt.subplots(figsize=(6.2, 3.9))
    rows = sorted(torn, key=lambda r: abs(math.log10(max(r[2], 1e-7) / max(r[1], 1e-7))))
    for i, (nm, lo, hi) in enumerate(rows):
        ax.barh(i, (hi - lo) * 100, left=lo * 100, alpha=.7)
    ax.axvline(torn_base * 100, color="k", ls=":"); ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows], fontsize=8)
    ax.set_xlabel("Undetected-error probability (%) when parameter x0.5 to x2"); ax.set_title("One-at-a-time sensitivity (full HydraSense)"); f.tight_layout()
    figs["fig7_sensitivity.png"] = f

    f, ax = plt.subplots(figsize=(5.4, 3.2))
    cs = np.cumsum(conv["trials"]) / np.arange(1, n + 1); idx = np.unique(np.logspace(3, math.log10(n), 100).astype(int)) - 1
    ax.semilogx(idx + 1, cs[idx] * 100); ax.axhline(cs[-1] * 100, color="k", ls=":")
    ax.set_xlabel("Transfers simulated"); ax.set_ylabel("Running estimate (%)"); ax.set_title("Monte Carlo convergence (full HydraSense)"); f.tight_layout()
    figs["fig8_convergence.png"] = f
    for nm, fg in figs.items(): fg.savefig(os.path.join(outdir, nm), dpi=170); plt.close(fg)

    results = dict(meta=dict(n=n, n_sweep=n_sweep, seed=seed, params=P.__dict__, runtime_s=round(time.time() - t0, 1)),
                   selftest=chk, archs=arch_res, tolerance=tol, ops=ops, comm=comm, complacency=comp, nfc=nfc,
                   battery=dict(median_y=float(np.median(life)), p05_y=float(np.percentile(life, 5)), p95_y=float(np.percentile(life, 95)),
                                mean_y=float(life.mean()), analytic_mean_y=life_an),
                   tornado=dict(base=torn_base, rows=torn))
    with open(os.path.join(outdir, "results.json"), "w") as fh: json.dump(results, fh, indent=1, default=float)
    db = sqlite3.connect(os.path.join(outdir, "mc_log.sqlite"))
    db.execute("CREATE TABLE IF NOT EXISTS runs(ts TEXT, route TEXT, arch TEXT, n INT, seed INT, params TEXT, summary TEXT)")
    for route, d in arch_res.items():
        for a, s in d.items():
            db.execute("INSERT INTO runs VALUES(?,?,?,?,?,?,?)", (time.strftime("%F %T"), route, a, n, seed, json.dumps(P.__dict__), json.dumps(s, default=float)))
    db.commit(); db.close()
    pp = lambda d: f"{d['p'] * 100:.3f}% [{d['lo'] * 100:.3f}, {d['hi'] * 100:.3f}]"
    md = [f"# HydraSense Monte Carlo results (n={n:,}, seed={seed})", "",
          "| Route | Architecture | Undetected error | False alarms / validation | Blocked |", "|---|---|---|---|---|"]
    for route, d in arch_res.items():
        for a, s in d.items():
            md.append(f"| {route} | {ARCHS[a].name} | {pp(s['any_und'])} | {s['fa_per_validation']:.3f} | {s['blocked']['p'] * 100:.1f}% |")
    open(os.path.join(outdir, "results.md"), "w").write("\n".join(md))
    return results

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--demo", action="store_true"); ap.add_argument("--reproduce", action="store_true")
    ap.add_argument("--route", default=None); ap.add_argument("--arch", default="full")
    ap.add_argument("--n", type=int, default=300_000); ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--outdir", default="hydrasense_mc_out")
    a = ap.parse_args()
    if a.demo:
        for k, (mc, an) in selftest().items(): print(f"{k:18s} MC {mc:.5f}  closed-form {an:.5f}")
        print("OK"); return
    if a.route:
        print(json.dumps(summarize(run(a.route, a.arch, Params(), a.n, a.seed)), indent=1, default=float)); return
    reproduce_paper(a.outdir, n=a.n, seed=a.seed); print("done ->", a.outdir)

if __name__ == "__main__":
    main()
