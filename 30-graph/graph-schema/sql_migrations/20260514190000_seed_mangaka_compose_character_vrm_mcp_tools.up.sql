-- P16-b of ADR-2605141200 — register the 7 NEW MCP tools backing
-- `compose_character_vrm.topology.yaml`. attachCharacterVrm (P13) is
-- already registered by 20260514180000 and is the 8th node in the
-- Pregel; here we cover the upstream pipeline.
--
-- Self-hosted invariant: every pod_image referenced in the
-- descriptions is on `ghcr.io/etzhayyimcojp/*` and runs open-weight / OSS
-- models on the VKE pool. External commercial APIs (Mixamo, OpenAI,
-- Anthropic, Hume, Adobe, …) are train-only teacher signals and never
-- appear on this runtime path — see `data/ghosthacker/TRAINING_PIPELINE.md`.
--
-- vertex_id slug = NSID with dots replaced by `-` (sync-mcp-registry.py
-- convention). PK=vertex_id makes the upsert idempotent and lets
-- `sync-mcp-registry.py --apply` reconcile schema_hash / version on
-- the next `etzhayyim contract sync`.

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord,
   nsid, actor_did, actor_host, lexicon_type, description,
   input_schema, output_schema,
   visibility, version, enabled, source_path,
   org_id, user_id, actor_id, created_at)
VALUES
  -- 1. loadCharacterProfile
  ('at://did:web:mangaka.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-mangaka-tools-loadCharacterProfile',
   0, 0,
   'com.etzhayyim.apps.mangaka.tools.loadCharacterProfile',
   'did:web:mangaka.etzhayyim.com', 'mangaka.etzhayyim.com', 'procedure',
   'P16 step 1: read kind=character row + B2 reference image, emit profile JSON + base64 PNG.',
   '{"type":"object","required":["characterRkey"],"properties":{"characterRkey":{"type":"string"},"rwUrl":{"type":"string"}}}',
   '{"type":"object","properties":{"profile":{"type":"object"},"referenceImageB64":{"type":"string"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/mangaka/tools/loadCharacterProfile.json',
   'anon', 'anon', '', '2026-05-14T19:00:00Z'),

  -- 2. generateMultiviewAnime (GPU — pod_pool vke-render-pool)
  ('at://did:web:mangaka.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-mangaka-tools-generateMultiviewAnime',
   0, 0,
   'com.etzhayyim.apps.mangaka.tools.generateMultiviewAnime',
   'did:web:mangaka.etzhayyim.com', 'mangaka.etzhayyim.com', 'procedure',
   'P16 step 3: CharacterGen anime-tuned multi-view (MIT, self-hosted on ghcr.io/etzhayyimcojp/character-gen:0.1).',
   '{"type":"object","required":["referenceImageB64","prompts"],"properties":{"referenceImageB64":{"type":"string"},"prompts":{"type":"object"},"numViews":{"type":"integer","minimum":4,"maximum":6},"seed":{"type":"integer"}}}',
   '{"type":"object","properties":{"multiviewImages":{"type":"array","items":{"type":"string"}},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/mangaka/tools/generateMultiviewAnime.json',
   'anon', 'anon', '', '2026-05-14T19:00:00Z'),

  -- 3. reconstructMesh (GPU — pod_pool vke-render-pool)
  ('at://did:web:mangaka.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-mangaka-tools-reconstructMesh',
   0, 0,
   'com.etzhayyim.apps.mangaka.tools.reconstructMesh',
   'did:web:mangaka.etzhayyim.com', 'mangaka.etzhayyim.com', 'procedure',
   'P16 step 4: Hunyuan3D-2 multi-view -> textured glb (OSS, self-hosted on ghcr.io/etzhayyimcojp/hunyuan3d-2:0.2).',
   '{"type":"object","required":["multiviewImages"],"properties":{"multiviewImages":{"type":"array","items":{"type":"string"}},"polyBudget":{"type":"integer","minimum":5000,"maximum":100000}}}',
   '{"type":"object","properties":{"meshGlbB64":{"type":"string"},"triCount":{"type":"integer"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/mangaka/tools/reconstructMesh.json',
   'anon', 'anon', '', '2026-05-14T19:00:00Z'),

  -- 4. extractFacialBlendshapes (CPU — pod_pool vke-cpu-pool)
  ('at://did:web:mangaka.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-mangaka-tools-extractFacialBlendshapes',
   0, 0,
   'com.etzhayyim.apps.mangaka.tools.extractFacialBlendshapes',
   'did:web:mangaka.etzhayyim.com', 'mangaka.etzhayyim.com', 'procedure',
   'P16 step 5: MediaPipe Face Landmarker (Apache-2.0, self-hosted on ghcr.io/etzhayyimcojp/mediapipe-face:1). 52 ARKit weights + 478 landmarks.',
   '{"type":"object","required":["referenceImageB64"],"properties":{"referenceImageB64":{"type":"string"}}}',
   '{"type":"object","properties":{"blendshapePack":{"type":"object"},"headLandmark":{"type":"object"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/mangaka/tools/extractFacialBlendshapes.json',
   'anon', 'anon', '', '2026-05-14T19:00:00Z'),

  -- 5. autoRigHumanoid (CPU — Blender Rigify primary + in-house RigNet fallback, self-hosted only)
  ('at://did:web:mangaka.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-mangaka-tools-autoRigHumanoid',
   0, 0,
   'com.etzhayyim.apps.mangaka.tools.autoRigHumanoid',
   'did:web:mangaka.etzhayyim.com', 'mangaka.etzhayyim.com', 'procedure',
   'P16 step 6: Blender Rigify template-fit + in-house RigNet distill fallback (ghcr.io/etzhayyimcojp/blender-rigify-rignet:0.1). No external rigging API — train-only teacher signals.',
   '{"type":"object","required":["meshGlbB64","blendshapePack"],"properties":{"meshGlbB64":{"type":"string"},"blendshapePack":{"type":"object"},"forceFallback":{"type":"boolean"}}}',
   '{"type":"object","properties":{"riggedGlbB64":{"type":"string"},"rigSource":{"type":"string"},"boneCount":{"type":"integer"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/mangaka/tools/autoRigHumanoid.json',
   'anon', 'anon', '', '2026-05-14T19:00:00Z'),

  -- 6. bindVrm (CPU — Blender headless + saturday06 VRM Add-on)
  ('at://did:web:mangaka.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-mangaka-tools-bindVrm',
   0, 0,
   'com.etzhayyim.apps.mangaka.tools.bindVrm',
   'did:web:mangaka.etzhayyim.com', 'mangaka.etzhayyim.com', 'procedure',
   'P16 step 7: Blender + saturday06 VRM Add-on -> VRM 1.0 binary (self-hosted on ghcr.io/etzhayyimcojp/blender-vrm:4.1).',
   '{"type":"object","required":["riggedGlbB64","blendshapePack","profile"],"properties":{"riggedGlbB64":{"type":"string"},"blendshapePack":{"type":"object"},"profile":{"type":"object"},"metaOverride":{"type":"object"}}}',
   '{"type":"object","properties":{"vrmB64":{"type":"string"},"byteSize":{"type":"integer"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/mangaka/tools/bindVrm.json',
   'anon', 'anon', '', '2026-05-14T19:00:00Z'),

  -- 7. validateVrm (CPU — kami_vrm::parse_vrm in-repo)
  ('at://did:web:mangaka.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-mangaka-tools-validateVrm',
   0, 0,
   'com.etzhayyim.apps.mangaka.tools.validateVrm',
   'did:web:mangaka.etzhayyim.com', 'mangaka.etzhayyim.com', 'procedure',
   'P16 step 8: parse with kami_vrm::parse_vrm — magic + humanoid bones >=18 + ARKit minimum set + tri budget. Drives DMN retry edge to bindVrm.',
   '{"type":"object","required":["vrmB64"],"properties":{"vrmB64":{"type":"string"}}}',
   '{"type":"object","properties":{"valid":{"type":"boolean"},"warnings":{"type":"array","items":{"type":"string"}},"errors":{"type":"array","items":{"type":"string"}},"stats":{"type":"object"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/mangaka/tools/validateVrm.json',
   'anon', 'anon', '', '2026-05-14T19:00:00Z');

FLUSH;
