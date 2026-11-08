# -*- coding: utf-8 -*-
"""Manuscript, part B: Results (Section 5), Discussion (6), Conclusions (7), declarations, references."""
import math

from common import *

ROUTE_NAMES = [("short_6", "6 valves"), ("transfer_14", "14 valves"), ("long_24", "24 valves")]
G = {(r["resp0"], r["k"]): r for r in RESP["grid"]}
TG = {(r["tol_bin"], r["tol_mid"]): r for r in TYP["grid"]}
RZ = {(r["ops"], r["rezero"]): r for r in REZ}
PIL_FA = {r["N"]: r for r in PIL["fa"]}
PIL_MISS = {r["injected"]: r for r in PIL["miss"]}


def tol_curve(r0, k):
    return [r for r in RESP["tol"] if r["resp0"] == r0 and r["k"] == k]


def tol_best(r0, k):
    return min(tol_curve(r0, k), key=lambda r: r["full"]["p"])


# ============================================================================================ 5 Results
add(("h1", "5. Results"))
add(("p", "Sections 5.1 to 5.6 are the base-case results of the first version of the study (single set of assumed inputs); Sections 5.7 to 5.13 are the extended studies. All probabilities are per transfer unless stated, for the 14-valve route unless stated."))
add(("h2", "5.1 Residual risk by architecture"))
se = lambda p, m: math.sqrt(p * (1 - p) / m)
nn = R["meta"]["n"]
d_se = (STEM - FULL) / math.sqrt(se(STEM, nn) ** 2 + se(FULL, nn) ** 2)
add(("p", fmt("For the 14-valve route (Table @T:resid@, Fig. @F:resid@), existing checks alone leave a probability of <<b>> per transfer that an error escapes. A handwheel turn-count collar reduces it to <<t>>, direct stem sensing to <<s>> and direct sensing with NFC identity to <<f>>, "
              "a <<r>>-fold reduction (95% sampling interval <<cl>> to <<ch>>, from 20 independent replications of 150,000 transfers). In the single runs of Table @T:resid@ the difference between direct sensing with and without NFC is <<d>> standard errors and is not resolved; with common random numbers in the replications, NFC lowers the residual risk by <<nf>> (<<nlo>> to <<nhi>>) relative to direct sensing, a small effect that should not be read as establishing the superiority of one architecture and that is small against the input uncertainty of Section 5.7. The NFC benefit appears mainly in prevention (Section 5.5). Absolute values depend on assumed error rates, "
              "but the ratios depend mainly on detection logic and are therefore more robust; Sections 5.7 and 5.17 test how robust.", b=pc(BASE, 2), t=pc(TURN, 2), s=pc(STEM, 2), f=pc(FULL, 2), r=n(RRF0), d=n(d_se, 1), cl=n(W["ci"]["rrf_full"][0], 1), ch=n(W["ci"]["rrf_full"][2], 1), nf=pc(W["ci"]["stem_minus_full_rel"][1], 0), nlo=pc(W["ci"]["stem_minus_full_rel"][0], 1), nhi=pc(W["ci"]["stem_minus_full_rel"][2], 1))))
rows = [[nm] + [pc(P_(rk, a), 3) for a in ("baseline", "turns", "stem", "full")] for rk, nm in ROUTE_NAMES]
add(("table", "Table @T:resid@. Probability per transfer that an error escapes all barriers (%s transfers per cell)." % n(nn), ["Route", "Existing checks", "Turn-count collar", "Direct sensing", "Direct + NFC"], rows, [1.5, 1.2, 1.3, 1.2, 1.2]))
add(("fig", "orig_fig1_architectures.png", "Fig. @F:resid@. Residual risk by architecture and route length.", 4.6))
add(("p", fmt("Residual risk grows with route length for every architecture, from <<a>> for 6 valves to <<b>> for 24 valves with the full layer, because more valves give more opportunities for error and more exposure to device unavailability.",
              a=pc(P_("short_6", "full"), 2), b=pc(P_("long_24", "full"), 2))))

add(("h2", "5.2 Alarm tolerance"))
st, tu = TOLS["stem"], TOLS["turns"]
add(("p", fmt("Alarm tolerance controls the trade-off between nuisance alarms and missed defects (Fig. @F:tol@). With direct sensing at a 5% tolerance, false alarms reach <<fa5>> per valve, equivalent to approximately <<al>> alarms per 14-valve validation, which is unlikely to be acceptable under alarm-management practice, which limits alarm rates to what an operator can handle [@IEC62682]. "
              "At 8%, false alarms drop to <<fa8>> per valve while <<m8>> of true defects are missed, and these misses concentrate in defects only slightly larger than the 0.10 definition. At 10% the miss rate increases to <<m10>>. For the turn collar at 8%, false alarms are <<tfa>> per valve, "
              "approximately four times higher than direct sensing. In the full-layer one-at-a-time analysis, tolerance moved the residual risk from <<lo>> at half the base value to <<hi>> at double, the largest effect of any parameter.",
              fa5=pc(st[0.05][1], 1), al=n(14 * st[0.05][1], 1), fa8=pc(st[0.08][1], 1), m8=pc(st[0.08][2], 1), m10=pc(st[0.1][2], 1), tfa=pc(tu[0.08][1], 1), lo=pc(TOR["alarm tolerance"][0], 2), hi=pc(TOR["alarm tolerance"][1], 2))))
add(("fig", "orig_fig2_tolerance_tradeoff.png", "Fig. @F:tol@. False alarms versus missed defects as alarm tolerance varies; aged curves assume 60 operations since calibration.", 4.6))

add(("h2", "5.3 Calibration age"))
so, to = OPS["stem"], OPS["turns"]
add(("p", fmt("Measurement quality degrades with operations since calibration (Fig. @F:age@). For direct sensing, false alarms rise from <<s1>> per valve at one operation to <<s30>> at 30 and <<s300>> at 300 operations. For the turn collar the corresponding values are <<t1>>, <<t30>> and <<t300>>. "
              "A turn collar is therefore suitable only for short deployments calibrated at every assignment, whereas direct sensing tolerates approximately 100 operations between calibrations (<<s100>> false alarms per valve) and supports longer installations.",
              s1=pc(so[1][1], 1), s30=pc(so[30][1], 1), s300=pc(so[300][1], 1), t1=pc(to[1][1], 1), t30=pc(to[30][1], 1), t300=pc(to[300][1], 1), s100=pc(so[100][1], 1))))
add(("fig", "orig_fig3_calibration_age.png", "Fig. @F:age@. False alarms and missed defects versus operations since calibration.", 4.6))

add(("h2", "5.4 Availability and bypass"))
b20, b0 = COMM["bypass_20"], COMM["bypass_0"]
add(("p", fmt("At the base device unavailability, validation is blocked in <<bl>> of transfers on the 14-valve route and bypass occurs in <<by>> (Fig. @F:avail@). If bypass were prohibited, residual risk would fall to <<r0>> regardless of communication quality in the range studied, "
              "while with 20% bypass it is <<r1>> at the base communication-loss probability of 0.003 and <<r2>> at 0.05. Blocking increases quickly with per-device communication loss, reaching <<b1>> at 0.01. Availability is thus an operational constraint, and bypass policy "
              "determines whether it becomes a safety constraint.", bl=pc(T14["full"]["blocked"]["p"], 1), by=pc(T14["full"]["bypass"]["p"], 1), r0=pc(b0[0.003][2], 2), r1=pc(b20[0.003][2], 2), r2=pc(b20[0.05][2], 2), b1=pc(b20[0.01][1], 0))))
add(("fig", "orig_fig4_availability_bypass.png", "Fig. @F:avail@. Validation blocked and residual risk versus per-device communication loss, with and without bypass.", 4.6))

add(("h2", "5.5 Operator complacency and identity checks"))
add(("p", fmt("If operators relax existing checks because a sensing layer is present, residual risk increases from <<c0>> with no complacency to <<c2>> at 20% and <<c8>> at 80% (Fig. @F:compl@), still far below <<b>> for existing checks alone, because the sensors observe independently. "
              "NFC tap-before-touch addresses a different problem: wrong-valve events, which move a valve that carries no device and are invisible to the sensing layer. At 90% tap compliance, wrong-valve events fall from <<w0>> to <<w9>> per 1000 transfers.",
              c0=pc(COMP[0.0], 3), c2=pc(COMP[0.2], 3), c8=pc(COMP[0.8], 3), b=pc(BASE, 2), w0=n(NFC[0.0], 1), w9=n(NFC[0.9], 1))))
add(("fig", "orig_fig5_complacency_nfc.png", "Fig. @F:compl@. Residual risk versus complacency (left) and wrong-valve events versus NFC tap compliance (right).", 4.6))

add(("h2", "5.6 One-at-a-time sensitivity and device energy"))
add(("p", fmt("In one-at-a-time sensitivity analysis over a factor 0.5 to 2 (Fig. @F:sens@), the ranking by effect on residual risk is alarm tolerance, calibration bias (<<cb0>> to <<cb1>>), the miss rate of existing barriers (<<mb0>> to <<mb1>>) and sensor noise, followed by bypass, availability and complacency. "
              "Operator error rates themselves have smaller effects once the sensing layer is present, because the layer detects defects regardless of how they arise. A design-level energy model (primary lithium cells, wake-on-motion, 16 s heartbeat) gives a median battery life of "
              "<<bm>> years with a 5th to 95th percentile range of <<b5>> to <<b95>> years (Supplementary Information); this must be confirmed by bench measurement.",
              cb0=pc(TOR["calibration bias"][0], 2), cb1=pc(TOR["calibration bias"][1], 2), mb0=pc(TOR["existing-barrier miss rate"][0], 2), mb1=pc(TOR["existing-barrier miss rate"][1], 2), bm=n(BAT["median_y"], 1), b5=n(BAT["p05_y"], 1), b95=n(BAT["p95_y"], 1))))
add(("fig", "orig_fig7_sensitivity.png", "Fig. @F:sens@. One-at-a-time sensitivity of residual risk for the full layer (parameters varied by 0.5 and 2 times).", 4.6))

# ------------------------------------------------------------------------------------------- 5.7 PSA
add(("h2", "5.7 Uncertainty of the assumed inputs"))
nm = PSA["names"]
top = sorted(range(len(nm)), key=lambda i: -abs(PSA["prcc_rrf"][i]))
pq = lambda a, d=2: [n(100 * x, d) for x in a]
add(("p", fmt("Varying the 13 assumed inputs of Table @T:prior@ together (Fig. @F:psa@, Table @T:psa@) gives a median residual risk of <<b>> with existing checks alone (5th to 95th percentile <<b5>> to <<b95>>) and <<f>> with the full layer (<<f5>> to <<f95>>). The risk-reduction factor has a median of <<m>> "
              "with a 5th to 95th percentile range of <<r5>> to <<r95>>; it exceeds 2 in <<g2>> of the draws, 5 in <<g5>> and 10 in <<g10>>. The nominal <<r0>>-fold reduction is exceeded in only <<ex>> of the draws, and the "
              "reduction is better stated as roughly a factor of 10 with a plausible range from 4 to 28 than as a single value. The nuisance-alarm rate has a median of <<fa>> per valve with an upper 95th percentile of <<fa95>>.",
              b=pc(PSA["baseline"][1], 1), b5=pc(PSA["baseline"][0], 1), b95=pc(PSA["baseline"][2], 0), f=pc(PSA["full"][1], 2), f5=pc(PSA["full"][0], 2), f95=pc(PSA["full"][2], 2), m=n(PSA["rrf"][1], 1), r5=n(PSA["rrf"][0], 1), r95=n(PSA["rrf"][2], 0),
              r0=n(RRF0, 0), ex=pc(sum(1 for x in PSA["arrays"]["rrf"] if x > RRF0) / len(PSA["arrays"]["rrf"]), 0), g2=pc(PSA["P_rrf_gt2"], 0), g5=pc(PSA["P_rrf_gt5"], 0), g10=pc(PSA["P_rrf_gt10"], 0), fa=pc(PSA["fa_per_valve"][1], 1), fa95=pc(PSA["fa_per_valve"][2], 1))))
rows = [["Existing checks only", *pq(PSA["baseline"])], ["Direct sensing", *pq(PSA["stem"])], ["Direct sensing + NFC (full layer)", *pq(PSA["full"])], ["Nuisance alarms per valve (full layer)", *pq(PSA["fa_per_valve"])],
        ["Risk-reduction factor (existing / full)", *[n(x, 1) for x in PSA["rrf"]]]]
add(("table", "Table @T:psa@. Probabilistic sensitivity analysis: percentiles of the residual risk per transfer (%%) and of the risk-reduction factor over %s draws of the assumed inputs (40,000 transfers per draw and case)." % n(PSA["ndraw"]), ["Quantity", "5th percentile", "Median", "95th percentile"], rows, [3.0, 1.2, 1.2, 1.2]))
add(("fig", "Fig9_psa.png", "Fig. @F:psa@. Probabilistic sensitivity analysis over the assumed inputs. (a) Distribution of the risk-reduction factor; the dotted line is the median. (b) Residual risk with the sensing layer against existing checks only for each draw; "
                            "the line is no reduction. (c) Partial rank correlation of each input with the logarithm of the risk-reduction factor.", 6.4))
add(("p", fmt("The strongest rank correlations with the risk-reduction factor are the miss rate of the existing barriers (<<c0>>), the sensor calibration bias (<<c1>>), device unavailability (<<c2>>), sensor noise (<<c3>>) and the bypass probability (<<c4>>). The sign has a simple reading: the "
              "more the existing barriers miss, or the more the operators err (<<oe>>), the more the layer adds; the worse the sensing layer performs or the more often it is unavailable or bypassed, the less. Sensor calibration and availability, "
              "which a design can control, are therefore as important to the benefit as the unknown human error rates that the study cannot control. These draws assume that operators always act on an alarm; Section 5.17 relaxes that assumption, with a much lower median.",
              c0=n(PSA["prcc_rrf"][top[0]], 2), c1=n(PSA["prcc_rrf"][top[1]], 2), c2=n(PSA["prcc_rrf"][top[2]], 2), c3=n(PSA["prcc_rrf"][top[3]], 2), c4=n(PSA["prcc_rrf"][top[4]], 2), oe=n(PSA["prcc_rrf"][PRIOR_IDX["operator error rates (x)"]], 2))))
assert [nm[i] for i in top[:5]] == ["existing-barrier miss rate (x)", "sensor calibration bias (x)", "device unavailability (x)", "sensor noise (x)", "bypass probability"], [nm[i] for i in top[:5]]

# ------------------------------------------------------------------------------------------- 5.8 common cause
add(("h2", "5.8 Common-cause variation"))
add(("p", fmt("Making the error rates of a transfer share a lognormal multiplier with mean one changes the per-transfer probability very little (<<s0>> to <<s1>> for existing checks and <<f0>> to <<f1>> for the full layer as the log-standard deviation grows from 0 to 1.5, Fig. @F:resp@a), "
              "and the risk-reduction factor from <<r0>> to <<r1>>. This is expected: a mean-preserving multiplier concentrates errors in fewer transfers but leaves the expected number almost unchanged, and the probability of at least one error is slightly reduced by the concentration. "
              "The independence assumption between valves therefore matters little for the headline probability, though it would matter for the probability of several simultaneous errors, which is not an output of this study.",
              s0=pc(CC[0]["baseline"]["p"], 2), s1=pc(CC[-1]["baseline"]["p"], 2), f0=pc(CC[0]["full"]["p"], 2), f1=pc(CC[-1]["full"]["p"], 2), r0=n(CC[0]["rrf"], 1), r1=n(CC[-1]["rrf"], 1))))

# ------------------------------------------------------------------------------------------- 5.9 response and tolerance
add(("h2", "5.9 Operator response and the choice of tolerance"))
add(("p", fmt("If operators act on only part of the true alarms the benefit decreases quickly (Fig. @F:resp@b gives the effect on the tolerance; the grid is in the Supplementary Information). With a response of 90% to an isolated alarm and no fatigue, the residual risk of the full layer increases from <<a0>> to <<a1>> "
              "and the risk-reduction factor decreases from <<r0>> to <<r1>>; with 80% response and a fatigue coefficient of 0.6 the factor is <<r2>>. A model without a response mechanism assumes a response of 100%; the extended model shows that the first result is the upper end of what a design can claim. "
              "The response also changes the optimum alarm tolerance. With perfect response, residual risk decreases steadily as the tolerance tightens (<<t4>> at 4%), at the price of <<fv4>> nuisance alarms per validation, against <<fv8>> at 8%. With a response of 95% and fatigue coefficients of "
              "0.3 and 0.6, the residual risk has its minimum at a tolerance of <<b1>> of stroke for both coefficients (<<m1>> and <<m2>>), because below it nuisance alarms teach the operator to ignore the true ones and above it defects go unflagged. "
              "The 8% tolerance used in the first version is therefore close to optimal once alarm fatigue is included, but the shallow minimum and the dependence on the assumed response mean that the tolerance should be set by the pilot (Section 5.13).",
              a0=pc(G[(1.0, 0.0)]["full"]["p"], 2), a1=pc(G[(0.9, 0.0)]["full"]["p"], 2), r0=n(G[(1.0, 0.0)]["rrf"], 1), r1=n(G[(0.9, 0.0)]["rrf"], 1), r2=n(G[(0.8, 0.6)]["rrf"], 1),
              t4=pc(tol_curve(1.0, 0.0)[0]["full"]["p"], 2), fv4=n(tol_curve(1.0, 0.0)[0]["fa_per_validation"], 1), fv8=n([r for r in tol_curve(1.0, 0.0) if r["tol"] == 0.08][0]["fa_per_validation"], 2),
              b1=pc(tol_best(0.95, 0.3)["tol"], 0), m1=pc(tol_best(0.95, 0.3)["full"]["p"], 2), m2=pc(tol_best(0.95, 0.6)["full"]["p"], 2))))
assert tol_best(0.95, 0.3)["tol"] == 0.08 and tol_best(0.95, 0.6)["tol"] == 0.08 and tol_best(1.0, 0.0)["tol"] == 0.04
add(("fig", "Fig10_cc_tolerance.png", "Fig. @F:resp@. (a) Common cause: undetected-error probability against the log-standard deviation of the shared multiplier. (b) Residual risk of the full layer against alarm tolerance for perfect and imperfect operator response. "
                                      "(c) Nuisance alarms per validation for direct sensing as the tolerances for binary and intermediate valves are varied separately.", 6.4))

# ------------------------------------------------------------------------------------------- 5.10 per type
add(("h2", "5.10 Separate tolerance for throttled valves"))
add(("p", fmt("With a common tolerance of 8%, the two throttled valves of the route produce <<sh>> of the nuisance alarms: <<fm>> per throttled valve against <<fb>> per binary valve, because the operator's setting scatter (standard deviation 0.04 of stroke) is a large part of the 0.08 band. "
              "Widening the tolerance of the throttled valves alone to 12% cuts the nuisance alarms per validation from <<v0>> to <<v1>> (Fig. @F:resp@c), but it also raises the share of defects that are missed from <<m0>> to <<m1>> and the residual risk of direct sensing from <<k0>> to <<k1>>, "
              "because the defect threshold (0.10 of stroke) lies inside the wider band. The trade-off follows from the definition of a defect: if the process tolerates a wider band on a throttled valve, the defect threshold and the alarm band should be widened together; if it does not, "
              "the nuisance alarms are the cost of detecting a real defect and the design should reduce the setting scatter (a graduated scale, a detent) instead.",
              sh=pc(TYP["base"]["fa_share_mid"], 0), fm=pc(TYP["base"]["fa_mid_per_valve"], 1), fb=pc(TYP["base"]["fa_bin_per_valve"], 1), v0=n(TG[(0.08, 0.08)]["fa_per_validation"], 2), v1=n(TG[(0.08, 0.12)]["fa_per_validation"], 2),
              m0=pc(TG[(0.08, 0.08)]["miss"], 1), m1=pc(TG[(0.08, 0.12)]["miss"], 1), k0=pc(TG[(0.08, 0.08)]["risk"]["p"], 2), k1=pc(TG[(0.08, 0.12)]["risk"]["p"], 2))))

# ------------------------------------------------------------------------------------------- 5.11 re-zero
add(("h2", "5.11 End-stop re-zeroing"))
add(("p", fmt("Re-zeroing a binary valve each time it reaches an end stop removes most of the calibration-age effect for those valves (Fig. @F:rez@a): at 100 operations since calibration the nuisance alarms are <<a1>> per valve with re-zeroing against <<a0>> without, and at 300 operations <<b1>> against <<b0>>. "
              "The throttled valves cannot be re-zeroed at an end stop, so the benefit is partial, and the share of missed defects is almost unchanged (<<m1>> against <<m0>> at 300 operations). The first version could only conjecture this benefit.",
              a0=pc(RZ[(100, False)]["fa_per_valve"], 1), a1=pc(RZ[(100, True)]["fa_per_valve"], 1), b0=pc(RZ[(300, False)]["fa_per_valve"], 1), b1=pc(RZ[(300, True)]["fa_per_valve"], 1), m0=pc(RZ[(300, False)]["miss"], 1), m1=pc(RZ[(300, True)]["miss"], 1))))

# ------------------------------------------------------------------------------------------- 5.12 collateral
add(("h2", "5.12 Coverage of neighboring valves"))
add(("p", fmt("A wrong-valve action that moves a neighbor without a device is invisible to the layer unless the neighbor is covered. With the NFC tap-before-touch check the layer already cuts the collateral events from <<e0>> to <<e1>> per 1000 transfers, and without any device on the neighbors the undetected events are "
              "<<u0>> per 1000 (existing checks alone: <<ub>>). The undetected events decrease in proportion to the coverage (Fig. @F:rez@c) and almost vanish when every neighbor carries a device (<<u1>>). Coverage of neighbors is therefore a design choice with a quantifiable return, and a partial coverage, "
              "for example of the valves adjacent to the route, removes a proportional part.", e0=n(COL[0]["baseline_events_per_1000"], 1), e1=n(COL[0]["events_per_1000"], 1), u0=n(COL[0]["full_per_1000"], 2), ub=n(COL[0]["baseline_per_1000"], 2), u1=n(COL[-1]["full_per_1000"], 2))))
add(("fig", "Fig11_rezero_pilot_collateral.png", "Fig. @F:rez@. (a) False alarms against operations since calibration with and without end-stop re-zeroing. (b) Pilot sizing for nuisance alarms: power at the modeled rate and risk of accepting an unacceptable rate. "
                                                 "(c) Undetected collateral events against the fraction of neighboring valves that carry a device.", 6.4))

# ------------------------------------------------------------------------------------------- 5.13 pilot
add(("h2", "5.13 Pilot sizing and acceptance criteria"))
rows = [[n(r["N"]), "≤ %d" % r["accept_max"], pc(r["power_at_1p4"], 0), pc(r["consumer_risk_at_3"], 1), pc(r["upper95_at_expected"], 1)] for r in PIL["fa"]]
add(("p", fmt("Table @T:pilot@ gives exact binomial acceptance numbers for the nuisance-alarm rate. A pilot of 1000 valves with an acceptance number of <<c>> has a power of <<pw>> at the modeled 1.4% and a risk of <<cr>> of accepting a device whose true rate is 3%; smaller pilots cannot separate the two "
              "(100 to 200 valves have a power below <<p2>>), and the extra information of more than 2000 valves is small. A pilot on one route therefore needs approximately 1000 valve validations, which at 14 valves per validation is approximately 70 transfers, or the same valves validated repeatedly across several routes.",
              c=str(PIL_FA[1000]["accept_max"]), pw=pc(PIL_FA[1000]["power_at_1p4"], 0), cr=pc(PIL_FA[1000]["consumer_risk_at_3"], 1), p2=pc(PIL_FA[200]["power_at_1p4"], 0))))
add(("table", "Table @T:pilot@. Pilot acceptance test for the nuisance-alarm rate: accept if the number of nuisance alarms among the N validated valves is at most the acceptance number (consumer risk 5% at a true rate of 3%).", ["Valves validated N", "Acceptance number", "Power at a true rate of 1.4%", "Risk of accepting a true rate of 3%", "Upper 95% limit if 1.4% is observed"], rows, [1.1, 1.1, 1.4, 1.4, 1.5]))
rows = [[n(r["injected"]), "≤ %d" % r["accept_max"] if r["accept_max"] >= 0 else "none", pc(r["power_at_6"], 0)] for r in PIL["miss"]]
acc = {r["readings"]: r for r in PIL["accuracy"]}
add(("p", fmt("For missed defects, the injected-defect test of Table @T:miss@ needs approximately <<i1>> deliberately misplaced valves to demonstrate a miss rate below 15% with a power of <<p1>> at the modeled 6% (<<i2>> valves give <<p2>>). The accuracy of the device is shown by repeated readings of a valve held at a known position: "
              "with 100 readings the 95% interval for the standard deviation is <<lo>> to <<hi>> times the observed value, with 500 readings <<lo5>> to <<hi5>>.",
              i1=str(80), p1=pc(PIL_MISS[80]["power_at_6"], 0), i2=str(150), p2=pc(PIL_MISS[150]["power_at_6"], 0), lo=n(acc[100]["sd_ratio_lo"], 2), hi=n(acc[100]["sd_ratio_hi"], 2), lo5=n(acc[500]["sd_ratio_lo"], 2), hi5=n(acc[500]["sd_ratio_hi"], 2))))
add(("table", "Table @T:miss@. Pilot acceptance test for missed defects: injected defects detected or missed (consumer risk 5% at a true miss rate of 15%).", ["Defects injected", "Accept if misses", "Power at a true miss rate of 6%"], rows, [1.5, 1.5, 2.0]))

