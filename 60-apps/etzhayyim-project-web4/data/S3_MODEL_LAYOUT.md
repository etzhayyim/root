# S3 Expert Distribution Layout

This project serves distributed expert bundles from an S3-compatible bucket
(`etzhayyim-static-sites`) and resolves them through control-plane manifests.

## Model prefixes

- `etzhayyim/etzhayyim-distributed-moe-260222` (Qwen)
  - experts: `models/qwen3-30b-a3b/experts/set-XXX.bin`
  - host: `models/qwen3-30b-a3b/host/*`
- `etzhayyim/etzhayyim-distributed-ti2v-moe-260222` (Wan2.2 TI2V)
  - experts: `models/wan2.2-ti2v-5b/experts/set-XXX.bin`
  - host: `models/wan2.2-ti2v-5b/host/*`

## Runtime manifest APIs

- list manifests: `/api/manifests`
- resolve one model manifest: `/api/manifest?model_id=<model_id>`
- resolve one set bundle: `/api/manifest/sets/<set_id>?model_id=<model_id>`

Browser workers fetch `blob_endpoint + blob_key` from manifest responses.
