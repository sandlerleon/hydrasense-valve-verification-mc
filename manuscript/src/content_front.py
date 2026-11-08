# -*- coding: utf-8 -*-
"""Manuscript front matter: title, author, highlights, abstract, keywords."""
from common import *

G = {(r["resp0"], r["k"]): r for r in RESP["grid"]}
add(("title", TITLE))
add(("author", "Leon Sandler"))
add(("small", "Independent Researcher, Northbrook, Illinois, USA"))
add(("small", "ORCID: https://orcid.org/0009-0007-4584-808X"))
add(("small", "Corresponding author: " + EMAIL))
add(("blank",))
add(("h1", "Highlights"))
HIGH = [
    "Independent position sensing cuts modeled undetected misrouting %s-fold" % n(RRF0),
    "Over assumed priors the reduction factor is %s (5th–95th percentile %s–%s)" % (n(PSA["rrf"][1], 1), n(PSA["rrf"][0], 1), n(PSA["rrf"][2])),
    "Operator response to alarms is the weakest link: 90%% response gives %s-fold" % n(G[(0.9, 0.0)]["rrf"], 1),
    "An 8% alarm tolerance stays near-optimal once alarm fatigue is included",
    "Exact binomial acceptance criteria are derived for a pilot of 1000 valves",
]
for h in HIGH:
    assert len(h) <= 85, (len(h), h)
    add(("bullet", h))
add(("h1", "Abstract"))
add(("p0", fmt("Manual valve line-ups before product transfers rely on rounds, radio confirmation and checklists, none of which observes valve position independently. We assess an additional protection layer: temporary, reassignable clamp-on sensors that measure the actual "
               "position of existing manual valves, identify the operator and report to a plant historian. A Monte Carlo model of the line-up covers skipped, wrong-valve, incomplete and imprecise actions, out-of-sequence steps, unauthorized movement, detection by existing checks, "
               "and sensor bias, noise, drift, slip, wrong assignment, availability, bypass and operator complacency; it is verified against closed-form results and an automated test suite. With assumed inputs for a 14-valve route, the probability of at least one "
               "undetected error per transfer fell from <<b>> to <<f>> with direct stem sensing and NFC identity (<<r>>-fold), against <<t>> for handwheel turn counting, which also gave four times more nuisance alarms. A probabilistic sensitivity analysis over the assumed "
               "priors gave a median risk-reduction factor of <<m>> (5th–95th percentile <<lo>>–<<hi>>), above 5 in <<p5>> of draws; the miss rate of existing barriers, calibration bias and device availability were the main drivers. The factor fell to <<r9>> if operators "
               "acted on only 90% of true alarms, and an alarm tolerance near 8% of stroke remained best once alarm fatigue was included. Separate tolerances for throttled valves, end-stop re-zeroing and coverage of neighboring valves were quantified, and exact binomial "
               "acceptance criteria for a pilot were derived. The inputs are assumed, not measured: the results are specification targets, not credited risk reduction.",
               b=pc(BASE, 2), f=pc(FULL, 2), r=n(RRF0), t=pc(TURN, 2), m=n(PSA["rrf"][1], 1), lo=n(PSA["rrf"][0], 1), hi=n(PSA["rrf"][2]), p5=pc(PSA["P_rrf_gt5"], 0), r9=n(G[(0.9, 0.0)]["rrf"], 1))))
add(("p0", "Keywords: Manual valve verification; line-up error; human reliability; protection layer; Monte Carlo simulation; probabilistic sensitivity analysis; wireless position sensing"))
