MERGE (p:SeigenPolicy {policyId: $policyId})
SET
  p.provider = $provider,
  p.product = $product,
  p.version = $version,
  p.sourceDate = $sourceDate,
  p.cueSource = $cueSource,
  p.updatedAt = datetime(),
  p.actorDid = $actorDid,
  p.locale = $locale
RETURN p.policyId AS policyId, p.version AS version, p.updatedAt AS updatedAt;
