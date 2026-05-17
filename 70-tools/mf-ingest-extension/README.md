# MF CSV Ingest Helper (Chrome MV3)

Unpacked Chrome extension for ADR-0031 MoneyForward replacement pipeline.
Renames CSV downloads from the four MoneyForward cloud services into
`~/Downloads/mf-ingest/<canonical-name>.csv` so the ingest script can
pick them up without guessing.

## Load

1. Open `chrome://extensions` in the Chrome used for MoneyForward.
2. Toggle **Developer mode** (top right).
3. Click **Load unpacked** and pick this directory
   (`70-tools/mf-ingest-extension/`).
4. The extension icon (puzzle piece) appears on the toolbar. Pin it.

## Use

1. Click the extension icon → popup.
2. Pick the target name (e.g. `mf_journals.csv`).
3. In the MoneyForward tab, trigger the normal CSV export
   (エクスポート → MF形式 / CSV出力 / CSV エクスポート).
4. Chrome's next download from `*.moneyforward.com` goes to
   `~/Downloads/mf-ingest/<canonical-name>.csv`
   (conflict action: overwrite).
5. Popup shows "Captured" when done. Pick the next target.

`/tmp/mf-ingest/` is symlinked to the same directory, so the ingest
script at `30-graph/graph-schema/scripts/` can read from either path.

## Scope

Host permissions limited to the four MoneyForward cloud origins:
`accounting.moneyforward.com`, `invoice.moneyforward.com`,
`contract.moneyforward.com`, `pc.moneyforward.com`. The
`onDeterminingFilename` listener further filters by URL before
renaming. Other downloads pass through untouched.

## Privacy

No cookies, response bodies, or page contents are read. The extension
only observes download events (URL + suggested filename) and rewrites
the save path. Session storage holds only the pending target name.

## Related

- `90-docs/adr/0031-moneyforward-actor-replacement.md` — pipeline spec
- `30-graph/graph-schema/migrations/20260417200000_moneyforward_replacement_base.ts` — target schema
