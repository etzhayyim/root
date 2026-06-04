-- P16-e of ADR-2605141200 — register the `vrmBindRetry` DMN decision in
-- `vertex_dmn_model` so the compose_character_vrm topology's
--   `conditional_edges[*].condition_ref = dmn:com.etzhayyim.policies.mangaka.vrmBindRetry@1.0.0`
-- resolves at runtime once `pymagatama.langgraph_node_resolvers` learns
-- to evaluate DMN refs (Phase C activation, blocker shared with the
-- composeScene3dRefinement DMN).
--
-- SSoT for the XML body:
--   00-contracts/dmn/com/etzhayyim/policies/mangaka/vrmBindRetry.dmn
--
-- Idempotent — NOT EXISTS guard mirrors
-- 20260514150000_seed_mangaka_compose_scene_3d_refinement_dmn.up.sql.

INSERT INTO vertex_dmn_model (
  vertex_id, _seq, created_date, sensitivity_ord, owner_did,
  rkey, repo, did,
  decision_key, name, description, version,
  decision_type, hit_policy, aggregation,
  inputs_json, outputs_json, rules_json,
  expression_text, expression_language,
  required_decisions_json,
  dmn_xml, status
)
SELECT
  'at://did:web:mangaka.etzhayyim.com/com.etzhayyim.dmn.model/vrmBindRetry-v1',
  0, '2026-05-14'::date, 0, 'did:web:mangaka.etzhayyim.com',
  'vrmBindRetry-v1',
  'did:web:mangaka.etzhayyim.com',
  'did:web:mangaka.etzhayyim.com',
  'com.etzhayyim.policies.mangaka.vrmBindRetry',
  'vrmBindRetry',
  'compose_character_vrm validate_vrm routing — accept on valid=true, retry bind_vrm once on valid=false with iteration<2, else reject.',
  1,
  'decisionTable',
  'FIRST',
  NULL,
  $$[
    {"name": "valid", "typeRef": "boolean"},
    {"name": "iteration", "typeRef": "number"}
  ]$$,
  $$[
    {"name": "route", "typeRef": "string"},
    {"name": "reason", "typeRef": "string"}
  ]$$,
  $$[
    {
      "id": "VrmBindRule_accept",
      "inputEntries": ["true", "-"],
      "outputEntries": ["accept", "validation-passed"]
    },
    {
      "id": "VrmBindRule_retry",
      "inputEntries": ["false", "< 2"],
      "outputEntries": ["retry", "validation-failed-retry-allowed"]
    },
    {
      "id": "VrmBindRule_reject",
      "inputEntries": ["-", "-"],
      "outputEntries": ["reject", "validation-failed-budget-exhausted"]
    }
  ]$$,
  NULL,
  NULL,
  NULL,
  $$<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="https://www.omg.org/spec/DMN/20191111/MODEL/"
             id="Definitions_vrm_bind_retry"
             name="vrmBindRetry"
             namespace="https://etzhayyim.ai/dmn/mangaka">
  <decision id="com.etzhayyim.policies.mangaka.vrmBindRetry"
            name="vrmBindRetry">
    <decisionTable id="DecisionTable_vrmBindRetry" hitPolicy="FIRST">
      <input id="Input_valid">
        <inputExpression id="InputExpression_valid" typeRef="boolean">
          <text>valid</text>
        </inputExpression>
      </input>
      <input id="Input_iteration">
        <inputExpression id="InputExpression_iteration" typeRef="number">
          <text>iteration</text>
        </inputExpression>
      </input>
      <output id="Output_route" label="route" typeRef="string" name="route"/>
      <output id="Output_reason" label="reason" typeRef="string" name="reason"/>
      <rule id="VrmBindRule_accept">
        <inputEntry id="VrmBindRule_accept_ie_valid"><text>true</text></inputEntry>
        <inputEntry id="VrmBindRule_accept_ie_iteration"><text>-</text></inputEntry>
        <outputEntry id="VrmBindRule_accept_oe_route"><text>"accept"</text></outputEntry>
        <outputEntry id="VrmBindRule_accept_oe_reason"><text>"validation-passed"</text></outputEntry>
      </rule>
      <rule id="VrmBindRule_retry">
        <inputEntry id="VrmBindRule_retry_ie_valid"><text>false</text></inputEntry>
        <inputEntry id="VrmBindRule_retry_ie_iteration"><text>&lt; 2</text></inputEntry>
        <outputEntry id="VrmBindRule_retry_oe_route"><text>"retry"</text></outputEntry>
        <outputEntry id="VrmBindRule_retry_oe_reason"><text>"validation-failed-retry-allowed"</text></outputEntry>
      </rule>
      <rule id="VrmBindRule_reject">
        <inputEntry id="VrmBindRule_reject_ie_valid"><text>-</text></inputEntry>
        <inputEntry id="VrmBindRule_reject_ie_iteration"><text>-</text></inputEntry>
        <outputEntry id="VrmBindRule_reject_oe_route"><text>"reject"</text></outputEntry>
        <outputEntry id="VrmBindRule_reject_oe_reason"><text>"validation-failed-budget-exhausted"</text></outputEntry>
      </rule>
    </decisionTable>
  </decision>
</definitions>$$,
  'active'
WHERE NOT EXISTS (
  SELECT 1 FROM vertex_dmn_model
  WHERE decision_key = 'com.etzhayyim.policies.mangaka.vrmBindRetry'
    AND version = 1
);
