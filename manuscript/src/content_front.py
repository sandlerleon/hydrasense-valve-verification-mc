# -*- coding: utf-8 -*-
"""Manuscript front matter: title, author, highlights, abstract, keywords."""
from common import *

G = {(r["resp0"], r["k"]): r for r in RESP["grid"]}
P2 = W["psa2"]; BD = W["bounds"]["bounds"]; EV = W["eventtree"]; CIR = W["ci"]
CL = {(r["design"].split(" (")[0], r["rho"]): r for r in W["cluster"]}
add(("title", TITLE))
add(("author", "Leon Sandler"))
add(("small", "Independent Researcher, Northbrook, Illinois, USA"))
add(("small", "ORCID: https://orcid.org/0009-0007-4584-808X"))
add(("small", "Corresponding author: " + EMAIL))
add(("blank",))
add(("h1", "Highlights"))
HIGH = [
    "Independent position sensing cuts modeled undetected misrouting %s-fold" % n(RRF0),
    "With uncertain operator response the median reduction falls to %s-fold" % n(P2["rrf"][1], 1),
    "A 10-fold reduction needs about %s alarm response and bypass below %s" % (pc(BD["10"]["response_min"], 0), pc(BD["10"]["bypass_max"], 0)),
    "Fail-safe blocking neutralizes gateway outages; wrong identification erodes benefit",
    "Pilot power drops from %s to %s when validations cluster by valve" % (pc(CL[("12 valves x 83 validations", 0.0)]["power_at_1p4"], 0), pc(CL[("12 valves x 83 validations", 0.05)]["power_at_1p4"], 0)),
]
for h in HIGH:
    assert len(h) <= 85, (len(h), h)
    add(("bullet", h))
add(("h1", "Abstract"))
add(("p0", fmt("Manual valve line-ups before product transfers rely on rounds, radio confirmation and checklists, none of which observes valve position independently. We ask when an additional layer of temporary clamp-on position sensors on existing manual valves reduces transfer risk, and when alarm fatigue, bypass, common-cause failures and incomplete coverage remove the benefit. "
               "A Monte Carlo model of the line-up task, verified against closed-form results, an independent analytic model and automated tests, gave with assumed inputs for a 14-valve route an undetected-error probability per transfer of <<b>> with existing checks and <<f>> with direct sensing and NFC identity (<<r>>-fold; sampling interval <<cl>>–<<ch>>), "
               "assuming that operators always act on alarms. Varying 13 inputs gave a median reduction of <<m1>> (5th–95th percentile <<l1>>–<<h1>>); adding uncertain operator response, alarm fatigue and common-cause failures of the sensing layer gave <<m2>> (<<l2>>–<<h2>>), with response the strongest driver. "
               "A mean response time of 10 min against 20 min available gave a factor of about 2. A factor of 10 required a response of at least <<r10>>, bypass below <<b10>> and common-cause probability below <<c10>>. An illustrative event tree gave a <<e>>-fold reduction in expected loss. "
               "Clustering of validations by valve cut the power of a 1000-validation pilot from <<p0>> to <<p5>>. Inputs, consequence probabilities and losses are assumed: the results are conditional, not credited risk reduction.",
               b=pc(BASE, 2), f=pc(FULL, 2), r=n(RRF0), cl=n(CIR["rrf_full"][0], 1), ch=n(CIR["rrf_full"][2], 1), m1=n(PSA["rrf"][1], 1), l1=n(PSA["rrf"][0], 1), h1=n(PSA["rrf"][2]), m2=n(P2["rrf"][1], 1), l2=n(P2["rrf"][0], 1), h2=n(P2["rrf"][2], 1),
               r10=pc(BD["10"]["response_min"], 0), b10=pc(BD["10"]["bypass_max"], 0), c10=pc(BD["10"]["cc_all_max"], 1), e=n(EV["full"]["rrf_eal"], 0),
               p0=pc(CL[("12 valves x 83 validations", 0.0)]["power_at_1p4"], 0), p5=pc(CL[("12 valves x 83 validations", 0.05)]["power_at_1p4"], 0))))
add(("p0", "Keywords: Manual valve verification; line-up error; human reliability; protection layer; common-cause failure; alarm response; Monte Carlo simulation; probabilistic sensitivity analysis; event tree"))
