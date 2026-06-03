-- P13 of ADR-2605141200 — register the attachCharacterVrm ingestion tool.
-- Operators / artists call this via the MCP adapter at
-- atproto.etzhayyim.com/xrpc/com.etzhayyim.mcp.message (or directly against the pod's
-- /xrpc/{nsid}) to attach a VRM 1.0 binary to a vertex_mangaka character.
-- The blob lands at `blobs/mangaka/vrm/{sha256hex}` and the character
-- row's `props.vrmBlobKey` gets patched in-place.
--
-- Follow-on to the P10.2b seed (20260514160000); rolls forward the
-- vertex_mcp_tool_def list to 9 mangaka.tools.* rows.

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord,
   nsid, actor_did, actor_host, lexicon_type, description,
   input_schema, output_schema,
   visibility, version, enabled, source_path,
   org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:mangaka.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-mangaka-tools-attachCharacterVrm',
   0, 0,
   'com.etzhayyim.apps.mangaka.tools.attachCharacterVrm',
   'did:web:mangaka.etzhayyim.com', 'mangaka.etzhayyim.com', 'procedure',
   'P13 VRM ingestion: glTF magic check + B2 content-addressed PUT + character vertex props patch.',
   '{"type":"object","required":["characterRkey","vrmContentB64"],"properties":{"characterRkey":{"type":"string"},"vrmContentB64":{"type":"string"},"rwUrl":{"type":"string"}}}',
   '{"type":"object","properties":{"blobKey":{"type":"string"},"vertexId":{"type":"string"},"status":{"type":"string"},"warning":{"type":"string"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/mangaka/tools/attachCharacterVrm.json',
   'anon', 'anon', '', '2026-05-14T18:00:00Z');

FLUSH;
