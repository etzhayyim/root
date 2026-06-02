-- P16-e of ADR-2605141200 — rollback the vrmBindRetry DMN registration.

DELETE FROM vertex_dmn_model
WHERE decision_key = 'com.etzhayyim.policies.mangaka.vrmBindRetry'
  AND version = 1;
