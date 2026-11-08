# Quantifying the effectiveness of independent manual-valve verification in preventing product-transfer risks: a Monte Carlo process-safety assessment

Leon Sandler, Independent Researcher — sandler.leon@gmail.com — ORCID 0009-0007-4584-808X

Code, data and manuscript for a probabilistic assessment of an additional protection layer for manual valve line-ups before product transfers (HydraSense: temporary, reassignable clamp-on position sensors with NFC identity, reporting through WirelessHART to a plant historian), prepared for the **Journal of Loss Prevention in the Process Industries** (Elsevier).
Manuscript: `manuscript/HydraSense_JLPPI_Manuscript.{docx,pdf}`, supplementary information `manuscript/HydraSense_Supplementary_Information.{docx,pdf}`, cover letter `manuscript/HydraSense_Cover_Letter.{docx,pdf}`.
Archived on Zenodo (all versions): paper 10.5281/zenodo.24046771, code 10.5281/zenodo.24046773. Version 1.1.1 (this one) revises the study after a pre-submission review (1.1.0: new studies; 1.1.1: language edits from a Rubriq check merged selectively); version 1.0.0 (paper 10.5281/zenodo.24046772, code 10.5281/zenodo.24046774) is superseded.

**All input probabilities are assumed design-stage priors, not measurements, and the device has not been built or tested. The results are model probabilities under assumed inputs, not field reliabilities; the layer is an advisory barrier, not a safety instrumented function or a credited protection layer.**

## What the study does

1. **First suite (`HydraSense_MC.py`, unchanged).** A Monte Carlo model of the line-up task (skipped, wrong-valve, incomplete, imprecise, out-of-sequence and unauthorized actions), detection by existing barriers, and a sensing layer with bias, noise, drift, slip, wrong assignment, availability, bypass and operator complacency; closed-form checks; four architectures (existing checks, handwheel turn-count collar, direct stem sensing, direct sensing with NFC identity); alarm tolerance, calibration age, availability and bypass, complacency, NFC compliance, one-at-a-time sensitivity and a battery model.
2. **Extension (`hydrasense_v2.py`).** Switchable mechanisms (all off = first suite draw for draw): common-cause variation of the error rates, operator response to alarms with fatigue, separate tolerance for throttled valves, end-stop re-zeroing, collateral movement of neighboring valves. Studies: a **probabilistic sensitivity analysis** over 13 assumed inputs (risk-reduction factor, partial rank correlations), the response and tolerance trade-off, per-type tolerances, re-zeroing, coverage, and **exact binomial pilot sizing**.
3. **Version 1.1.0 studies (`hydrasense_v3.py`).** Common-cause failures of the sensing layer (gateway and historian outages, wrong valve identification, calibration error; fail-safe blocking versus ignored outage), time-dependent operator response against the time available, boundaries (bypass, response, common cause, communication loss) for a required risk-reduction factor, sensitivity to the defect threshold, sampling intervals of the risk-reduction factor, a second probabilistic sensitivity analysis that includes response and common cause, an illustrative consequence event tree (all consequence probabilities and losses assumed), beta-binomial pilot tests for clustered validations, and a closed-form check (including slip) and an independent analytic model.
4. **Main findings (under assumed inputs).** On a 14-valve route the probability of an undetected error per transfer falls from 4.03 % to 0.29 % with direct stem sensing plus NFC identity (14-fold, sampling interval 13.6-14.3) if operators always act on alarms. With 13 inputs varied the median risk-reduction factor is 9.7 (5th-95th percentile 4.4-28); with operator response (0.7-1.0), alarm fatigue and common cause also uncertain it is 2.5 (0.9-4.8), response being the strongest driver. A mean response time of 10 min against 20 min available leaves a factor of about 2. A factor of 10 needs a response of at least 97 %, bypass below 53 % and a common-cause probability below 2.3 % per validation. Clustering of validations by valve cuts the power of a 1000-validation pilot from 95 % to 50 % at an intraclass correlation of 0.05.

## Reproduce

```
pip install -r requirements.txt
python HydraSense_MC.py --reproduce      # first suite -> hydrasense_mc_out/ (identical to results/original_results.json)
python hydrasense_v2.py --all            # extended studies -> results/results_v2.json and figures/ (about 4.5 min)
python make_schematic.py                 # Fig. 1
python hydrasense_v3.py --all            # version 1.1.0 studies -> results/results_v3.json (about 8 min)
python tests/test_all.py                 # 16 automated checks
python manuscript/src/build_manuscript.py          # manuscript and supplementary information (.docx)
python manuscript/src/build_cover_letter.py        # cover letter (.docx)
python manuscript/src/build_submission_files.py    # highlights and title page (.docx)
```

Seeds are fixed (`SEED = 2026`); every number in the manuscript is read from `results/*.json`.

## Layout

| Path | Content |
|---|---|
| `HydraSense_MC.py` | first-suite single-file model (unchanged; sha256 checked by the tests) |
| `hydrasense_v2.py` | extension and studies |
| `hydrasense_v3.py` | version 1.1.0 studies |
| `results/` | `original_results.json`, `results_v2.json`, `results_v3.json` |
| `figures/` | figures of the manuscript (`orig_fig*.png` from the first suite, `Fig*.png` from the extension) |
| `tests/test_all.py` | automated checks |
| `manuscript/` | builders (`src/`), manuscript, supplementary information, cover letter |

## Note on the source of the problem

The problem statement (real-time verification of manual valve position during critical product transfers; WirelessHART, ATEX, plant historian) is taken from a public scouting challenge on a third-party innovation platform (Wazoku / InnoCentive, read 7 November 2026). The author has prepared a related proposal and may benefit commercially from the concept; this repository is independent research and is not affiliated with or endorsed by the challenge's seeker.

## License

MIT for the code, CC-BY-4.0 for the manuscript. See `LICENSE`.
