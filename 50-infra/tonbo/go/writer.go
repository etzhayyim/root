package lancedbrest

// WriteBuffer accumulates rows for a single table and flushes as merge_insert batches.
// Not goroutine-safe — designed for sequential SpinApp handler use (TinyGo compatible).
//
// Usage pattern:
//
//	buf := lancedbrest.NewWriteBuffer(graph.NodeTableName, 500)
//	for _, node := range nodes {
//	    row := graph.NodeToRow(node, orgID, userID, actorID)
//	    buf.Add(row["_doc_id"].(string), row)
//	    if err := buf.MaybeFlush(client); err != nil {
//	        return err
//	    }
//	}
//	return buf.Flush(client) // drain remainder
type WriteBuffer struct {
	table    string
	maxBatch int
	pending  []AnyRow
}

// DefaultBatchSize is the default flush threshold (500 rows per merge_insert request).
const DefaultBatchSize = 500

// NewWriteBuffer creates a buffer for the named table.
// maxBatch controls when MaybeFlush auto-flushes; <= 0 uses DefaultBatchSize.
func NewWriteBuffer(table string, maxBatch int) *WriteBuffer {
	if maxBatch <= 0 {
		maxBatch = DefaultBatchSize
	}
	return &WriteBuffer{table: table, maxBatch: maxBatch}
}

// Add buffers a single row. docID is written as _doc_id in the flushed payload.
func (b *WriteBuffer) Add(docID string, row AnyRow) {
	doc := make(AnyRow, len(row)+1)
	for k, v := range row {
		doc[k] = v
	}
	doc["_doc_id"] = docID
	b.pending = append(b.pending, doc)
}

// Len returns the number of buffered (unflushed) rows.
func (b *WriteBuffer) Len() int { return len(b.pending) }

// MaybeFlush flushes when the buffer has reached maxBatch.
// Call after every Add in a tight loop.
func (b *WriteBuffer) MaybeFlush(c *Client) error {
	if len(b.pending) >= b.maxBatch {
		return b.Flush(c)
	}
	return nil
}

// Flush sends all buffered rows as a single AppendBatch and clears the buffer.
// Returns nil immediately when the buffer is empty.
func (b *WriteBuffer) Flush(c *Client) error {
	if len(b.pending) == 0 {
		return nil
	}
	if err := c.AppendBatch(b.table, b.pending); err != nil {
		return err
	}
	b.pending = b.pending[:0]
	return nil
}
