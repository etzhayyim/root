DELETE FROM dim_app_host_alias
    WHERE alias_host = 'pb';

INSERT INTO dim_app_host_alias (alias_host, canonical_host)
    VALUES ('pb', 'public-fund');

DELETE FROM dim_world_domain_collection
    WHERE domain = 'public_fund';

INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES
      ('public_fund', 'public-fund', 'ai.gftd.apps.publicFund.fundProgram', 150000, 'public funds', 'governance'),
      ('public_fund', 'public-fund', 'ai.gftd.apps.publicFund.fundCampaign', 150000, 'public funds', 'governance'),
      ('public_fund', 'public-fund', 'ai.gftd.apps.publicFund.pledge', 150000, 'public funds', 'governance'),
      ('public_fund', 'public-fund', 'ai.gftd.apps.publicFund.routedAllocation', 150000, 'public funds', 'governance'),
      ('public_fund', 'public-fund', 'ai.gftd.apps.publicFund.eligibilityPolicy', 150000, 'public funds', 'governance'),
      ('public_fund', 'public-fund', 'ai.gftd.apps.publicFund.application', 150000, 'public funds', 'governance'),
      ('public_fund', 'public-fund', 'ai.gftd.apps.publicFund.decision', 150000, 'public funds', 'governance'),
      ('public_fund', 'public-fund', 'ai.gftd.apps.publicFund.disbursement', 150000, 'public funds', 'governance');
