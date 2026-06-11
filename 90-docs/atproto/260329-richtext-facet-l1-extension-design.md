---
id: richtext-facet-l1-extension
title: "Richtext Facet L1 Extension — Notion-Level Block & Inline Formatting via AT Protocol Facets"
status: active
doc_type: explanation
topic: richtext-facet-extension
authoritative: true
last_verified: 2026-03-29
authoritative_for:
  - W Protocol richtext facet extension
  - L1 inline formatting facets
  - L1 block structure facets
  - Notion feature coverage via facets
related:
  - atproto-layer-separation
  - w-protocol-at-superset
  - wit-lexicon-typed-alignment
supersedes: []
superseded_by: []
---

# Richtext Facet L1 Extension Design

## Goal

AT Protocol の facet アーキテクチャを L1 拡張し、Notion 同等の richtext を実現する。L0 (mention/link/tag) を壊さず、AT client はプレーンテキスト表示を維持。

## Decision

`kotodama:bsky/richtext@1.0.0` の `facet-feature` variant を `@field` 番号帯で L0/L1 分離し、inline formatting (7 types) + block structure (10 types) を追加。

## Architecture

### Facet = Byte-Indexed Annotation

```
text:   "見出し\n太字のテキスト\n- リスト1\n- リスト2"
facets: [
  { index: {0, 9},   features: [heading(1)] },
  { index: {10, 22}, features: [bold] },
  { index: {23, 35}, features: [bulleted-list(indent:0)] },
  { index: {36, 48}, features: [bulleted-list(indent:0)] },
]
```

- テキストはプレーン文字列 (改行 `\n` でブロック区切り)
- facet が範囲に意味を付与 (inline = 装飾、block = 構造)
- 同一範囲に複数 facet 可 (例: bold + italic、blockquote + bulleted-list)

### `@field` 番号帯

| 帯 | Layer | 用途 |
|---|---|---|
| 0–9 | L0 (AT Protocol) | mention, link, tag |
| 10–19 | L1 inline | bold, italic, underline, strikethrough, inline-code, color, math |
| 20–39 | L1 block | heading, blockquote, code-block, callout, list, todo, toggle, divider, table-cell |

AT client は未知の `@field` を無視 → テキストのみ表示。Layer Separation (Category A 拡張) 準拠。

### WIT Definition

Evidence: `00-contracts/wit/deps/kotodama-bsky/package.wit` (richtext interface)

## Notion Feature Coverage

### Inline Formatting

| Notion Feature | Facet | Status | Notes |
|---|---|---|---|
| **Bold** | `bold` | [DESIGN] | `@field 10` |
| **Italic** | `italic` | [DESIGN] | `@field 11` |
| **Underline** | `underline` | [DESIGN] | `@field 12` |
| **Strikethrough** | `strikethrough` | [DESIGN] | `@field 13` |
| **Inline code** | `inline-code` | [DESIGN] | `@field 14` |
| **Text color** | `color("red")` | [DESIGN] | 10 colors (Notion palette) |
| **Background highlight** | `color("yellow_background")` | [DESIGN] | `_background` suffix |
| **Inline math** | `math(block:false)` | [DESIGN] | KaTeX source in text range |
| **Mention** | `mention(did)` | [PRODUCTION] | L0 AT Protocol |
| **Link** | `link(uri)` | [PRODUCTION] | L0 AT Protocol |
| **Comment** | — | N/A | Notion UI feature, not text format |

**Inline coverage: 10/10** (Comment は UI 機能のため対象外)

### Block Types

| Notion Block | Facet | Status | Notes |
|---|---|---|---|
| **Text (paragraph)** | (default — no block facet) | [PRODUCTION] | 既存動作 |
| **Heading 1** | `heading(level:1)` | [DESIGN] | `@field 20` |
| **Heading 2** | `heading(level:2)` | [DESIGN] | `@field 20` |
| **Heading 3** | `heading(level:3)` | [DESIGN] | `@field 20` |
| **Bulleted list** | `bulleted-list(indent)` | [DESIGN] | 8 段ネスト |
| **Numbered list** | `numbered-list(indent)` | [DESIGN] | 8 段ネスト |
| **To-do list** | `todo(checked, indent)` | [DESIGN] | checkbox |
| **Toggle list** | `toggle(indent)` | [DESIGN] | heading + toggle = toggle heading |
| **Quote** | `blockquote` | [DESIGN] | `@field 21` |
| **Divider** | `divider` | [DESIGN] | `@field 28` |
| **Callout** | `callout(icon, color)` | [DESIGN] | emoji + color |
| **Code block** | `code-block(language)` | [DESIGN] | syntax highlight |
| **Block equation** | `math(block:true)` | [DESIGN] | KaTeX display mode |
| **Table** | `table-cell(row, col, header)` | [DESIGN] | simple table |
| **Toggle heading** | `heading` + `toggle` (same range) | [DESIGN] | composite |

**Block coverage: 15/15**

### Notion Features NOT in Facet Scope (Embed/Media — handled by `post-embed`)

| Notion Feature | W Protocol Equivalent | Reason |
|---|---|---|
| Image | `post-embed.images` | Binary — embed, not facet |
| Video | `post-embed.video` | Binary — embed, not facet |
| Bookmark | `post-embed.external` | Link preview — embed |
| File attachment | `com.etzhayyim.files.*` | Binary — file upload NSID |
| Database / Linked DB | `com.etzhayyim.apps.*.query` | Application-level, not text annotation |
| Synced block | — | Notion-specific collaborative feature |
| Column layout | — | UI layout, not text semantics |
| Table of contents | — | Derived from headings at render time |
| Breadcrumb | — | Navigation UI |

### Coverage Summary

| Category | Covered | Total | Coverage |
|---|---|---|---|
| Inline formatting | 10 | 10 | **100%** |
| Block types | 15 | 15 | **100%** |
| Embed/Media | 3 | 3 | **100%** (via post-embed) |
| Notion-only UI | 0 | 5 | N/A (UI features) |
| **Total (text semantics)** | **28** | **28** | **100%** |

## Editor Integration (Future)

| Layer | Component | Role |
|---|---|---|
| Input | Lexical (Meta) or TipTap (ProseMirror) | Block editor engine |
| Serialize | `editorStateToFacets()` | Editor tree → facet array |
| Deserialize | `facetsToEditorState()` | Facet array → editor tree |
| Wire | `facet-feature` variant | AT Record 保存 |
| Render | `RichText.svelte` | facet → HTML |

## L0/L1 Degradation

```
W Protocol client:  # 見出し1  **太字** テキスト  - リスト
AT Protocol client: 見出し1\n太字 テキスト\nリスト
```

AT client は L1 facet を無視し、プレーンテキスト + L0 facet (mention/link/tag) のみ表示。情報損失はあるが機能損失なし (readable fallback)。

## References

- `00-contracts/wit/deps/kotodama-bsky/package.wit` — WIT definition (authoritative)
- `90-docs/260325-atproto-layer-separation-design.md` — L0/L1 layer separation
- `90-docs/260324-wit-lexicon-typed-alignment-design.md` — WIT ↔ Lexicon alignment
- Notion Block Types: https://developers.notion.com/reference/block
- AT Protocol Richtext: https://atproto.com/specs/handle#richtext-facets
