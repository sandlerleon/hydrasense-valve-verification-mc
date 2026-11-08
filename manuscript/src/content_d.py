# -*- coding: utf-8 -*-
"""Manuscript, part D: Discussion (Section 6), Conclusions (7), declarations, references."""
import math

from common import *

G = {(r["resp0"], r["k"]): r for r in RESP["grid"]}
PIL_FA = {r["N"]: r for r in PIL["fa"]}

# ============================================================================================ 6 Discussion
P2 = W["psa2"]; BD = W["bounds"]["bounds"]; EV = W["eventtree"]; CL = {(r["design"].split(" (")[0], r["rho"]): r for r in W["cluster"]}
add(("h1", "6. Discussion"))
add(("p", fmt("Five findings are useful for specification. First, the headline reduction should be quoted as a distribution and as conditional on operators acting on the alarms, not as the nominal <<r0>>-fold. With the operator always responding the median is <<m1>> (plausible range <<lo1>> to <<hi1>>); with uncertain response, fatigue and common cause it is <<m2>> (<<lo2>> to <<hi2>>), "
              "and a mean response time of 10 min against a window of 20 min leaves a factor of about 2. The benefit is a property of the whole layer, sensor plus people plus procedure, and a pilot must measure the response, not only the sensor (H1 holds across the sensor and human-error ranges, but its size depends on the response). "
              "Second, alarm tolerance has an interior optimum once alarm fatigue is included (H2): 8% with two-point calibration at every assignment keeps nuisance alarms near 1% per valve with direct sensing; end-stop re-zeroing of binary valves removes most of the dependence on calibration age; throttled valves need their own, explicitly derived band; "
              "and the defect threshold itself, which changes the factor by an order of magnitude between 5% and 15%, must be set per valve from the consequences. Third, the boundaries of H3 are concrete: a factor of 10 needs a response of at least <<r10>>, bypass below <<b10>> and a common-cause probability below <<c10>>, and a factor of 5 still needs a response of at least <<r5>>. "
              "On-site calibration quality, availability, bypass policy and fail-safe blocking of outages, not the radio technology, govern what the sensors contribute. Fourth, the common causes differ in kind: an outage that blocks the transfer costs time but not protection, an ignored outage erodes it slowly, and systematic wrong identification is the most damaging, which supports the NFC assignment check and a validation that the assignments match the procedure. "
              "Fifth, a pilot with the clustering that real validations have needs more valves than repeats: 1000 validations from 12 valves have a power of <<p5>> at an intraclass correlation of 0.05, against <<p0>> if validations were independent.",
              r0=n(RRF0, 0), m1=n(PSA["rrf"][1], 1), lo1=n(PSA["rrf"][0], 1), hi1=n(PSA["rrf"][2], 0), m2=n(P2["rrf"][1], 1), lo2=n(P2["rrf"][0], 1), hi2=n(P2["rrf"][2], 1), r10=pc(BD["10"]["response_min"], 0), b10=pc(BD["10"]["bypass_max"], 0), c10=pc(BD["10"]["cc_all_max"], 1), r5=pc(BD["5"]["response_min"], 0),
              p5=pc(CL[("12 valves x 83 validations", 0.05)]["power_at_1p4"], 0), p0=pc(CL[("12 valves x 83 validations", 0.0)]["power_at_1p4"], 0))))
add(("p", "The comparison of the two sensing concepts supports sensing at the stem or indicator where this is mechanically feasible. The turn collar remains attractive where only the handwheel is accessible, but the simulation indicates it needs recalibration at nearly every assignment and a wider tolerance."))
add(("h2", "6.1 Position relative to layer-of-protection practice"))
add(("p", "A protection layer is credited in layer-of-protection analysis only when it is independent of the initiating event and of other layers, specific, dependable and auditable [@CCPS2015]. The sensing layer is independent of the operator's report by construction, and its time-stamped record "
          "is auditable. It is not dependable in the required sense until its availability, accuracy, common-cause behavior and the response time of the people who act on it have been measured; the study shows that these are the parameters that decide the benefit. The layer is therefore proposed as an advisory "
          "barrier whose value is to be demonstrated by a pilot with the acceptance criteria of Section 5.13, and not as a credited independent protection layer or a safety instrumented function. Table @T:claims@ keeps the status of each claim explicit."))
add(("table", "Table @T:claims@. Claims and their support.", ["Claim", "Support in this paper"],
     [["The modeled architecture reduces undetected errors under assumed conditions", "Supported by the simulations"], ["Alarm response, response time and tolerance materially change the modeled benefit", "Supported by the sensitivity, time-response and boundary analyses"],
      ["A given pilot size can test chosen thresholds", "Supported conditionally by the binomial and beta-binomial assumptions"], ["The hardware will reach the assumed measurement accuracy", "Not demonstrated"],
      ["The system reduces actual accident frequency", "Not demonstrated; the event tree is illustrative"], ["The system qualifies as a credited independent protection layer", "Not demonstrated"]], [3.8, 3.2]))
add(("h2", "6.2 Limitations"))
add(("p", "The study has important limitations. (i) All input probabilities, the consequence probabilities and the losses are assumed. The probabilistic sensitivity analyses propagate the uncertainty of the input ranges, but the ranges are themselves assumptions, and human-error rates, existing-barrier detection and valve behavior at a real facility "
          "may differ by more than the factors used. (ii) Common cause of the operator error rates is a shared multiplier, and common cause of the sensing layer is represented by four scenarios with assumed probabilities; other dependencies (a shared firmware fault, a shared mounting error, correlated environmental conditions) are not modeled. "
          "(iii) The operator-response models are parametric descriptions with assumed coefficients, not fitted models; the exponential response time is illustrative, and the alarm during pumping and the pre-transfer alarm are the only two windows considered. "
          "(iv) The event tree is a simplified single-level tree with assumed conditional probabilities; it does not model the process hydraulics of any specific route, and the defect threshold of 10% of stroke is a convention. (v) Detection of out-of-sequence steps is represented by a single probability rather than a full procedure model. "
          "(vi) Security, electromagnetic and mechanical failure modes, hazardous-area certification and the installation effort were not simulated. (vii) The device concept has not been built or tested, and the battery estimate is analytical. "
          "(viii) The literature cited for the human-reliability and incident background was checked for existence and bibliographic data, not read in full for each statement; this must be completed before submission."))
add(("h2", "6.3 Relation to existing practice and future work"))
add(("p", "Permanent position transmitters and limit switches provide equivalent information at higher installation cost per valve, and they are the natural choice for valves on critical lines that are operated frequently. The temporary, reassignable layer studied here addresses the complementary case "
          "of many manual valves that matter only on some routes or during some operations. The next step is the pilot of Section 5.13, which measures sensor accuracy, nuisance alarms, availability, installation time, the intraclass correlation of the validations and the operator's action and its delay on every alarm, replaces the assumed inputs with data "
          "and allows the model to be calibrated; the sensitivity analyses can then be rerun with posterior distributions and with a consequence analysis of the actual route."))

# ============================================================================================ 7 Conclusions
add(("h1", "7. Conclusions"))
add(("p", fmt("The size of the benefit of an independent sensing layer on existing manual valves depends on the operators' response more than on the sensors. With assumed inputs and operators who always act on the alarms, the modeled probability of an undetected misalignment or unauthorized movement per transfer falls from <<b>> to <<f>> on a 14-valve route (<<r0>>-fold), "
              "and by a median factor of <<m1>> when the uncertainty of the inputs is propagated; when the response of the operators, alarm fatigue and common-cause failures of the sensing layer are also uncertain, the median factor is <<m2>> (5th to 95th percentile <<lo2>> to <<hi2>>). "
              "A factor of 10 needs a response of at least <<r10>>, bypass below <<b10>> and a common-cause probability below <<c10>>; fail-safe blocking neutralizes gateway outages, and wrong valve identification is the most damaging common cause. An illustrative event tree translates the detection reduction into a <<e>>-fold reduction in expected loss under assumed consequence probabilities. "
              "Direct stem sensing outperforms handwheel turn counting in false alarms and in robustness to calibration age; an alarm tolerance near 8% of stroke, end-stop re-zeroing, a separate band and an explicit defect threshold for throttled valves, spare availability and no unrecorded bypass are the main design levers. "
              "A pilot needs about 1000 validated valves from more valves rather than more repeats, with an acceptance number set for the clustering observed, and an injected-deviation test with logged operator actions and delays. The layer cannot be credited as a quantified protection layer before that.",
              b=pc(BASE, 2), f=pc(FULL, 2), r0=n(RRF0, 0), m1=n(PSA["rrf"][1], 1), m2=n(P2["rrf"][1], 1), lo2=n(P2["rrf"][0], 1), hi2=n(P2["rrf"][2], 1), r10=pc(BD["10"]["response_min"], 0), b10=pc(BD["10"]["bypass_max"], 0), c10=pc(BD["10"]["cc_all_max"], 1), e=n(EV["full"]["rrf_eal"], 0))))

# ============================================================================================ declarations
add(("h1", "Declaration of competing interest"))
add(("p0", "The author has prepared a related commercial proposal in response to a public open-innovation challenge concerning real-time verification of manual valve position and may benefit commercially from the concept described. The author has no other competing interests."))
add(("h1", "Funding"))
add(("p0", "This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors."))
add(("h1", "CRediT authorship contribution statement"))
add(("p0", "Leon Sandler: Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Visualization, Writing – original draft, Writing – review and editing."))
add(("h1", "Data availability"))
add(("p0", "The simulation code, the data behind every figure and table, the automated tests and the manuscript sources (version %s) are archived at https://doi.org/%s (software, all versions) and https://doi.org/%s (manuscript, all versions), and are available at %s. The study uses no field data." % (VERSION, DOIS["code_concept"], DOIS["paper_concept"], GITHUB)))
add(("h1", "Declaration of generative AI and AI-assisted technologies in the writing process"))
add(("p0", "During the preparation of this work the author used Claude (Anthropic) to assist with drafting text, writing and testing simulation code and generating figures from that code. After using this tool, the author reviewed and edited the content as needed and takes full responsibility for the content of the publication."))
add(("refs",))
