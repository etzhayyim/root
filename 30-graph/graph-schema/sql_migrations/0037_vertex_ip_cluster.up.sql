CREATE TABLE IF NOT EXISTS vertex_patent (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      did               VARCHAR,
      status            VARCHAR,
      jurisdiction      VARCHAR,
      app_number        VARCHAR,
      pub_number        VARCHAR,
      grant_number      VARCHAR,
      title             VARCHAR,
      abstract          VARCHAR,
      ipc_codes         VARCHAR,
      cpc_codes         VARCHAR,
      filed_at          VARCHAR,
      published_at      VARCHAR,
      granted_at        VARCHAR,
      source_url        VARCHAR,
      source_did        VARCHAR,
      collected_at      VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_trademark (
      vertex_id               VARCHAR PRIMARY KEY,
      _seq                    BIGINT,
      created_date            DATE,
      sensitivity_ord         BIGINT,
      owner_did               VARCHAR,
      rkey                    VARCHAR,
      repo                    VARCHAR,
      did                     VARCHAR,
      status                  VARCHAR,
      jurisdiction            VARCHAR,
      reg_number              VARCHAR,
      app_number              VARCHAR,
      mark                    VARCHAR,
      mark_type               VARCHAR,
      nice_classes            VARCHAR,
      vienna_codes            VARCHAR,
      filed_at                VARCHAR,
      registered_at           VARCHAR,
      expires_at              VARCHAR,
      madrid_intl_reg_number  VARCHAR,
      source_url              VARCHAR,
      source_did              VARCHAR,
      collected_at            VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_work (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT,
      created_date         DATE,
      sensitivity_ord      BIGINT,
      owner_did            VARCHAR,
      rkey                 VARCHAR,
      repo                 VARCHAR,
      did                  VARCHAR,
      status               VARCHAR,
      kind                 VARCHAR,
      title                VARCHAR,
      publisher_did        VARCHAR,
      author_dids          VARCHAR,
      doi                  VARCHAR,
      isbn13               VARCHAR,
      isrc                 VARCHAR,
      iswc                 VARCHAR,
      registry             VARCHAR,
      reg_id               VARCHAR,
      license              VARCHAR,
      first_published_at   VARCHAR,
      jurisdiction         VARCHAR,
      berne_automatic      BOOLEAN,
      source_url           VARCHAR,
      source_did           VARCHAR,
      collected_at         VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_patent_cites (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      kind            VARCHAR,
      category        VARCHAR,
      examiner_did    VARCHAR,
      cited_at        VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_family_member (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      kind            VARCHAR,
      added_at        VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_classified_as (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      system          VARCHAR,
      code            VARCHAR,
      attached_at     VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_owned_by (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      role            VARCHAR,
      linked_at       VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_authored_by (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      author_order    BIGINT,
      role            VARCHAR,
      linked_at       VARCHAR
    );
