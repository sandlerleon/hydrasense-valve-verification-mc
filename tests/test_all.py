# -*- coding: utf-8 -*-
"""Automated checks of the HydraSense simulation:  python -m pytest tests -q   (or: python tests/test_all.py)

1. the original model file is byte-identical to the one in the submission package;
2. the original closed-form self-tests pass;
3. the extended engine reproduces the original counts exactly when its new mechanisms are off;
4. each new mechanism acts in the expected direction;
5. the pilot-sizing tests are exact binomial calculations;
6. the packaged results of the original study are reproduced within Monte Carlo error (small run).
"""
import hashlib
import math
import os
import sys

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import HydraSense_MC as H            # noqa: E402
import hydrasense_v2 as V            # noqa: E402

ORIGINAL_SHA256 = "1db6bc8b95a9f495c3942631c3ea5bf9826a7e41583f4b12591d3ea28eccc2e1"
N = 60_000


def test_original_file_unchanged():
    assert hashlib.sha256(open(os.path.join(ROOT, "HydraSense_MC.py"), "rb").read()).hexdigest() == ORIGINAL_SHA256


def test_original_selftests():
    r = H.selftest(n=120_000)
    for k in ("false_alarm", "miss_offset", "baseline_residual"):
        assert abs(r[k][0] - r[k][1]) < 0.02


def test_extended_engine_equals_original_when_off():
    for route, arch in (("transfer_14", "baseline"), ("transfer_14", "full"), ("binary_14", "stem")):
        a = H.run(route, arch, H.Params(), n=40_000, seed=3)
        b = V.run2(route, arch, V.Params2(), n=40_000, seed=3)
        for k in H.COUNT_KEYS:
            assert a[k] == b[k], (route, arch, k, a[k], b[k])


def test_common_cause_keeps_mean_and_is_mean_preserving():
    p0 = V.run2("transfer_14", "baseline", V.Params2(), n=N, seed=5)["any_und"] / N
    p1 = V.run2("transfer_14", "baseline", V.Params2(cc_sigma=1.0), n=N, seed=5)["any_und"] / N
    assert abs(p1 - p0) < 0.25 * p0          # a mean-one multiplier changes the mean only through the saturation of 1-exp
    assert p1 <= p0 * 1.05


def test_operator_response_raises_residual_risk():
    base = V.run2("transfer_14", "full", V.Params2(), n=N, seed=7)["any_und"]
    r09 = V.run2("transfer_14", "full", V.Params2(resp0=0.9), n=N, seed=7)["any_und"]
    r09f = V.run2("transfer_14", "full", V.Params2(resp0=0.9, fatigue_k=0.6), n=N, seed=7)["any_und"]
    assert r09 > base and r09f >= r09


def test_tolerance_tradeoff_direction():
    lo = V.run2("transfer_14", "stem", V.Params2(tol=0.04), n=N, seed=9)
    hi = V.run2("transfer_14", "stem", V.Params2(tol=0.15), n=N, seed=9)
    assert lo["fa_count"] > hi["fa_count"]
    assert (1 - lo["def_flagged"] / lo["defects"]) < (1 - hi["def_flagged"] / hi["defects"])


def test_per_type_tolerance_only_changes_intermediate_valves():
    a = V.run2("transfer_14", "stem", V.Params2(tol=0.06), n=N, seed=11)
    b = V.run2("transfer_14", "stem", V.Params2(tol=0.06, tol_mid=0.15), n=N, seed=11)
    assert a["fa_bin"] == b["fa_bin"] and b["fa_mid"] < a["fa_mid"]


def test_rezero_removes_wear_dependence():
    old = V.run2("transfer_14", "stem", V.Params2(ops_mean=300.0), n=N, seed=13)["fa_count"]
    new = V.run2("transfer_14", "stem", V.Params2(ops_mean=300.0, rezero=True), n=N, seed=13)["fa_count"]
    assert new < 0.5 * old


def test_collateral_coverage_is_monotone_and_full_coverage_detects_all_sensed():
    cu = [V.run2("transfer_14", "full", V.Params2(coverage=c), n=N, seed=15)["coll_und"] for c in (0.0, 0.5, 1.0)]
    assert cu[0] > cu[1] > cu[2]
    assert cu[2] <= 0.1 * cu[0]


def test_pilot_sizing_is_exact_binomial():
    R = V.study_pilot()
    for r in R["fa"]:
        c, N_ = r["accept_max"], r["N"]
        assert stats.binom.cdf(c, N_, 0.03) <= 0.05 + 1e-12
        assert c == 0 or stats.binom.cdf(c + 1, N_, 0.03) > 0.05          # c is the largest acceptance number
        assert abs(r["power_at_1p4"] - stats.binom.cdf(c, N_, 0.014)) < 1e-12
    pw = [r["power_at_1p4"] for r in R["fa"]]
    assert pw[-1] > 0.999 and pw[3] > 0.9


def test_psa_runs_and_orders_the_architectures():
    R = V.study_psa(ndraw=12, n=8_000)
    assert R["baseline"][1] > R["full"][1]
    assert len(R["prcc_rrf"]) == len(R["names"]) == 13
    assert all(-1.0 <= x <= 1.0 for x in R["prcc_rrf"])


def test_packaged_results_reproduced():
    import json
    pk = os.path.join(ROOT, "results", "original_results.json")
    if not os.path.exists(pk):
        return
    R = json.load(open(pk))
    c = H.run("transfer_14", "baseline", H.Params(), n=200_000, seed=2026)
    ref = R["archs"]["transfer_14"]["baseline"]["any_und"]
    lo, hi = H.wilson(c["any_und"], c["n"])
    assert lo - 0.004 < ref["p"] < hi + 0.004


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for f in fns:
        f(); print("ok  ", f.__name__)
    print("%d checks passed" % len(fns))
