-- GFTD op log head: latest op sequence number per DID.
MODEL (
  name dev.mv_gftd_op_log_head,
  kind FULL,
  dialect postgres,
  description 'Per DID: maximum op_seq (head of the op log).',
  grain [did],
  tags [gftd, did, op_log, identity]
);

SELECT
  did,
  MAX(op_seq) AS head_seq
FROM vertex_gftd_op_log
GROUP BY did
