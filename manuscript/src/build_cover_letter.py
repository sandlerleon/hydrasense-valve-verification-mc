# -*- coding: utf-8 -*-
"""Cover letter for the submission to the Journal of Loss Prevention in the Process Industries (Elsevier); numbers from results/*.json, DOIs from dois.json.

    python build_cover_letter.py   -> manuscript/HydraSense_Cover_Letter.docx
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from docx import Document
from docx.shared import Pt, Inches

from common import *

G = {(r["resp0"], r["k"]): r for r in RESP["grid"]}
d = Document()
st = d.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(11); st.paragraph_format.space_after = Pt(8)
for s in d.sections:
    s.left_margin = s.right_margin = Inches(1.0); s.top_margin = s.bottom_margin = Inches(0.75)


def para(t, bold=False, after=None):
    p = d.add_paragraph(); r = p.add_run(t); r.bold = bold
    if after is not None:
        p.paragraph_format.space_after = Pt(after)
    return p


para("Leon Sandler", True, 0)
for t in ("Independent Researcher", "Northbrook, Illinois, USA", EMAIL, "ORCID 0009-0007-4584-808X"):
    para(t, after=0)
para("")
para(datetime.date.today().strftime("%d %B %Y").lstrip("0"))
para("The Editor-in-Chief", after=0); para("Journal of Loss Prevention in the Process Industries", after=0); para("Elsevier")
para("Dear Editor,")
para("I submit the manuscript “%s” as a research article for consideration in the Journal of Loss Prevention in the Process Industries." % TITLE)
P2 = W["psa2"]; BD = W["bounds"]["bounds"]; EV = W["eventtree"]; CIR = W["ci"]
CL = {(r["design"].split(" (")[0], r["rho"]): r for r in W["cluster"]}
para("Product transfers through manual valve line-ups depend on operators setting the right valves to the right positions, and the barriers that exist today, inspection rounds, radio confirmation and checklists, observe the position only through the operator's report. "
     "The manuscript asks under what conditions a temporary, reassignable layer of clamp-on position sensors on existing manual valves, which identifies the operator and reports to the plant historian, produces a meaningful reduction in transfer risk, "
     "and when alarm fatigue, slow response, bypass, common-cause failures and incomplete coverage undermine it. It is organized around three hypotheses: that independent verification reduces undetected errors across the assumed ranges, that alarm fatigue creates an interior optimum for alarm tolerance, and that common-cause failures, bypass, slow response and incomplete coverage define quantifiable boundaries of the benefit.")
para("The manuscript makes five contributions to the loss-prevention literature. (i) A Monte Carlo model of the line-up task, verified against closed-form results, an independent analytic model and 16 automated tests; with the assumed inputs the probability of an undetected error per transfer on a 14-valve route falls from %s to %s (%s-fold, sampling interval %s to %s), if operators always act on the alarms. "
     "(ii) Probabilistic sensitivity analyses that lead with the uncertainty: a median risk-reduction factor of %s (5th to 95th percentile %s to %s) with the operator always responding, and %s (%s to %s) when operator response, alarm fatigue and common-cause failures of the sensing layer are uncertain, with the response as the strongest driver. "
     "(iii) Common-cause failures of the sensing layer (gateway and historian outages, wrong valve identification, calibration error, with fail-safe blocking distinguished from ignored outages), a time-dependent operator response compared with the time available before a consequence develops, and boundaries for a required factor (a factor of 10 needs a response of at least %s, bypass below %s and a common-cause probability below %s). "
     "(iv) An illustrative consequence-based event tree and expected annual loss, with all conditional probabilities and losses declared as assumed, and a sensitivity of the results to the defect threshold. (v) Pilot acceptance criteria with exact binomial and beta-binomial tests: clustering of validations by valve cuts the power of a 1000-validation pilot from %s to %s."
     % (pc(BASE, 2), pc(FULL, 2), n(RRF0), n(CIR["rrf_full"][0], 1), n(CIR["rrf_full"][2], 1), n(PSA["rrf"][1], 1), n(PSA["rrf"][0], 1), n(PSA["rrf"][2]), n(P2["rrf"][1], 1), n(P2["rrf"][0], 1), n(P2["rrf"][2], 1),
        pc(BD["10"]["response_min"], 0), pc(BD["10"]["bypass_max"], 0), pc(BD["10"]["cc_all_max"], 1), pc(CL[("12 valves x 83 validations", 0.0)]["power_at_1p4"], 0), pc(CL[("12 valves x 83 validations", 0.05)]["power_at_1p4"], 0)))
para("The study is explicit about what it is. Every input probability, consequence probability and loss is an assumed design-stage value, because no distribution specific to this task was available; the device concept has not been built or tested; and the results are model probabilities under assumed inputs, not field reliabilities. "
     "The layer is proposed as an advisory barrier, not as a safety instrumented function or a credited independent protection layer, and the manuscript states what a pilot would have to demonstrate before it could be credited.")
para("The code, the data behind every figure and table, the tests and the manuscript sources are openly available at %s and archived at https://doi.org/%s (code, all versions); the manuscript and its Supplementary Information are archived at https://doi.org/%s "
     "(all versions). One command regenerates every number and figure." % (GITHUB, DOIS["code_concept"], DOIS["paper_concept"]))
para("Disclosure. The application was taken from a public industrial scouting challenge on a third-party innovation platform, and I have prepared a related commercial proposal in response to it; I may therefore benefit commercially from the concept, as stated in the manuscript. The work received no external funding.")
para("Author affiliation and email address. I am an independent researcher with no current institutional affiliation, and I am the sole author. The corresponding-author email address, %s, is my personal address." % EMAIL)
para("A generative AI tool (Claude, Anthropic) assisted with drafting text, writing and testing simulation code and generating figures from that code; I reviewed and edited all of it and take full responsibility for the content, as disclosed in the manuscript. "
     "The manuscript is original, has not been published elsewhere and is not under consideration at any other journal. I am the sole author.")
para("Thank you for considering this submission.")
para("Sincerely,")
para("Leon Sandler", True)
out = os.path.join(OUT, "HydraSense_Cover_Letter.docx")
d.save(out)
print("saved", out)
