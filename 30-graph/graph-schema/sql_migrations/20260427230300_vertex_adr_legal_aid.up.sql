CREATE TABLE vertex_adr_arbitrator (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      arbitrator_did     varchar NOT NULL,
      full_name          varchar NOT NULL,
      institution        varchar NOT NULL,
      panel              varchar,
      nationality        varchar,
      languages_csv      varchar,
      expertise_csv      varchar,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    );

CREATE INDEX idx_adr_arbitrator_did ON vertex_adr_arbitrator(arbitrator_did);

CREATE INDEX idx_adr_arbitrator_institution ON vertex_adr_arbitrator(institution);

CREATE TABLE vertex_adr_case (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      case_ref           varchar NOT NULL,
      institution        varchar NOT NULL,
      panel              varchar,
      seat               varchar,
      governing_law      varchar,
      parties_enc        varchar,
      claim_amount_enc   varchar,
      currency           varchar,
      status             varchar NOT NULL,
      opened_at          varchar,
      award_at           varchar,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    );

CREATE INDEX idx_adr_case_institution ON vertex_adr_case(institution);

CREATE TABLE vertex_legal_aid_office (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      office_did         varchar NOT NULL,
      display_name       varchar NOT NULL,
      jurisdiction       varchar NOT NULL,
      office_type        varchar NOT NULL,
      address_locality   varchar,
      languages_csv      varchar,
      specialties_csv    varchar,
      intake_url         varchar,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    );

CREATE INDEX idx_legal_aid_office_did ON vertex_legal_aid_office(office_did);

CREATE INDEX idx_legal_aid_office_jurisdiction ON vertex_legal_aid_office(jurisdiction);

CREATE TABLE vertex_legal_aid_case (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      office_did         varchar NOT NULL,
      applicant_hash     varchar NOT NULL,
      applicant_pii_enc  varchar,
      matter_area        varchar NOT NULL,
      income_bracket     varchar,
      language_code      varchar,
      intake_channel     varchar,
      opened_at          varchar NOT NULL,
      closed_at          varchar,
      status             varchar NOT NULL,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    );

CREATE INDEX idx_legal_aid_case_office ON vertex_legal_aid_case(office_did);

CREATE INDEX idx_legal_aid_case_applicant ON vertex_legal_aid_case(applicant_hash);
