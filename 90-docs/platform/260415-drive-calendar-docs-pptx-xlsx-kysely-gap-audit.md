# Kysely / Vertex-Edge-MV Gap Audit (drive, calendar, docs, pptx, excel)

- Date: 2026-04-15
- Scope:
  - `etzhayyim-project-drive`
  - `etzhayyim-project-calendar`
  - `etzhayyim-project-docs`
  - `etzhayyim-project-pptx`
  - `etzhayyim-project-sheets` (Excel相当)
  - `20-actors/xlsx` (Excel actor)

## Ground Truth

- Graph storage has canonical catch-all table `vertex_repo_record` for AT records.
  - `30-graph/graph-schema/src/database.ts` lines 3816-3824, 4562
- `vertex_<label>` / `edge_<type>` naming convention is the policy.
  - `30-graph/graph-schema/CLAUDE.md` lines 31-33

## App Collections (declared)

- Drive collections:
  - `com.etzhayyim.apps.drive.file`
  - `com.etzhayyim.apps.drive.folder`
  - `com.etzhayyim.apps.drive.fileShare`
  - `com.etzhayyim.apps.drive.fileDeletion`
  - `com.etzhayyim.apps.drive.fileMove`
  - `com.etzhayyim.apps.drive.fileStatusUpdate`
  - `com.etzhayyim.apps.drive.fileLocationUpdate`
  - Ref: `60-apps/etzhayyim-project-drive/appview/drive-app-component/kotodama.jsonld` lines 58-64

- Calendar collections (used in app code):
  - `com.etzhayyim.apps.calendar.event`
  - `com.etzhayyim.apps.calendar.invitation`
  - `com.etzhayyim.apps.calendar.recurrence`
  - `com.etzhayyim.apps.calendar.rsvp`
  - `com.etzhayyim.apps.calendar.reminder`
  - Ref: `60-apps/etzhayyim-project-calendar/appview/calendar-mcp-component/src/app.ts`

- Docs collections:
  - `com.etzhayyim.apps.docs.docsEntity`
  - `com.etzhayyim.apps.docs.docsEvent`
  - `com.etzhayyim.apps.docs.docsReport`
  - Ref: `60-apps/etzhayyim-project-docs/appview/docs-performers-r5ycqp6x/kotodama.jsonld` lines 78-80

- PPTX collections:
  - `com.etzhayyim.apps.pptx.presentation`
  - `com.etzhayyim.apps.pptx.slide`
  - `com.etzhayyim.apps.pptx.shape`
  - `com.etzhayyim.apps.pptx.textRun`
  - `com.etzhayyim.apps.pptx.image`
  - `com.etzhayyim.apps.pptx.slideTemplate`
  - Ref: `60-apps/etzhayyim-project-pptx/appview/etzhayyim-wasm-pptx-t53br1o0/kotodama.jsonld` lines 70-75

- Sheets collections (Excel相当):
  - `com.etzhayyim.apps.sheets.sheetsEntity`
  - `com.etzhayyim.apps.sheets.sheetsEvent`
  - `com.etzhayyim.apps.sheets.sheetsReport`
  - Ref: `60-apps/etzhayyim-project-sheets/appview/sheets-mcp-component/kotodama.jsonld` lines 78-80

- XLSX actor collections:
  - `com.etzhayyim.apps.xlsx.workbook`
  - `com.etzhayyim.apps.xlsx.sheet`
  - `com.etzhayyim.apps.xlsx.pivot`
  - Ref: `20-actors/xlsx/actor-manifest.jsonld` line 30

## Gap Matrix (as-is)

| Area | Kysely usage in app | Dedicated `vertex_*` | Dedicated `edge_*` | Dedicated `mv_*` | Status |
|---|---|---|---|---|---|
| drive | not found (runtime query path) | not found | not found | not found | partial (AT records only) |
| calendar | imported, but read path TODO / disabled | not found | not found | not found | missing |
| docs | not found (runtime query path) | not found | not found | not found | partial (AT records only) |
| pptx | not found (runtime query path) | not found | not found | not found | partial (AT records only) |
| sheets/excel | not found (runtime query path) | not found | not found | not found | partial (AT records only) |

### Evidence for calendar missing state

`60-apps/etzhayyim-project-calendar/appview/calendar-mcp-component/src/app.ts`
- lines 30-31: `vertex_calendar_* not in @etzhayyim/graph-schema`
- line 119: pre-existence check skipped
- line 193: events list unavailable
- line 208: event/rsvp lookup unavailable
- lines 473-480: reactive enrichment skipped

### Evidence for dedicated schema not existing

Search in graph-schema for these prefixes returned no matches:
- `vertex_calendar|edge_calendar|mv_calendar`
- `vertex_drive|edge_drive|mv_drive`
- `vertex_docs|edge_docs|mv_docs`
- `vertex_pptx|edge_pptx|mv_pptx`
- `vertex_sheets|edge_sheets|mv_sheets`
- `vertex_xlsx|edge_xlsx|mv_xlsx`

## Concrete TODO (migration backlog)

1. Calendar (priority P0)
- Add vertices:
  - `vertex_calendar_event`
  - `vertex_calendar_invitation`
  - `vertex_calendar_rsvp`
  - `vertex_calendar_reminder`
  - optional: `vertex_calendar_recurrence`
- Add edges:
  - `edge_calendar_event_owner` (event -> actor)
  - `edge_calendar_event_attendee` (event -> actor)
  - `edge_calendar_invitation_event` (invitation -> event)
  - `edge_calendar_rsvp_event` (rsvp -> event)
  - `edge_calendar_reminder_event` (reminder -> event)
- Add MVs:
  - `mv_calendar_events_by_owner_time`
  - `mv_calendar_rsvp_summary`

2. Drive
- Add vertices:
  - `vertex_drive_file`, `vertex_drive_folder`, `vertex_drive_share`
- Add edges:
  - `edge_drive_contains` (folder -> file/folder)
  - `edge_drive_shared_with` (file -> actor)
- Add MVs:
  - `mv_drive_folder_size_rollup`
  - `mv_drive_recent_activity`

3. Docs
- Add vertices:
  - `vertex_docs_entity`, `vertex_docs_event`, `vertex_docs_report`
- Add edges:
  - `edge_docs_event_entity`, `edge_docs_report_entity`
- Add MVs:
  - `mv_docs_entity_activity`

4. PPTX
- Add vertices:
  - `vertex_pptx_presentation`, `vertex_pptx_slide`, `vertex_pptx_shape`, `vertex_pptx_text_run`, `vertex_pptx_image`
- Add edges:
  - `edge_pptx_presentation_slide`, `edge_pptx_slide_shape`, `edge_pptx_shape_text_run`, `edge_pptx_shape_image`
- Add MVs:
  - `mv_pptx_slide_stats`, `mv_pptx_text_index`

5. Sheets/XLSX (Excel)
- Add vertices:
  - `vertex_xlsx_workbook`, `vertex_xlsx_sheet`, `vertex_xlsx_pivot`
  - optional: `vertex_xlsx_cell_range`
- Add edges:
  - `edge_xlsx_workbook_sheet`, `edge_xlsx_sheet_pivot`
- Add MVs:
  - `mv_xlsx_sheet_metrics`, `mv_xlsx_formula_dependency`

## Notes

- Current system can still function via `vertex_repo_record` catch-all, but typed query ergonomics and performance guarantees (`edge` joins / domain-specific MVs) are not yet established for this scope.
- For calendar, missing typed schema is already user-visible in code paths (explicit TODO + empty-result behavior).
