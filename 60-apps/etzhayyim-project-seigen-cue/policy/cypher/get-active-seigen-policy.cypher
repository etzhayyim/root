MATCH (p:SeigenPolicy {policyId: $policyId})
RETURN
  p.policyId AS policyId,
  p.provider AS provider,
  p.product AS product,
  p.version AS version,
  p.sourceDate AS sourceDate,
  p.cueSource AS cueSource,
  p.locale AS locale,
  p.updatedAt AS updatedAt,
  p.actorDid AS actorDid
ORDER BY p.updatedAt DESC
LIMIT 1;
