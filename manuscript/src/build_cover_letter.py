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
para("Product transfers through manual valve line-ups depend on operators setting the right valves to the right positions, and the barriers that exist today, inspection rounds, radio confirmation and checklists, observe the position only through the operator's report. "
     "The manuscript asks how much a temporary, reassignable layer of clamp-on position sensors on existing manual valves, which identifies the operator and reports to the plant historian, would reduce the probability of an undetected misrouting, "
     "and how much of that reduction survives when the assumed inputs and the behavior of the people who must act on the alarms are allowed to vary.")
para("The manuscript makes five contributions to the loss-prevention literature. (i) A Monte Carlo model of the line-up task with skipped, wrong-valve, incomplete, imprecise, out-of-sequence and unauthorized actions, existing-barrier detection and the errors of the sensing layer, verified against closed-form results and 12 automated tests; "
     "with the assumed inputs the probability of an undetected error per transfer on a 14-valve route falls from %s to %s (%s-fold). (ii) A probabilistic sensitivity analysis over 13 assumed inputs, which gives a median risk-reduction factor of %s "
     "(5th to 95th percentile %s to %s) and identifies the miss rate of the existing barriers, sensor calibration bias and device availability as the main drivers. (iii) A model of operator response to alarms, including alarm fatigue: the factor falls to %s if operators act on only 90%% of the true alarms, "
     "and an alarm tolerance near 8%% of stroke remains best once alarm fatigue is included. (iv) Design questions answered quantitatively: separate tolerance for throttled valves, end-stop re-zeroing, coverage of neighboring valves and the comparison of handwheel turn counting with direct stem sensing. "
     "(v) Exact binomial acceptance criteria and sample sizes for a pilot (about %s validated valves with an acceptance number of %s nuisance alarms) that would replace the assumed inputs with data."
     % (pc(BASE, 2), pc(FULL, 2), n(RRF0), n(PSA["rrf"][1], 1), n(PSA["rrf"][0], 1), n(PSA["rrf"][2]), n(G[(0.9, 0.0)]["rrf"], 1), "1000", PIL["fa"][3]["accept_max"]))
para("The study is explicit about what it is. Every input probability is an assumed design-stage value, because no distribution specific to this task was available; the device concept has not been built or tested; and the results are model probabilities under assumed inputs, not field reliabilities. "
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
