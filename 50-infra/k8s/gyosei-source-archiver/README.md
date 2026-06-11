# gyosei-source-archiver

Kubernetes CronJob for archiving `gyosei` legal sources to Backblaze B2.

Namespace: `mitama-udf`

## What it does

- mounts the current repo's `capture_gyosei_sources_to_b2.py`
- mounts `80-data/gyosei/source-manifest.json`
- installs runtime dependencies in the job container
- runs the archiver on a schedule
- skips unchanged sources by comparing current source sha256 with prior `metadata.json`
- upserts `vertex_gyosei_source_blob` when `KOTOBA_URL` is available

## Prereqs

Create the B2 secret in `mitama-udf`:

```bash
kubectl create ns mitama-udf 2>/dev/null || true
kubectl -n mitama-udf create secret generic gyosei-source-archiver-b2 \
  --from-literal=etzhayyim_B2_KEY_ID="$(security find-generic-password -s etzhayyim.b2 -a APPLICATION_KEY_ID -w)" \
  --from-literal=etzhayyim_B2_APP_KEY="$(security find-generic-password -s etzhayyim.b2 -a APPLICATION_KEY -w)"
```

Optional overrides:

```bash
kubectl -n mitama-udf create secret generic gyosei-source-archiver-env \
  --from-literal=etzhayyim_B2_BUCKET=etzhayyim-nats \
  --from-literal=etzhayyim_B2_ENDPOINT=https://s3.us-west-004.backblazeb2.com \
  --from-literal=etzhayyim_B2_PREFIX=legal-sources/gyosei
```

The job also reuses secret `mitama-udf-pool-rw` when present so archived
sources are mirrored into graph table `vertex_gyosei_source_blob`.

## Deploy

```bash
cd /Users/junkawasaki/github/etzhayyim-root
50-infra/k8s/gyosei-source-archiver/deploy.sh
```

## Verify

```bash
kubectl -n mitama-udf get cronjob gyosei-source-archiver
JOB_NAME="gyosei-source-archiver-manual-$(date +%s)"
kubectl -n mitama-udf create job --from=cronjob/gyosei-source-archiver "$JOB_NAME"
kubectl -n mitama-udf logs "job/$JOB_NAME"
```

## Notes

- This job intentionally does not use the `default` namespace.
- The container installs `chromium`, `poppler-utils`, `boto3`, and `Pillow` at runtime.
- Schedule defaults to daily `17 2 * * *` UTC and can be overridden with `SCHEDULE=... deploy.sh`.
