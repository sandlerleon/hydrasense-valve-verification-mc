# -*- coding: utf-8 -*-
"""Supplementary information, part 2: studies added in version 1.1.0 and the complete configuration."""
from common import *

adds(("h1", "S3. Studies added in version 1.1.0"))
CI_ = W["ci"]; SL = W["slipcheck"]
adds(("p", fmt("Sampling uncertainty. <<reps>> independent replications of <<nr>> transfers (common random numbers across architectures within a replication) give a residual risk of <<b>> for existing checks and <<f>> for the full layer, a risk-reduction factor of <<r>> (95% bootstrap interval <<rl>> to <<rh>>) and of <<rs>> (<<rsl>> to <<rsh>>) for direct sensing without NFC; "
               "the relative reduction of residual risk by NFC is <<nf>> (<<nl>> to <<nh>>). Slip check: <<n>> draws of the sensor error for a defect of 15% of stroke give a miss probability of <<mc>> (95% interval <<lo>> to <<hi>>); the closed form without slip is <<cw>> and with slip <<cs>>.",
               reps=str(CI_["reps"]), nr=n(CI_["n_per_rep"]), b=pc(CI_["base"], 3), f=pc(CI_["full"], 3), r=n(CI_["rrf_full"][1], 2), rl=n(CI_["rrf_full"][0], 2), rh=n(CI_["rrf_full"][2], 2), rs=n(CI_["rrf_stem"][1], 2), rsl=n(CI_["rrf_stem"][0], 2), rsh=n(CI_["rrf_stem"][2], 2),
               nf=pc(CI_["stem_minus_full_rel"][1], 1), nl=pc(CI_["stem_minus_full_rel"][0], 1), nh=pc(CI_["stem_minus_full_rel"][2], 1), n=n(SL["n"]), mc=pc(SL["mc"], 3), lo=pc(SL["lo"], 3), hi=pc(SL["hi"], 3), cw=pc(SL["closed_form_without_slip"], 3), cs=pc(SL["closed_form_with_slip"], 3))))
SC = W["sensingcc"]
rows = [[r_["name"]] + [n(d["rrf"], 1) for d in r_["full"]] for r_ in SC["rows"]]
adds(("table", "Table S16. Risk-reduction factor of the full layer against the probability q of a common cause of the sensing layer per validation (existing checks %s; no common cause: %s)." % (pc(SC["base"], 2), n(SC["base"] / SC["nominal_full"]["p"], 1)), ["Scenario"] + ["%g" % q for q in SC["q"]], rows, [3.0] + [0.6] * 7, 14))
TR = W["timeresp"]
rows = [[n(g["kappa"], 1), n(g["rt"], 0), n(g["d_ev"], 0), pc(g["full"]["p"], 3), n(g["rrf"], 1), pc(g["share_event"], 0)] for g in TR["grid"]]
adds(("table", "Table S17. Time-dependent operator response: fatigue coefficient, mean response time (min), median time available after a movement during the transfer (min), residual risk of the full layer, risk-reduction factor and share of the residual risk from movements during the transfer (pre-transfer window 10 min).", ["Fatigue", "Mean response (min)", "Time available (min)", "Residual risk", "Factor", "Share from movements"], rows, [0.8, 1.2, 1.3, 1.2, 0.8, 1.2], 14))
rows = [[pc(r_["resp0"], 0), n(r_["k"], 1), pc(r_["full"], 3), n(r_["rrf"], 1)] for r_ in W["fatigue"]]
adds(("table", "Table S18. Response probability and fatigue coefficient: residual risk of the full layer and risk-reduction factor.", ["Response", "Fatigue coefficient", "Residual risk", "Risk-reduction factor"], rows, [1.0, 1.3, 1.3, 1.5]))
rows = []
for k, v in W["bounds"]["sweeps"].items():
    for x, rr in zip(v["x"], v["rrf"]):
        rows.append([{"bypass": "bypass probability", "response": "response probability", "cc_all": "common-cause probability (each of four)", "comm": "communication-loss probability", "tol": "alarm tolerance"}[k], "%g" % x, n(rr, 1)])
adds(("table", "Table S19. Single-parameter sweeps of the risk-reduction factor (14-valve route, other parameters at base values).", ["Parameter", "Value", "Risk-reduction factor"], rows, [3.0, 1.2, 1.5], 14))
rows = [[pc(r_["d_true"], 0), r_["tol_rule"], pc(r_["tol"], 0), "%s (%s)" % (pc(r_["base"]["p"], 2), ci(r_["base"]["lo"], r_["base"]["hi"], 2)), "%s (%s)" % (pc(r_["full"]["p"], 3), ci(r_["full"]["lo"], r_["full"]["hi"], 3)), n(r_["rrf"], 1), n(r_["fa_per_validation"], 2), pc(r_["miss"], 1)] for r_ in W["threshold"]]
adds(("table", "Table S20. Defect threshold and alarm tolerance (direct sensing plus NFC).", ["Threshold", "Tolerance rule", "Tolerance", "Existing checks", "Full layer", "Factor", "Alarms per validation", "Defects missed"], rows, [0.8, 1.3, 0.8, 1.5, 1.5, 0.7, 0.9, 0.9], 13))
rows = [[r_["design"].split(" (")[0], "%.2f" % r_["rho"], n(r_["deff"], 1), n(r_["n_eff"]), "≤ %d" % r_["accept_max"], pc(r_["power_at_1p4"], 1), pc(r_["risk_at_3"], 1)] for r_ in W["cluster"]]
adds(("table", "Table S21. Clustered pilot (beta-binomial): design effect, effective sample size, acceptance number, power at 1.4% and risk of accepting 3%.", ["Design", "Intraclass correlation", "Design effect", "Effective sample size", "Acceptance number", "Power", "Risk at 3%"], rows, [2.4, 1.0, 0.9, 1.0, 1.0, 0.8, 0.8], 14))
CV = W["coverage"]
rows = [[pc(r_["coverage"], 0), n(r_["realistic"], 2), n(r_["ideal"], 2), n(r_["baseline"], 2), n(r_["events_full"], 2), n(r_["events_baseline"], 2)] for r_ in CV]
adds(("table", "Table S22. Coverage of neighboring valves with a realistic sensor (noise, bias, availability) and with certain detection: undetected collateral events per 1000 transfers.", ["Coverage", "Realistic sensor", "Certain detection", "Existing checks", "Events with NFC", "Events without NFC"], rows, [0.9, 1.2, 1.2, 1.2, 1.2, 1.3]))
EV = W["eventtree"]; A = EV["assumptions"]
rows = [[sc_] + ["%.2f" % x for x in A["pcond"][i]] + [n(1000 * EV["baseline"]["scenario_per_transfer"][i], 2), n(1000 * EV["full"]["scenario_per_transfer"][i], 2)] for i, sc_ in enumerate(A["scenarios"])]
adds(("table", "Table S23. Event tree (all values assumed or illustrative): conditional probabilities of each consequence given each undetected-error scenario, and scenario probabilities per 1000 transfers (half of the neighbors covered).", ["Scenario"] + ["P(" + c_.split(" ")[0] + ")" for c_ in A["consequences"]] + ["Existing checks per 1000", "Full layer per 1000"], rows, [2.6, 0.8, 0.9, 0.8, 0.9, 1.0, 1.0], 13))
rows = [[c_, n(l_)] for c_, l_ in zip(A["consequences"], A["loss"])] + [["Transfers per year N_T", n(A["transfers_per_year"])]]
adds(("table", "Table S24. Assumed losses per consequence (illustrative currency units) and transfers per year.", ["Item", "Value"], rows, [3.6, 1.5]))

adds(("h1", "S4. Configuration, seeds and tests"))
adds(("p", "Seeds: first suite 2026 (300,000 transfers per case, 120,000 per sweep point); extended studies 2026 (hydrasense_v2.py); version 1.1.0 studies 2027 (hydrasense_v3.py: replications 20270 to 20289; common-cause sweeps seed 21, 300,000 transfers per point; time-response seed 31, 200,000; boundaries seed 41, 200,000; "
          "defect threshold seed 51, 300,000; fatigue grid seed 61, 100,000; event tree seed 71, 300,000 per architecture with coverage 0.5 and 4000 draws of the consequence assumptions; second sensitivity analysis 150 draws of 40,000 transfers per case, seeds 7000 to 7149). "
          "Base parameters are those of the Params and Arch classes in HydraSense_MC.py (listed in Table 1 and Section 4); new parameters and defaults are the fields of Params2 in hydrasense_v2.py. Tests: python tests/test_all.py (16 checks; the independent analytic model is tests/independent_check.py)."))
