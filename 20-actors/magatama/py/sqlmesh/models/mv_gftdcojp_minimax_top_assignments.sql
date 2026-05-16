-- Gftdcojp minimax top assignments: assignments passing spirit floor with regret/loss/value.
MODEL (
  name dev.mv_gftdcojp_minimax_top_assignments,
  kind FULL,
  dialect postgres,
  description 'Per minimax decision (passing spirit floor): candidate, person, regret, loss, value, recommendation.',
  grain [decision_kind, candidate_target, person_did],
  tags [gftdcojp, minimax, assignment, decision]
);

SELECT
  decision_kind,
  candidate_target,
  person_did,
  regret_score,
  worst_case_loss_jpy,
  expected_value_jpy,
  spirit_floor_violated,
  ip_leak_risk,
  recommendation,
  assessed_at
FROM vertex_gftdcojp_person_minimax
WHERE spirit_floor_violated = FALSE
