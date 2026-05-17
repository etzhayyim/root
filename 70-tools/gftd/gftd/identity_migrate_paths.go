// gftd identity migrate-paths — ADR-0029 did:gftd path DID migration CLI.
//
// Reads source DIDs (legacy nanoids from deps.toml, or did:web:site path DIDs
// from RisingWave), builds canonical DAG-CBOR genesis ops, computes CIDv1
// (multibase 'b' base32 + multicodec raw + sha2-256 multihash), and submits
// each op to PDS XRPC ai.gftd.identity.submitOp in topological-sort order
// (root → leaf), preserving the legacy DID via `legacy_did` column +
// `alsoKnownAs` field for AT Protocol federation continuity.
//
// Spec: 90-docs/adr/0029-did-gftd-method-specification.md
//
// Usage:
//   gftd identity migrate-paths --source legacy-nanoids                 # dry-run, default
//   gftd identity migrate-paths --source legacy-nanoids --apply         # actually submit
//   gftd identity migrate-paths --source legacy-nanoids --limit 5       # first 5 only
//   gftd identity migrate-paths --source legacy-nanoids --filter foo    # filter by name substring
//   gftd identity migrate-paths --source did-web-site --root did:web:site.etzhayyim.com  # planned (v0.2)

package main

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"sort"
	"strings"
	"time"
)

// ───────────────────────────────────────────────────────────────────────────
// Multibase 'b' (base32 lowercase, RFC 4648 §6 without padding)
// ───────────────────────────────────────────────────────────────────────────

const base32LowerAlphabet = "abcdefghijklmnopqrstuvwxyz234567"

func encodeBase32(b []byte) string {
	var bits, value int
	var sb strings.Builder
	for _, by := range b {
		value = (value << 8) | int(by)
		bits += 8
		for bits >= 5 {
			sb.WriteByte(base32LowerAlphabet[(value>>(bits-5))&0x1f])
			bits -= 5
		}
	}
	if bits > 0 {
		sb.WriteByte(base32LowerAlphabet[(value<<(5-bits))&0x1f])
	}
	return sb.String()
}

// ───────────────────────────────────────────────────────────────────────────
// CIDv1 (multibase 'b' + multicodec raw 0x55 + multihash sha2-256)
//   bytes = 0x01 ‖ 0x55 ‖ 0x12 ‖ 0x20 ‖ sha256(content)
// ───────────────────────────────────────────────────────────────────────────

func cidv1RawSha256(content []byte) string {
	digest := sha256.Sum256(content)
	body := make([]byte, 0, 4+32)
	body = append(body, 0x01, 0x55, 0x12, 0x20)
	body = append(body, digest[:]...)
	return "b" + encodeBase32(body)
}

// ───────────────────────────────────────────────────────────────────────────
// Canonical DAG-CBOR encoder (subset for did:gftd genesis ops).
// Spec: https://ipld.io/specs/codecs/dag-cbor/spec/
//
// Constraints:
//   - Map keys MUST be UTF-8 strings, sorted by length asc then bytewise.
//   - Integers MUST use the smallest CBOR encoding.
//   - No floats, no tags, no indefinite-length items.
// ───────────────────────────────────────────────────────────────────────────

func cborEncodeUint(major byte, value uint64) []byte {
	head := byte(major) << 5
	switch {
	case value < 24:
		return []byte{head | byte(value)}
	case value < 0x100:
		return []byte{head | 24, byte(value)}
	case value < 0x10000:
		return []byte{head | 25, byte(value >> 8), byte(value)}
	case value < 0x100000000:
		return []byte{head | 26, byte(value >> 24), byte(value >> 16), byte(value >> 8), byte(value)}
	default:
		return []byte{head | 27,
			byte(value >> 56), byte(value >> 48), byte(value >> 40), byte(value >> 32),
			byte(value >> 24), byte(value >> 16), byte(value >> 8), byte(value)}
	}
}

// CborValue is a typed sum used by the canonical encoder.
type CborValue struct {
	kind  string // "null" | "bool" | "uint" | "int" | "string" | "bytes" | "array" | "map"
	bv    bool
	uv    uint64
	sv    string
	bsv   []byte
	av    []CborValue
	mv    map[string]CborValue
}

func cborNull() CborValue                    { return CborValue{kind: "null"} }
func cborBool(b bool) CborValue              { return CborValue{kind: "bool", bv: b} }
func cborUint(u uint64) CborValue            { return CborValue{kind: "uint", uv: u} }
func cborStr(s string) CborValue             { return CborValue{kind: "string", sv: s} }
func cborArr(a []CborValue) CborValue        { return CborValue{kind: "array", av: a} }
func cborMap(m map[string]CborValue) CborValue { return CborValue{kind: "map", mv: m} }

func cborEncode(v CborValue) []byte {
	switch v.kind {
	case "null":
		return []byte{0xf6}
	case "bool":
		if v.bv {
			return []byte{0xf5}
		}
		return []byte{0xf4}
	case "uint":
		return cborEncodeUint(0, v.uv)
	case "string":
		head := cborEncodeUint(3, uint64(len(v.sv)))
		return append(head, []byte(v.sv)...)
	case "bytes":
		head := cborEncodeUint(2, uint64(len(v.bsv)))
		return append(head, v.bsv...)
	case "array":
		out := cborEncodeUint(4, uint64(len(v.av)))
		for _, item := range v.av {
			out = append(out, cborEncode(item)...)
		}
		return out
	case "map":
		keys := make([]string, 0, len(v.mv))
		for k := range v.mv {
			keys = append(keys, k)
		}
		sort.Slice(keys, func(i, j int) bool {
			a, b := []byte(keys[i]), []byte(keys[j])
			if len(a) != len(b) {
				return len(a) < len(b)
			}
			return bytes.Compare(a, b) < 0
		})
		out := cborEncodeUint(5, uint64(len(keys)))
		for _, k := range keys {
			out = append(out, cborEncode(cborStr(k))...)
			out = append(out, cborEncode(v.mv[k])...)
		}
		return out
	}
	panic(fmt.Sprintf("cborEncode: unsupported kind %q", v.kind))
}

// ───────────────────────────────────────────────────────────────────────────
// Genesis op builder
// ───────────────────────────────────────────────────────────────────────────

type vmInput struct {
	id                 string
	pubkeyMultibase    string
}

func buildGenesisOp(parentDid, segment string, vms []vmInput, alsoKnownAs []string, createdAt string) (op CborValue, opJSON map[string]any) {
	vmArr := make([]CborValue, 0, len(vms))
	vmJSON := make([]any, 0, len(vms))
	for _, vm := range vms {
		vmArr = append(vmArr, cborMap(map[string]CborValue{
			"id":                 cborStr(vm.id),
			"type":               cborStr("Multikey"),
			"publicKeyMultibase": cborStr(vm.pubkeyMultibase),
		}))
		vmJSON = append(vmJSON, map[string]any{
			"id":                 vm.id,
			"type":               "Multikey",
			"publicKeyMultibase": vm.pubkeyMultibase,
		})
	}

	akaArr := make([]CborValue, 0, len(alsoKnownAs))
	akaJSON := make([]any, 0, len(alsoKnownAs))
	for _, a := range alsoKnownAs {
		akaArr = append(akaArr, cborStr(a))
		akaJSON = append(akaJSON, a)
	}

	parentVal := cborNull()
	parentJSONVal := any(nil)
	segmentVal := cborNull()
	segmentJSONVal := any(nil)
	typeStr := "root"
	if parentDid != "" {
		parentVal = cborStr(parentDid)
		parentJSONVal = parentDid
		segmentVal = cborStr(segment)
		segmentJSONVal = segment
		typeStr = "child"
	}

	op = cborMap(map[string]CborValue{
		"v":           cborUint(1),
		"type":        cborStr(typeStr),
		"parent":      parentVal,
		"segment":     segmentVal,
		"vm":          cborArr(vmArr),
		"alsoKnownAs": cborArr(akaArr),
		"service":     cborArr(nil),
		"createdAt":   cborStr(createdAt),
	})

	opJSON = map[string]any{
		"v":           1,
		"type":        typeStr,
		"parent":      parentJSONVal,
		"segment":     segmentJSONVal,
		"vm":          vmJSON,
		"alsoKnownAs": akaJSON,
		"service":     []any{},
		"createdAt":   createdAt,
	}
	return op, opJSON
}

// ───────────────────────────────────────────────────────────────────────────
// deps.toml [[legacy_nanoids]] reader
// ───────────────────────────────────────────────────────────────────────────

type legacyNanoid struct {
	Name   string // actor name
	Nanoid string
	Handle string // e.g. nist.etzhayyim.com
	Did    string // current did (did:web:* etc), if explicit
}

func parseLegacyNanoids(path string) ([]legacyNanoid, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read %s: %w", path, err)
	}
	lines := strings.Split(string(data), "\n")

	var out []legacyNanoid
	var cur *legacyNanoid
	inSection := false
	for _, raw := range lines {
		line := strings.TrimSpace(raw)
		if line == "[[legacy_nanoids]]" {
			if cur != nil && cur.Name != "" {
				out = append(out, *cur)
			}
			cur = &legacyNanoid{}
			inSection = true
			continue
		}
		if strings.HasPrefix(line, "[") && line != "[[legacy_nanoids]]" {
			if cur != nil && cur.Name != "" {
				out = append(out, *cur)
			}
			cur = nil
			inSection = false
			continue
		}
		if !inSection || cur == nil {
			continue
		}
		if eq := strings.Index(line, "="); eq > 0 {
			k := strings.TrimSpace(line[:eq])
			v := strings.TrimSpace(line[eq+1:])
			v = strings.Trim(v, `"`)
			switch k {
			case "name", "actor":
				cur.Name = v
			case "nanoid":
				cur.Nanoid = v
			case "handle":
				cur.Handle = v
			case "did":
				cur.Did = v
			}
		}
	}
	if cur != nil && cur.Name != "" {
		out = append(out, *cur)
	}
	return out, nil
}

// ───────────────────────────────────────────────────────────────────────────
// PDS XRPC submitOp client
// ───────────────────────────────────────────────────────────────────────────

type submitOpRequest struct {
	Did    string         `json:"did"`
	OpType string         `json:"opType"`
	Op     map[string]any `json:"op"`
	Prev   string         `json:"prev,omitempty"`
	Sig    string         `json:"sig,omitempty"`
	SigKid string         `json:"sigKid,omitempty"`
}

type submitOpResponse struct {
	Did      string `json:"did"`
	OpCid    string `json:"opCid"`
	OpSeq    int    `json:"opSeq"`
	Accepted bool   `json:"accepted"`
	Error    string `json:"error,omitempty"`
	Message  string `json:"message,omitempty"`
}

func submitOp(pdsURL string, req submitOpRequest) (*submitOpResponse, error) {
	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("marshal: %w", err)
	}
	httpReq, err := http.NewRequest("POST", pdsURL+"/xrpc/ai.gftd.identity.submitOp", bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("new request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")
	setAuthHeaders(httpReq)

	resp, err := http.DefaultClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("http: %w", err)
	}
	defer resp.Body.Close()
	respBytes, _ := io.ReadAll(resp.Body)

	var out submitOpResponse
	if err := json.Unmarshal(respBytes, &out); err != nil {
		return nil, fmt.Errorf("decode (status %d): %w; body=%s", resp.StatusCode, err, string(respBytes))
	}
	if resp.StatusCode >= 400 {
		return &out, fmt.Errorf("HTTP %d: %s — %s", resp.StatusCode, out.Error, out.Message)
	}
	return &out, nil
}

// ───────────────────────────────────────────────────────────────────────────
// CLI
// ───────────────────────────────────────────────────────────────────────────

func runIdentityMigratePaths(args []string) error {
	fs := flag.NewFlagSet("identity migrate-paths", flag.ContinueOnError)
	source := fs.String("source", "legacy-nanoids", "migration source: legacy-nanoids | did-web-site (planned v0.2)")
	depsPath := fs.String("deps", "deps.toml", "path to deps.toml")
	pdsURL := fs.String("pds", "https://atproto.etzhayyim.com", "PDS base URL")
	apply := fs.Bool("apply", false, "actually POST to PDS (default: dry-run)")
	limit := fs.Int("limit", 0, "max number of DIDs to migrate (0 = all)")
	filter := fs.String("filter", "", "filter source by name substring")
	jsonOut := fs.Bool("json", false, "JSON output")
	rootKey := fs.String("root-key", "zDnaerDaTF5BXEavCrfRZEk316dpbLsfPDZ3WJ5hRTPFU2169", "publicKeyMultibase for root genesis op (must already be provisioned for caller)")
	verbose := fs.Bool("v", false, "verbose progress")

	if err := fs.Parse(args); err != nil {
		return err
	}

	now := time.Now().UTC().Format(time.RFC3339)

	_ = jsonOut
	switch *source {
	case "legacy-nanoids":
		return migrateLegacyNanoids(*depsPath, *pdsURL, *apply, *limit, *filter, *rootKey, *verbose, now)
	case "did-web-site":
		return migrateDidWebSite(*pdsURL, *apply, *limit, *filter, *rootKey, *verbose, now)
	default:
		return fmt.Errorf("unknown --source %q (valid: legacy-nanoids, did-web-site)", *source)
	}
}

// ───────────────────────────────────────────────────────────────────────────
// v0.2: did-web-site source — bulk topological-sort migration of
// `did:web:site.etzhayyim.com:*` path DIDs from RisingWave into vertex_gftd_identity.
//
// Bulk INSERT is performed directly via pgxpool (NOT via PDS XRPC) because:
//   - PDS XRPC at 15K calls × ~100ms RTT ≈ 25 minutes
//   - Schema is identical to what the PDS submitOp handler writes
//   - Topological order is enforced by depth-first batching
//   - PDS handler validation already verified end-to-end (E2E test 2026-04-17)
// ───────────────────────────────────────────────────────────────────────────

func migrateDidWebSite(pdsURL string, apply bool, limit int, filter, rootKey string, verbose bool, now string) error {
	_ = pdsURL // direct DB write; PDS bypassed by design for bulk load
	ctx := context.Background()
	pool, err := dbPool(ctx)
	if err != nil {
		return fmt.Errorf("db pool: %w", err)
	}

	pattern := "did:web:site.etzhayyim.com:%"
	// No ORDER BY — Hummock S3 cold-tier sort triggers rate-limit (503).
	// In-memory topological sort by depth happens after fetch.
	// SQL LIMIT pushed down to reduce S3 read pressure on large scans.
	query := "SELECT did FROM vertex_did WHERE did LIKE $1"
	if limit > 0 {
		// RisingWave requires LIMIT to be a constant; can't use $2.
		query += fmt.Sprintf(" LIMIT %d", limit*2)
	}
	rows, err := pool.Query(ctx, query, pattern)
	if err != nil {
		return fmt.Errorf("query vertex_did: %w", err)
	}
	if err != nil {
		return fmt.Errorf("query vertex_did: %w", err)
	}
	defer rows.Close()

	type pathNode struct {
		LegacyDid string
		Segments  []string // parts after "did:web:site.etzhayyim.com:"
		Depth     int      // len(Segments)
	}
	var nodes []pathNode
	for rows.Next() {
		var did string
		if err := rows.Scan(&did); err != nil {
			return fmt.Errorf("scan: %w", err)
		}
		tail := strings.TrimPrefix(did, "did:web:site.etzhayyim.com")
		tail = strings.TrimPrefix(tail, ":")
		segs := strings.Split(tail, ":")
		if len(segs) == 1 && segs[0] == "" {
			segs = nil
		}
		if filter != "" && !strings.Contains(did, filter) {
			continue
		}
		nodes = append(nodes, pathNode{LegacyDid: did, Segments: segs, Depth: len(segs)})
	}
	if rows.Err() != nil {
		return fmt.Errorf("rows: %w", rows.Err())
	}
	if len(nodes) == 0 {
		return fmt.Errorf("no did:web:site.etzhayyim.com:* paths found in vertex_did")
	}

	// Synthesize implied parent nodes (vertex_did is sparse — depth-5 leaves
	// often have no depth-1..4 ancestor records). Each prefix becomes its own
	// did:gftd path node so the chain is valid topologically. Dedup by full
	// segments path to avoid double-inserting parents that exist in vertex_did.
	if limit > 0 && len(nodes) > limit {
		nodes = nodes[:limit]
	}
	seen := map[string]bool{}
	deduped := nodes[:0]
	for _, n := range nodes {
		key := strings.Join(n.Segments, ":")
		if !seen[key] {
			seen[key] = true
			deduped = append(deduped, n)
		}
	}
	nodes = deduped
	for _, n := range append([]pathNode{}, nodes...) {
		for d := 1; d < n.Depth; d++ {
			key := strings.Join(n.Segments[:d], ":")
			if !seen[key] {
				seen[key] = true
				nodes = append(nodes, pathNode{
					LegacyDid: "did:web:site.etzhayyim.com:" + key,
					Segments:  append([]string{}, n.Segments[:d]...),
					Depth:     d,
				})
			}
		}
	}
	// Topological sort: depth ascending so each child sees its parent.
	sort.Slice(nodes, func(i, j int) bool {
		if nodes[i].Depth != nodes[j].Depth {
			return nodes[i].Depth < nodes[j].Depth
		}
		return nodes[i].LegacyDid < nodes[j].LegacyDid
	})

	// Build root genesis (the platform-wide site root, depth 0 ancestor).
	rootGenesis, _ := buildGenesisOp("", "", []vmInput{
		{id: "#key-1", pubkeyMultibase: rootKey},
	}, []string{"at://site.etzhayyim.com", "did:web:site.etzhayyim.com"}, now)
	rootCBOR := cborEncode(rootGenesis)
	rootCid := cidv1RawSha256(rootCBOR)
	rootDid := "did:gftd:" + rootCid

	// segmentChain → did:gftd cidv1 chain (built level by level).
	chainCache := map[string]string{"": rootDid} // key = "seg1:seg2:..."
	type plan struct {
		LegacyDid string
		NewDid    string
		Parent    string
		Segment   string
		Depth     int
		OpJSON    map[string]any
	}
	plans := make([]plan, 0, len(nodes)+1)
	plans = append(plans, plan{
		NewDid: rootDid, Parent: "", Segment: "", Depth: 0,
		OpJSON: map[string]any{"v": 1, "type": "root"},
	})

	for _, n := range nodes {
		var parentDid string
		var segment string
		if n.Depth == 0 {
			parentDid = ""
			segment = ""
		} else {
			parentSegs := n.Segments[:n.Depth-1]
			parentKey := strings.Join(parentSegs, ":")
			pd, ok := chainCache[parentKey]
			if !ok {
				return fmt.Errorf("topo violation: parent for %s not yet migrated (segs=%v)", n.LegacyDid, parentSegs)
			}
			parentDid = pd
			segment = n.Segments[n.Depth-1]
		}
		genesis, opJSON := buildGenesisOp(parentDid, segment, []vmInput{
			{id: "#key-1", pubkeyMultibase: rootKey},
		}, []string{n.LegacyDid}, now)
		childCBOR := cborEncode(genesis)
		childCid := cidv1RawSha256(childCBOR)
		var newDid string
		if parentDid == "" {
			newDid = "did:gftd:" + childCid
		} else {
			newDid = parentDid + ":" + childCid
		}
		chainCache[strings.Join(n.Segments, ":")] = newDid
		plans = append(plans, plan{
			LegacyDid: n.LegacyDid, NewDid: newDid, Parent: parentDid,
			Segment: segment, Depth: n.Depth, OpJSON: opJSON,
		})
	}

	// Plan output
	fmt.Printf("── plan (%d ops, dry-run=%v) ──\n", len(plans), !apply)
	fmt.Printf("  root:   %s\n", rootDid)
	fmt.Printf("  source: did:web:site.etzhayyim.com:* (%d nodes)\n", len(nodes))
	depthCount := map[int]int{}
	for _, p := range plans {
		depthCount[p.Depth]++
	}
	for d := 0; d <= 8; d++ {
		if c := depthCount[d]; c > 0 {
			fmt.Printf("  depth %d:  %d nodes\n", d, c)
		}
	}
	if verbose {
		shown := 0
		for _, p := range plans {
			if shown >= 5 && shown < len(plans)-3 {
				if shown == 5 {
					fmt.Printf("  ... (%d more) ...\n", len(plans)-8)
				}
				shown++
				continue
			}
			fmt.Printf("  [%d] legacy=%-50s  →  %s\n", p.Depth, truncIdent(p.LegacyDid, 50), p.NewDid)
			shown++
		}
	}

	if !apply {
		fmt.Println("\n(dry-run — re-run with --apply to bulk INSERT into RisingWave)")
		return nil
	}

	// Phase 3: bulk INSERT directly into RisingWave.
	// Done via individual INSERTs (RisingWave doesn't support COPY for streaming
	// tables) but batched into single transaction-equivalent loops with FLUSH.
	fmt.Println("\n── inserting (direct RisingWave INSERT, bypassing PDS) ──")
	successes, conflicts, errors := 0, 0, 0
	for i, p := range plans {
		akaJSON := "[]"
		if aka, ok := p.OpJSON["alsoKnownAs"].([]any); ok && len(aka) > 0 {
			b, _ := json.Marshal(aka)
			akaJSON = string(b)
		}
		var parentArg interface{}
		var segArg interface{}
		if p.Parent == "" {
			parentArg = nil
		} else {
			parentArg = p.Parent
		}
		if p.Segment == "" {
			segArg = nil
		} else {
			segArg = p.Segment
		}
		genesisCid := strings.Split(p.NewDid, ":")
		opCid := genesisCid[len(genesisCid)-1]

		_, err := pool.Exec(ctx, `INSERT INTO vertex_gftd_identity
			(vertex_id, _seq, created_date, sensitivity_ord, owner_did,
			 did, public_key_multibase, authentication_methods,
			 cid_version, multicodec, multihash_code, multibase_prefix,
			 genesis_op_cid, root_did, parent_did, path_segment, depth,
			 status, created_at, updated_at)
			VALUES ($1, 0, '2026-04-18', 0, $1,
			        $1, $2, $3,
			        1, 'raw', 'sha2-256', 'b',
			        $4, $5, $6, $7, $8,
			        'active', $9, $9)`,
			p.NewDid, rootKey, akaJSON,
			opCid, rootDid, parentArg, segArg, p.Depth,
			now)
		if err != nil {
			if strings.Contains(err.Error(), "duplicate key") || strings.Contains(err.Error(), "already exists") {
				conflicts++
				continue
			}
			errors++
			fmt.Printf("  ✗ [%d] %s: %v\n", p.Depth, p.NewDid, err)
			if errors >= 5 {
				return fmt.Errorf("too many errors, aborting (last: %v)", err)
			}
			continue
		}
		if p.Parent != "" {
			_, _ = pool.Exec(ctx, `INSERT INTO edge_gftd_path_child
				(edge_id, src_vid, dst_vid, _seq, created_date, sensitivity_ord, owner_did, segment, created_at)
				VALUES ($1, $2, $3, 0, '2026-04-18', 0, $3, $4, $5)`,
				p.Parent+"->"+p.NewDid, p.Parent, p.NewDid, segArg, now)
		}
		successes++
		if successes%500 == 0 {
			pool.Exec(ctx, "FLUSH")
			fmt.Printf("  … %d / %d inserted (depth=%d)\n", i+1, len(plans), p.Depth)
		}
	}
	pool.Exec(ctx, "FLUSH")

	fmt.Printf("\n── summary: %d created, %d already-exists, %d errors ──\n", successes, conflicts, errors)
	if errors > 0 {
		return fmt.Errorf("%d insertion errors", errors)
	}
	return nil
}

type migrationPlan struct {
	Name      string `json:"name"`
	LegacyDid string `json:"legacyDid"`
	NewDid    string `json:"newDid"`
	Segment   string `json:"segment"`
	Depth     int    `json:"depth"`
	OpCidHex  string `json:"opCidHex,omitempty"`
}

func migrateLegacyNanoids(depsPath, pdsURL string, apply bool, limit int, filter, rootKey string, verbose bool, now string) error {
	entries, err := parseLegacyNanoids(depsPath)
	if err != nil {
		return err
	}
	if len(entries) == 0 {
		return fmt.Errorf("no [[legacy_nanoids]] entries found in %s", depsPath)
	}

	if filter != "" {
		filtered := entries[:0]
		for _, e := range entries {
			if strings.Contains(e.Name, filter) || strings.Contains(e.Nanoid, filter) {
				filtered = append(filtered, e)
			}
		}
		entries = filtered
	}
	if limit > 0 && len(entries) > limit {
		entries = entries[:limit]
	}

	// Phase 1: build root DID once (parent of all legacy nanoids).
	// All legacy nanoids become children of a single did:gftd root that
	// represents the platform legacy namespace. This keeps lineage explicit
	// and lets the resolver expose a single ancestor for graph traversal.
	rootGenesis, _ := buildGenesisOp("", "", []vmInput{
		{id: "#key-1", pubkeyMultibase: rootKey},
	}, []string{"at://legacy.etzhayyim.com", "did:web:etzhayyim.com"}, now)
	rootCBOR := cborEncode(rootGenesis)
	rootCid := cidv1RawSha256(rootCBOR)
	rootDid := "did:gftd:" + rootCid

	plans := make([]migrationPlan, 0, len(entries)+1)
	plans = append(plans, migrationPlan{
		Name: "_root_legacy_namespace", LegacyDid: "", NewDid: rootDid,
		Segment: "", Depth: 0, OpCidHex: hex.EncodeToString(sha256Sum(rootCBOR)),
	})

	// Phase 2: per legacy nanoid, build child genesis op (depth 1).
	for _, e := range entries {
		segment := e.Name
		if e.Nanoid != "" {
			segment = e.Name + "#" + e.Nanoid
		}
		aka := []string{}
		if e.Did != "" {
			aka = append(aka, e.Did)
		}
		if e.Handle != "" {
			aka = append(aka, "at://"+e.Handle)
		}
		if e.Nanoid != "" {
			aka = append(aka, "did:web:"+e.Nanoid+".etzhayyim.com")
		}
		_, childJSON := buildGenesisOp(rootDid, segment, []vmInput{
			{id: "#key-1", pubkeyMultibase: rootKey},
		}, aka, now)
		// Build CBOR for hashing
		childGenesis, _ := buildGenesisOp(rootDid, segment, []vmInput{
			{id: "#key-1", pubkeyMultibase: rootKey},
		}, aka, now)
		_ = childJSON
		childCBOR := cborEncode(childGenesis)
		childCid := cidv1RawSha256(childCBOR)
		childDid := rootDid + ":" + childCid
		plans = append(plans, migrationPlan{
			Name: e.Name, LegacyDid: e.Did, NewDid: childDid,
			Segment: segment, Depth: 1, OpCidHex: hex.EncodeToString(sha256Sum(childCBOR)),
		})
	}

	// Print plan
	fmt.Printf("── plan (%d ops, dry-run=%v) ──\n", len(plans), !apply)
	if !apply {
		fmt.Printf("  PDS:    %s (not contacted)\n", pdsURL)
	} else {
		fmt.Printf("  PDS:    %s\n", pdsURL)
	}
	fmt.Printf("  root:   %s\n", rootDid)
	for i, p := range plans {
		marker := "+"
		if i == 0 {
			marker = "★"
		}
		fmt.Printf("  %s [%d] %-32s  legacy=%-40s  →  %s\n", marker, p.Depth, p.Name, truncIdent(p.LegacyDid, 40), p.NewDid)
		if verbose {
			fmt.Printf("      segment=%q opCid=%s...\n", p.Segment, p.OpCidHex[:16])
		}
	}

	if !apply {
		fmt.Println("\n(dry-run — re-run with --apply to POST to PDS)")
		return nil
	}

	// Phase 3: submit in topological order (root first, then children).
	fmt.Println("\n── submitting ──")
	successes, conflicts, errors := 0, 0, 0
	for i, p := range plans {
		var parentDid string
		var segment string
		if i == 0 {
			parentDid = ""
			segment = ""
		} else {
			parentDid = rootDid
			segment = p.Segment
		}

		aka := []string{}
		if i > 0 {
			e := entries[i-1]
			if e.Did != "" {
				aka = append(aka, e.Did)
			}
			if e.Handle != "" {
				aka = append(aka, "at://"+e.Handle)
			}
			if e.Nanoid != "" {
				aka = append(aka, "did:web:"+e.Nanoid+".etzhayyim.com")
			}
		} else {
			aka = []string{"at://legacy.etzhayyim.com", "did:web:etzhayyim.com"}
		}

		_, opJSON := buildGenesisOp(parentDid, segment, []vmInput{
			{id: "#key-1", pubkeyMultibase: rootKey},
		}, aka, now)

		req := submitOpRequest{
			Did:    p.NewDid,
			OpType: "create",
			Op:     opJSON,
		}
		resp, err := submitOp(pdsURL, req)
		if err != nil {
			if resp != nil && resp.Error == "Conflict" {
				conflicts++
				fmt.Printf("  ◌ %-32s  already exists (skip)\n", p.Name)
				continue
			}
			errors++
			fmt.Printf("  ✗ %-32s  %v\n", p.Name, err)
			continue
		}
		successes++
		fmt.Printf("  ✓ %-32s  → opSeq=%d\n", p.Name, resp.OpSeq)
	}

	fmt.Printf("\n── summary: %d created, %d already-exists, %d errors ──\n", successes, conflicts, errors)
	if errors > 0 {
		return fmt.Errorf("%d submission errors", errors)
	}
	return nil
}

func sha256Sum(b []byte) []byte {
	d := sha256.Sum256(b)
	return d[:]
}

func truncIdent(s string, n int) string {
	if s == "" {
		return "(none)"
	}
	if len(s) <= n {
		return s
	}
	return s[:n-3] + "..."
}
