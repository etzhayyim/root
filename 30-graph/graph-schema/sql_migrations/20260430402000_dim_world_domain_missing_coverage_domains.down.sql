DELETE FROM dim_world_domain
    WHERE domain IN (
      'gov_org', 'gov_municipality', 'food_product', 'drug_product',
      'blockchain_actor', 'trademark', 'work', 'legal_aid',
      'investor_fund', 'mutual_fund', 'pension_fund', 'private_fund',
      'government_fund', 'sovereign_fund', 'adr', 'family',
      'game_actor', 'game_item', 'energy_facility', 'crypto_asset_freeze',
      'rare_earth_coverage', 'gtin_product', 'industry', 'dns_observation',
      'business_person', 'spatial', 'transport'
    );
