CREATE VIEW view_resource_flow_actor_label AS
    -- Branch A: facade DID lookup (did:web / did:plc).
    SELECT
      p.did                                                AS did,
      'facade'::VARCHAR                                    AS kind,
      p.did                                                AS facade_did,
      e.root_did                                           AS root_did,
      p.handle                                             AS handle,
      p.display_name                                       AS display_name,
      p.description                                        AS description,
      e.root_identity_addr                                 AS root_identity_addr
    FROM vertex_profile p
    LEFT JOIN edge_erc725_facade_did e ON e.facade_did = p.did
    UNION ALL
    -- Branch B: ERC725 root DID lookup. Resolves through facade for the
    -- display fields; if no facade exists yet, the row still surfaces
    -- the root_did for completeness (display_name = NULL).
    SELECT
      e.root_did                                           AS did,
      'root'::VARCHAR                                      AS kind,
      e.facade_did                                         AS facade_did,
      e.root_did                                           AS root_did,
      p.handle                                             AS handle,
      p.display_name                                       AS display_name,
      p.description                                        AS description,
      e.root_identity_addr                                 AS root_identity_addr
    FROM edge_erc725_facade_did e
    LEFT JOIN vertex_profile p ON p.did = e.facade_did;
