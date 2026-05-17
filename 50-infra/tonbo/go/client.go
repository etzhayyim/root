package lancedbrest

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"
)

const (
	defaultBaseURL  = "http://localhost:8084"
	defaultPageSize = 1000
)

var (
	selectSQLPattern = regexp.MustCompile(`(?is)^\s*select\s+(.*?)\s+from\s+("?[\w\-]+"?)(?:\s+where\s+(.*?))?(?:\s+order\s+by\s+(.*?))?(?:\s+limit\s+(\d+))?(?:\s+offset\s+(\d+))?\s*;?\s*$`)
	insertSQLPattern = regexp.MustCompile(`(?is)^\s*insert(?:\s+or\s+replace)?\s+into\s+("?[\w\-]+"?)\s*\((.*?)\)\s*values\s*\((.*)\)\s*;?\s*$`)
	createSQLPattern = regexp.MustCompile(`(?is)^\s*create\s+table\s+if\s+not\s+exists\s+`)
	httpSender       func(*http.Request) (*http.Response, error)
)

func SetHTTPSender(sender func(*http.Request) (*http.Response, error)) {
	httpSender = sender
}

type Config struct {
	BaseURL    string
	Endpoint   string
	Username   string
	Password   string
	Headers    map[string]string
	Timeout    time.Duration
	HTTPClient *http.Client
	Transport  http.RoundTripper
	ActorID    string
}

type Client struct {
	baseURL    string
	headers    map[string]string
	timeout    time.Duration
	httpClient *http.Client
}

type Row map[string]any
type AnyRow map[string]any
type QueryResult struct {
	Rows []Row `json:"rows"`
}

func New(cfg *Config) *Client {
	timeout := 15 * time.Second
	if cfg != nil && cfg.Timeout > 0 {
		timeout = cfg.Timeout
	}
	baseURL := strings.TrimRight(strings.TrimSpace(clientFirstNonEmpty(
		clientConfigBaseURL(cfg),
		os.Getenv("LANCEDB_BASE_URL"),
		os.Getenv("NATA_BASE_URL"),
		os.Getenv("SPIN_VARIABLE_LANCEDB_BASE_URL"),
		os.Getenv("SPIN_VARIABLE_NATA_BASE_URL"),
		baseURLFromEndpoint(clientConfigEndpoint(cfg)),
		defaultBaseURL,
	)), "/")
	httpClient := clientConfigHTTPClient(cfg)
	if httpClient == nil {
		var transport http.RoundTripper
		if cfg != nil && cfg.Transport != nil {
			transport = cfg.Transport
		} else if httpSender == nil {
			transport = defaultHTTPTransport()
		}
		httpClient = &http.Client{
			Timeout:   timeout,
			Transport: transport,
		}
	}
	if httpClient.Timeout <= 0 {
		httpClient.Timeout = timeout
	}
	return &Client{
		baseURL:    baseURL,
		headers:    clientCloneHeaders(clientConfigHeaders(cfg)),
		timeout:    timeout,
		httpClient: httpClient,
	}
}

// QueryCursor executes a single-page query using a cursor predicate instead of OFFSET.
// cursorFilter is ANDed with filter (when both are non-empty), e.g. "seq_in_room < 1234".
// Use for hot timeline reads where OFFSET-based deep pagination is prohibited.
func (c *Client) QueryCursor(table, filter, cursorFilter, orderBy string, limit int) (*QueryResult, error) {
	combined := cursorFilter
	if filter != "" && cursorFilter != "" {
		combined = filter + " AND " + cursorFilter
	} else if filter != "" {
		combined = filter
	}
	rows, err := c.queryOrderedRows(table, combined, orderBy, limit, 0)
	if err != nil {
		return nil, err
	}
	return &QueryResult{Rows: rows}, nil
}

func (c *Client) QueryOrdered(table, filter, orderBy string, limit, offset int) (*QueryResult, error) {
	rows, err := c.queryOrderedRows(table, filter, orderBy, limit, offset)
	if err != nil {
		return nil, err
	}
	return &QueryResult{Rows: rows}, nil
}

func (c *Client) queryOrderedRows(table, filter, orderBy string, limit, offset int) ([]Row, error) {
	table = strings.TrimSpace(table)
	if table == "" {
		return nil, fmt.Errorf("table is required")
	}
	body := map[string]any{}
	if filter = strings.TrimSpace(filter); filter != "" {
		body["filter"] = filter
	}
	if orderBy = strings.TrimSpace(orderBy); orderBy != "" {
		body["order_by"] = orderBy
	}
	if limit > 0 {
		body["limit"] = limit
		body["offset"] = offset
		resp, err := c.postQuery(table, body)
		if err != nil {
			return nil, err
		}
		return toRows(resp["rows"]), nil
	}
	rows := make([]Row, 0, defaultPageSize)
	pageOffset := offset
	for {
		body["limit"] = defaultPageSize
		body["offset"] = pageOffset
		resp, err := c.postQuery(table, body)
		if err != nil {
			return nil, err
		}
		chunk := toRows(resp["rows"])
		rows = append(rows, chunk...)
		if len(chunk) < defaultPageSize {
			return rows, nil
		}
		pageOffset += defaultPageSize
	}
}

func (c *Client) Count(table, filter string) (int, error) {
	table = strings.TrimSpace(table)
	if table == "" {
		return 0, fmt.Errorf("table is required")
	}
	body := map[string]any{}
	if filter = strings.TrimSpace(filter); filter != "" {
		body["filter"] = filter
	}
	resp, err := c.doJSON(context.Background(), http.MethodPost, "/v1/table/"+url.PathEscape(table)+"/count_rows/", body)
	if err == nil {
		count, ok := resp["count"]
		if !ok {
			return 0, nil
		}
		switch v := count.(type) {
		case json.Number:
			n, numErr := v.Int64()
			return int(n), numErr
		case float64:
			return int(v), nil
		default:
			return strconv.Atoi(strings.TrimSpace(fmt.Sprint(v)))
		}
	}
	total := 0
	pageOffset := 0
	for {
		resp, err := c.postQuery(table, map[string]any{
			"filter": filter,
			"limit":  defaultPageSize,
			"offset": pageOffset,
		})
		if err != nil {
			return 0, err
		}
		chunk := toRows(resp["rows"])
		total += len(chunk)
		if len(chunk) < defaultPageSize {
			return total, nil
		}
		pageOffset += defaultPageSize
	}
}

func (c *Client) UpsertOneAny(table, docID string, row AnyRow) error {
	if strings.TrimSpace(table) == "" {
		return fmt.Errorf("table is required")
	}
	docID = strings.TrimSpace(docID)
	if docID == "" {
		return fmt.Errorf("missing _doc_id")
	}
	doc := make(map[string]any, len(row)+1)
	for key, value := range row {
		doc[key] = value
	}
	doc["_doc_id"] = docID
	body := map[string]any{
		"on":   "_doc_id",
		"rows": []map[string]any{doc},
	}
	_, err := c.doJSON(context.Background(), http.MethodPost, "/v1/table/"+url.PathEscape(table)+"/merge_insert/", body)
	if err == nil {
		return nil
	}
	if strings.Contains(err.Error(), "status=404") {
		_, err = c.doJSON(context.Background(), http.MethodPost, "/v1/table/"+url.PathEscape(table)+"/merge_insert", body)
	}
	return err
}

// AppendBatch appends multiple rows to a table in a single Arrow IPC request.
// Rows should already include _doc_id if needed by the table schema.
func (c *Client) AppendBatch(table string, rows []AnyRow) error {
	if strings.TrimSpace(table) == "" {
		return fmt.Errorf("table is required")
	}
	if len(rows) == 0 {
		return nil
	}
	docs := make([]map[string]any, len(rows))
	for i, row := range rows {
		doc := make(map[string]any, len(row))
		for k, v := range row {
			doc[k] = v
		}
		docs[i] = doc
	}
	body := map[string]any{
		"on":   []string{"_doc_id"},
		"rows": docs,
	}
	_, err := c.doJSON(context.Background(), http.MethodPost, "/v1/table/"+url.PathEscape(table)+"/merge_insert/", body)
	if err == nil {
		return nil
	}
	if strings.Contains(err.Error(), "status=404") {
		_, err = c.doJSON(context.Background(), http.MethodPost, "/v1/table/"+url.PathEscape(table)+"/merge_insert", body)
	}
	return err
}

// CompactTable triggers LanceDB fragment compaction + index cleanup for the table.
// Equivalent to the LanceDB REST POST /v1/table/{name}/optimize endpoint.
// Uses a 10-minute timeout regardless of the client's default timeout, because
// compacting hundreds of B2 fragments can take several minutes.
func (c *Client) CompactTable(table string) error {
	table = strings.TrimSpace(table)
	if table == "" {
		return fmt.Errorf("table name is required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()
	_, err := c.doJSON(ctx, http.MethodPost, "/v1/table/"+url.PathEscape(table)+"/optimize", map[string]any{})
	return err
}

// ListTables returns the names of all tables registered in Tonbo.
// Uses GET /v1/table (no trailing slash). Returns a set (map[string]bool) for O(1) lookup.
func (c *Client) ListTables() (map[string]bool, error) {
	resp, err := c.doJSON(context.Background(), http.MethodGet, "/v1/table", nil)
	if err != nil {
		return nil, err
	}
	raw, ok := resp["tables"]
	if !ok {
		return map[string]bool{}, nil
	}
	arr, ok := raw.([]any)
	if !ok {
		return map[string]bool{}, nil
	}
	set := make(map[string]bool, len(arr))
	for _, v := range arr {
		if s, ok := v.(string); ok && s != "" {
			set[s] = true
		}
	}
	return set, nil
}

// ── Index management ───────────────────────────────────────────────────────────

// ScalarIndexType is the index variant for non-vector columns.
type ScalarIndexType string

const (
	// ScalarIndexBTree is a B-Tree index for ordered scalar columns (org_id, src_id, ts_month …).
	ScalarIndexBTree ScalarIndexType = "BTREE"
	// ScalarIndexBitmap is a Bitmap index for low-cardinality columns (obj_kind, valid_to …).
	ScalarIndexBitmap ScalarIndexType = "BITMAP"
	// ScalarIndexLabelList is a inverted index for List<Utf8> columns (types …).
	ScalarIndexLabelList ScalarIndexType = "LABEL_LIST"
)

// VectorIndexConfig configures an IVF-PQ approximate nearest-neighbour index.
type VectorIndexConfig struct {
	Column        string // Arrow column name, e.g. "embedding"
	MetricType    string // "cosine" | "l2" | "dot"  (default: "cosine")
	NumPartitions int    // IVF partition count       (default: 256)
	NumSubVectors int    // PQ sub-vector count       (default: 96)
	MaxIterations int    // k-means max iterations    (default: 50)
}

// IndexInfo describes one index returned by ListIndexes.
type IndexInfo struct {
	Name    string   `json:"index_name"`
	Columns []string `json:"columns"`
	Type    string   `json:"index_type"`
	Status  string   `json:"status"` // "indexed" | "building"
}

// CreateScalarIndex creates a BTree/Bitmap/LabelList index on a column.
// Idempotent: returns nil when the index already exists or when the endpoint
// is not yet implemented by the server (404/501).
// When replace is true, an existing index is dropped and rebuilt (use when the
// index file on object storage is corrupt or unreachable).
func (c *Client) CreateScalarIndex(table, column string, idxType ScalarIndexType, replace ...bool) error {
	table = strings.TrimSpace(table)
	column = strings.TrimSpace(column)
	if table == "" || column == "" {
		return fmt.Errorf("CreateScalarIndex: table and column are required")
	}
	doReplace := len(replace) > 0 && replace[0]
	body := map[string]any{
		"column":     column,
		"index_type": string(idxType),
	}
	if doReplace {
		body["replace"] = true
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()
	_, err := c.doJSON(ctx, http.MethodPost,
		"/v1/table/"+url.PathEscape(table)+"/create_scalar_index/", body)
	if err == nil {
		return nil
	}
	if !doReplace && (isIndexExistsError(err) || isNotImplementedError(err)) {
		return nil
	}
	_, err2 := c.doJSON(ctx, http.MethodPost,
		"/v1/table/"+url.PathEscape(table)+"/create_scalar_index", body)
	if err2 == nil || (!doReplace && (isIndexExistsError(err2) || isNotImplementedError(err2))) {
		return nil
	}
	return err2
}

// CreateVectorIndex creates an IVF-PQ vector index on an embedding column.
// Idempotent: returns nil when the index already exists or when the endpoint
// is not yet implemented by the server (404/501).
func (c *Client) CreateVectorIndex(table string, cfg VectorIndexConfig) error {
	table = strings.TrimSpace(table)
	if table == "" || cfg.Column == "" {
		return fmt.Errorf("CreateVectorIndex: table and column are required")
	}
	metric := cfg.MetricType
	if metric == "" {
		metric = "cosine"
	}
	numParts := cfg.NumPartitions
	if numParts <= 0 {
		numParts = 256
	}
	numSub := cfg.NumSubVectors
	if numSub <= 0 {
		numSub = 96
	}
	maxIter := cfg.MaxIterations
	if maxIter <= 0 {
		maxIter = 50
	}
	body := map[string]any{
		"column":          cfg.Column,
		"index_type":      "IVF_PQ",
		"metric_type":     metric,
		"num_partitions":  numParts,
		"num_sub_vectors": numSub,
		"max_iterations":  maxIter,
	}
	_, err := c.doJSON(context.Background(), http.MethodPost,
		"/v1/table/"+url.PathEscape(table)+"/create_index/", body)
	if err == nil {
		return nil
	}
	if isIndexExistsError(err) || isNotImplementedError(err) {
		return nil
	}
	_, err2 := c.doJSON(context.Background(), http.MethodPost,
		"/v1/table/"+url.PathEscape(table)+"/create_index", body)
	if err2 == nil || isIndexExistsError(err2) || isNotImplementedError(err2) {
		return nil
	}
	return err2
}

// DropIndex removes a named index from a table.
// Returns nil when the index does not exist (idempotent).
func (c *Client) DropIndex(table, indexName string) error {
	table = strings.TrimSpace(table)
	indexName = strings.TrimSpace(indexName)
	if table == "" || indexName == "" {
		return fmt.Errorf("DropIndex: table and indexName are required")
	}
	_, err := c.doJSON(context.Background(), http.MethodDelete,
		"/v1/table/"+url.PathEscape(table)+"/index/"+url.PathEscape(indexName)+"/", nil)
	if err != nil && strings.Contains(err.Error(), "status=404") {
		return nil
	}
	return err
}

// ListIndexes returns metadata for all indexes on a table.
func (c *Client) ListIndexes(table string) ([]IndexInfo, error) {
	table = strings.TrimSpace(table)
	if table == "" {
		return nil, fmt.Errorf("ListIndexes: table is required")
	}
	resp, err := c.doJSON(context.Background(), http.MethodGet,
		"/v1/table/"+url.PathEscape(table)+"/index/", nil)
	if err != nil {
		return nil, err
	}
	raw, ok := resp["indexes"]
	if !ok {
		return nil, nil
	}
	items, _ := raw.([]any)
	out := make([]IndexInfo, 0, len(items))
	for _, item := range items {
		m, ok := item.(map[string]any)
		if !ok {
			continue
		}
		info := IndexInfo{
			Name:   stringify(m["index_name"]),
			Type:   stringify(m["index_type"]),
			Status: stringify(m["status"]),
		}
		if cols, ok := m["columns"].([]any); ok {
			for _, col := range cols {
				info.Columns = append(info.Columns, fmt.Sprint(col))
			}
		}
		out = append(out, info)
	}
	return out, nil
}

func isIndexExistsError(err error) bool {
	if err == nil {
		return false
	}
	msg := strings.ToLower(err.Error())
	return strings.Contains(msg, "already exists") ||
		strings.Contains(msg, "status=409") ||
		strings.Contains(msg, "index exists")
}

// isNotImplementedError returns true when the server returns 404 or 501 for an index
// management endpoint, indicating the feature is not yet supported by this server version.
func isNotImplementedError(err error) bool {
	if err == nil {
		return false
	}
	msg := err.Error()
	return strings.Contains(msg, "status=404") ||
		strings.Contains(msg, "status=501") ||
		strings.Contains(msg, "not implemented")
}

func (c *Client) DeleteOne(table, docID string) error {
	table = strings.TrimSpace(table)
	docID = strings.TrimSpace(docID)
	if table == "" || docID == "" {
		return fmt.Errorf("table and docID are required")
	}
	body := map[string]any{
		"predicate": "_doc_id = '" + strings.ReplaceAll(docID, "'", "''") + "'",
	}
	_, err := c.doJSON(context.Background(), http.MethodPost, "/v1/table/"+url.PathEscape(table)+"/delete/", body)
	return err
}

func (c *Client) QuerySQL(sql string) ([]Row, error) {
	stmt, err := parseSelectSQL(sql)
	if err != nil {
		return nil, err
	}
	if stmt.countAlias != "" {
		count, err := c.Count(stmt.table, stmt.filter)
		if err != nil {
			return nil, err
		}
		return []Row{{stmt.countAlias: count}}, nil
	}
	body := map[string]any{}
	if stmt.filter != "" {
		body["filter"] = stmt.filter
	}
	if stmt.orderBy != "" {
		body["order_by"] = stmt.orderBy
	}
	if stmt.limit > 0 {
		body["limit"] = stmt.limit
		body["offset"] = stmt.offset
		resp, err := c.postQuery(stmt.table, body)
		if err != nil {
			return nil, err
		}
		return toRows(resp["rows"]), nil
	}
	rows := make([]Row, 0, defaultPageSize)
	pageOffset := stmt.offset
	for {
		body["limit"] = defaultPageSize
		body["offset"] = pageOffset
		resp, err := c.postQuery(stmt.table, body)
		if err != nil {
			return nil, err
		}
		chunk := toRows(resp["rows"])
		rows = append(rows, chunk...)
		if len(chunk) < defaultPageSize {
			return rows, nil
		}
		pageOffset += defaultPageSize
	}
}

func (c *Client) ExecSQL(sql string) error {
	raw := strings.TrimSpace(sql)
	if raw == "" {
		return nil
	}
	if createSQLPattern.MatchString(raw) {
		return c.createTableFromDDL(raw)
	}
	stmt, err := parseInsertSQL(raw)
	if err != nil {
		return err
	}
	docID, _ := stmt.row["_doc_id"]
	return c.UpsertOneAny(stmt.table, stringify(docID), stmt.row)
}

func (c *Client) createTableFromDDL(ddl string) error {
	table, fields := parseDDLToFields(ddl)
	if table == "" {
		return nil
	}
	body := map[string]any{
		"fields": fields,
	}
	_, err := c.doJSON(context.Background(), http.MethodPost, "/v1/table/"+url.PathEscape(table)+"/create", body)
	if err != nil {
		if strings.Contains(err.Error(), "already exists") || strings.Contains(err.Error(), "status=409") {
			return nil
		}
		return err
	}
	return nil
}

// parseDDLToFields parses a CREATE TABLE IF NOT EXISTS DDL and returns
// the table name and a fields array compatible with the tonbo /create API
// {"fields": [{"name": "col", "type": "string", "nullable": true}, ...]}.
func parseDDLToFields(ddl string) (string, []map[string]any) {
	upper := strings.ToUpper(ddl)
	idx := strings.Index(upper, "EXISTS")
	if idx < 0 {
		return "", nil
	}
	rest := strings.TrimSpace(ddl[idx+6:])
	parenIdx := strings.Index(rest, "(")
	if parenIdx < 0 {
		return "", nil
	}
	table := trimIdentifier(rest[:parenIdx])
	colDefs := rest[parenIdx+1:]
	if lastParen := strings.LastIndex(colDefs, ")"); lastParen >= 0 {
		colDefs = colDefs[:lastParen]
	}
	var fields []map[string]any
	for _, part := range splitColumnDefs(colDefs) {
		part = strings.TrimSpace(part)
		if strings.HasPrefix(strings.ToUpper(part), "PRIMARY KEY") {
			continue
		}
		tokens := strings.Fields(part)
		if len(tokens) < 2 {
			continue
		}
		colName := trimIdentifier(tokens[0])
		colType := strings.ToUpper(tokens[1])
		var arrowType string
		switch colType {
		case "BIGINT", "INT", "INTEGER":
			arrowType = "int64"
		case "DOUBLE", "FLOAT", "REAL":
			arrowType = "float64"
		case "BOOLEAN", "BOOL":
			arrowType = "bool"
		default:
			arrowType = "string"
		}
		fields = append(fields, map[string]any{
			"name":     colName,
			"type":     arrowType,
			"nullable": true,
		})
	}
	return table, fields
}

func splitColumnDefs(s string) []string {
	var parts []string
	depth := 0
	start := 0
	for i := 0; i < len(s); i++ {
		switch s[i] {
		case '(':
			depth++
		case ')':
			depth--
		case ',':
			if depth == 0 {
				parts = append(parts, s[start:i])
				start = i + 1
			}
		}
	}
	if start < len(s) {
		parts = append(parts, s[start:])
	}
	return parts
}

type selectStatement struct {
	table      string
	columns    []string
	filter     string
	orderBy    string
	limit      int
	offset     int
	countAlias string
}

type insertStatement struct {
	table string
	row   AnyRow
}

func parseSelectSQL(sql string) (selectStatement, error) {
	matches := selectSQLPattern.FindStringSubmatch(strings.TrimSpace(sql))
	if len(matches) != 7 {
		return selectStatement{}, fmt.Errorf("unsupported select sql: %s", sql)
	}
	table := trimIdentifier(matches[2])
	cols := strings.TrimSpace(matches[1])
	stmt := selectStatement{
		table:   table,
		filter:  strings.TrimSpace(matches[3]),
		orderBy: strings.TrimSpace(matches[4]),
	}
	if matches[5] != "" {
		stmt.limit, _ = strconv.Atoi(matches[5])
	}
	if matches[6] != "" {
		stmt.offset, _ = strconv.Atoi(matches[6])
	}
	if alias := parseCountAlias(cols); alias != "" {
		stmt.countAlias = alias
		return stmt, nil
	}
	if cols == "*" {
		return stmt, nil
	}
	parts := splitCSV(cols)
	columns := make([]string, 0, len(parts))
	for _, part := range parts {
		part = strings.TrimSpace(part)
		if part == "" {
			continue
		}
		if !isPlainIdentifier(part) {
			return selectStatement{
				table:   table,
				filter:  stmt.filter,
				orderBy: stmt.orderBy,
				limit:   stmt.limit,
				offset:  stmt.offset,
			}, nil
		}
		columns = append(columns, trimIdentifier(part))
	}
	stmt.columns = columns
	return stmt, nil
}

func parseInsertSQL(sql string) (insertStatement, error) {
	matches := insertSQLPattern.FindStringSubmatch(strings.TrimSpace(sql))
	if len(matches) != 4 {
		return insertStatement{}, fmt.Errorf("unsupported exec sql: %s", sql)
	}
	columns := splitCSV(matches[2])
	values := splitCSV(matches[3])
	if len(columns) != len(values) {
		return insertStatement{}, fmt.Errorf("insert columns/values mismatch")
	}
	row := AnyRow{}
	for i := range columns {
		row[trimIdentifier(columns[i])] = parseSQLLiteral(values[i])
	}
	return insertStatement{
		table: trimIdentifier(matches[1]),
		row:   row,
	}, nil
}

func (c *Client) postQuery(table string, body map[string]any) (map[string]any, error) {
	return c.doJSON(context.Background(), http.MethodPost, "/v1/table/"+url.PathEscape(table)+"/query/", normalizeBody(body))
}

func normalizeBody(body map[string]any) map[string]any {
	out := make(map[string]any, len(body))
	for key, value := range body {
		switch v := value.(type) {
		case string:
			if strings.TrimSpace(v) == "" {
				continue
			}
			out[key] = v
		case []string:
			if key == "columns" {
				paths := make([][]string, 0, len(v))
				for _, item := range v {
					if strings.TrimSpace(item) == "" {
						continue
					}
					paths = append(paths, []string{strings.TrimSpace(item)})
				}
				out[key] = paths
				continue
			}
			out[key] = v
		default:
			out[key] = value
		}
	}
	return out
}

func (c *Client) doJSON(ctx context.Context, method, path string, body any) (map[string]any, error) {
	if c == nil || strings.TrimSpace(c.baseURL) == "" {
		return nil, fmt.Errorf("lancedb base URL is empty")
	}
	client := c.httpClient
	if client == nil {
		client = http.DefaultClient
	}
	if client == nil {
		client = &http.Client{}
	}
	if c.timeout > 0 && client.Timeout <= 0 {
		client.Timeout = c.timeout
	}
	if ctx == nil {
		ctx = context.Background()
	}
	if _, ok := ctx.Deadline(); !ok && c.timeout > 0 {
		var cancel context.CancelFunc
		ctx, cancel = context.WithTimeout(ctx, c.timeout)
		defer cancel()
	}
	var reader io.Reader
	var payload []byte
	var err error
	if body != nil {
		payload, err = marshalJSONBody(body)
		if err != nil {
			return nil, err
		}
		reader = bytes.NewReader(payload)
	}
	req, err := http.NewRequestWithContext(ctx, method, c.baseURL+path, reader)
	if err != nil {
		return nil, err
	}
	for key, value := range c.headers {
		req.Header.Set(key, value)
	}
	req.Header.Set("Accept", "application/json")
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	var resp *http.Response
	if httpSender != nil {
		resp, err = httpSender(req)
	} else {
		resp, err = client.Do(req)
	}
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 300 {
		return nil, fmt.Errorf("%s %s status=%d body=%s", method, path, resp.StatusCode, strings.TrimSpace(string(raw)))
	}
	if len(raw) == 0 {
		return map[string]any{}, nil
	}
	// Unmarshal into interface{} first to avoid TinyGo 0.35 panic
	// (json.Unmarshal into *map[string]any triggers reflect.Implements → AssignableTo panic,
	// but *interface{} takes a different code path that works)
	var m interface{}
	if err := json.Unmarshal(raw, &m); err != nil {
		return nil, err
	}
	if out, ok := m.(map[string]interface{}); ok {
		return out, nil
	}
	return map[string]any{}, nil
}

func (c *Client) doBytes(ctx context.Context, method, path, contentType string, body []byte) ([]byte, error) {
	if c == nil || strings.TrimSpace(c.baseURL) == "" {
		return nil, fmt.Errorf("lancedb base URL is empty")
	}
	client := c.httpClient
	if client == nil {
		client = http.DefaultClient
	}
	if client == nil {
		client = &http.Client{}
	}
	if c.timeout > 0 && client.Timeout <= 0 {
		client.Timeout = c.timeout
	}
	if ctx == nil {
		ctx = context.Background()
	}
	if _, ok := ctx.Deadline(); !ok && c.timeout > 0 {
		var cancel context.CancelFunc
		ctx, cancel = context.WithTimeout(ctx, c.timeout)
		defer cancel()
	}
	req, err := http.NewRequestWithContext(ctx, method, c.baseURL+path, bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	for key, value := range c.headers {
		req.Header.Set(key, value)
	}
	if strings.TrimSpace(contentType) != "" {
		req.Header.Set("Content-Type", contentType)
	}
	var resp *http.Response
	if httpSender != nil {
		resp, err = httpSender(req)
	} else {
		resp, err = client.Do(req)
	}
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 300 {
		return nil, fmt.Errorf("%s %s status=%d body=%s", method, path, resp.StatusCode, strings.TrimSpace(string(raw)))
	}
	return raw, nil
}

func marshalJSONBody(body any) ([]byte, error) {
	switch v := body.(type) {
	case nil:
		return nil, nil
	case []byte:
		return v, nil
	case string:
		return []byte(v), nil
	default:
		var buf bytes.Buffer
		if err := writeJSONValue(&buf, body); err != nil {
			return nil, err
		}
		return buf.Bytes(), nil
	}
}

func writeJSONValue(buf *bytes.Buffer, value any) error {
	switch v := value.(type) {
	case nil:
		buf.WriteString("null")
	case string:
		writeJSONString(buf, v)
	case bool:
		if v {
			buf.WriteString("true")
		} else {
			buf.WriteString("false")
		}
	case int:
		buf.WriteString(strconv.Itoa(v))
	case int8:
		buf.WriteString(strconv.FormatInt(int64(v), 10))
	case int16:
		buf.WriteString(strconv.FormatInt(int64(v), 10))
	case int32:
		buf.WriteString(strconv.FormatInt(int64(v), 10))
	case int64:
		buf.WriteString(strconv.FormatInt(v, 10))
	case uint:
		buf.WriteString(strconv.FormatUint(uint64(v), 10))
	case uint8:
		buf.WriteString(strconv.FormatUint(uint64(v), 10))
	case uint16:
		buf.WriteString(strconv.FormatUint(uint64(v), 10))
	case uint32:
		buf.WriteString(strconv.FormatUint(uint64(v), 10))
	case uint64:
		buf.WriteString(strconv.FormatUint(v, 10))
	case float32:
		buf.WriteString(strconv.FormatFloat(float64(v), 'f', -1, 32))
	case float64:
		buf.WriteString(strconv.FormatFloat(v, 'f', -1, 64))
	case []string:
		buf.WriteByte('[')
		for i, item := range v {
			if i > 0 {
				buf.WriteByte(',')
			}
			if err := writeJSONValue(buf, item); err != nil {
				return err
			}
		}
		buf.WriteByte(']')
	case [][]string:
		buf.WriteByte('[')
		for i, item := range v {
			if i > 0 {
				buf.WriteByte(',')
			}
			if err := writeJSONValue(buf, item); err != nil {
				return err
			}
		}
		buf.WriteByte(']')
	case []any:
		buf.WriteByte('[')
		for i, item := range v {
			if i > 0 {
				buf.WriteByte(',')
			}
			if err := writeJSONValue(buf, item); err != nil {
				return err
			}
		}
		buf.WriteByte(']')
	case []map[string]any:
		buf.WriteByte('[')
		for i, item := range v {
			if i > 0 {
				buf.WriteByte(',')
			}
			if err := writeJSONValue(buf, item); err != nil {
				return err
			}
		}
		buf.WriteByte(']')
	case map[string]string:
		keys := make([]string, 0, len(v))
		for key := range v {
			keys = append(keys, key)
		}
		sort.Strings(keys)
		buf.WriteByte('{')
		for i, key := range keys {
			if i > 0 {
				buf.WriteByte(',')
			}
			if err := writeJSONValue(buf, key); err != nil {
				return err
			}
			buf.WriteByte(':')
			if err := writeJSONValue(buf, v[key]); err != nil {
				return err
			}
		}
		buf.WriteByte('}')
	case map[string]any:
		keys := make([]string, 0, len(v))
		for key := range v {
			keys = append(keys, key)
		}
		sort.Strings(keys)
		buf.WriteByte('{')
		for i, key := range keys {
			if i > 0 {
				buf.WriteByte(',')
			}
			if err := writeJSONValue(buf, key); err != nil {
				return err
			}
			buf.WriteByte(':')
			if err := writeJSONValue(buf, v[key]); err != nil {
				return err
			}
		}
		buf.WriteByte('}')
	default:
		return fmt.Errorf("unsupported json body type %T", value)
	}
	return nil
}

func writeJSONString(buf *bytes.Buffer, value string) {
	buf.WriteByte('"')
	for _, r := range value {
		switch r {
		case '\\', '"':
			buf.WriteByte('\\')
			buf.WriteRune(r)
		case '\b':
			buf.WriteString(`\b`)
		case '\f':
			buf.WriteString(`\f`)
		case '\n':
			buf.WriteString(`\n`)
		case '\r':
			buf.WriteString(`\r`)
		case '\t':
			buf.WriteString(`\t`)
		default:
			if r < 0x20 {
				buf.WriteString(`\u`)
				buf.WriteString(fmt.Sprintf("%04x", r))
				continue
			}
			buf.WriteRune(r)
		}
	}
	buf.WriteByte('"')
}

func toRows(raw any) []Row {
	items, _ := raw.([]any)
	rows := make([]Row, 0, len(items))
	for _, item := range items {
		row, ok := item.(map[string]any)
		if !ok {
			continue
		}
		rows = append(rows, Row(row))
	}
	return rows
}

func parseCountAlias(expr string) string {
	expr = strings.TrimSpace(strings.ToLower(expr))
	if !strings.HasPrefix(expr, "count(*)") && !strings.HasPrefix(expr, "count()") {
		return ""
	}
	if idx := strings.Index(expr, " as "); idx >= 0 {
		return strings.TrimSpace(expr[idx+4:])
	}
	return "count"
}

func splitCSV(raw string) []string {
	parts := make([]string, 0, 8)
	var b strings.Builder
	inQuote := false
	for i := 0; i < len(raw); i++ {
		ch := raw[i]
		if ch == '\'' {
			b.WriteByte(ch)
			if inQuote && i+1 < len(raw) && raw[i+1] == '\'' {
				i++
				b.WriteByte(raw[i])
				continue
			}
			inQuote = !inQuote
			continue
		}
		if ch == ',' && !inQuote {
			parts = append(parts, strings.TrimSpace(b.String()))
			b.Reset()
			continue
		}
		b.WriteByte(ch)
	}
	if b.Len() > 0 {
		parts = append(parts, strings.TrimSpace(b.String()))
	}
	return parts
}

func parseSQLLiteral(raw string) any {
	value := strings.TrimSpace(raw)
	switch {
	case value == "", strings.EqualFold(value, "null"):
		return nil
	case strings.HasPrefix(value, "'") && strings.HasSuffix(value, "'"):
		return strings.ReplaceAll(value[1:len(value)-1], "''", "'")
	case strings.EqualFold(value, "true"):
		return true
	case strings.EqualFold(value, "false"):
		return false
	}
	if i, err := strconv.ParseInt(value, 10, 64); err == nil {
		return i
	}
	if f, err := strconv.ParseFloat(value, 64); err == nil {
		return f
	}
	return value
}

func trimIdentifier(raw string) string {
	return strings.Trim(strings.TrimSpace(raw), `"`)
}

func isPlainIdentifier(raw string) bool {
	raw = trimIdentifier(raw)
	if raw == "" {
		return false
	}
	for i, r := range raw {
		if (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z') || r == '_' || r == '-' || (i > 0 && r >= '0' && r <= '9') {
			continue
		}
		return false
	}
	return true
}

func stringify(v any) string {
	switch x := v.(type) {
	case nil:
		return ""
	case string:
		return strings.TrimSpace(x)
	case json.Number:
		return x.String()
	default:
		return strings.TrimSpace(fmt.Sprint(x))
	}
}

func baseURLFromEndpoint(endpoint string) string {
	endpoint = strings.TrimSpace(endpoint)
	if endpoint == "" {
		return ""
	}
	if !strings.Contains(endpoint, "://") {
		endpoint = "http://" + endpoint
	}
	parsed, err := url.Parse(endpoint)
	if err != nil || parsed.Host == "" {
		return ""
	}
	host := parsed.Host
	if strings.HasSuffix(host, ":50050") {
		host = strings.TrimSuffix(host, ":50050") + ":8084"
	}
	if parsed.Scheme == "" {
		parsed.Scheme = "http"
	}
	return parsed.Scheme + "://" + host
}

func clientCloneHeaders(in map[string]string) map[string]string {
	if len(in) == 0 {
		return nil
	}
	out := make(map[string]string, len(in))
	for key, value := range in {
		out[key] = value
	}
	return out
}

func clientFirstNonEmpty(values ...string) string {
	for _, value := range values {
		if strings.TrimSpace(value) != "" {
			return strings.TrimSpace(value)
		}
	}
	return ""
}

func clientConfigBaseURL(cfg *Config) string {
	if cfg == nil {
		return ""
	}
	return cfg.BaseURL
}

func clientConfigEndpoint(cfg *Config) string {
	if cfg == nil {
		return ""
	}
	return cfg.Endpoint
}

func clientConfigHeaders(cfg *Config) map[string]string {
	if cfg == nil {
		return nil
	}
	return cfg.Headers
}

func clientConfigHTTPClient(cfg *Config) *http.Client {
	if cfg == nil {
		return nil
	}
	return cfg.HTTPClient
}
