-- GFTD delegation chain: flat projection of delegation edges.
MODEL (
  name dev.mv_gftd_delegation_chain,
  kind FULL,
  dialect postgres,
  description 'Per delegation edge: delegatee DID, delegator DID, RACI role, scope.',
  grain [delegatee_did, delegator_did],
  tags [gftd, delegation, raci, identity]
);

SELECT
  dst_vid AS delegatee_did,
  src_vid AS delegator_did,
  raci,
  role,
  scope
FROM edge_gftd_delegates_to
