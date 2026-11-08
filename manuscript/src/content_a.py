# -*- coding: utf-8 -*-
"""Manuscript, part A: Introduction, problem definition, architecture, model (Sections 1-4)."""
from common import *

# ============================================================================================ 1 Introduction
add(("h1", "1. Introduction"))
add(("p", "Product transfers between tanks, plants and terminals depend on a correct valve line-up. Where valves are manual, the line-up is established by field operators who open and close a defined set of valves in sequence, and it is confirmed by inspection "
          "rounds, radio communication between control rooms and checklists. This arrangement is well established, but it observes valve position only indirectly, through the report of the person who handled the valve. Human reliability analysis treats omission of a step, "
          "selection of the wrong item and incomplete execution as distinct and persistent error modes [@Swain1983;@Kirwan1994;@Reason1990;@Kirwan1992], and quantification methods such as HEART assign them generic error probabilities that are modified by "
          "conditions of the task [@Williams1988]. Analyses of process accidents repeatedly identify human and organizational factors [@Zarei2019], and collections of process-plant case histories include accidents in which the position of a manual valve was a factor [@Kletz2019]. "
          "In a transfer line-up each error mode can lead to a closed loop, contamination of another tank or delivery of the wrong product to a receiving site."))
add(("p", "Process safety practice already places protection layers between such errors and their consequences, including procedures, second-person checks, locked valves and instrumented position indication on automated valves [@Mannan2012;@CCPS2015]. For manual valves in remote tank areas, "
          "continuous independent position indication is often not installed, because permanent limit switches or position transmitters require wiring, hazardous-area installation effort and capital cost per valve. Retrofit wireless position monitoring of valves has been demonstrated "
          "[@Chraim2013], and industrial demand reflects the same gap: operators want the position, identity and time of every manual valve action visible in the plant historian without replacing or automating the valve, as illustrated by a recent open-innovation call for such a solution [@YPF2026]."))
add(("p", "Quantitative evidence for such a layer is scarce, and a design-stage assessment has two obvious weaknesses. It rests on assumed human-error rates, and it tends to assume that the people involved react to every alarm. The first version of this study "
          "(retained unchanged in the repository) addressed the architecture and the main trade-offs under one set of assumed inputs. This paper extends it in five ways that bear on those weaknesses: (i) a probabilistic sensitivity analysis that propagates the uncertainty of "
          "the assumed inputs to the risk-reduction factor; (ii) a model of the operator's response to alarms, including alarm fatigue [@Laberge2014]; (iii) common-cause variation of the error rates; (iv) separate alarm tolerances for throttled valves, end-stop re-zeroing and "
          "coverage of neighboring valves, three design questions left open before; and (v) exact binomial acceptance criteria and sample sizes for a pilot that would replace the assumed inputs with data. Each added mechanism reduces to the first version when it is switched off, "
          "and this is tested (Section 4.9)."))
add(("p", "The study makes three contributions. First, it describes a sensing-layer architecture for temporary, reassignable, non-invasive verification of manual valve position that combines position, operator identity, time and procedure step. Second, it presents a Monte Carlo "
          "framework that quantifies how such a layer changes the probability that an error goes undetected at pump start or during the transfer, with the false-alarm cost, and how robust that change is to the assumed inputs. Third, it derives specification guidance and "
          "pilot acceptance criteria from the simulated trade-offs. It is a design-stage assessment based on assumed inputs and reports no field data."))

# ============================================================================================ 2 Problem
add(("h1", "2. Problem definition"))
add(("h2", "2.1 The line-up task"))
add(("p", "A representative task is an interplant transfer of a gasoline blend between a refinery and a logistics terminal. Before pumping, operators at both sites manually set a defined list of valves to required positions, mostly fully open or fully closed, with occasional "
          "intermediate settings. The route has $V$ valves; this work examines routes of 6, 14 and 24 valves, and uses the 14-valve route (eight to be opened, four closed, two throttled) as the reference."))
add(("h2", "2.2 Error modes and existing barriers"))
add(("p", "Six error classes are considered: (i) a required valve action is skipped, including a false report that it was done; (ii) the wrong valve is operated and the intended valve is left unchanged; (iii) the movement stops short; (iv) an intermediate valve is set imprecisely; "
          "(v) steps are performed out of sequence; and (vi) a valve is moved without authorization after validation. Existing barriers (inspection rounds, radio confirmation, paper checklist) detect each class with some probability, but none provides independent, "
          "time-stamped observation of the physical position."))
add(("h2", "2.3 Requirements for an additional layer"))
add(("p", "The additional layer should (a) measure actual position, including intermediate openings, independently of operator confirmation; (b) record movements and deviations with time stamps; (c) work on existing manual valves without modification or process shutdown; "
          "(d) be installable for a few days and reassigned unambiguously to another valve, with an assignment history; (e) suit classified areas; (f) tolerate wrench operation; (g) use existing industrial wireless infrastructure and feed a plant historian; and "
          "(h) alarm on loss of signal, battery or communication while buffering data locally. These requirements follow the problem statement of an industrial open-innovation call for such a solution [@YPF2026]."))

# ============================================================================================ 3 Architecture
add(("h1", "3. Sensing-layer architecture"))
add(("fig", "Fig1_architecture.png", "Fig. @F:arch@. Architecture of the sensing layer: a clamp-on sensor on the stem or indicator of an existing manual valve, an NFC tag for identity and assignment, a wireless link to the gateway and historian, "
                                      "a route-validation service that compares required and measured positions, and the existing barriers, which are unchanged.", 6.4))
add(("h2", "3.1 Measurement principle"))
add(("p", "Two measurement concepts are compared. In the handwheel turn-count collar, a clamp-on device on the handwheel counts rotations and converts turns to percent of a calibrated stroke. It is simple to mount on many valves, but position is inferred: gear-operator lash, "
          "slippage and lost counts accumulate error. In direct stem or indicator sensing, a clamp-on kit reads the angle of the stem or position indicator (rotary) or the stem travel (rising stem), quantities that move with the closure element. Direct sensing also needs "
          "calibration but is not exposed to handwheel slip. The device is mounted outside the tool path and shrouded, so operation with a wrench does not load the sensor."))
add(("h2", "3.2 Identity, assignment and event logic"))
add(("p", "A passive near-field communication (NFC) tag carrying the valve identity is fixed to each valve. Tapping the device on the tag assigns it to the valve; a guided two-point calibration (fully closed and fully open) follows; and a backend ledger stores assignments over time. "
          "Tapping the operator badge before touching a valve links each movement to a person. A mismatch between the tapped valve and the valve required by the current procedure step can alarm before the wrong valve is moved, which converts some detection into prevention."))
add(("h2", "3.3 Communication and integration"))
add(("p", "Each device reports through a certified WirelessHART link [@IEC62591] to the plant gateway, and the gateway forwards data to the plant historian through standard industrial protocols. Movements are reported on event, with a periodic heartbeat. The device stores events "
          "locally and forwards them when communication returns. A route-validation service compares required and measured positions and displays alignment status before pumping begins."))
add(("h2", "3.4 Role as a protection layer"))
add(("p", "The layer is advisory. It does not interlock pumps and is not claimed as a safety instrumented function under the functional-safety standards for the process sector [@IEC61511]. Its value is an additional, independent detection opportunity for human errors. "
          "Hazardous-area use requires an appropriate protection concept such as intrinsic safety [@IEC60079], which also limits the energy available to the electronics and motivates a low-power design."))

# ============================================================================================ 4 Model
add(("h1", "4. Monte Carlo model"))
add(("h2", "4.1 Overview"))
add(("p", "The model simulates $N$ independent transfers. For each transfer, the actual position $a_v$ of every route valve $v$ is generated from the required position $r_v$ and the error model of Section 4.2; existing barriers then detect some defects (Section 4.3); and the "
          "sensing layer measures positions and raises alarms (Section 4.4). A defect is defined as $|a_v-r_v|>0.10$ of stroke. The Monte Carlo method follows its standard formulation [@Metropolis1949], and probabilities are reported with Wilson 95% intervals [@Wilson1927;@Brown2001]."))
add(("h2", "4.2 Operator error model"))
add(("p", "Per valve action, the probabilities of skipping, operating the wrong valve and stopping short are 0.002, 0.0015 and 0.006. These are order-of-magnitude values in the range used in human reliability practice for procedural tasks [@Swain1983;@Kirwan1994], and they are "
          "assumed priors, not measurements. A skipped or wrong-valve action leaves the intended valve at its random initial state. An incomplete movement completes a fraction uniformly distributed between 0.60 and 0.97 of the required travel. Intermediate valves are set with "
          "a standard deviation of 0.04 of stroke. Out-of-sequence steps occur with probability 0.004 per transfer. Unauthorized or accidental movement occurs at $5×10^{-5}$ per valve-hour over a lognormal transfer duration with median 8 h; its size is uniform between "
          "0.10 and 1.0 of stroke."))
add(("h2", "4.3 Existing barriers"))
add(("p", "Existing checks detect a skipped, wrong-valve, incomplete, imprecise, out-of-sequence and post-validation defect with probabilities 0.80, 0.80, 0.60, 0.50, 0.10 and 0.20 respectively. Each probability is perturbed per transfer on the logit scale with standard deviation 0.5 "
          "to represent uncertainty. When a sensing layer is present, operator complacency reduces the effectiveness of the existing checks by a relative factor, taken as 0.20 in the base case, because operators may rely on the system."))
add(("h2", "4.4 Sensing layer"))
add(("p", "The measured position of valve $v$ is $m_v=a_v+b+e+d√k+s$, where $b$ is the calibration bias (standard deviation $σ_c$), $e$ is noise ($σ_n$), $d$ is drift per square root of operation for $k$ operations since calibration, and $s$ is a slip event that occurs "
          "with probability $1-(1-p_s)^k$ and has magnitude uniform between 0.05 and 0.30 of stroke with random sign. The device alarms if $|m_v-r_v|>τ$, with $τ=0.08$ in the base case. With probability $p_a$ the device is linked to the wrong valve, so that it measures another "
          "route valve. A device is unavailable at validation with probability 0.006 (communication 0.003, battery 0.001, hardware 0.002); if any route device is unavailable the validation is blocked, and with probability 0.20 the operator proceeds without sensor validation "
          "(bypass). Table @T:arch@ lists the architecture parameters."))
ARCH_ROWS = [["Noise $σ_n$ (stroke)", "–", "0.020", "0.015", "0.015"], ["Calibration bias $σ_c$ (stroke)", "–", "0.030", "0.020", "0.020"], ["Drift $d$ (stroke per √operation)", "–", "0.0040", "0.0005", "0.0005"],
             ["Slip probability $p_s$ per operation", "–", "0.0040", "0.0003", "0.0003"], ["Wrong-device assignment $p_a$", "–", "0.005", "0.005", "0.0002"], ["NFC identity and tap-before-touch", "no", "no", "no", "yes"]]
add(("table", "Table @T:arch@. Sensing architectures compared (assumed parameters).", ["Parameter", "Existing checks", "Turn-count collar", "Direct sensing", "Direct + NFC"], ARCH_ROWS, [2.6, 1.0, 1.1, 1.1, 1.0]))
add(("h2", "4.5 Outputs and closed-form verification"))
add(("p", "The primary output is the probability per transfer that at least one defect, out-of-sequence step or post-validation movement escapes all barriers. Secondary outputs are false alarms (an alarm on a valve that is not defective), the share of true defects missed by the "
          "sensors, the probability that validation is blocked, and detection within 60 s of a post-validation movement. The simulation was checked against three closed-form results. For ideal Gaussian measurement with standard deviation $σ$, the false-alarm probability is "
          "$2[1-Φ(τ/σ)]$. For a defect of offset $e$, the miss probability is $Φ((τ-e)/σ)-Φ((-τ-e)/σ)$. For independent binary-valve defects detected by existing barriers with probabilities $d_i$, the residual risk is $1-∏(1-q_i(1-d_i))$. "
          "Simulated and closed-form values were %s and %s, %s and %s, and %s and %s, respectively." %
          (pc(R["selftest"]["false_alarm"][0], 3), pc(R["selftest"]["false_alarm"][1], 3), pc(R["selftest"]["miss_offset"][0], 3), pc(R["selftest"]["miss_offset"][1], 3), pc(R["selftest"]["baseline_residual"][0], 2), pc(R["selftest"]["baseline_residual"][1], 2))))
add(("p", "The base case uses %s transfers per architecture and route, %s per sweep point and fixed random seeds; it follows the structure of an open simulation framework previously published by the author [@MyUncle]." % (n(R["meta"]["n"]), n(R["meta"]["n_sweep"]))))

# ------------------------------------------------------------------------------------------- 4.6 extensions
add(("h2", "4.6 Extensions of the model"))
add(("p", "Five mechanisms were added to the first version; each can be switched off. (i) Common cause: the three operator error rates of a transfer are multiplied by a lognormal factor with mean one and log-standard deviation $σ_{cc}$, which represents fatigue, poor lighting or a "
          "mislabeled valve group acting on all the valves of one transfer. (ii) Operator response: an alarm on a truly defective valve is acted on with probability $ρ=ρ_0 exp(-κF)$, where $F$ is the number of nuisance alarms (alarms on valves that are not defective) in "
          "the same validation, $ρ_0$ is the response to an isolated alarm and $κ$ is a fatigue coefficient; this is a parametric description of alarm fatigue [@Laberge2014], not a fitted model, and it applies to all alarm-driven detections. (iii) Separate alarm tolerance "
          "for intermediate (throttled) valves. (iv) End-stop re-zeroing: when a binary valve reaches its end stop the sensor offset is re-zeroed, so that for those valves the operations since the last zero are at most one. (v) Collateral movement: a wrong-valve action "
          "moves a neighboring valve that carries no route device with probability 0.5; the neighbor carries a device with probability equal to the coverage $c$; a covered movement is detected unless the validation was bypassed and is then acted on with the response probability $ρ$, and an uncovered movement is detected only by the existing barriers (detection probability 0.50 for such events)."))
add(("h2", "4.7 Probabilistic sensitivity analysis"))
add(("p", fmt("The first version varied one input at a time. Here the 13 uncertain inputs of Table @T:prior@ are varied together. Each draw samples the inputs from the distributions of the table (lognormal multipliers whose 90% interval is the stated factor, and uniform "
          "distributions for the three policy and behavior inputs), simulates 40,000 transfers for each of the existing-checks, direct-sensing and direct-plus-NFC cases with the same seed, and records the residual risks and the risk-reduction factor "
          "$RRF=P_{existing}/P_{full}$. <<nd>> draws were made. The percentiles of the draws describe the effect of the assumed uncertainty, not of the sampling (the sampling error of a proportion near 0.9 from 200 draws is about 0.02). Partial rank correlation "
          "coefficients (PRCC) between the inputs and the logarithm of the output rank the drivers [@Marino2008]. The prior distributions are assumed; they are wider than a typical expert interval on purpose, because the model has no plant data to narrow them.", nd=n(PSA["ndraw"]))))
PR = [["Operator error rates (skip, wrong, incomplete)", "× 1", "lognormal, 90% factor 4"], ["Existing-barrier miss probability", "× 1", "lognormal, 90% factor 3"], ["Out-of-sequence rate", "0.004", "lognormal, 90% factor 3"], ["Unauthorized-movement rate", "5e−5 per valve-hour", "lognormal, 90% factor 3"],
      ["Sensor noise", "× 1", "lognormal, 90% factor 2"], ["Sensor calibration bias", "× 1", "lognormal, 90% factor 2"], ["Sensor drift", "× 1", "lognormal, 90% factor 3"], ["Slip rate", "× 1", "lognormal, 90% factor 3"], ["Wrong-device assignment", "× 1", "lognormal, 90% factor 3"],
      ["Device unavailability (communication, battery, hardware)", "× 1", "lognormal, 90% factor 4"], ["Bypass probability when blocked", "0.20", "uniform 0–0.5"], ["Operator complacency", "0.20", "uniform 0–0.6"], ["Time-stamp sequence detection", "0.95", "uniform 0.7–1.0"]]
add(("table", "Table @T:prior@. Input distributions of the probabilistic sensitivity analysis (assumed). A lognormal multiplier with 90% factor $f$ has 5th and 95th percentiles $1/f$ and $f$.", ["Input", "Base value", "Distribution"], PR, [3.2, 1.5, 2.0]))
add(("h2", "4.8 Pilot sizing"))
add(("p", "The acceptance criteria of a pilot are exact binomial tests. For nuisance alarms, a pilot validates $N$ valves and accepts the device if no more than $c$ nuisance alarms occur, where $c$ is the largest count whose probability under the unacceptable rate (3% per valve, "
          "twice the modeled rate) is at most 5% (consumer risk); the power is the probability of acceptance at the modeled 1.4% per valve. For missed defects, a number of defects injected on purpose (valves set deliberately off by more than the defect threshold) is detected or not, and "
          "the test is built the same way for an unacceptable miss rate of 15%, with the power evaluated at the modeled 6%. The accuracy of a device is described by the width of the chi-square interval for the standard deviation of repeated readings. The unacceptable rates "
          "are illustrative thresholds chosen for this study, not criteria set by any operator."))
add(("h2", "4.9 Verification and reproducibility"))
add(("p", "The extended engine imports the first version unchanged (its file hash is checked) and, with all new mechanisms off, reproduces its event counts exactly for the same seeds. A suite of 12 automated checks covers this equivalence, the closed-form cases of Section 4.5, "
          "the direction of every added mechanism (response, tolerance, per-type tolerance, re-zeroing, coverage), the exact binomial calculations of the pilot, the probabilistic sensitivity analysis and the reproduction of the packaged results of the first version. "
          "One command regenerates every number and figure; the code, results and manuscript sources are archived with DOIs (Data availability)."))
