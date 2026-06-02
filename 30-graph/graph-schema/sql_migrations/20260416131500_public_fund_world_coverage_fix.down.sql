DELETE FROM dim_world_domain_collection
    WHERE domain = 'public_fund'
      AND collection IN (
        'com.etzhayyim.apps.publicFund.fundProgram',
        'com.etzhayyim.apps.publicFund.fundCampaign',
        'com.etzhayyim.apps.publicFund.pledge',
        'com.etzhayyim.apps.publicFund.routedAllocation',
        'com.etzhayyim.apps.publicFund.eligibilityPolicy',
        'com.etzhayyim.apps.publicFund.application',
        'com.etzhayyim.apps.publicFund.decision',
        'com.etzhayyim.apps.publicFund.disbursement'
      );

INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('public_fund', 'public-fund', 'com.etzhayyim.coverage.bootstrap', 150000, 'public funds', 'governance');

DELETE FROM dim_app_host_alias
    WHERE alias_host = 'pb' AND canonical_host = 'public-fund';
