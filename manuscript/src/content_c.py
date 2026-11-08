# -*- coding: utf-8 -*-
"""Manuscript, part C: results added in version 1.1.0 (Sections 5.13 continued, 5.14-5.19)."""
from common import *

SC, TR, BD, TH, EV, P2, CL, FT = W["sensingcc"], W["timeresp"], W["bounds"], W["threshold"], W["eventtree"], W["psa2"], W["cluster"], W["fatigue"]
SCN = {r["name"]: r for r in SC["rows"]}
QI = {q: i for i, q in enumerate(SC["q"])}
TRG = {(r["kappa"], r["rt"], r["d_ev"]): r for r in TR["grid"]}
rrf2 = P2["arrays"]["rrf"]
frac_lt1 = sum(1 for x in rrf2 if x < 1) / len(rrf2)
CLU = {(r["design"].split(" (")[0], r["rho"]): r for r in CL}
D12, D30, D71 = "12 valves x 83 validations", "30 valves x 33 validations", "71 transfers x 14 valves"

# ------------------------------------------------------------------------------------------- 5.13 continued: clustering
add(("p", fmt("The binomial tests assume that validations are independent. Validations of the same valve share its device, mount and calibration, and validations of the same transfer share its operator and conditions, so nuisance alarms are clustered. With an intraclass correlation $ρ$ and $m$ validations per cluster the effective sample size is "
              "$N/(1+(m-1)ρ)$, and a beta-binomial model gives the acceptance number and power that keep the 5% consumer risk (Table @T:clu@). With 12 valves of 83 validations each, an intraclass correlation of 0.05 cuts the effective sample size from approximately 1000 to <<ne>> and the power at the modeled 1.4% from <<p0>> to <<p5>>; "
              "30 valves of 33 validations keep <<p30>>, and clusters formed by 71 transfers keep <<p71>>. A pilot is therefore better served by more valves than by more repetitions of the same few, and its first task is to estimate the intraclass correlation, which is unknown. "
              "Valves validated, validation events and transfers are different sampling units: a validation event is one line-up check of a route, it contains one validation of each valve of the route, and a transfer may contain more than one validation event; in this paper a transfer has one validation event unless stated.",
              ne=n(CLU[(D12, 0.05)]["n_eff"]), p0=pc(CLU[(D12, 0.0)]["power_at_1p4"], 0), p5=pc(CLU[(D12, 0.05)]["power_at_1p4"], 0), p30=pc(CLU[(D30, 0.05)]["power_at_1p4"], 0), p71=pc(CLU[(D71, 0.05)]["power_at_1p4"], 0))))
rows = [[d, "%.2f" % r, n(CLU[(d, r)]["n_eff"]), "≤ %d" % CLU[(d, r)]["accept_max"], pc(CLU[(d, r)]["power_at_1p4"], 0), pc(CLU[(d, r)]["risk_at_3"], 1)] for d in (D12, D30, D71) for r in (0.0, 0.02, 0.05, 0.10)]
add(("table", "Table @T:clu@. Pilot acceptance test for nuisance alarms when validations are clustered (beta-binomial; approximately 1000 validations; consumer risk at most 5% at a true rate of 3%).", ["Design (clusters)", "Intraclass correlation", "Effective sample size", "Acceptance number", "Power at 1.4%", "Risk at 3%"], rows, [2.6, 1.1, 1.1, 1.1, 1.0, 0.9], 15))

# ------------------------------------------------------------------------------------------- 5.14 sensing common cause
add(("h2", "5.14 Common-cause failures of the sensing layer"))
g, gf, hi_, idn, cal, al, alf = (SCN[k] for k in ("gateway outage, ignored", "gateway outage, fail-safe blocking", "historian failure, ignored", "wrong valve identification", "calibration procedure error", "all four, outages ignored", "all four, fail-safe blocking"))
r = lambda row, q: n(row["full"][QI[q]]["rrf"], 1)
add(("p", fmt("The independence of the sensing layer from the operator does not make its devices independent of each other. Four common causes were simulated (Fig. @F:cc3@b), each with a probability $q$ per validation from $10^{-4}$ to $10^{-1}$: an outage of the gateway or of the historian and route-validation service, which makes validation unavailable for all devices at once; "
              "wrong valve identification, a systematic shift of all device assignments by one valve; and a calibration procedure error, a shared systematic bias (standard deviation 0.06 of stroke) on all devices of the transfer. An outage that is ignored (the operator proceeds as in the bypass of Section 5.4, probability 0.20) and an outage that blocks the transfer (fail-safe) are distinguished. "
              "At $q=10^{-2}$ the risk-reduction factor is <<g2>> for an ignored gateway outage, <<i2>> for incorrect identification and <<c2>> for a calibration error, against <<n0>> without common cause; at $q=10^{-1}$ it decreases to <<g3>>, <<i3>> and <<c3>>. Fail-safe blocking removes the effect of outages entirely (<<f3>> at $q=10^{-1}$) at the price of delayed transfers in a fraction $q$ of validations. "
              "All four causes together at $q=10^{-2}$ give <<a2>> if outages are ignored and <<af2>> with blocking, and at $q=10^{-1}$ <<a3>> and <<af3>>. Incorrect identification is the most damaging single cause, because it produces both missed defects and nuisance alarms; it is the failure that the NFC assignment check is meant to prevent.",
              g2=r(g, 1e-2), i2=r(idn, 1e-2), c2=r(cal, 1e-2), n0=n(BASE / FULL, 1), g3=r(g, 1e-1), i3=r(idn, 1e-1), c3=r(cal, 1e-1), f3=r(gf, 1e-1), a2=r(al, 1e-2), af2=r(alf, 1e-2), a3=r(al, 1e-1), af3=r(alf, 1e-1))))

# ------------------------------------------------------------------------------------------- 5.15 time-dependent response
add(("h2", "5.15 Time-dependent operator response"))
add(("p", fmt("A response probability ignores when the operator acts. In a time-dependent model the response time to an isolated alarm is exponential with mean $m$ (an illustrative distribution, not an empirical operator model), multiplied by $\\exp(κF)$ for $F$ nuisance alarms in the validation. Alarms of the pre-transfer validation have 10 min before pump start; "
              "after a movement during the transfer the time before a consequence develops is lognormal with a median of 5 to 40 min (log-standard deviation 0.7), and an alarm acted on after that time is not a barrier. With a mean response time of 1 min the risk-reduction factor is <<a1>> to <<b1>> (shortest to longest time available), "
              "with 3 min <<a3>> to <<b3>>, with 10 min <<a10>> to <<b10>> and with 20 min <<a20>> to <<b20>>, against <<pm>> for the probability model with certain response (Fig. @F:cc3@c). "
              "The benefit therefore depends on the response time relative to the time available much more than on the sensor. The alarm design must put the information in front of someone who can act within minutes, and the pre-transfer validation, which gives a long window, is the more robust use of the layer than the alarm during pumping.",
              a1=n(TRG[(0.0, 1.0, 5.0)]["rrf"], 1), b1=n(TRG[(0.0, 1.0, 40.0)]["rrf"], 1), a3=n(TRG[(0.0, 3.0, 5.0)]["rrf"], 1), b3=n(TRG[(0.0, 3.0, 40.0)]["rrf"], 1), a10=n(TRG[(0.0, 10.0, 5.0)]["rrf"], 1), b10=n(TRG[(0.0, 10.0, 40.0)]["rrf"], 1),
              a20=n(TRG[(0.0, 20.0, 5.0)]["rrf"], 1), b20=n(TRG[(0.0, 20.0, 40.0)]["rrf"], 1), pm=n(TR["probability_model_rrf"], 1))))
FG = {(r["resp0"], r["k"]): r["rrf"] for r in FT}
add(("p", fmt("Because the alarm-fatigue parameters are assumed, the response probability (0.7 to 1.0) and fatigue coefficient (0 to 1.0) were varied on a grid (Supplementary Information). The risk-reduction factor is <<a>> at a response of 1.0 and no fatigue, <<b>> at 0.9 and no fatigue, <<c>> at 0.9 and a coefficient of 1.0, and <<d>> at 0.7 and no fatigue. "
              "In a pilot these parameters can be estimated rather than assumed: every injected deviation (Section 5.13) is an alarm to which the operator's action and its delay are recorded, so that 80 injections give the response probability to about ±8 percentage points (Wilson interval at 0.9), and regression of the logged action on the number of nuisance alarms in the same validation estimates the fatigue coefficient.",
              a=n(FG[(1.0, 0.0)], 1), b=n(FG[(0.9, 0.0)], 1), c=n(FG[(0.9, 1.0)], 1), d=n(FG[(0.7, 0.0)], 1))))
add(("fig", "Fig12_eventtree_cc_time.png", "Fig. @F:cc3@. (a) Consequences per 1000 transfers of the undetected errors, from the illustrative event tree of Section 5.19. (b) Risk-reduction factor against the probability of a common cause of the sensing layer (dotted line: factor 5). "
                                           "(c) Risk-reduction factor against the mean operator response time for different times available before a consequence develops.", 6.5))

# ------------------------------------------------------------------------------------------- 5.16 defect threshold
add(("h2", "5.16 Sensitivity to the defect threshold"))
THR = {(r["d_true"], r["tol_rule"]): r for r in TH}
rows = [[pc(d, 0), pc(THR[(d, t)]["tol"], 0), "%s" % pc(THR[(d, t)]["base"]["p"], 1), pc(THR[(d, t)]["full"]["p"], 2), n(THR[(d, t)]["rrf"], 1), n(THR[(d, t)]["fa_per_validation"], 2)] for d in (0.05, 0.10, 0.15, 0.20) for t in ("fixed 8%", "0.8 x threshold") if not (d == 0.10 and t != "fixed 8%")]
add(("p", fmt("The 10%-of-stroke threshold that defines a defect is not a hazardous valve position; it is a convention that a plant would replace by the deviation that matters for its piping. Varying it (Table @T:thr@) shows that the risk-reduction factor is a property of the pair of defect threshold and alarm tolerance. With a threshold of 5% an 8% tolerance cannot detect the defects and the factor is <<a>>; "
              "a tolerance of 4% restores <<b>> but gives <<c>> nuisance alarms per validation. With thresholds of 15% and 20% the factor is <<d>> and <<e>> at 8% tolerance with few nuisance alarms. The threshold, and the tolerance derived from it, must therefore be set per valve from a consequence analysis (for example how far a valve can be off before the line is hydraulically wrong), "
              "and the results of this paper for the 10% case should not be transferred to other thresholds.",
              a=n(THR[(0.05, "fixed 8%")]["rrf"], 1), b=n(THR[(0.05, "0.8 x threshold")]["rrf"], 1), c=n(THR[(0.05, "0.8 x threshold")]["fa_per_validation"], 1), d=n(THR[(0.15, "fixed 8%")]["rrf"], 0), e=n(THR[(0.20, "fixed 8%")]["rrf"], 0))))
add(("table", "Table @T:thr@. Defect threshold and alarm tolerance: probability of an undetected error with existing checks and with the full layer, risk-reduction factor and nuisance alarms per validation (14-valve route).", ["Defect threshold", "Alarm tolerance", "Existing checks", "Full layer", "Risk-reduction factor", "Nuisance alarms per validation"], rows, [1.1, 1.1, 1.1, 1.0, 1.2, 1.4], 15))

# ------------------------------------------------------------------------------------------- 5.17 PSA 2
add(("h2", "5.17 Uncertainty including operator response and common cause"))
nm2 = P2["names"]; top2 = sorted(range(len(nm2)), key=lambda i: -abs(P2["prcc_rrf"][i]))
add(("p", fmt("Section 5.7 varied the inputs with the operator always responding. Repeating it with the response probability uniform between 0.7 and 1.0, the fatigue coefficient uniform between 0 and 1.0 and a common-cause probability, the same for the four sensing-layer causes, log-uniform between $10^{-4}$ and $10^{-1.5}$ (<<nd>> draws, Fig. @F:bnd@b) gives a median risk-reduction factor of <<m>> "
              "with a 5th to 95th percentile range of <<lo>> to <<hi>>; it exceeds 2 in <<g2>> of the draws and 5 in <<g5>>, and in <<l1>> of the draws the layer does not reduce the risk at all (factor below 1), because relaxed existing checks are then not compensated by alarms that are acted on. "
              "The operator's response to the alarm is now the strongest driver (rank correlation <<c0>>), ahead of the miss rate of the existing barriers (<<c1>>) and the sensor calibration bias (<<c2>>). The assumed ranges are pessimistic on purpose and are not data; "
              "the contrast with the median of Section 5.7 is the finding. A claim of order-of-magnitude risk reduction rests on operators who act on the alarm, and it cannot be separated from the human-factors design of the alarm.",
              nd=n(P2["ndraw"]), m=n(P2["rrf"][1], 1), lo=n(P2["rrf"][0], 1), hi=n(P2["rrf"][2], 1), g2=pc(P2["P_rrf_gt2"], 0), g5=pc(P2["P_rrf_gt5"], 0), l1=pc(frac_lt1, 0), c0=n(P2["prcc_rrf"][top2[0]], 2), c1=n(P2["prcc_rrf"][top2[1]], 2), c2=n(P2["prcc_rrf"][top2[2]], 2))))
assert nm2[top2[0]] == "operator response to an isolated alarm"

# ------------------------------------------------------------------------------------------- 5.18 boundaries
add(("h2", "5.18 Boundaries of the benefit"))
B5, B10 = BD["bounds"]["5"], BD["bounds"]["10"]
f2 = lambda x, d=2: "none within the range studied" if x is None else n(x, d)
rows = [["Probability of proceeding without validation (bypass), at most", f2(B5["bypass_max"]), f2(B10["bypass_max"])], ["Response to an alarm, at least", n(B5["response_min"], 2), n(B10["response_min"], 2)],
        ["Common-cause probability of the sensing layer (each of four, outages ignored), at most", n(B5["cc_all_max"], 3), n(B10["cc_all_max"], 3)], ["Communication-loss probability per device, at most", n(B5["comm_max"], 3), n(B10["comm_max"], 3)]]
add(("p", fmt("From sweeps of single parameters with the others at their base values (Fig. @F:bnd@a), the largest bypass probability, the smallest response probability and the largest common-cause and communication-loss probabilities that keep the risk-reduction factor at or above a required value are given in Table @T:bnd@. "
              "A factor of 5 survives complete bypass (the factor is still <<bp>> if every blocked validation is bypassed) but needs a response of at least <<r5>> and a common-cause probability below <<c5>>; a factor of 10 needs a response of at least <<r10>>, bypass below <<b10>>, a common-cause probability below <<c10>> and a communication-loss probability below <<m10>>. "
              "These boundaries are conditional on the other parameters and on the assumed model, but they translate the abstract claim of independence into conditions that a plant can check: how often devices are unavailable, whether an unavailable device may be bypassed, and how quickly alarms are acted on.",
              bp=n(BD["sweeps"]["bypass"]["rrf"][-1], 1), r5=n(B5["response_min"], 2), c5=n(B5["cc_all_max"], 2), r10=n(B10["response_min"], 2), b10=n(B10["bypass_max"], 2), c10=n(B10["cc_all_max"], 3), m10=n(B10["comm_max"], 3))))
add(("table", "Table @T:bnd@. Boundaries for a required risk-reduction factor (single-parameter sweeps, 14-valve route, other parameters at base values).", ["Condition", "Factor of at least 5", "Factor of at least 10"], rows, [4.2, 1.5, 1.5]))
add(("fig", "Fig13_bounds_psa2_cluster.png", "Fig. @F:bnd@. (a) Risk-reduction factor against the bypass probability and against the response probability (dotted lines: factors 5 and 10). (b) Distribution of the risk-reduction factor with response and common cause varied with the other inputs. "
                                             "(c) Power of the nuisance-alarm acceptance test at the modeled 1.4% when validations are clustered, against the intraclass correlation.", 6.5))

# ------------------------------------------------------------------------------------------- 5.19 consequences
add(("h2", "5.19 Consequence-based illustration"))
cons = ["benign", "contamination", "overflow", "overpressure"]
rows = []
for j, nm_ in enumerate(EV["assumptions"]["consequences"]):
    b_, f_ = EV["baseline"]["cons_per_transfer"][j] * 1000, EV["full"]["cons_per_transfer"][j] * 1000
    rows.append([nm_, n(b_, 2), n(f_, 2), n(b_ / f_, 1)])
rows.append(["Expected annual loss, %s transfers per year (illustrative units)" % n(EV["assumptions"]["transfers_per_year"]), n(EV["baseline"]["eal"] / 1e6, 2) + " M", n(EV["full"]["eal"] / 1e6, 2) + " M", n(EV["full"]["rrf_eal"], 1)])
U = EV["uncertainty"]
add(("p", fmt("An undetected valve error is not an accident. To connect the detection results to consequences, each undetected-error scenario $E_i$ (a required-open valve left closed or partly closed, a required-closed valve left open or partly open, an out-of-sequence step, a movement after validation, a collateral movement of a neighbor with half the neighbors covered) was assigned "
              "assumed conditional probabilities $P(C_j\\mid E_i)$ of four consequences $C_j$ (benign or recoverable, product contamination or misrouting, tank overflow or release, blocked-in or overpressure) and an assumed loss $L_j$, so that $P(C_j)=Σ_i P(E_i)P(C_j\\mid E_i)$ and the expected annual loss is $N_T Σ_j P(C_j) L_j$ for $N_T$ = <<nt>> transfers per year (Supplementary Information lists all assumptions). "
              "These numbers are illustrative, chosen to show the method; they are not accident frequencies or costs. With them (Table @T:cons@, Fig. @F:cc3@a) the full layer reduces the consequence probabilities by factors of <<c1>> (contamination), <<c2>> (overflow) and <<c3>> (overpressure), and the expected annual loss by <<e>>. "
              "When the conditional probabilities of the hazardous consequences and the losses are varied by lognormal factors with a 90% factor of 3 (<<nd>> draws), the reduction in expected loss has a median of <<em>> (5th to 95th percentile <<elo>> to <<ehi>>); this range covers only the consequence assumptions and not the input uncertainty of Sections 5.7 and 5.17, which would be multiplied onto it. "
              "The reduction in expected loss is similar to the reduction in detection probability because the layer acts on all scenarios in a similar proportion; the absolute figures depend entirely on the assumed matrix, and the method is the contribution.",
              nt=n(EV["assumptions"]["transfers_per_year"]), c1=n(EV["full"]["rrf_cons"][1], 1), c2=n(EV["full"]["rrf_cons"][2], 1), c3=n(EV["full"]["rrf_cons"][3], 1), e=n(EV["full"]["rrf_eal"], 1), nd=n(U["draws"]), em=n(U["rrf_eal"][1], 1), elo=n(U["rrf_eal"][0], 1), ehi=n(U["rrf_eal"][2], 1))))
add(("table", "Table @T:cons@. Illustrative consequence-based assessment (assumed conditional probabilities and losses): undetected-error consequences per 1000 transfers and expected annual loss, existing checks and full layer.", ["Consequence", "Existing checks", "Full layer", "Reduction factor"], rows, [3.4, 1.3, 1.3, 1.2]))
