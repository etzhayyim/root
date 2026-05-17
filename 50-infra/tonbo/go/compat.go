//go:build !tinygo

package lancedbrest

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/base32"
	"encoding/base64"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"math"
	"net/http"
	"net/url"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/apache/arrow/go/v17/arrow"
	"github.com/apache/arrow/go/v17/arrow/array"
	"github.com/apache/arrow/go/v17/arrow/ipc"
	"github.com/apache/arrow/go/v17/arrow/memory"
)

var (
	ErrKeyNotFound = errors.New("key not found")
	identPattern   = regexp.MustCompile(`^[A-Za-z_][A-Za-z0-9_]*$`)
	base32lower    = base32.NewEncoding("abcdefghijklmnopqrstuvwxyz234567").WithPadding(base32.NoPadding)
)

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
	final   bool
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
	case []byte:
		return string(x)
	case fmt.Stringer:
		return x.String()
	case json.Number:
		return x.String()
	case float64:
		return strconv.FormatFloat(x, 'f', -1, 64)
	case float32:
		return strconv.FormatFloat(float64(x), 'f', -1, 32)
	case int:
		return strconv.Itoa(x)
	case int64:
		return strconv.FormatInt(x, 10)
	case int32:
		return strconv.FormatInt(int64(x), 10)
	case int16:
		return strconv.FormatInt(int64(x), 10)
	case int8:
		return strconv.FormatInt(int64(x), 10)
	case uint:
		return strconv.FormatUint(uint64(x), 10)
	case uint64:
		return strconv.FormatUint(x, 10)
	case uint32:
		return strconv.FormatUint(uint64(x), 10)
	case uint16:
		return strconv.FormatUint(uint64(x), 10)
	case uint8:
		return strconv.FormatUint(uint64(x), 10)
	case bool:
		return strconv.FormatBool(x)
	default:
		b, err := json.Marshal(x)
		if err != nil {
			return fmt.Sprint(x)
		}
		return string(b)
	}
}

func Itoa(v int) string {
	return strconv.Itoa(v)
}

func (c *Client) Table(name string) *TableHandle {
	return &TableHandle{client: c, name: strings.TrimSpace(name)}
}

func (c *Client) Query(table, filter string, limit int) (*QueryResult, error) {
	return c.QueryOrdered(table, filter, "", limit, 0)
}

func (c *Client) CountRows(table, filter string) (int, error) {
	return c.Count(table, filter)
}

func (c *Client) FilterQuery(table, filter string, limit, offset int) ([]map[string]any, error) {
	res, err := c.QueryOrdered(table, filter, "", limit, offset)
	if err != nil || res == nil {
		return nil, err
	}
	out := make([]map[string]any, 0, len(res.Rows))
	for _, row := range res.Rows {
		out = append(out, map[string]any(row))
	}
	return out, nil
}

func (c *Client) TableStats(table string) (int, int64, error) {
	count, err := c.Count(table, "")
	return count, 0, err
}

func (c *Client) FullTextSearchColumns(table string, columns []string, query string, limit int) ([]map[string]any, error) {
	return c.FullTextSearchColumnsWithFilter(table, columns, query, "", limit)
}

func (c *Client) FullTextSearchColumnsWithFilter(table string, columns []string, query, filter string, limit int) ([]map[string]any, error) {
	q := strings.ToLower(strings.TrimSpace(query))
	if q == "" {
		return nil, nil
	}
	terms := make([]string, 0, len(columns))
	for _, col := range columns {
		col = strings.TrimSpace(col)
		if col == "" {
			continue
		}
		terms = append(terms, fmt.Sprintf(`LOWER(COALESCE(%s, '')) LIKE %s`, quoteIdentifier(col), sqlLiteral("%"+q+"%")))
	}
	combined := strings.Join(terms, " OR ")
	if strings.TrimSpace(filter) != "" && combined != "" {
		combined = "(" + combined + ") AND (" + filter + ")"
	}
	return c.FilterQuery(table, combined, limit, 0)
}

func (c *Client) UpsertOne(table, docID string, row Row) error {
	return c.UpsertOneAny(table, docID, AnyRow(row))
}

func (c *Client) Upsert(table string, rows []Row) error {
	for _, row := range rows {
		docID := strings.TrimSpace(RowStr(row, "_doc_id"))
		if docID == "" {
			return fmt.Errorf("upsert row missing _doc_id for %s", table)
		}
		if err := c.UpsertOne(table, docID, row); err != nil {
			return err
		}
	}
	return nil
}

func (c *Client) EnsureTableSchema(schema TableSchema) error {
	return c.EnsureTable(schema.Table, schema)
}

func (c *Client) EnsureTable(table string, schema TableSchema) error {
	table = strings.TrimSpace(table)
	if table == "" {
		return fmt.Errorf("table name is required")
	}
	exists, err := c.TableExists(table)
	if err != nil {
		return err
	}
	if exists {
		return nil
	}
	fields := make([]map[string]any, 0, len(schema.Fields)+1)
	seen := map[string]bool{}
	if pk := strings.TrimSpace(schema.PrimaryKey); pk != "" {
		found := false
		for _, f := range schema.Fields {
			if strings.TrimSpace(f.Name) == pk {
				found = true
				break
			}
		}
		if !found {
			fields = append(fields, map[string]any{"name": pk, "type": "string", "nullable": false})
			seen[pk] = true
		}
	}
	for _, field := range schema.Fields {
		name := strings.TrimSpace(field.Name)
		if name == "" || seen[name] {
			continue
		}
		seen[name] = true
		fields = append(fields, map[string]any{
			"name":     name,
			"type":     fieldTypeToArrow(field.Type),
			"nullable": name != strings.TrimSpace(schema.PrimaryKey),
		})
	}
	if len(fields) == 0 {
		return fmt.Errorf("table %s has no columns", table)
	}
	seedID := "__tonbo_seed__"
	seed := AnyRow{}
	for _, field := range fields {
		name := strings.TrimSpace(stringify(field["name"]))
		if name == "" {
			continue
		}
		fieldType := strings.ToLower(strings.TrimSpace(stringify(field["type"])))
		switch fieldType {
		case "int64", "int32", "int16", "int8", "int", "integer", "long":
			seed[name] = int64(0)
		case "float64", "float32", "float", "double":
			seed[name] = float64(0)
		case "bool", "boolean":
			seed[name] = false
		default:
			seed[name] = ""
		}
	}
	seed["_doc_id"] = seedID
	if err := c.UpsertOneAny(table, seedID, seed); err != nil {
		return err
	}
	_ = c.DeleteOne(table, seedID)
	return nil
}

func (c *Client) CreateTable(table string, fields []map[string]any) error {
	body := map[string]any{"fields": fields}
	_, err := c.doJSON(context.Background(), http.MethodPost, "/v1/table/"+url.PathEscape(table)+"/create/", body)
	if err != nil && strings.Contains(err.Error(), "already exists") {
		return nil
	}
	return err
}

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

func (c *Client) DropTable(table string) error {
	_, err := c.doJSON(context.Background(), http.MethodPost, "/v1/table/"+url.PathEscape(table)+"/drop/", nil)
	return err
}


func (c *Client) DescribeTable(table string) (map[string]any, error) {
	return c.doJSON(context.Background(), http.MethodPost, "/v1/table/"+url.PathEscape(table)+"/describe/", map[string]any{})
}

func fieldTypeToArrow(ft FieldType) string {
	switch ft {
	case FieldInt64:
		return "int64"
	case FieldFloat64:
		return "float64"
	case FieldBoolean:
		return "boolean"
	default:
		return "string"
	}
}

func buildArrowSchema(schema TableSchema) *arrow.Schema {
	fields := make([]arrow.Field, 0, len(schema.Fields))
	seen := map[string]struct{}{}
	for _, field := range schema.Fields {
		name := strings.TrimSpace(field.Name)
		if name == "" {
			continue
		}
		if _, ok := seen[name]; ok {
			continue
		}
		seen[name] = struct{}{}
		fields = append(fields, arrow.Field{Name: name, Type: arrowType(field.Type), Nullable: true})
	}
	if pk := strings.TrimSpace(schema.PrimaryKey); pk != "" {
		if _, ok := seen[pk]; !ok {
			fields = append([]arrow.Field{{Name: pk, Type: arrow.BinaryTypes.String, Nullable: true}}, fields...)
		}
	}
	return arrow.NewSchema(fields, nil)
}

func arrowType(fieldType FieldType) arrow.DataType {
	switch fieldType {
	case FieldInt64:
		return arrow.PrimitiveTypes.Int64
	case FieldFloat64:
		return arrow.PrimitiveTypes.Float64
	case FieldBoolean:
		return arrow.FixedWidthTypes.Boolean
	default:
		return arrow.BinaryTypes.String
	}
}

func encodeArrowCreatePayload(schema *arrow.Schema) ([]byte, error) {
	pool := memory.NewGoAllocator()
	builder := array.NewRecordBuilder(pool, schema)
	defer builder.Release()

	record := builder.NewRecord()
	defer record.Release()

	var buf bytes.Buffer
	writer := ipc.NewWriter(&buf, ipc.WithSchema(schema))
	if err := writer.Write(record); err != nil {
		_ = writer.Close()
		return nil, err
	}
	if err := writer.Close(); err != nil {
		return nil, err
	}
	return buf.Bytes(), nil
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

func (c *Client) Delete(table, docID string, _ Row) error {
	return c.DeleteOne(table, docID)
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
	if len(parts) == 2 && identPattern.MatchString(strings.TrimSpace(parts[0])) {
		dir := strings.ToUpper(strings.TrimSpace(parts[1]))
		if dir == "ASC" || dir == "DESC" {
			q.orderBy = append(q.orderBy, quoteIdentifier(parts[0])+" "+dir)
			return q
		}
	}
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
	return strconv.Atoi(strings.TrimSpace(firstNonEmpty(RowStr(rows[0], "row_count"), RowStr(rows[0], "count"), "0")))
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

func (c *Client) BlobPut(table, blobKey, contentType, dataB64 string, size int, visibility string) (string, error) {
	cid := blobCIDV1([]byte(dataB64))
	row := AnyRow{
		"_doc_id":      blobKey,
		"blob_key":     blobKey,
		"content_type": contentType,
		"data_b64":     dataB64,
		"size":         strconv.Itoa(size),
		"cid":          cid,
		"s3_key":       "blobs/" + table + "/" + cid,
		"visibility":   visibility,
		"s3_pending":   "1",
	}
	return cid, c.UpsertOneAny(table, blobKey, row)
}

func (c *Client) BlobPutRaw(table, blobKey, contentType string, data []byte, visibility string) (string, error) {
	return c.BlobPut(table, blobKey, contentType, base64.StdEncoding.EncodeToString(data), len(data), visibility)
}

func (c *Client) BlobSetVisibility(table, blobKey, visibility string) error {
	row, err := c.Table(table).Select("*").Final().WhereEq("blob_key", blobKey).Row()
	if err != nil {
		return err
	}
	row["visibility"] = visibility
	return c.UpsertOne(table, blobKey, row)
}

func (c *Client) BlobGet(table, blobKey string) (contentType string, dataB64 string, size int, ok bool) {
	row, err := c.Table(table).Select("*").Final().WhereEq("blob_key", blobKey).Row()
	if err != nil {
		return "", "", 0, false
	}
	return RowStr(row, "content_type"), RowStr(row, "data_b64"), rowInt(row, "size"), true
}

func (c *Client) BlobGetMeta(table, blobKey string) (contentType string, cid string, size int, ok bool) {
	row, err := c.Table(table).Select("*").Final().WhereEq("blob_key", blobKey).Row()
	if err != nil {
		return "", "", 0, false
	}
	return RowStr(row, "content_type"), RowStr(row, "cid"), rowInt(row, "size"), true
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

func renderSelectExpr(expr string) string {
	expr = strings.TrimSpace(expr)
	if expr == "" || expr == "*" {
		return "*"
	}
	if identPattern.MatchString(expr) {
		return quoteIdentifier(expr)
	}
	return expr
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

func quoteIdentifier(name string) string {
	return `"` + strings.ReplaceAll(strings.TrimSpace(name), `"`, `""`) + `"`
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
		if math.IsNaN(float64(x)) || math.IsInf(float64(x), 0) {
			return "0"
		}
		return strconv.FormatFloat(float64(x), 'f', -1, 32)
	case float64:
		if math.IsNaN(x) || math.IsInf(x, 0) {
			return "0"
		}
		return strconv.FormatFloat(x, 'f', -1, 64)
	case time.Time:
		if x.IsZero() {
			return "NULL"
		}
		return "'" + x.UTC().Format(time.RFC3339Nano) + "'"
	default:
		b, err := json.Marshal(x)
		if err != nil {
			return "'" + strings.ReplaceAll(fmt.Sprint(x), "'", "''") + "'"
		}
		return "'" + strings.ReplaceAll(string(b), "'", "''") + "'"
	}
}

func sqlType(ft FieldType) string {
	switch ft {
	case FieldInt64:
		return "BIGINT"
	case FieldFloat64:
		return "DOUBLE"
	case FieldBoolean:
		return "BOOLEAN"
	case FieldTimestamp:
		return "TEXT"
	default:
		return "TEXT"
	}
}

func rowInt(row Row, key string) int {
	n, _ := strconv.Atoi(strings.TrimSpace(RowStr(row, key)))
	return n
}

func blobCIDV1(data []byte) string {
	digest := sha256.Sum256(data)
	var buf [64]byte
	n := 0
	n += binary.PutUvarint(buf[n:], 0x01)
	n += binary.PutUvarint(buf[n:], 0x55)
	n += binary.PutUvarint(buf[n:], 0x12)
	n += binary.PutUvarint(buf[n:], 32)
	copy(buf[n:], digest[:])
	n += 32
	return "b" + base32lower.EncodeToString(buf[:n])
}

func firstNonEmpty(values ...string) string {
	for _, value := range values {
		if strings.TrimSpace(value) != "" {
			return strings.TrimSpace(value)
		}
	}
	return ""
}
