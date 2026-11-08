# -*- coding: utf-8 -*-
"""Supplementary information, part 3: reproducibility."""
from common import *

adds(("h1", "S5. Reproducibility"))
adds(("p", fmt("The repository (%s, version %s) contains the unchanged first-suite model (HydraSense_MC.py), the extended engine and studies (hydrasense_v2.py), the results (results/original_results.json, results/results_v2.json, results/results_v3.json), the figures, the 16 automated tests (tests/test_all.py) and the manuscript sources. "
               "Commands: python HydraSense_MC.py --reproduce reproduces the first suite; python hydrasense_v2.py --all runs the extended studies (approximately 4.5 min on one core), python tests/test_all.py runs the tests; python hydrasense_v3.py --all runs the studies of version 1.1.0 (approximately 8 min), python make_schematic.py draws Fig. 1. "
               "The seed of the extended studies is %s; every study uses fixed seeds, so rerunning reproduces every number in the text. The code needs Python 3, numpy, scipy and matplotlib." % (GITHUB, VERSION, X["seed"]))))
