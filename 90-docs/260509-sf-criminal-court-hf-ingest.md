# SF Criminal Court HF Ingest + World Export

`70-tools/scripts/ingest/legal-court-hf-datasets.py` covers two related jobs:

1. Ingest `jamiequint/sf_criminal_court` from Hugging Face into
   `vertex_hf_dataset` and `vertex_hf_dataset_record`.
2. Create a non-SF worldwide court-record parquet export from
   `vertex_legal_corpus_document`, optionally pushing it to a Hugging Face
   dataset repo.

The SF dataset contains public court records with names and case numbers. The
script defaults to `sensitivity_ord=1`, which keeps rows out of
`mv_hf_dataset_text_for_training`. Use `--allow-training` only after the target
use has passed policy review.

## Smoke Test

```bash
python3 70-tools/scripts/ingest/legal-court-hf-datasets.py \
  ingest-sf \
  --table attorneys \
  --limit 1 \
  --dry-run
```

## Ingest SF Dataset

```bash
export KOTOBA_URL='postgresql://...'
export HF_TOKEN='...'

python3 70-tools/scripts/ingest/legal-court-hf-datasets.py ingest-sf
```

Limit to one table while testing:

```bash
python3 70-tools/scripts/ingest/legal-court-hf-datasets.py \
  ingest-sf \
  --table cases \
  --limit 1000
```

## Export Worldwide Non-SF Dataset

```bash
export KOTOBA_URL='postgresql://...'

python3 70-tools/scripts/ingest/legal-court-hf-datasets.py \
  export-world \
  --out-dir /tmp/world_criminal_court \
  --limit 1000000
```

The export writes:

- `cases.parquet`
- `register_of_actions.parquet`
- `sources.parquet`
- `README.md`

Push to Hugging Face:

```bash
export HF_TOKEN='...'

python3 70-tools/scripts/ingest/legal-court-hf-datasets.py \
  export-world \
  --repo-id etzhayyim/world_criminal_court \
  --push
```

Use `--no-criminal-only` if the worldwide corpus should include all public
court records rather than only rows with criminal/penal indicators.
