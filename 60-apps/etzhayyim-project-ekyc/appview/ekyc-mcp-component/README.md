# etzhayyim-project-ekyc App migration

このディレクトリは `legacy-runtime/ekyc-service-ephj2jf6` の App MCP facade です。

## 方針

- App runtime 依存 (`App HTTP API`) を廃止
- MCP JSON-RPC `tools/list` と `tools/call` を `POST /api/mcp` で提供
- インメモリ実装の暫定状態を返却（本体 DB/状態整合は別コミットで拡張）

## MCP tools

- `ekyc.submit_verification`
- `ekyc.get_verification_status`
- `ekyc.list_verifications`
- `ekyc.update_verification_status`
- `ekyc.initiate_liveness_check`
- `ekyc.submit_liveness_check`
