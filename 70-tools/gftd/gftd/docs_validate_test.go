package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestValidateDocsRegistrySuccess(t *testing.T) {
	root := t.TempDir()
	writeDocsFixture(t, root, docsFixtureOptions{})

	if err := validateDocsRegistry(root); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestValidateDocsRegistryDetectsDuplicateAuthoritativeTopic(t *testing.T) {
	root := t.TempDir()
	writeDocsFixture(t, root, docsFixtureOptions{
		Registry: `{
  "version": 1,
  "updated_at": "2026-03-20",
  "entries": [
    {
      "id": "doc-a",
      "path": "docs/doc-a.md",
      "title": "Doc A",
      "status": "active",
      "doc_type": "explanation",
      "topic": "same-topic",
      "authoritative": true,
      "authoritative_for": ["topic a"]
    },
    {
      "id": "doc-b",
      "path": "docs/doc-b.md",
      "title": "Doc B",
      "status": "active",
      "doc_type": "reference",
      "topic": "same-topic",
      "authoritative": true,
      "authoritative_for": ["topic b"]
    }
  ]
}`,
	})

	err := validateDocsRegistry(root)
	if err == nil || !strings.Contains(err.Error(), "more than one authoritative doc") {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestValidateDocsRegistryDetectsFrontMatterMismatch(t *testing.T) {
	root := t.TempDir()
	writeDocsFixture(t, root, docsFixtureOptions{
		DocB: `---
id: doc-b
title: Doc B Broken
status: active
doc_type: reference
topic: topic-b
authoritative: false
last_verified: 2026-03-20
authoritative_for:
  - topic b
---

# Doc B
`,
	})

	err := validateDocsRegistry(root)
	if err == nil || !strings.Contains(err.Error(), "front matter \"title\"") {
		t.Fatalf("unexpected error: %v", err)
	}
}

type docsFixtureOptions struct {
	Registry string
	Graph    string
	DocA     string
	DocB     string
}

func writeDocsFixture(t *testing.T, root string, opts docsFixtureOptions) {
	t.Helper()

	writeTestFile(t, filepath.Join(root, ".git", "keep"), "")
	writeTestFile(t, filepath.Join(root, "docs", "_registry", "schemas", "docs.schema.json"), "{}\n")
	writeTestFile(t, filepath.Join(root, "docs", "_registry", "schemas", "graph.schema.json"), "{}\n")

	registry := opts.Registry
	if registry == "" {
		registry = `{
  "version": 1,
  "updated_at": "2026-03-20",
  "entries": [
    {
      "id": "doc-a",
      "path": "docs/doc-a.md",
      "title": "Doc A",
      "status": "active",
      "doc_type": "explanation",
      "topic": "topic-a",
      "authoritative": true,
      "authoritative_for": ["topic a"]
    },
    {
      "id": "doc-b",
      "path": "docs/doc-b.md",
      "title": "Doc B",
      "status": "active",
      "doc_type": "reference",
      "topic": "topic-b",
      "authoritative": false,
      "authoritative_for": ["topic b"]
    }
  ]
}`
	}
	writeTestFile(t, filepath.Join(root, "docs", "_registry", "docs.json"), registry)

	graph := opts.Graph
	if graph == "" {
		graph = `{
  "@context": {},
  "@graph": [
    {
      "id": "doc:doc-a",
      "type": "TechArticle",
      "title": "Doc A",
      "status": "active",
      "topic": "topic-a",
      "authoritative": true,
      "authoritativeFor": ["topic a"],
      "related": ["doc:doc-b"]
    },
    {
      "id": "doc:doc-b",
      "type": "TechArticle",
      "title": "Doc B",
      "status": "active",
      "topic": "topic-b",
      "authoritative": false,
      "authoritativeFor": ["topic b"],
      "related": ["doc:doc-a"]
    }
  ]
}`
	}
	writeTestFile(t, filepath.Join(root, "docs", "_registry", "graph.jsonld"), graph)

	docA := opts.DocA
	if docA == "" {
		docA = `---
id: doc-a
title: Doc A
status: active
doc_type: explanation
topic: topic-a
authoritative: true
last_verified: 2026-03-20
authoritative_for:
  - topic a
---

# Doc A
`
	}
	writeTestFile(t, filepath.Join(root, "docs", "doc-a.md"), docA)

	docB := opts.DocB
	if docB == "" {
		docB = `---
id: doc-b
title: Doc B
status: active
doc_type: reference
topic: topic-b
authoritative: false
last_verified: 2026-03-20
authoritative_for:
  - topic b
---

# Doc B
`
	}
	writeTestFile(t, filepath.Join(root, "docs", "doc-b.md"), docB)
}

func TestRunDocsValidateFindsRepoRoot(t *testing.T) {
	root := t.TempDir()
	writeDocsFixture(t, root, docsFixtureOptions{})
	prev, err := os.Getwd()
	if err != nil {
		t.Fatalf("getwd: %v", err)
	}
	defer func() {
		_ = os.Chdir(prev)
	}()
	if err := os.Chdir(filepath.Join(root, "docs")); err != nil {
		t.Fatalf("chdir: %v", err)
	}
	if err := runDocs([]string{"validate"}); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
}
