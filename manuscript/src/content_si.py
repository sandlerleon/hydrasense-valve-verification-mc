# -*- coding: utf-8 -*-
"""Supplementary information."""
from common import *

adds(("title", "Supplementary Information"))
adds(("small", TITLE))
adds(("author", "Leon Sandler"))
adds(("small", "Independent Researcher, Northbrook, Illinois, USA. " + EMAIL))
adds(("blank",))

# ------------------------------------------------------------------------------------------- S1 first suite
adds(("h1", "S1. First suite: all outputs for the 14-valve route"))
names = [("baseline", "Existing checks"), ("turns", "Turn-count collar"), ("stem", "Direct sensing"), ("full", "Direct + NFC")]
rows = []
for key, lab, f in (("any_und", "Undetected error per transfer", lambda d: "%s (%s)" % (pc(d["p"], 3), ci(d["lo"], d["hi"], 3))), ("und_state_trials", "  from a valve position", lambda d: pc(d["p"], 3)), ("und_seq", "  from an out-of-sequence step", lambda d: pc(d["p"], 3)),
                    ("und_ev", "  from a post-validation movement", lambda d: pc(d["p"], 3)), ("fa_trials", "Validation with at least one nuisance alarm", lambda d: pc(d["p"], 1)), ("blocked", "Validation blocked (device unavailable)", lambda d: pc(d["p"], 1)),
                    ("bypass", "Bypass of a blocked validation", lambda d: pc(d["p"], 2))):
    rows.append([lab] + [f(T14[a][key]) for a, _ in names])
rows.append(["Nuisance alarms per valve"] + [pc(T14[a]["fa_per_valve"], 2) for a, _ in names])
rows.append(["Defects missed by the sensors"] + [("–" if a == "baseline" else pc(T14[a]["sensor_miss_rate"], 1)) for a, _ in names])
rows.append(["Detection of a post-validation movement within 60 s"] + [("–" if a == "baseline" else pc(T14[a]["ev_detect_60s"], 1)) for a, _ in names])
rows.append(["Wrong-valve events per 1000 transfers"] + [n(T14[a]["collateral_per_1000"], 1) for a, _ in names])
adds(("table", "Table S1. Outputs of the first suite for the 14-valve route (%s transfers per cell; Wilson 95%% interval for the primary output)." % n(R["meta"]["n"]), ["Output"] + [lab for _, lab in names], rows, [3.0, 1.5, 1.2, 1.2, 1.2], 15))

rows = []
for tol in sorted(TOLS["stem"]):
    rows.append([pc(tol, 0), pc(TOLS["stem"][tol][1], 1), pc(TOLS["stem"][tol][2], 1), pc(TOLS["turns"][tol][1], 1), pc(TOLS["turns"][tol][2], 1), pc(TOLS["stem_aged"][tol][1], 1), pc(TOLS["stem_aged"][tol][2], 1), pc(TOLS["turns_aged"][tol][1], 1), pc(TOLS["turns_aged"][tol][2], 1)])
adds(("table", "Table S2. Alarm tolerance sweep (nuisance alarms per valve, share of true defects missed); aged = 60 operations since calibration.", ["Tolerance", "Direct: alarms", "Direct: missed", "Turns: alarms", "Turns: missed", "Direct aged: alarms", "Direct aged: missed", "Turns aged: alarms", "Turns aged: missed"], rows, [0.8, 0.9, 0.9, 0.9, 0.9, 1.0, 1.0, 1.0, 1.0], 14))
rows = [[str(k), pc(OPS["stem"][k][1], 1), pc(OPS["stem"][k][2], 1), pc(OPS["turns"][k][1], 1), pc(OPS["turns"][k][2], 1)] for k in sorted(OPS["stem"])]
adds(("table", "Table S3. Operations since calibration (tolerance 8%).", ["Operations", "Direct: alarms per valve", "Direct: missed", "Turns: alarms per valve", "Turns: missed"], rows, [1.0, 1.3, 1.2, 1.3, 1.2]))
rows = [[n(pcomm, 4), pc(COMM["bypass_20"][pcomm][1], 1), pc(COMM["bypass_20"][pcomm][2], 3), pc(COMM["bypass_0"][pcomm][2], 3)] for pcomm in sorted(COMM["bypass_20"])]
adds(("table", "Table S4. Per-device communication-loss probability: validation blocked, and residual risk of the full layer with 20% and 0% bypass.", ["Communication loss", "Validation blocked", "Residual risk, 20% bypass", "Residual risk, no bypass"], rows, [1.4, 1.3, 1.5, 1.5]))
rows = [[pc(c, 0), pc(COMP[c], 3)] for c in sorted(COMP)]
adds(("table", "Table S5. Operator complacency (relative reduction of the effectiveness of existing checks) and residual risk of the full layer.", ["Complacency", "Residual risk"], rows, [1.2, 1.2]))
rows = [[pc(t, 0), n(NFC[t], 1)] for t in sorted(NFC)]
adds(("table", "Table S6. NFC tap compliance and wrong-valve events per 1000 transfers.", ["Tap compliance", "Wrong-valve events per 1000"], rows, [1.2, 1.6]))
rows = [[nm_, pc(lo, 2), pc(hi, 2)] for nm_, (lo, hi) in TOR.items()]
adds(("table", "Table S7. One-at-a-time sensitivity of the residual risk of the full layer (base %s) for the parameter at half and double its base value." % pc(R["tornado"]["base"], 2), ["Parameter", "Half", "Double"], rows, [2.6, 1.0, 1.0]))
adds(("fig", "orig_fig6_battery.png", "Fig. S1. Design-level battery-life estimate (primary lithium cells, wake-on-motion, 16 s heartbeat): median %s years, 5th to 95th percentile %s to %s years; the analytic mean is %s years." % (n(BAT["median_y"], 1), n(BAT["p05_y"], 1), n(BAT["p95_y"], 1), n(BAT["analytic_mean_y"], 1)), 3.8))
adds(("fig", "orig_fig8_convergence.png", "Fig. S2. Convergence of the Monte Carlo estimate of the residual risk with the number of transfers.", 3.8))

# ------------------------------------------------------------------------------------------- S2 extended
adds(("h1", "S2. Extended studies: all cases"))
rows = [[pc(r["resp0"], 0), n(r["k"], 1), "%s (%s)" % (pc(r["full"]["p"], 3), ci(r["full"]["lo"], r["full"]["hi"], 3)), n(r["rrf"], 1)] for r in RESP["grid"]]
adds(("table", "Table S8. Operator response to an isolated alarm, fatigue coefficient, residual risk of the full layer (Wilson 95%% interval) and risk-reduction factor (existing checks %s)." % pc(CC[0]["baseline"]["p"], 2), ["Response", "Fatigue coefficient", "Residual risk", "Risk-reduction factor"], rows, [1.0, 1.2, 2.4, 1.5]))
rows = []
for r0, k in ((1.0, 0.0), (0.95, 0.3), (0.95, 0.6)):
    for r in [x for x in RESP["tol"] if x["resp0"] == r0 and x["k"] == k]:
        rows.append([pc(r0, 0), n(k, 1), pc(r["tol"], 0), pc(r["full"]["p"], 3), n(r["fa_per_validation"], 2)])
adds(("table", "Table S9. Alarm tolerance with operator response: residual risk of the full layer and nuisance alarms per validation.", ["Response", "Fatigue", "Tolerance", "Residual risk", "Nuisance alarms per validation"], rows, [1.0, 0.9, 1.0, 1.2, 1.7], 15))
rows = [[pc(r["tol_bin"], 0), pc(r["tol_mid"], 0), pc(r["fa_bin_per_valve"], 2), pc(r["fa_mid_per_valve"], 2), n(r["fa_per_validation"], 3), pc(r["miss"], 1), pc(r["risk"]["p"], 3)] for r in TYP["grid"]]
adds(("table", "Table S10. Separate tolerances for binary and intermediate valves (direct sensing, 14-valve route).", ["Binary tol.", "Intermediate tol.", "Alarms per binary valve", "Alarms per intermediate valve", "Alarms per validation", "Defects missed", "Residual risk"], rows, [0.9, 1.0, 1.1, 1.2, 1.1, 1.0, 1.0], 15))
rows = [[str(r["ops"]), "re-zero at end stops" if r["rezero"] else "calibration at assignment", pc(r["fa_per_valve"], 2), pc(r["miss"], 1)] for r in REZ]
adds(("table", "Table S11. End-stop re-zeroing (direct sensing).", ["Operations", "Calibration", "Nuisance alarms per valve", "Defects missed"], rows, [1.0, 2.0, 1.6, 1.2]))
rows = [[pc(r["coverage"], 0), n(r["full_per_1000"], 2), n(r["baseline_per_1000"], 2), n(r["events_per_1000"], 2), n(r["baseline_events_per_1000"], 2)] for r in COL]
adds(("table", "Table S12. Coverage of neighboring valves: undetected collateral events per 1000 transfers (full layer and existing checks), and collateral events (with and without NFC tap-before-touch).", ["Coverage", "Undetected, full layer", "Undetected, existing checks", "Events, with NFC", "Events, without NFC"], rows, [1.0, 1.4, 1.5, 1.2, 1.2]))
rows = [[n(r["sigma"], 1), "%s (%s)" % (pc(r["baseline"]["p"], 2), ci(r["baseline"]["lo"], r["baseline"]["hi"], 2)), "%s (%s)" % (pc(r["full"]["p"], 3), ci(r["full"]["lo"], r["full"]["hi"], 3)), n(r["rrf"], 1)] for r in CC]
adds(("table", "Table S13. Common cause: log-standard deviation of the shared multiplier of the operator error rates.", ["Log-standard deviation", "Existing checks (95% interval)", "Full layer (95% interval)", "Risk-reduction factor"], rows, [1.2, 2.0, 2.0, 1.2]))
order = sorted(range(len(PSA["names"])), key=lambda i: -abs(PSA["prcc_rrf"][i]))
rows = [[PSA["names"][i], n(PSA["prcc_rrf"][i], 2), n(PSA["prcc_full"][i], 2), n(PSA["prcc_baseline"][i], 2)] for i in order]
adds(("table", "Table S14. Partial rank correlation coefficients of the 13 assumed inputs with the logarithm of the risk-reduction factor, of the residual risk of the full layer and of the residual risk of existing checks.", ["Input", "Risk-reduction factor", "Full layer risk", "Existing-checks risk"], rows, [3.0, 1.2, 1.2, 1.2]))
rows2 = [[n(r["readings"]), n(r["sd_ratio_lo"], 3), n(r["sd_ratio_hi"], 3)] for r in PIL["accuracy"]]
adds(("table", "Table S15. 95% interval for the standard deviation of repeated readings, as a multiple of the observed value.", ["Readings", "Lower", "Upper"], rows2, [1.2, 1.2, 1.2]))

# ------------------------------------------------------------------------------------------- S3 reproducibility
adds(("h1", "S3. Reproducibility"))
adds(("p", fmt("The repository (%s, version %s) contains the unchanged first-suite model (HydraSense_MC.py), the extended engine and studies (hydrasense_v2.py), the results (results/original_results.json, results/results_v2.json), the figures, the 12 automated tests (tests/test_all.py) and the manuscript sources. "
               "Commands: python HydraSense_MC.py --reproduce reproduces the first suite; python hydrasense_v2.py --all runs the extended studies (about 4.5 min on one core), python tests/test_all.py runs the tests, python make_schematic.py draws Fig. 1. "
               "The seed of the extended studies is %s; every study uses fixed seeds, so rerunning reproduces every number in the text. The code needs Python 3, numpy, scipy and matplotlib." % (GITHUB, VERSION, X["seed"]))))
