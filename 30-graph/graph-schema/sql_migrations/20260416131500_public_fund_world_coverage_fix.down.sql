DELETE FROM dim_world_domain_collection
    WHERE domain = 'public_fund'
      AND collection IN (
        'ai.gftd.apps.publicFund.fundProgram',
        'ai.gftd.apps.publicFund.fundCampaign',
        'ai.gftd.apps.publicFund.pledge',
        'ai.gftd.apps.publicFund.routedAllocation',
        'ai.gftd.apps.publicFund.eligibilityPolicy',
        'ai.gftd.apps.publicFund.application',
        'ai.gftd.apps.publicFund.decision',
        'ai.gftd.apps.publicFund.disbursement'
      );

INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('public_fund', 'public-fund', 'ai.gftd.coverage.bootstrap', 150000, 'public funds', 'governance');

DELETE FROM dim_app_host_alias
    WHERE alias_host = 'pb' AND canonical_host = 'public-fund';
