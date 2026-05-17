package flight

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"testing"
	"time"
)

func TestHandshakeProtoRoundTrip(t *testing.T) {
	req := HandshakeRequest{
		ProtocolVersion: 7,
		Payload:         []byte("token"),
	}
	raw, err := marshalHandshakeRequest(req)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}

	got, err := unmarshalHandshakeResponse(raw)
	if err != nil {
		t.Fatalf("unmarshal: %v", err)
	}
	if got.ProtocolVersion != req.ProtocolVersion {
		t.Fatalf("protocol=%d want %d", got.ProtocolVersion, req.ProtocolVersion)
	}
	if !bytes.Equal(got.Payload, req.Payload) {
		t.Fatalf("payload=%q want %q", got.Payload, req.Payload)
	}
}

func TestUnmarshalHandshakeResponseRejectsBadInput(t *testing.T) {
	if _, err := unmarshalHandshakeResponse([]byte{0x0a, 0x05, 0x01}); err == nil {
		t.Fatal("expected error")
	}
}

func TestFlightInfoDecode(t *testing.T) {
	desc, _ := marshalFlightDescriptor(FlightDescriptor{
		Type: DescriptorCmd,
		Cmd:  []byte("cmd"),
	})
	ticket, _ := marshalTicket(Ticket{Ticket: []byte("ticket-1")})
	loc := appendBytesField(nil, 1, []byte("grpc://host:50051"))

	raw := appendBytesField(nil, 1, []byte("schema"))
	raw = appendBytesField(raw, 2, desc)
	raw = appendBytesField(raw, 3, appendBytesField(appendBytesField(nil, 1, ticket), 2, loc))
	raw = appendVarintField(raw, 4, 12)
	raw = appendVarintField(raw, 5, 34)
	raw = appendVarintField(raw, 6, 1)
	raw = appendBytesField(raw, 7, []byte("meta"))

	info, err := unmarshalFlightInfo(raw)
	if err != nil {
		t.Fatalf("unmarshal flight info: %v", err)
	}
	if info.TotalRecords != 12 || info.TotalBytes != 34 || !info.Ordered {
		t.Fatalf("bad counters: %+v", info)
	}
	if len(info.Endpoint) != 1 || string(info.Endpoint[0].Ticket.Ticket) != "ticket-1" {
		t.Fatalf("bad endpoints: %+v", info.Endpoint)
	}
	if len(info.Endpoint[0].Location) != 1 || info.Endpoint[0].Location[0].URI != "grpc://host:50051" {
		t.Fatalf("bad locations: %+v", info.Endpoint[0].Location)
	}
}

func TestFlightDataDecode(t *testing.T) {
	desc, _ := marshalFlightDescriptor(FlightDescriptor{Type: DescriptorCmd, Cmd: []byte("cmd")})
	raw := appendBytesField(nil, 1, desc)
	raw = appendBytesField(raw, 2, []byte("header"))
	raw = appendBytesField(raw, 3, []byte("meta"))
	raw = appendBytesField(raw, 1000, []byte("body"))

	got, err := unmarshalFlightData(raw)
	if err != nil {
		t.Fatalf("unmarshal flight data: %v", err)
	}
	if got.FlightDescriptor == nil || got.FlightDescriptor.Type != DescriptorCmd {
		t.Fatalf("bad descriptor: %+v", got.FlightDescriptor)
	}
	if !bytes.Equal(got.DataBody, []byte("body")) {
		t.Fatalf("bad body: %q", got.DataBody)
	}
}

func TestPreparedStatementProto(t *testing.T) {
	raw, err := marshalCommandPreparedStatementQuery([]byte("handle-1"))
	if err != nil {
		t.Fatalf("marshal prepared statement query: %v", err)
	}
	if !bytes.Contains(raw, []byte("handle-1")) {
		t.Fatalf("prepared statement raw=%q", raw)
	}

	action, err := marshalAction(Action{Type: createPreparedStatementActionType, Body: []byte("q")})
	if err != nil {
		t.Fatalf("marshal action: %v", err)
	}
	if !bytes.Contains(action, []byte(createPreparedStatementActionType)) {
		t.Fatalf("action raw=%q", action)
	}

	resultRaw := appendBytesField(nil, 1, []byte("handle"))
	resultRaw = appendBytesField(resultRaw, 2, []byte("dataset"))
	resultRaw = appendBytesField(resultRaw, 3, []byte("params"))
	result, err := unmarshalCreatePreparedStatementResult(resultRaw)
	if err != nil {
		t.Fatalf("unmarshal prepared statement result: %v", err)
	}
	if string(result.PreparedStatementHandle) != "handle" {
		t.Fatalf("handle=%q", result.PreparedStatementHandle)
	}
	if string(result.DatasetSchema) != "dataset" || string(result.ParameterSchema) != "params" {
		t.Fatalf("bad prepared statement result: %#v", result)
	}
}

func TestDoPutProto(t *testing.T) {
	raw, err := marshalFlightData(FlightData{
		FlightDescriptor: &FlightDescriptor{Type: DescriptorCmd, Cmd: []byte("cmd")},
		DataHeader:       []byte("header"),
		AppMetadata:      []byte("meta"),
		DataBody:         []byte("body"),
	})
	if err != nil {
		t.Fatalf("marshal flight data: %v", err)
	}
	got, err := unmarshalFlightData(raw)
	if err != nil {
		t.Fatalf("unmarshal flight data: %v", err)
	}
	if got.FlightDescriptor == nil || got.FlightDescriptor.Type != DescriptorCmd {
		t.Fatalf("bad descriptor: %#v", got.FlightDescriptor)
	}
	if !bytes.Equal(got.DataBody, []byte("body")) {
		t.Fatalf("bad body: %q", got.DataBody)
	}

	putRaw := appendBytesField(nil, 1, []byte("ack"))
	put, err := unmarshalPutResult(putRaw)
	if err != nil {
		t.Fatalf("unmarshal put result: %v", err)
	}
	if string(put.AppMetadata) != "ack" {
		t.Fatalf("put metadata=%q", put.AppMetadata)
	}
}

func TestRecordBatchRows(t *testing.T) {
	batch := &RecordBatch{
		Schema: Schema{Fields: []Field{
			{Name: "name", Type: ColumnTypeString},
			{Name: "score", Type: ColumnTypeFloat64},
			{Name: "ok", Type: ColumnTypeBool},
		}},
		Columns: []Column{
			{Name: "name", Values: []string{"a", "b"}},
			{Name: "score", Values: []float64{1.5, 2.5}},
			{Name: "ok", Values: []bool{true, false}},
		},
		NumRows: 2,
	}

	rows := batch.Rows()
	if len(rows) != 2 {
		t.Fatalf("rows=%d want 2", len(rows))
	}
	if rows[0]["name"] != "a" || rows[1]["score"] != 2.5 || rows[1]["ok"] != false {
		t.Fatalf("unexpected rows: %#v", rows)
	}
}

func TestRecordBatchRowsPreserveNulls(t *testing.T) {
	batch := &RecordBatch{
		Schema: Schema{Fields: []Field{
			{Name: "name", Type: ColumnTypeString, Nullable: true},
			{Name: "score", Type: ColumnTypeFloat64, Nullable: true},
			{Name: "ok", Type: ColumnTypeBool, Nullable: true},
		}},
		Columns: []Column{
			{Name: "name", Values: []string{"a", ""}, Nulls: []bool{false, true}},
			{Name: "score", Values: []float64{0, 2.5}, Nulls: []bool{true, false}},
			{Name: "ok", Values: []bool{true, false}, Nulls: []bool{false, true}},
		},
		NumRows: 2,
	}

	rows := batch.Rows()
	if rows[0]["score"] != nil {
		t.Fatalf("row 0 score=%#v want nil", rows[0]["score"])
	}
	if rows[1]["name"] != nil {
		t.Fatalf("row 1 name=%#v want nil", rows[1]["name"])
	}
	if rows[1]["ok"] != nil {
		t.Fatalf("row 1 ok=%#v want nil", rows[1]["ok"])
	}

	raw, err := json.Marshal(rows)
	if err != nil {
		t.Fatalf("marshal rows: %v", err)
	}
	if !bytes.Contains(raw, []byte(`"score":null`)) {
		t.Fatalf("json rows=%s want null score", raw)
	}
}

func TestRecordBatchRowsTemporalAndUnsigned(t *testing.T) {
	when := time.Date(2026, 3, 12, 10, 11, 12, 0, time.UTC)
	batch := &RecordBatch{
		Schema: Schema{Fields: []Field{
			{Name: "created_at", Type: ColumnTypeTimestamp},
			{Name: "day", Type: ColumnTypeDate32},
			{Name: "count_u32", Type: ColumnTypeUint32},
			{Name: "count_u64", Type: ColumnTypeUint64},
			{Name: "delta_i32", Type: ColumnTypeInt32},
		}},
		Columns: []Column{
			{Name: "created_at", Values: []time.Time{when}},
			{Name: "day", Values: []time.Time{when}},
			{Name: "count_u32", Values: []uint32{7}},
			{Name: "count_u64", Values: []uint64{9}},
			{Name: "delta_i32", Values: []int32{-3}},
		},
		NumRows: 1,
	}

	rows := batch.Rows()
	if got := rows[0]["count_u32"]; got != uint32(7) {
		t.Fatalf("count_u32=%#v want 7", got)
	}
	if got := rows[0]["count_u64"]; got != uint64(9) {
		t.Fatalf("count_u64=%#v want 9", got)
	}
	if got := rows[0]["delta_i32"]; got != int32(-3) {
		t.Fatalf("delta_i32=%#v want -3", got)
	}
	raw, err := json.Marshal(rows)
	if err != nil {
		t.Fatalf("marshal rows: %v", err)
	}
	if !bytes.Contains(raw, []byte(`"created_at":"2026-03-12T10:11:12Z"`)) {
		t.Fatalf("json rows=%s want RFC3339 timestamp", raw)
	}
}

func TestDecodeColumnTemporalAndUnsigned(t *testing.T) {
	validity := []byte{0x01}

	dateBuf := make([]byte, 4)
	binary.LittleEndian.PutUint32(dateBuf, uint32(2))
	col, used, err := decodeColumn(
		Field{Name: "day", Type: ColumnTypeDate32},
		fieldNode{length: 1},
		[]bufferRange{{offset: 0, length: int64(len(validity))}, {offset: int64(len(validity)), length: int64(len(dateBuf))}},
		append(append([]byte{}, validity...), dateBuf...),
		nil,
	)
	if err != nil || used != 2 {
		t.Fatalf("decode date32 err=%v used=%d", err, used)
	}
	dates := col.Values.([]time.Time)
	if got := dates[0].Format(time.RFC3339); got != "1970-01-03T00:00:00Z" {
		t.Fatalf("date32=%s want 1970-01-03T00:00:00Z", got)
	}

	tsBuf := make([]byte, 8)
	binary.LittleEndian.PutUint64(tsBuf, uint64(1500))
	col, used, err = decodeColumn(
		Field{Name: "ts", Type: ColumnTypeTimestamp, TimeUnit: ipcTimeUnitMillisecond},
		fieldNode{length: 1},
		[]bufferRange{{offset: 0, length: int64(len(validity))}, {offset: int64(len(validity)), length: int64(len(tsBuf))}},
		append(append([]byte{}, validity...), tsBuf...),
		nil,
	)
	if err != nil || used != 2 {
		t.Fatalf("decode timestamp err=%v used=%d", err, used)
	}
	times := col.Values.([]time.Time)
	if got := times[0].Format(time.RFC3339Nano); got != "1970-01-01T00:00:01.5Z" {
		t.Fatalf("timestamp=%s want 1970-01-01T00:00:01.5Z", got)
	}

	u32Buf := make([]byte, 4)
	binary.LittleEndian.PutUint32(u32Buf, 42)
	col, used, err = decodeColumn(
		Field{Name: "u32", Type: ColumnTypeUint32},
		fieldNode{length: 1},
		[]bufferRange{{offset: 0, length: int64(len(validity))}, {offset: int64(len(validity)), length: int64(len(u32Buf))}},
		append(append([]byte{}, validity...), u32Buf...),
		nil,
	)
	if err != nil || used != 2 {
		t.Fatalf("decode uint32 err=%v used=%d", err, used)
	}
	if got := col.Values.([]uint32)[0]; got != 42 {
		t.Fatalf("uint32=%d want 42", got)
	}
}

func TestDecodeColumnDecimal(t *testing.T) {
	validity := []byte{0x03}
	pos := decimal128FromInt64(12345)
	neg := decimal128FromInt64(-12345)
	body := append(append(append([]byte{}, validity...), pos...), neg...)

	col, used, err := decodeColumn(
		Field{Name: "price", Type: ColumnTypeDecimal, Scale: 2, BitWidth: 128},
		fieldNode{length: 2},
		[]bufferRange{
			{offset: 0, length: int64(len(validity))},
			{offset: int64(len(validity)), length: int64(len(pos) + len(neg))},
		},
		body,
		nil,
	)
	if err != nil || used != 2 {
		t.Fatalf("decode decimal err=%v used=%d", err, used)
	}
	values := col.Values.([]string)
	if values[0] != "123.45" {
		t.Fatalf("decimal[0]=%q want 123.45", values[0])
	}
	if values[1] != "-123.45" {
		t.Fatalf("decimal[1]=%q want -123.45", values[1])
	}
}

func TestRecordBatchRowsDecimal(t *testing.T) {
	batch := &RecordBatch{
		Schema:  Schema{Fields: []Field{{Name: "amount", Type: ColumnTypeDecimal}}},
		Columns: []Column{{Name: "amount", Values: []string{"12.34", "-0.50"}}},
		NumRows: 2,
	}
	rows := batch.Rows()
	if rows[0]["amount"] != "12.34" || rows[1]["amount"] != "-0.50" {
		t.Fatalf("unexpected rows: %#v", rows)
	}
}

func TestDecodeDictionaryColumn(t *testing.T) {
	dict := Column{Name: "label", Values: []string{"red", "green", "blue"}}
	indices := make([]byte, 8)
	binary.LittleEndian.PutUint32(indices[0:4], 2)
	binary.LittleEndian.PutUint32(indices[4:8], 1)
	col, used, err := decodeColumn(
		Field{
			Name: "label",
			Type: ColumnTypeString,
			Dict: &DictionaryEncoding{ID: 7, IndexBitWidth: 32, ValueField: Field{Name: "label", Type: ColumnTypeString}},
		},
		fieldNode{length: 2},
		[]bufferRange{
			{offset: 0, length: 0},
			{offset: 0, length: int64(len(indices))},
		},
		indices,
		map[int64]Column{7: dict},
	)
	if err != nil || used != 2 {
		t.Fatalf("decode dictionary err=%v used=%d", err, used)
	}
	values := col.Values.([]any)
	if values[0] != "blue" || values[1] != "green" {
		t.Fatalf("dictionary values=%#v", values)
	}
}

func TestDecodeListColumn(t *testing.T) {
	validity := []byte{0x03}
	offsets := make([]byte, 12)
	binary.LittleEndian.PutUint32(offsets[0:4], 0)
	binary.LittleEndian.PutUint32(offsets[4:8], 2)
	binary.LittleEndian.PutUint32(offsets[8:12], 3)
	childValidity := []byte{}
	childValues := make([]byte, 12)
	binary.LittleEndian.PutUint32(childValues[0:4], 10)
	binary.LittleEndian.PutUint32(childValues[4:8], 20)
	binary.LittleEndian.PutUint32(childValues[8:12], 30)
	body := append(append(append(append([]byte{}, validity...), offsets...), childValidity...), childValues...)

	col, usedNodes, usedBuffers, err := decodeFieldColumn(
		Field{
			Name:     "nums",
			Type:     ColumnTypeList,
			Children: []Field{{Name: "item", Type: ColumnTypeInt32}},
			BitWidth: 32,
		},
		[]fieldNode{{length: 2}, {length: 3}},
		[]bufferRange{
			{offset: 0, length: int64(len(validity))},
			{offset: int64(len(validity)), length: int64(len(offsets))},
			{offset: int64(len(validity) + len(offsets)), length: int64(len(childValidity))},
			{offset: int64(len(validity) + len(offsets) + len(childValidity)), length: int64(len(childValues))},
		},
		body,
		nil,
	)
	if err != nil {
		t.Fatalf("decode list: %v", err)
	}
	if usedNodes != 2 || usedBuffers != 4 {
		t.Fatalf("used nodes=%d buffers=%d", usedNodes, usedBuffers)
	}
	rows := col.Values.([][]any)
	if len(rows) != 2 {
		t.Fatalf("rows=%d want 2", len(rows))
	}
	if rows[0][0] != int32(10) || rows[0][1] != int32(20) || rows[1][0] != int32(30) {
		t.Fatalf("unexpected list rows: %#v", rows)
	}
}

func TestDecodeStructColumn(t *testing.T) {
	validity := []byte{0x03}
	childAValidity := []byte{}
	childA := make([]byte, 8)
	binary.LittleEndian.PutUint32(childA[0:4], 1)
	binary.LittleEndian.PutUint32(childA[4:8], 2)
	childBValidity := []byte{}
	childB := []byte{0x01}
	body := append(append(append(append(append([]byte{}, validity...), childAValidity...), childA...), childBValidity...), childB...)

	col, usedNodes, usedBuffers, err := decodeFieldColumn(
		Field{
			Name: "pair",
			Type: ColumnTypeStruct,
			Children: []Field{
				{Name: "id", Type: ColumnTypeInt32},
				{Name: "ok", Type: ColumnTypeBool},
			},
		},
		[]fieldNode{{length: 2}, {length: 2}, {length: 2}},
		[]bufferRange{
			{offset: 0, length: int64(len(validity))},
			{offset: int64(len(validity)), length: int64(len(childAValidity))},
			{offset: int64(len(validity) + len(childAValidity)), length: int64(len(childA))},
			{offset: int64(len(validity) + len(childAValidity) + len(childA)), length: int64(len(childBValidity))},
			{offset: int64(len(validity) + len(childAValidity) + len(childA) + len(childBValidity)), length: int64(len(childB))},
		},
		body,
		nil,
	)
	if err != nil {
		t.Fatalf("decode struct: %v", err)
	}
	if usedNodes != 3 || usedBuffers != 5 {
		t.Fatalf("used nodes=%d buffers=%d", usedNodes, usedBuffers)
	}
	rows := col.Values.([]map[string]any)
	if rows[0]["id"] != int32(1) || rows[1]["id"] != int32(2) {
		t.Fatalf("unexpected struct rows: %#v", rows)
	}
	if rows[0]["ok"] != true || rows[1]["ok"] != false {
		t.Fatalf("unexpected struct bool rows: %#v", rows)
	}
}

func TestDecodeMapColumn(t *testing.T) {
	validity := []byte{0x01}
	offsets := make([]byte, 8)
	binary.LittleEndian.PutUint32(offsets[0:4], 0)
	binary.LittleEndian.PutUint32(offsets[4:8], 2)

	entryValidity := []byte{}
	keyValidity := []byte{}
	keyOffsets := make([]byte, 12)
	binary.LittleEndian.PutUint32(keyOffsets[0:4], 0)
	binary.LittleEndian.PutUint32(keyOffsets[4:8], 1)
	binary.LittleEndian.PutUint32(keyOffsets[8:12], 2)
	keyData := []byte("ab")

	valValidity := []byte{}
	valData := make([]byte, 8)
	binary.LittleEndian.PutUint32(valData[0:4], 10)
	binary.LittleEndian.PutUint32(valData[4:8], 20)

	body := append([]byte{}, validity...)
	body = append(body, offsets...)
	body = append(body, entryValidity...)
	body = append(body, keyValidity...)
	body = append(body, keyOffsets...)
	body = append(body, keyData...)
	body = append(body, valValidity...)
	body = append(body, valData...)

	col, usedNodes, usedBuffers, err := decodeFieldColumn(
		Field{
			Name: "attrs",
			Type: ColumnTypeMap,
			Children: []Field{{
				Name: "entries",
				Type: ColumnTypeStruct,
				Children: []Field{
					{Name: "key", Type: ColumnTypeString},
					{Name: "value", Type: ColumnTypeInt32},
				},
			}},
			BitWidth: 32,
		},
		[]fieldNode{{length: 1}, {length: 2}, {length: 2}, {length: 2}},
		[]bufferRange{
			{offset: 0, length: int64(len(validity))},
			{offset: int64(len(validity)), length: int64(len(offsets))},
			{offset: int64(len(validity) + len(offsets)), length: int64(len(entryValidity))},
			{offset: int64(len(validity) + len(offsets) + len(entryValidity)), length: int64(len(keyValidity))},
			{offset: int64(len(validity) + len(offsets) + len(entryValidity) + len(keyValidity)), length: int64(len(keyOffsets))},
			{offset: int64(len(validity) + len(offsets) + len(entryValidity) + len(keyValidity) + len(keyOffsets)), length: int64(len(keyData))},
			{offset: int64(len(validity) + len(offsets) + len(entryValidity) + len(keyValidity) + len(keyOffsets) + len(keyData)), length: int64(len(valValidity))},
			{offset: int64(len(validity) + len(offsets) + len(entryValidity) + len(keyValidity) + len(keyOffsets) + len(keyData) + len(valValidity)), length: int64(len(valData))},
		},
		body,
		nil,
	)
	if err != nil {
		t.Fatalf("decode map: %v", err)
	}
	if usedNodes != 4 || usedBuffers != 8 {
		t.Fatalf("used nodes=%d buffers=%d", usedNodes, usedBuffers)
	}
	rows := col.Values.([]map[string]any)
	if rows[0]["a"] != int32(10) || rows[0]["b"] != int32(20) {
		t.Fatalf("unexpected map rows: %#v", rows)
	}
}

func TestDecodeSmallScalarColumns(t *testing.T) {
	validity := []byte{0x01}

	i8 := []byte{0xfe}
	col, used, err := decodeColumn(Field{Name: "i8", Type: ColumnTypeInt8}, fieldNode{length: 1}, []bufferRange{
		{offset: 0, length: int64(len(validity))},
		{offset: int64(len(validity)), length: int64(len(i8))},
	}, append(append([]byte{}, validity...), i8...), nil)
	if err != nil || used != 2 || col.Values.([]int8)[0] != -2 {
		t.Fatalf("decode int8 err=%v used=%d col=%#v", err, used, col.Values)
	}

	i16 := make([]byte, 2)
	binary.LittleEndian.PutUint16(i16, uint16(65535))
	col, used, err = decodeColumn(Field{Name: "i16", Type: ColumnTypeInt16}, fieldNode{length: 1}, []bufferRange{
		{offset: 0, length: int64(len(validity))},
		{offset: int64(len(validity)), length: int64(len(i16))},
	}, append(append([]byte{}, validity...), i16...), nil)
	if err != nil || used != 2 || col.Values.([]int16)[0] != -1 {
		t.Fatalf("decode int16 err=%v used=%d col=%#v", err, used, col.Values)
	}

	u8 := []byte{0xff}
	col, used, err = decodeColumn(Field{Name: "u8", Type: ColumnTypeUint8}, fieldNode{length: 1}, []bufferRange{
		{offset: 0, length: int64(len(validity))},
		{offset: int64(len(validity)), length: int64(len(u8))},
	}, append(append([]byte{}, validity...), u8...), nil)
	if err != nil || used != 2 || col.Values.([]uint8)[0] != 255 {
		t.Fatalf("decode uint8 err=%v used=%d col=%#v", err, used, col.Values)
	}

	u16 := make([]byte, 2)
	binary.LittleEndian.PutUint16(u16, 42)
	col, used, err = decodeColumn(Field{Name: "u16", Type: ColumnTypeUint16}, fieldNode{length: 1}, []bufferRange{
		{offset: 0, length: int64(len(validity))},
		{offset: int64(len(validity)), length: int64(len(u16))},
	}, append(append([]byte{}, validity...), u16...), nil)
	if err != nil || used != 2 || col.Values.([]uint16)[0] != 42 {
		t.Fatalf("decode uint16 err=%v used=%d col=%#v", err, used, col.Values)
	}
}

func TestDecodeTimeDurationAndFixedBinary(t *testing.T) {
	validity := []byte{0x01}

	f16 := make([]byte, 2)
	binary.LittleEndian.PutUint16(f16, 0x3c00)
	col, used, err := decodeColumn(Field{Name: "f16", Type: ColumnTypeFloat16}, fieldNode{length: 1}, []bufferRange{
		{offset: 0, length: int64(len(validity))},
		{offset: int64(len(validity)), length: int64(len(f16))},
	}, append(append([]byte{}, validity...), f16...), nil)
	if err != nil || used != 2 || col.Values.([]float32)[0] != 1 {
		t.Fatalf("decode float16 err=%v used=%d col=%#v", err, used, col.Values)
	}

	time32 := make([]byte, 4)
	binary.LittleEndian.PutUint32(time32, 1234)
	col, used, err = decodeColumn(Field{Name: "t32", Type: ColumnTypeTime, BitWidth: 32, TimeUnit: ipcTimeUnitMillisecond}, fieldNode{length: 1}, []bufferRange{
		{offset: 0, length: int64(len(validity))},
		{offset: int64(len(validity)), length: int64(len(time32))},
	}, append(append([]byte{}, validity...), time32...), nil)
	if err != nil || used != 2 || col.Values.([]time.Duration)[0] != 1234*time.Millisecond {
		t.Fatalf("decode time32 err=%v used=%d col=%#v", err, used, col.Values)
	}

	dur := make([]byte, 8)
	binary.LittleEndian.PutUint64(dur, 9)
	col, used, err = decodeColumn(Field{Name: "dur", Type: ColumnTypeDuration, TimeUnit: ipcTimeUnitSecond}, fieldNode{length: 1}, []bufferRange{
		{offset: 0, length: int64(len(validity))},
		{offset: int64(len(validity)), length: int64(len(dur))},
	}, append(append([]byte{}, validity...), dur...), nil)
	if err != nil || used != 2 || col.Values.([]time.Duration)[0] != 9*time.Second {
		t.Fatalf("decode duration err=%v used=%d col=%#v", err, used, col.Values)
	}

	fixed := []byte{0xaa, 0xbb, 0xcc, 0xdd}
	col, used, err = decodeColumn(Field{Name: "fx", Type: ColumnTypeFixedBinary, BitWidth: 2}, fieldNode{length: 2}, []bufferRange{
		{offset: 0, length: int64(len(validity))},
		{offset: int64(len(validity)), length: int64(len(fixed))},
	}, append(append([]byte{}, validity...), fixed...), nil)
	if err != nil || used != 2 {
		t.Fatalf("decode fixed binary err=%v used=%d", err, used)
	}
	got := col.Values.([][]byte)
	if !bytes.Equal(got[0], []byte{0xaa, 0xbb}) || !bytes.Equal(got[1], []byte{0xcc, 0xdd}) {
		t.Fatalf("decode fixed binary values=%#v", got)
	}
}

func decimal128FromInt64(v int64) []byte {
	out := make([]byte, 16)
	negative := v < 0
	var mag uint64
	if negative {
		mag = uint64(-(v + 1))
		mag++
	} else {
		mag = uint64(v)
	}
	binary.LittleEndian.PutUint64(out[:8], mag)
	if negative {
		for i := range out {
			out[i] = ^out[i]
		}
		carry := byte(1)
		for i := range out {
			sum := uint16(out[i]) + uint16(carry)
			out[i] = byte(sum)
			carry = byte(sum >> 8)
			if carry == 0 {
				break
			}
		}
	}
	return out
}
