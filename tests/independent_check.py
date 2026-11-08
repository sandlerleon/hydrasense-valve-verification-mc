# -*- coding: utf-8 -*-
"""Independent closed-form barrier model (no code shared with the simulation engine) for the binary 14-valve route with a Gaussian sensor
(no drift, slip, wrong assignment, sequence or unauthorized-movement terms, nominal detection probabilities).
It computes the probability that at least one valve-position defect escapes the existing barriers and the sensing layer, and compares it with the Monte Carlo estimate.

    python tests/independent_check.py
"""
import math
import os
import sys
from dataclasses import replace

from scipy.integrate import quad

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import HydraSense_MC as H            # only for the parameter values and the Monte Carlo run being checked
import hydrasense_v2 as V


def Phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def analytic(P, sigma, V_=14, n_dev=14):
    tol = P.tol
    f = lambda dev: 1 - (Phi((tol - dev) / sigma) - Phi((-tol - dev) / sigma))              # alarm probability for a valve that is dev (stroke) off
    comp = P.complacency
    # per valve, probability of an undetected defect given that the sensing layer is active or not
    def per_valve(active):
        fl = (lambda d: f(d)) if active else (lambda d: 0.0)
        d_skip = P.d_skip * (1 - comp)          # complacency applies whenever a sensing layer is installed, also when its validation is bypassed
        d_wrong = P.d_wrong * (1 - comp)          # complacency applies whenever a sensing layer is installed, also when its validation is bypassed
        d_inc = P.d_inc * (1 - comp)          # complacency applies whenever a sensing layer is installed, also when its validation is bypassed
        u = P.p_skip * 0.5 * (1 - d_skip) * (1 - fl(1.0)) + P.p_wrong * 0.5 * (1 - d_wrong) * (1 - fl(1.0))
        lo, hi = P.d_true, 0.40                                                              # incomplete movement leaves 1-frac of the travel, uniform 0.03..0.40
        u += P.p_inc * 0.5 * quad(lambda d: (1 - d_inc) * (1 - fl(d)) / 0.37, lo, hi)[0]
        return u
    p_unav = 1 - (1 - P.p_comm) * (1 - P.p_batt) * (1 - P.p_hw)
    p_blocked = 1 - (1 - p_unav) ** n_dev
    a_ = 1 - p_blocked * P.bypass                                                           # probability that the validation is not bypassed
    return 1 - (a_ * (1 - per_valve(True)) ** V_ + (1 - a_) * (1 - per_valve(False)) ** V_)


def main(n=1_200_000):
    arch = H.Arch("gauss", "stem", 0.015, 0.02, 0.0, 0.0, False, 0.0)
    P = replace(V.Params2(), p_seq=0.0, lam_unauth=0.0)
    sigma = math.sqrt(0.015 ** 2 + 0.02 ** 2)
    an = analytic(P, sigma)
    c = V.run2("binary_14", "x", P, n=n, seed=5, nominal=True, arch_obj=arch)
    lo, hi = H.wilson(c["any_und"], c["n"])
    print("closed form %.5f   Monte Carlo %.5f  [%.5f, %.5f]" % (an, c["any_und"] / c["n"], lo, hi))
    assert lo - 1e-4 <= an <= hi + 1e-4
    return an, c["any_und"] / c["n"], lo, hi


def test_independent_closed_form():
    main(600_000)


if __name__ == "__main__":
    main()
    print("ok")
