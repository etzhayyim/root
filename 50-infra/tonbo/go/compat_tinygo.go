//go:build tinygo

package lancedbrest

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"net/url"
	"strconv"
	"strings"
)

var ErrKeyNotFound = errors.New("key not found")

type DataFrame = QueryResult
type FieldType string

const (
	FieldString    FieldType = "TEXT"
	FieldInt64     FieldType = "BIGINT"
	FieldFloat64   FieldType = "DOUBLE"
	FieldTimestamp FieldType = "TEXT"
	FieldBoolean   FieldType = "BOOLEAN"
)

type Field struct {
	Name string
	Type FieldType
}

type TableSchema struct {
	Table      string
	PrimaryKey string
	Fields     []Field
}

// EnsureTableSchema keeps tinygo builds aligned with the non-tinygo compatibility layer.
// It creates the table when missing, using a minimal schema mapping.
func (c *Client) EnsureTableSchema(schema TableSchema) error {
	return c.EnsureTable(schema.Table, schema)
}

// TableExists probes whether the table exists in Tonbo. Returns false on 404.
func (c *Client) TableExists(table string) (bool, error) {
	_, err := c.doJSON(context.Background(), http.MethodPost, "/v1/table/"+url.PathEscape(table)+"/exists/", map[string]any{})
	if err == nil {
		return true, nil
	}
	if strings.Contains(err.Error(), "status=404") {
		return false, nil
	}
	return false, err
}

// EnsureTable creates the table if it does not exist.
func (c *Client) EnsureTable(table string, schema TableSchema) error {
	table = strings.TrimSpace(table)
	if table == "" {
		return fmt.Errorf("table name is required")
	}
	// Check existence first so we never run warmup on an already-initialized table.
	// createTableFromDDL absorbs the 409 and returns nil, so we cannot use its return
	// value to distinguish "was created now" from "already existed".
	if exists, err := c.TableExists(table); err == nil && exists {
		return nil
	}
	fields := make([]string, 0, len(schema.Fields)+2)
	seen := map[string]bool{}
	seen["_doc_id"] = true
	fields = append(fields, `"_doc_id" TEXT`)
	if pk := strings.TrimSpace(schema.PrimaryKey); pk != "" {
		seen[pk] = true
		fields = append(fields, fmt.Sprintf(`"%s" %s`, strings.ReplaceAll(pk, `"`, `"`+`"`), "TEXT"))
	}
	for _, field := range schema.Fields {
		name := strings.TrimSpace(field.Name)
		if name == "" || seen[name] {
			continue
		}
		seen[name] = true
		fields = append(fields, fmt.Sprintf(`"%s" %s`, strings.ReplaceAll(name, `"`, `"`+`"`), fieldTypeSQL(field.Type)))
	}
	if len(fields) == 0 {
		return fmt.Errorf("table %s has no columns", table)
	}
	ddl := fmt.Sprintf(`CREATE TABLE IF NOT EXISTS "%s" (%s)`, strings.ReplaceAll(table, `"`, `"`+`"`), strings.Join(fields, ", "))
	// Use createTableFromDDL directly to avoid regexp in ExecSQL (TinyGo: regexp causes runtime panic).
	if err := c.createTableFromDDL(ddl); err != nil {
		if strings.Contains(err.Error(), "already exists") || strings.Contains(err.Error(), "status=409") {
			return nil
		}
		return err
	}
	// Warmup: Lance /create builds an empty schema placeholder. Without a real row, WHERE
	// filters cause "column not found". Insert a sentinel row then delete it to establish schema.
	const seedID = "__tonbo_seed__"
	seed := make(AnyRow, len(schema.Fields)+2)
	seed["_doc_id"] = seedID
	if pk := strings.TrimSpace(schema.PrimaryKey); pk != "" {
		seed[pk] = ""
	}
	for _, field := range schema.Fields {
		name := strings.TrimSpace(field.Name)
		if name == "" {
			continue
		}
		switch field.Type {
		case FieldInt64:
			seed[name] = int64(0)
		case FieldFloat64:
			seed[name] = float64(0)
		case FieldBoolean:
			seed[name] = false
		default:
			seed[name] = ""
		}
	}
	if err := c.UpsertOneAny(table, seedID, seed); err != nil {
		return err
	}
	_ = c.DeleteOne(table, seedID)
	return nil
}

func fieldTypeSQL(ft FieldType) string {
	switch string(ft) {
	case string(FieldInt64):
		return "BIGINT"
	case string(FieldFloat64):
		return "DOUBLE"
	case string(FieldBoolean):
		return "BOOLEAN"
	case string(FieldTimestamp):
		return "TEXT"
	default:
		return "TEXT"
	}
}

func RowStr(row Row, key string) string {
	if row == nil {
		return ""
	}
	v, ok := row[key]
	if !ok || v == nil {
		return ""
	}
	switch x := v.(type) {
	case string:
		return x
	case float64:
		return strconv.FormatFloat(x, 'f', -1, 64)
	case int:
		return strconv.Itoa(x)
	case int64:
		return strconv.FormatInt(x, 10)
	case bool:
		return strconv.FormatBool(x)
	default:
		return fmt.Sprint(x)
	}
}

func Itoa(v int) string {
	return strconv.Itoa(v)
}

// ── Table/QueryBuilder fluent API (TinyGo-compatible) ────────────────────

type TableHandle struct {
	client *Client
	name   string
}

type QueryBuilder struct {
	client  *Client
	table   string
	columns []string
	filters []string
	orderBy []string
	limit   int
	offset  int
	final   bool // ignored in TinyGo build (no FINAL clause)
}

func (c *Client) Table(name string) *TableHandle {
	return &TableHandle{client: c, name: strings.TrimSpace(name)}
}

func (c *Client) UpsertOne(table, docID string, row Row) error {
	return c.UpsertOneAny(table, docID, AnyRow(row))
}

func (c *Client) Query(table, filter string, limit int) (*QueryResult, error) {
	return c.QueryOrdered(table, filter, "", limit, 0)
}

func (c *Client) CountRows(table, filter string) (int, error) {
	return c.Count(table, filter)
}

func (c *Client) Delete(table, docID string, _ Row) error {
	return c.DeleteOne(table, docID)
}

func (t *TableHandle) Select(columns ...string) *QueryBuilder {
	return &QueryBuilder{
		client:  t.client,
		table:   t.name,
		columns: normalizeColumns(columns),
	}
}

func (t *TableHandle) Insert(row Row) error {
	if t == nil || t.client == nil {
		return fmt.Errorf("lancedbrest table client is nil")
	}
	docID := strings.TrimSpace(RowStr(row, "_doc_id"))
	if docID == "" {
		return t.client.ExecSQL(insertSQL(t.name, map[string]any(row)))
	}
	return t.client.UpsertOne(t.name, docID, row)
}

func (t *TableHandle) InsertBatch(rows []Row) error {
	if t == nil || t.client == nil {
		return fmt.Errorf("lancedbrest table client is nil")
	}
	for _, row := range rows {
		if err := t.Insert(row); err != nil {
			return err
		}
	}
	return nil
}

func (t *TableHandle) Delete(docID string) error {
	if t == nil || t.client == nil {
		return fmt.Errorf("lancedbrest table client is nil")
	}
	return t.client.DeleteOne(t.name, docID)
}

func (q *QueryBuilder) Final() *QueryBuilder {
	q.final = true
	return q
}

func (q *QueryBuilder) WhereEq(column string, value any) *QueryBuilder {
	q.filters = append(q.filters, fmt.Sprintf(`%s = %s`, quoteIdentifier(column), sqlLiteral(value)))
	return q
}

func (q *QueryBuilder) Where(filter string) *QueryBuilder {
	filter = strings.TrimSpace(filter)
	if filter != "" {
		q.filters = append(q.filters, filter)
	}
	return q
}

func (q *QueryBuilder) OrderBy(parts ...string) *QueryBuilder {
	for _, part := range parts {
		part = strings.TrimSpace(part)
		if part != "" {
			q.orderBy = append(q.orderBy, part)
		}
	}
	return q
}

func (q *QueryBuilder) Limit(limit int) *QueryBuilder {
	q.limit = limit
	return q
}

func (q *QueryBuilder) Offset(offset int) *QueryBuilder {
	q.offset = offset
	return q
}

func (q *QueryBuilder) Rows() ([]Row, error) {
	if q == nil || q.client == nil {
		return nil, fmt.Errorf("lancedbrest query is nil")
	}
	return q.client.QuerySQL(q.buildSelectSQL(false))
}

func (q *QueryBuilder) Query() ([]Row, error) {
	return q.Rows()
}

func (q *QueryBuilder) Row() (Row, error) {
	if q == nil || q.client == nil {
		return nil, fmt.Errorf("lancedbrest query is nil")
	}
	clone := *q
	if clone.limit <= 0 {
		clone.limit = 1
	}
	if clone.final && len(clone.orderBy) == 0 {
		clone.orderBy = append(clone.orderBy, finalOrderFallback()...)
	}
	rows, err := clone.client.QuerySQL(clone.buildSelectSQL(false))
	if err != nil {
		return nil, err
	}
	if len(rows) == 0 {
		return nil, ErrKeyNotFound
	}
	return rows[0], nil
}

func (q *QueryBuilder) Count() (int, error) {
	if q == nil || q.client == nil {
		return 0, fmt.Errorf("lancedbrest query is nil")
	}
	rows, err := q.client.QuerySQL(q.buildSelectSQL(true))
	if err != nil {
		return 0, err
	}
	if len(rows) == 0 {
		return 0, nil
	}
	v := strings.TrimSpace(firstNonEmpty(RowStr(rows[0], "row_count"), RowStr(rows[0], "count"), "0"))
	n, _ := strconv.Atoi(v)
	return n, nil
}

func (q *QueryBuilder) buildSelectSQL(countOnly bool) string {
	selectExpr := "*"
	if countOnly {
		selectExpr = "COUNT(*) AS row_count"
	} else if len(q.columns) > 0 {
		out := make([]string, 0, len(q.columns))
		for _, col := range q.columns {
			out = append(out, renderSelectExpr(col))
		}
		selectExpr = strings.Join(out, ", ")
	}
	sql := fmt.Sprintf(`SELECT %s FROM %s`, selectExpr, quoteIdentifier(q.table))
	if len(q.filters) > 0 {
		sql += " WHERE " + strings.Join(q.filters, " AND ")
	}
	if !countOnly && len(q.orderBy) > 0 {
		sql += " ORDER BY " + strings.Join(q.orderBy, ", ")
	}
	if !countOnly && q.limit > 0 {
		sql += fmt.Sprintf(" LIMIT %d", q.limit)
	}
	if !countOnly && q.offset > 0 {
		sql += fmt.Sprintf(" OFFSET %d", q.offset)
	}
	return sql
}

// ── SQL helpers (TinyGo-compatible, no regexp/math/time) ─────────────────

func quoteIdentifier(name string) string {
	return `"` + strings.ReplaceAll(strings.TrimSpace(name), `"`, `""`) + `"`
}

// isSimpleIdent returns true for plain column names (letters, digits, underscore, starts with letter or underscore).
func isSimpleIdent(s string) bool {
	if len(s) == 0 {
		return false
	}
	for i, c := range s {
		if i == 0 {
			if !((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || c == '_') {
				return false
			}
		} else {
			if !((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '_') {
				return false
			}
		}
	}
	return true
}

func renderSelectExpr(expr string) string {
	expr = strings.TrimSpace(expr)
	if expr == "" || expr == "*" {
		return "*"
	}
	if isSimpleIdent(expr) {
		return quoteIdentifier(expr)
	}
	return expr
}

func sqlLiteral(v any) string {
	switch x := v.(type) {
	case nil:
		return "NULL"
	case string:
		return "'" + strings.ReplaceAll(x, "'", "''") + "'"
	case []byte:
		return "'" + strings.ReplaceAll(string(x), "'", "''") + "'"
	case bool:
		if x {
			return "1"
		}
		return "0"
	case int:
		return strconv.Itoa(x)
	case int8:
		return strconv.FormatInt(int64(x), 10)
	case int16:
		return strconv.FormatInt(int64(x), 10)
	case int32:
		return strconv.FormatInt(int64(x), 10)
	case int64:
		return strconv.FormatInt(x, 10)
	case uint:
		return strconv.FormatUint(uint64(x), 10)
	case uint8:
		return strconv.FormatUint(uint64(x), 10)
	case uint16:
		return strconv.FormatUint(uint64(x), 10)
	case uint32:
		return strconv.FormatUint(uint64(x), 10)
	case uint64:
		return strconv.FormatUint(x, 10)
	case float32:
		return strconv.FormatFloat(float64(x), 'f', -1, 32)
	case float64:
		return strconv.FormatFloat(x, 'f', -1, 64)
	default:
		return "'" + strings.ReplaceAll(fmt.Sprint(x), "'", "''") + "'"
	}
}

func insertSQL(table string, row map[string]any) string {
	cols := sortedKeys(row)
	values := make([]string, 0, len(cols))
	for _, col := range cols {
		values = append(values, sqlLiteral(row[col]))
	}
	return fmt.Sprintf(`INSERT INTO %s (%s) VALUES (%s)`, quoteIdentifier(table), joinQuoted(cols), strings.Join(values, ", "))
}

func sortedKeys(m map[string]any) []string {
	keys := make([]string, 0, len(m))
	for key := range m {
		keys = append(keys, key)
	}
	for i := 0; i < len(keys); i++ {
		for j := i + 1; j < len(keys); j++ {
			if keys[j] < keys[i] {
				keys[i], keys[j] = keys[j], keys[i]
			}
		}
	}
	return keys
}

func joinQuoted(cols []string) string {
	out := make([]string, 0, len(cols))
	for _, col := range cols {
		out = append(out, quoteIdentifier(col))
	}
	return strings.Join(out, ", ")
}

func normalizeColumns(columns []string) []string {
	if len(columns) == 0 {
		return nil
	}
	out := make([]string, 0, len(columns))
	for _, col := range columns {
		col = strings.TrimSpace(col)
		if col == "" || col == "*" {
			continue
		}
		out = append(out, col)
	}
	return out
}

func finalOrderFallback() []string {
	return []string{
		`"updated_epoch" DESC`,
		`"updated_at" DESC`,
		`"occurred_epoch" DESC`,
		`"occurred_at" DESC`,
		`"created_at" DESC`,
	}
}

func firstNonEmpty(values ...string) string {
	for _, value := range values {
		if strings.TrimSpace(value) != "" {
			return strings.TrimSpace(value)
		}
	}
	return ""
}

func rowInt(row Row, key string) int {
	n, _ := strconv.Atoi(strings.TrimSpace(RowStr(row, key)))
	return n
}
