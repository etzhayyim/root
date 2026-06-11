# etzhayyim-scap App migration

このディレクトリは `legacy-runtime` 実装を残したまま、App 版を段階移行するための配置先です。

## 対象 App services

- `scap-j6el1fza`
- `scap-services-activities-ynpx5pvw`
- `scap-services-graphql-l9ppuofy`
- `scap-services-scap-data-service-ic0vy2wi`
- `scap-services-scap-scan-service-6aqus19w`
- `scap-services-workflow-engine-zsclvd3i`
- `scap-systems-worker-kps5k0ps`

## App 実装方針

- 各 service は `projects/*/wasm/*-component` として順次実装。
- 既存 App runtime は互換運用のため維持。
- HTTP/cron/job エンドポイントから優先して移植。
