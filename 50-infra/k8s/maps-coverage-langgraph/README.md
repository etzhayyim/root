# maps-coverage-langgraph

`maps-coverage-ticker` と `maps-coverage-stats-ticker` の LangGraph 版。`bpmn-dispatcher` 経由 curl tick (2026-05-10 以降 404 で停止) を置き換える。

## 構成

| CronJob | Schedule | Graph 構造 |
|---|---|---|
| `maps-coverage-ticker` | `*/1 * * * *` | StateGraph + Pregel `Send`: `advance → (fan-out per picked job) → aggregate → refresh → END` |
| `maps-coverage-stats-ticker` | `*/15 * * * *` | StateGraph chain: `refresh → END` |

両方とも:

- Image: `ghcr.io/etzhayyim/pymagatama:ndl-oai-resident-...` (ndl-online-oai-resident と同一)
- 接続: `mitama-udf-pool-rw` secret の `RW_URL` で Kotoba/Datomic 直接
- 実装: `pymagatama.ingest.maps_collection.{advance_coverage, refresh_coverage_stats}` を `asyncio.to_thread` で wrap して node にする
- graph 定義は CronJob YAML 内 inline (image 再ビルド不要)

## 旧フロー (廃止)

```
CronJob (curl) → bpmn-dispatcher → legacy broker worker → batchCoverageCycle
```

2026-05-10 17:59 UTC 以降、`com.etzhayyim.apps.maps.batchCoverageCycle` の lexicon binding が dispatcher cache から消えて 404。`maps-coverage-stats-ticker` も同様。

## 新フロー

```
CronJob pod
  python -c '... LangGraph StateGraph ...'
    advance_node (asyncio.to_thread → advance_coverage)
      Send fan-out per picked job
        run_item (in-memory status record, reducer=list.append)
    aggregate (barrier)
    refresh_node (asyncio.to_thread → refresh_coverage_stats, 条件付き)
  → Kotoba/Datomic (vertex_maps_*, view_maps_coverage_gap_ranked)
```

## Apply

```bash
# 既存 (bpmn 版) を replace
kubectl apply -f 50-infra/k8s/maps-coverage-langgraph/cronjob-cycle.yaml
kubectl apply -f 50-infra/k8s/maps-coverage-langgraph/cronjob-stats.yaml

# 確認
kubectl get cronjob -n mitama-udf maps-coverage-ticker maps-coverage-stats-ticker
kubectl create job -n mitama-udf maps-coverage-ticker-smoke --from=cronjob/maps-coverage-ticker
kubectl logs -n mitama-udf -l job-name=maps-coverage-ticker-smoke -f
```

## Rollback

旧 manifests は git history (commit `2d58b66585a` 以前) を参照。`kubectl apply` で復元可能だが、bpmn-dispatcher 側の lexicon binding 復旧が別途必要。
