-- ADR-2605141200 P6 (graph-as-data) + ADR-2604261100 (DMN SSoT) — register
-- the `composeScene3dRefinement` DMN decision in `vertex_dmn_model` so the
-- topology assistant's
--   `conditional_edges[*].condition_ref = dmn:com.etzhayyim.policies.mangaka.composeScene3dRefinement@1.0.0`
-- resolves at runtime once `pymagatama.langgraph_node_resolvers` learns to
-- evaluate DMN refs (Phase C activation, blocker #3).
--
-- Until then the row is authoritative for audit / governance / lineage
-- tooling. The Phase A in-tree Python predicate
-- (`compose_scene_3d._route_after_critique`) implements the same decision
-- verbatim, so behaviour is unchanged at runtime.
--
-- SSoT for the XML body: 00-contracts/dmn/com/etzhayyim/policies/mangaka/composeScene3dRefinement.dmn
--
-- Idempotent — NOT EXISTS guard mirrors 20260514130000_seed_mangaka_compose_scene_3d_assistant.up.sql.

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
  'at://did:web:mangaka.etzhayyim.com/com.etzhayyim.dmn.model/composeScene3dRefinement-v1',
  0, '2026-05-14'::date, 0, 'did:web:mangaka.etzhayyim.com',
  'composeScene3dRefinement-v1',
  'did:web:mangaka.etzhayyim.com',
  'did:web:mangaka.etzhayyim.com',
  'com.etzhayyim.policies.mangaka.composeScene3dRefinement',
  'composeScene3dRefinement',
  'compose_scene_3d refinement loop routing — emits "cinematography" when score < 0.75 and iteration budget remains, else "persist".',
  1,
  'decisionTable',
  'FIRST',
  NULL,
  $$[
    {"name": "score", "typeRef": "number"},
    {"name": "iteration", "typeRef": "number"},
    {"name": "maxIter", "typeRef": "number"}
  ]$$,
  $$[
    {"name": "route", "typeRef": "string"},
    {"name": "reason", "typeRef": "string"}
  ]$$,
  $$[
    {
      "id": "RefinementRule_refine",
      "inputEntries": ["< 0.75", "< maxIter", "-"],
      "outputEntries": ["cinematography", "score-below-acceptance-bar"]
    },
    {
      "id": "RefinementRule_persist",
      "inputEntries": ["-", "-", "-"],
      "outputEntries": ["persist", "accept-or-budget-exhausted"]
    }
  ]$$,
  NULL,
  NULL,
  NULL,
  $$<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="https://www.omg.org/spec/DMN/20191111/MODEL/"
             id="Definitions_compose_scene_3d_refinement"
             name="composeScene3dRefinement"
             namespace="https://etzhayyim.ai/dmn/mangaka">
  <decision id="com.etzhayyim.policies.mangaka.composeScene3dRefinement"
            name="composeScene3dRefinement">
    <decisionTable id="DecisionTable_composeScene3dRefinement" hitPolicy="FIRST">
      <input id="Input_score">
        <inputExpression id="InputExpression_score" typeRef="number">
          <text>score</text>
        </inputExpression>
      </input>
      <input id="Input_iteration">
        <inputExpression id="InputExpression_iteration" typeRef="number">
          <text>iteration</text>
        </inputExpression>
      </input>
      <input id="Input_maxIter">
        <inputExpression id="InputExpression_maxIter" typeRef="number">
          <text>maxIter</text>
        </inputExpression>
      </input>
      <output id="Output_route" label="route" typeRef="string" name="route"/>
      <output id="Output_reason" label="reason" typeRef="string" name="reason"/>
      <rule id="RefinementRule_refine">
        <inputEntry id="RefinementRule_refine_ie_score"><text>&lt; 0.75</text></inputEntry>
        <inputEntry id="RefinementRule_refine_ie_iteration"><text>&lt; maxIter</text></inputEntry>
        <inputEntry id="RefinementRule_refine_ie_maxIter"><text>-</text></inputEntry>
        <outputEntry id="RefinementRule_refine_oe_route"><text>"cinematography"</text></outputEntry>
        <outputEntry id="RefinementRule_refine_oe_reason"><text>"score-below-acceptance-bar"</text></outputEntry>
      </rule>
      <rule id="RefinementRule_persist">
        <inputEntry id="RefinementRule_persist_ie_score"><text>-</text></inputEntry>
        <inputEntry id="RefinementRule_persist_ie_iteration"><text>-</text></inputEntry>
        <inputEntry id="RefinementRule_persist_ie_maxIter"><text>-</text></inputEntry>
        <outputEntry id="RefinementRule_persist_oe_route"><text>"persist"</text></outputEntry>
        <outputEntry id="RefinementRule_persist_oe_reason"><text>"accept-or-budget-exhausted"</text></outputEntry>
      </rule>
    </decisionTable>
  </decision>
</definitions>$$,
  'active'
WHERE NOT EXISTS (
  SELECT 1 FROM vertex_dmn_model
  WHERE decision_key = 'com.etzhayyim.policies.mangaka.composeScene3dRefinement'
    AND version = 1
);
