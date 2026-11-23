# Synthetic ID, schema and metadata checker

Author: Malahil Ghauri · Licence: MIT

Standalone checker for synthetic per-query result files, agreed in the
"Contract v0.3 and next milestone" thread with Ryan Gomez (latest, 21 Nov
2026). It is the two-hour standalone task: it validates synthetic files
only. It does not read `results/`, does not change `compute_recall.py` or
`bootstrap_ci.py`, and does not run retrieval, indexing or a model.

## What it checks

- **Schema** — each record has exactly `query_id`, `score`, `dataset_id`,
  `metric`, `scale`, `k`; `metric` is `recall`, `scale` is `per-query`,
  `k` is 2, 5 or 10, `score` is a number in [0, 1].
- **IDs** — strict ID-set equality between the two files. IDs are sorted
  before pairing, so a reordered file passes and a missing or extra ID
  blocks validation and is named in the report.
- **Metadata** — `dataset_id`, `metric`, `scale` and `k` must agree within
  each file and between the two files.
- **Manifest** — `manifest.json`, next to the two files, must record each
  file's SHA-256, `n` and recomputed mean score, plus the declared
  metadata and the exact analysis revision (`v0.3`). A hash or mean
  mismatch blocks validation. The manifest is a consistency check only;
  it is not independent proof of provenance.
- **Recomputed recall** — means are recomputed from the scores, never
  trusted from the manifest. Per-query differences use tolerance 1e-9,
  so improved / worsened / tied are mutually exclusive and sum to `n`.

A blocked run still writes a diagnostic report, clearly marked
`"status": "diagnostic"`. It is not a validated result.

## Run

```bash
python check_synthetic.py fixtures/reordered/baseline.json \
    fixtures/reordered/variant.json fixtures/reordered/manifest.json \
    --report fixtures/reordered/report.json
# VALIDATED: n=5 k=10 baseline=0.6000 variant=0.4000 diff=+0.2000
#   improved=1 worsened=0 tied=4

python check_synthetic.py fixtures/mismatched/baseline.json \
    fixtures/mismatched/variant.json fixtures/mismatched/manifest.json \
    --report fixtures/mismatched/report.json
# BLOCKED: ... diagnostic report written ...
```

Exit 0 is validated, exit 2 is blocked (diagnostic report written),
exit 1 is unreadable input. Standard library only; Python 3.12.

```bash
python -m unittest discover -s tests -v
```

## Fixtures

Both fixtures are synthetic, invented for this checker, and use the
agreed field names. Neither is a real MuSiQue result.

- `fixtures/reordered/` — the same five query IDs in a different order
  in the variant file. Expected: validated. This is the reordered-ID
  fixture: order alone must not change the pairing or the result.
- `fixtures/mismatched/` — the variant file replaces `syn-q05` with
  `syn-q99`. Expected: blocked, with `syn-q05` and `syn-q99` named as
  the offending IDs. This is the mismatched-ID fixture.

## Limits

- Synthetic files only, one `k` per file, recall only.
- The checker cannot verify that a score was measured correctly, only
  that the two files and their manifest are internally consistent.
- No resampling is done here; sorting before pairing is what makes a
  later paired bootstrap order-independent.
