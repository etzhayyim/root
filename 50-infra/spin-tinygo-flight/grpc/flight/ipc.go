package flight

import (
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"math"
	"strings"
	"time"

	flatbuffers "github.com/google/flatbuffers/go"
)

type ColumnType int

const (
	ColumnTypeString ColumnType = iota
	ColumnTypeList
	ColumnTypeMap
	ColumnTypeStruct
	ColumnTypeInt8
	ColumnTypeInt16
	ColumnTypeInt32
	ColumnTypeInt64
	ColumnTypeUint8
	ColumnTypeUint16
	ColumnTypeUint32
	ColumnTypeUint64
	ColumnTypeFloat64
	ColumnTypeFloat32
	ColumnTypeFloat16
	ColumnTypeBool
	ColumnTypeBinary
	ColumnTypeFixedBinary
	ColumnTypeDate32
	ColumnTypeDate64
	ColumnTypeTime
	ColumnTypeTimestamp
	ColumnTypeDuration
	ColumnTypeDecimal
)

type Field struct {
	Name      string
	Type      ColumnType
	Nullable  bool
	Metadata  map[string]string
	TimeUnit  int16
	TimeZone  string
	Precision int32
	Scale     int32
	BitWidth  int32
	Dict      *DictionaryEncoding
	Children  []Field
}

type Schema struct {
	Fields   []Field
	Metadata map[string]string
}

type DictionaryEncoding struct {
	ID            int64
	IndexBitWidth int32
	IndexSigned   bool
	IsOrdered     bool
	ValueField    Field
}

type Column struct {
	Name   string
	Values any
	Nulls  []bool
}

type RecordBatch struct {
	Schema  Schema
	Columns []Column
	NumRows int
}

// Rows materializes the record batch into row-oriented maps.
func (b *RecordBatch) Rows() []map[string]any {
	if b == nil || b.NumRows == 0 {
		return nil
	}
	rows := make([]map[string]any, b.NumRows)
	for i := 0; i < b.NumRows; i++ {
		row := make(map[string]any, len(b.Columns))
		for _, col := range b.Columns {
			row[col.Name] = columnValueAt(col, i)
		}
		rows[i] = row
	}
	return rows
}

func (s *DataStream) NextRecordBatch() (*RecordBatch, error) {
	if s.dicts == nil {
		s.dicts = make(map[int64]Column)
	}
	for {
		msg, err := s.Next()
		if err != nil {
			return nil, err
		}
		headerType, header, err := parseIPCMessage(msg.DataHeader)
		if err != nil {
			return nil, err
		}
		switch headerType {
		case ipcHeaderSchema:
			s.schema, err = decodeSchema(header)
			if err != nil {
				return nil, err
			}
		case ipcHeaderDictionaryBatch:
			if s.schema == nil {
				return nil, errors.New("arrow ipc schema not received before dictionary batch")
			}
			if err := s.applyDictionaryBatch(header, msg.DataBody); err != nil {
				return nil, err
			}
		case ipcHeaderRecordBatch:
			if s.schema == nil {
				return nil, errors.New("arrow ipc schema not received before record batch")
			}
			return decodeRecordBatch(*s.schema, header, msg.DataBody, s.dicts)
		default:
			// Ignore unsupported message types for now.
		}
	}
}

const (
	ipcHeaderSchema          = 1
	ipcHeaderDictionaryBatch = 2
	ipcHeaderRecordBatch     = 3
)

const (
	ipcTypeInt         = 2
	ipcTypeFloat       = 3
	ipcTypeBinary      = 4
	ipcTypeUtf8        = 5
	ipcTypeBool        = 6
	ipcTypeDecimal     = 7
	ipcTypeDate        = 8
	ipcTypeTime        = 9
	ipcTypeTimestamp   = 10
	ipcTypeList        = 12
	ipcTypeStruct      = 13
	ipcTypeFixedBinary = 15
	ipcTypeLargeBinary = 19
	ipcTypeLargeUtf8   = 20
	ipcTypeMap         = 30
	ipcTypeDuration    = 33
	ipcTypeLargeList   = 36
)

const (
	ipcPrecisionHalf   = 0
	ipcPrecisionSingle = 1
	ipcPrecisionDouble = 2
)

const (
	ipcDateUnitDay         = 0
	ipcDateUnitMillisecond = 1
)

const (
	ipcTimeUnitSecond      = 0
	ipcTimeUnitMillisecond = 1
	ipcTimeUnitMicrosecond = 2
	ipcTimeUnitNanosecond  = 3
)

type ipcTable struct {
	buf []byte
	tab flatbuffers.Table
}

func rootTable(buf []byte) ipcTable {
	pos := flatbuffers.GetUOffsetT(buf)
	return ipcTable{
		buf: buf,
		tab: flatbuffers.Table{Bytes: buf, Pos: pos},
	}
}

func parseIPCMessage(buf []byte) (byte, []byte, error) {
	msg := rootTable(buf)
	headerType := msg.tab.GetByteSlot(6, 0)
	off := msg.tab.Offset(8)
	if off == 0 {
		return 0, nil, errors.New("arrow ipc message missing header")
	}
	unionPos := msg.tab.Pos + flatbuffers.UOffsetT(off)
	unionPos += msg.tab.GetUOffsetT(unionPos)
	return headerType, msg.buf[unionPos:], nil
}

func decodeSchema(buf []byte) (*Schema, error) {
	sch := rootTable(buf)
	fieldVec := sch.tab.Offset(6)
	out := &Schema{Metadata: decodeMetadataVector(sch.buf, sch.tab, 8)}
	if fieldVec != 0 {
		n := sch.tab.VectorLen(flatbuffers.UOffsetT(fieldVec))
		fields := make([]Field, 0, n)
		for i := 0; i < n; i++ {
			elem := sch.tab.Vector(flatbuffers.UOffsetT(fieldVec)) + flatbuffers.UOffsetT(i*4)
			fieldPos := sch.tab.Indirect(elem)
			field, err := decodeField(sch.buf, fieldPos)
			if err != nil {
				return nil, err
			}
			if field.Type == -1 {
				return nil, fmt.Errorf("unsupported arrow field type for %q", field.Name)
			}
			if field.Nullable {
				// keep as-is
			}
			fields = append(fields, field)
		}
		out.Fields = fields
	}
	return out, nil
}

func decodeField(buf []byte, pos flatbuffers.UOffsetT) (Field, error) {
	tab := flatbuffers.Table{Bytes: buf, Pos: pos}
	name := ""
	if nameOff := tab.Offset(4); nameOff != 0 {
		name = string(tab.ByteVector(pos + flatbuffers.UOffsetT(nameOff)))
	}
	field := Field{
		Name:     name,
		Nullable: tab.GetBoolSlot(6, false),
		Type:     ColumnType(-1),
		Metadata: decodeMetadataVector(buf, tab, 16),
	}
	typeType := tab.GetByteSlot(8, 0)
	typeOff := tab.Offset(10)
	if typeOff == 0 {
		return field, errors.New("arrow field missing type union")
	}
	unionPos := pos + flatbuffers.UOffsetT(typeOff)
	unionPos += tab.GetUOffsetT(unionPos)
	union := flatbuffers.Table{Bytes: buf, Pos: unionPos}
	switch typeType {
	case ipcTypeUtf8, ipcTypeLargeUtf8:
		field.Type = ColumnTypeString
	case ipcTypeList, ipcTypeLargeList:
		field.Type = ColumnTypeList
		if typeType == ipcTypeLargeList {
			field.BitWidth = 64
		} else {
			field.BitWidth = 32
		}
	case ipcTypeMap:
		field.Type = ColumnTypeMap
		field.BitWidth = 32
	case ipcTypeStruct:
		field.Type = ColumnTypeStruct
	case ipcTypeBinary, ipcTypeLargeBinary:
		field.Type = ColumnTypeBinary
	case ipcTypeFixedBinary:
		field.Type = ColumnTypeFixedBinary
		field.BitWidth = union.GetInt32Slot(4, 0)
	case ipcTypeBool:
		field.Type = ColumnTypeBool
	case ipcTypeInt:
		bitWidth := union.GetInt32Slot(4, 0)
		isSigned := union.GetBoolSlot(6, false)
		switch {
		case bitWidth == 8 && isSigned:
			field.Type = ColumnTypeInt8
		case bitWidth == 16 && isSigned:
			field.Type = ColumnTypeInt16
		case bitWidth == 32 && isSigned:
			field.Type = ColumnTypeInt32
		case bitWidth == 64 && isSigned:
			field.Type = ColumnTypeInt64
		case bitWidth == 8 && !isSigned:
			field.Type = ColumnTypeUint8
		case bitWidth == 16 && !isSigned:
			field.Type = ColumnTypeUint16
		case bitWidth == 32 && !isSigned:
			field.Type = ColumnTypeUint32
		case bitWidth == 64 && !isSigned:
			field.Type = ColumnTypeUint64
		}
	case ipcTypeFloat:
		precision := union.GetInt16Slot(4, 0)
		switch precision {
		case ipcPrecisionHalf:
			field.Type = ColumnTypeFloat16
		case ipcPrecisionSingle:
			field.Type = ColumnTypeFloat32
		case ipcPrecisionDouble:
			field.Type = ColumnTypeFloat64
		}
	case ipcTypeDate:
		switch union.GetInt16Slot(4, 0) {
		case ipcDateUnitDay:
			field.Type = ColumnTypeDate32
			field.TimeUnit = ipcDateUnitDay
		case ipcDateUnitMillisecond:
			field.Type = ColumnTypeDate64
			field.TimeUnit = ipcDateUnitMillisecond
		}
	case ipcTypeTimestamp:
		field.Type = ColumnTypeTimestamp
		field.TimeUnit = union.GetInt16Slot(4, 0)
		if tzOff := union.Offset(6); tzOff != 0 {
			field.TimeZone = string(union.ByteVector(union.Pos + flatbuffers.UOffsetT(tzOff)))
		}
	case ipcTypeTime:
		field.Type = ColumnTypeTime
		field.TimeUnit = union.GetInt16Slot(4, 0)
		field.BitWidth = union.GetInt32Slot(6, 0)
	case ipcTypeDuration:
		field.Type = ColumnTypeDuration
		field.TimeUnit = union.GetInt16Slot(4, 0)
	case ipcTypeDecimal:
		field.Type = ColumnTypeDecimal
		field.Precision = union.GetInt32Slot(4, 0)
		field.Scale = union.GetInt32Slot(6, 0)
		field.BitWidth = union.GetInt32Slot(8, 0)
	}
	childVec := tab.Offset(14)
	if childVec != 0 {
		n := tab.VectorLen(flatbuffers.UOffsetT(childVec))
		field.Children = make([]Field, 0, n)
		for i := 0; i < n; i++ {
			elem := tab.Vector(flatbuffers.UOffsetT(childVec)) + flatbuffers.UOffsetT(i*4)
			childPos := tab.Indirect(elem)
			child, err := decodeField(buf, childPos)
			if err != nil {
				return field, err
			}
			field.Children = append(field.Children, child)
		}
	}
	if (field.Type == ColumnTypeList && len(field.Children) != 1) ||
		(field.Type == ColumnTypeMap && len(field.Children) != 1) ||
		(field.Type != ColumnTypeList && field.Type != ColumnTypeStruct && field.Type != ColumnTypeMap && len(field.Children) > 0) {
		return field, errors.New("unsupported arrow nested field layout")
	}
	if dictOff := tab.Offset(12); dictOff != 0 {
		dictPos := pos + flatbuffers.UOffsetT(dictOff)
		dictPos += tab.GetUOffsetT(dictPos)
		dict, err := decodeDictionaryEncoding(buf, dictPos, field)
		if err != nil {
			return field, err
		}
		field.Dict = dict
	}
	return field, nil
}

func decodeDictionaryEncoding(buf []byte, pos flatbuffers.UOffsetT, valueField Field) (*DictionaryEncoding, error) {
	tab := flatbuffers.Table{Bytes: buf, Pos: pos}
	indexOff := tab.Offset(6)
	if indexOff == 0 {
		return nil, errors.New("arrow dictionary missing index type")
	}
	indexPos := pos + flatbuffers.UOffsetT(indexOff)
	indexPos += tab.GetUOffsetT(indexPos)
	index := flatbuffers.Table{Bytes: buf, Pos: indexPos}
	return &DictionaryEncoding{
		ID:            tab.GetInt64Slot(4, 0),
		IndexBitWidth: index.GetInt32Slot(4, 0),
		IndexSigned:   index.GetBoolSlot(6, false),
		IsOrdered:     tab.GetBoolSlot(8, false),
		ValueField:    fieldWithoutDictionary(valueField),
	}, nil
}

func decodeRecordBatch(schema Schema, header []byte, body []byte, dicts map[int64]Column) (*RecordBatch, error) {
	rb := rootTable(header)
	numRows := int(rb.tab.GetInt64Slot(4, 0))
	nodesOff := rb.tab.Offset(6)
	bufsOff := rb.tab.Offset(8)
	if nodesOff == 0 || bufsOff == 0 {
		return nil, errors.New("arrow record batch missing nodes or buffers")
	}
	nodeCount := rb.tab.VectorLen(flatbuffers.UOffsetT(nodesOff))
	bufCount := rb.tab.VectorLen(flatbuffers.UOffsetT(bufsOff))
	if nodeCount < len(schema.Fields) {
		return nil, fmt.Errorf("arrow record batch nodes=%d fields=%d", nodeCount, len(schema.Fields))
	}
	if bufCount < len(schema.Fields)*2 {
		// variable-width columns need at least 3 buffers; this check is only a floor.
	}

	nodes := make([]fieldNode, nodeCount)
	nodeVec := rb.tab.Vector(flatbuffers.UOffsetT(nodesOff))
	for i := 0; i < nodeCount; i++ {
		pos := nodeVec + flatbuffers.UOffsetT(i*16)
		nodes[i] = fieldNode{
			length:    int64(rb.tab.GetInt64(pos)),
			nullCount: int64(rb.tab.GetInt64(pos + 8)),
		}
	}

	buffers := make([]bufferRange, bufCount)
	bufVec := rb.tab.Vector(flatbuffers.UOffsetT(bufsOff))
	for i := 0; i < bufCount; i++ {
		pos := bufVec + flatbuffers.UOffsetT(i*16)
		buffers[i] = bufferRange{
			offset: int64(rb.tab.GetInt64(pos)),
			length: int64(rb.tab.GetInt64(pos + 8)),
		}
	}

	cols := make([]Column, 0, len(schema.Fields))
	nodeIdx := 0
	bufIdx := 0
	for _, field := range schema.Fields {
		if nodeIdx >= len(nodes) {
			return nil, errors.New("arrow record batch node underflow")
		}
		col, usedNodes, usedBuffers, err := decodeFieldColumn(field, nodes[nodeIdx:], buffers[bufIdx:], body, dicts)
		if err != nil {
			return nil, fmt.Errorf("decode column %q: %w", field.Name, err)
		}
		nodeIdx += usedNodes
		bufIdx += usedBuffers
		cols = append(cols, col)
	}

	return &RecordBatch{
		Schema:  schema,
		Columns: cols,
		NumRows: numRows,
	}, nil
}

type fieldNode struct {
	length    int64
	nullCount int64
}

type bufferRange struct {
	offset int64
	length int64
}

func decodeFieldColumn(field Field, nodes []fieldNode, buffers []bufferRange, body []byte, dicts map[int64]Column) (Column, int, int, error) {
	if len(nodes) == 0 {
		return Column{}, 0, 0, errors.New("insufficient arrow nodes")
	}
	node := nodes[0]
	switch field.Type {
	case ColumnTypeList:
		return decodeListColumn(field, node, nodes[1:], buffers, body, dicts)
	case ColumnTypeMap:
		return decodeMapColumn(field, node, nodes[1:], buffers, body, dicts)
	case ColumnTypeStruct:
		return decodeStructColumn(field, node, nodes[1:], buffers, body, dicts)
	default:
		col, usedBuffers, err := decodeColumn(field, node, buffers, body, dicts)
		return col, 1, usedBuffers, err
	}
}

func decodeColumn(field Field, node fieldNode, buffers []bufferRange, body []byte, dicts map[int64]Column) (Column, int, error) {
	if len(buffers) < 2 {
		return Column{}, 0, errors.New("insufficient arrow buffers")
	}
	validity := sliceBuffer(buffers[0], body)
	if field.Dict != nil {
		dict, ok := dicts[field.Dict.ID]
		if !ok {
			return Column{}, 0, fmt.Errorf("dictionary %d not loaded", field.Dict.ID)
		}
		return decodeDictionaryColumn(field, node, validity, buffers[1], body, dict)
	}
	switch field.Type {
	case ColumnTypeBool:
		valuesBuf := sliceBuffer(buffers[1], body)
		values := make([]bool, int(node.length))
		nulls := nullBitmap(validity, field.Nullable, int(node.length))
		for i := range values {
			if isNull(validity, field.Nullable, i) {
				continue
			}
			values[i] = bitIsSet(valuesBuf, i)
		}
		return Column{Name: field.Name, Values: values, Nulls: nulls}, 2, nil
	case ColumnTypeInt8:
		valuesBuf := sliceBuffer(buffers[1], body)
		if len(valuesBuf) < int(node.length) {
			return Column{}, 0, errors.New("int8 buffer too short")
		}
		values := make([]int8, int(node.length))
		nulls := nullBitmap(validity, field.Nullable, int(node.length))
		for i := range values {
			if isNull(validity, field.Nullable, i) {
				continue
			}
			values[i] = int8(valuesBuf[i])
		}
		return Column{Name: field.Name, Values: values, Nulls: nulls}, 2, nil
	case ColumnTypeInt16:
		valuesBuf := sliceBuffer(buffers[1], body)
		if len(valuesBuf) < int(node.length)*2 {
			return Column{}, 0, errors.New("int16 buffer too short")
		}
		values := make([]int16, int(node.length))
		nulls := nullBitmap(validity, field.Nullable, int(node.length))
		for i := range values {
			if isNull(validity, field.Nullable, i) {
				continue
			}
			values[i] = int16(binary.LittleEndian.Uint16(valuesBuf[i*2:]))
		}
		return Column{Name: field.Name, Values: values, Nulls: nulls}, 2, nil
	case ColumnTypeInt64:
		valuesBuf := sliceBuffer(buffers[1], body)
		if len(valuesBuf) < int(node.length)*8 {
			return Column{}, 0, errors.New("int64 buffer too short")
		}
		values := make([]int64, int(node.length))
		nulls := nullBitmap(validity, field.Nullable, int(node.length))
		for i := range values {
			if isNull(validity, field.Nullable, i) {
				continue
			}
			values[i] = int64(binary.LittleEndian.Uint64(valuesBuf[i*8:]))
		}
		return Column{Name: field.Name, Values: values, Nulls: nulls}, 2, nil
	case ColumnTypeInt32:
		valuesBuf := sliceBuffer(buffers[1], body)
		if len(valuesBuf) < int(node.length)*4 {
			return Column{}, 0, errors.New("int32 buffer too short")
		}
		values := make([]int32, int(node.length))
		nulls := nullBitmap(validity, field.Nullable, int(node.length))
		for i := range values {
			if isNull(validity, field.Nullable, i) {
				continue
			}
			values[i] = int32(binary.LittleEndian.Uint32(valuesBuf[i*4:]))
		}
		return Column{Name: field.Name, Values: values, Nulls: nulls}, 2, nil
	case ColumnTypeUint8:
		valuesBuf := sliceBuffer(buffers[1], body)
		if len(valuesBuf) < int(node.length) {
			return Column{}, 0, errors.New("uint8 buffer too short")
		}
		values := make([]uint8, int(node.length))
		nulls := nullBitmap(validity, field.Nullable, int(node.length))
		for i := range values {
			if isNull(validity, field.Nullable, i) {
				continue
			}
			values[i] = valuesBuf[i]
		}
		return Column{Name: field.Name, Values: values, Nulls: nulls}, 2, nil
	case ColumnTypeUint16:
		valuesBuf := sliceBuffer(buffers[1], body)
		if len(valuesBuf) < int(node.length)*2 {
			return Column{}, 0, errors.New("uint16 buffer too short")
		}
		values := make([]uint16, int(node.length))
		nulls := nullBitmap(validity, field.Nullable, int(node.length))
		for i := range values {
			if isNull(validity, field.Nullable, i) {
				continue
			}
			values[i] = binary.LittleEndian.Uint16(valuesBuf[i*2:])
		}
		return Column{Name: field.Name, Values: values, Nulls: nulls}, 2, nil
	case ColumnTypeUint32:
		valuesBuf := sliceBuffer(buffers[1], body)
		if len(valuesBuf) < int(node.length)*4 {
			return Column{}, 0, errors.New("uint32 buffer too short")
		}
		values := make([]uint32, int(node.length))
		nulls := nullBitmap(validity, field.Nullable, int(node.length))
		for i := range values {
			if isNull(validity, field.Nullable, i) {
				continue
			}
			values[i] = binary.LittleEndian.Uint32(valuesBuf[i*4:])
		}
		return Column{Name: field.Name, Values: values, Nulls: nulls}, 2, nil
	case ColumnTypeUint64:
		valuesBuf := sliceBuffer(buffers[1], body)
		if len(valuesBuf) < int(node.length)*8 {
			return Column{}, 0, errors.New("uint64 buffer too short")
		}
		values := make([]uint64, int(node.length))
		nulls := nullBitmap(validity, field.Nullable, int(node.length))
		for i := range values {
			if isNull(validity, field.Nullable, i) {
				continue
			}
			values[i] = binary.LittleEndian.Uint64(valuesBuf[i*8:])
		}
		return Column{Name: field.Name, Values: values, Nulls: nulls}, 2, nil
	case ColumnTypeFloat64:
		valuesBuf := sliceBuffer(buffers[1], body)
		if len(valuesBuf) < int(node.length)*8 {
			return Column{}, 0, errors.New("float64 buffer too short")
		}
		values := make([]float64, int(node.length))
		nulls := nullBitmap(validity, field.Nullable, int(node.length))
		for i := range values {
			if isNull(validity, field.Nullable, i) {
				continue
			}
			values[i] = math.Float64frombits(binary.LittleEndian.Uint64(valuesBuf[i*8:]))
		}
		return Column{Name: field.Name, Values: values, Nulls: nulls}, 2, nil
	case ColumnTypeFloat32:
		valuesBuf := sliceBuffer(buffers[1], body)
		if len(valuesBuf) < int(node.length)*4 {
			return Column{}, 0, errors.New("float32 buffer too short")
		}
		values := make([]float32, int(node.length))
		nulls := nullBitmap(validity, field.Nullable, int(node.length))
		for i := range values {
			if isNull(validity, field.Nullable, i) {
				continue
			}
			values[i] = math.Float32frombits(binary.LittleEndian.Uint32(valuesBuf[i*4:]))
		}
		return Column{Name: field.Name, Values: values, Nulls: nulls}, 2, nil
	case ColumnTypeFloat16:
		valuesBuf := sliceBuffer(buffers[1], body)
		if len(valuesBuf) < int(node.length)*2 {
			return Column{}, 0, errors.New("float16 buffer too short")
		}
		values := make([]float32, int(node.length))
		nulls := nullBitmap(validity, field.Nullable, int(node.length))
		for i := range values {
			if isNull(validity, field.Nullable, i) {
				continue
			}
			values[i] = float16ToFloat32(binary.LittleEndian.Uint16(valuesBuf[i*2:]))
		}
		return Column{Name: field.Name, Values: values, Nulls: nulls}, 2, nil
	case ColumnTypeDate32:
		valuesBuf := sliceBuffer(buffers[1], body)
		if len(valuesBuf) < int(node.length)*4 {
			return Column{}, 0, errors.New("date32 buffer too short")
		}
		values := make([]time.Time, int(node.length))
		nulls := nullBitmap(validity, field.Nullable, int(node.length))
		for i := range values {
			if isNull(validity, field.Nullable, i) {
				continue
			}
			days := int32(binary.LittleEndian.Uint32(valuesBuf[i*4:]))
			values[i] = time.Unix(int64(days)*86400, 0).UTC()
		}
		return Column{Name: field.Name, Values: values, Nulls: nulls}, 2, nil
	case ColumnTypeDate64:
		valuesBuf := sliceBuffer(buffers[1], body)
		if len(valuesBuf) < int(node.length)*8 {
			return Column{}, 0, errors.New("date64 buffer too short")
		}
		values := make([]time.Time, int(node.length))
		nulls := nullBitmap(validity, field.Nullable, int(node.length))
		for i := range values {
			if isNull(validity, field.Nullable, i) {
				continue
			}
			millis := int64(binary.LittleEndian.Uint64(valuesBuf[i*8:]))
			values[i] = time.UnixMilli(millis).UTC()
		}
		return Column{Name: field.Name, Values: values, Nulls: nulls}, 2, nil
	case ColumnTypeTimestamp:
		valuesBuf := sliceBuffer(buffers[1], body)
		if len(valuesBuf) < int(node.length)*8 {
			return Column{}, 0, errors.New("timestamp buffer too short")
		}
		values := make([]time.Time, int(node.length))
		nulls := nullBitmap(validity, field.Nullable, int(node.length))
		for i := range values {
			if isNull(validity, field.Nullable, i) {
				continue
			}
			raw := int64(binary.LittleEndian.Uint64(valuesBuf[i*8:]))
			values[i] = timestampValue(raw, field.TimeUnit)
		}
		return Column{Name: field.Name, Values: values, Nulls: nulls}, 2, nil
	case ColumnTypeTime:
		width := field.BitWidth
		if width == 0 {
			width = 32
		}
		values, err := decodeTimeValues(sliceBuffer(buffers[1], body), int(node.length), width, field.TimeUnit, validity, field.Nullable)
		if err != nil {
			return Column{}, 0, err
		}
		return Column{Name: field.Name, Values: values, Nulls: nullBitmap(validity, field.Nullable, int(node.length))}, 2, nil
	case ColumnTypeDuration:
		valuesBuf := sliceBuffer(buffers[1], body)
		if len(valuesBuf) < int(node.length)*8 {
			return Column{}, 0, errors.New("duration buffer too short")
		}
		values := make([]time.Duration, int(node.length))
		nulls := nullBitmap(validity, field.Nullable, int(node.length))
		for i := range values {
			if isNull(validity, field.Nullable, i) {
				continue
			}
			raw := int64(binary.LittleEndian.Uint64(valuesBuf[i*8:]))
			values[i] = durationValue(raw, field.TimeUnit)
		}
		return Column{Name: field.Name, Values: values, Nulls: nulls}, 2, nil
	case ColumnTypeDecimal:
		bitWidth := field.BitWidth
		if bitWidth == 0 {
			bitWidth = 128
		}
		byteWidth := int(bitWidth / 8)
		valuesBuf := sliceBuffer(buffers[1], body)
		if byteWidth <= 0 {
			return Column{}, 0, errors.New("decimal bit width is invalid")
		}
		if len(valuesBuf) < int(node.length)*byteWidth {
			return Column{}, 0, errors.New("decimal buffer too short")
		}
		values := make([]string, int(node.length))
		nulls := nullBitmap(validity, field.Nullable, int(node.length))
		for i := range values {
			if isNull(validity, field.Nullable, i) {
				continue
			}
			start := i * byteWidth
			end := start + byteWidth
			values[i] = formatDecimalString(valuesBuf[start:end], field.Scale)
		}
		return Column{Name: field.Name, Values: values, Nulls: nulls}, 2, nil
	case ColumnTypeString:
		if len(buffers) < 3 {
			return Column{}, 0, errors.New("insufficient utf8 buffers")
		}
		col, used := decodeVariableString(field.Name, field.Nullable, node.length, validity, buffers[1], buffers[2], body)
		return col, used, nil
	case ColumnTypeBinary:
		if len(buffers) < 3 {
			return Column{}, 0, errors.New("insufficient binary buffers")
		}
		col, used := decodeVariableBinary(field.Name, field.Nullable, node.length, validity, buffers[1], buffers[2], body)
		return col, used, nil
	case ColumnTypeFixedBinary:
		width := int(field.BitWidth)
		valuesBuf := sliceBuffer(buffers[1], body)
		if width <= 0 {
			return Column{}, 0, errors.New("fixed-size binary width is invalid")
		}
		if len(valuesBuf) < int(node.length)*width {
			return Column{}, 0, errors.New("fixed-size binary buffer too short")
		}
		values := make([][]byte, int(node.length))
		nulls := nullBitmap(validity, field.Nullable, int(node.length))
		for i := range values {
			if isNull(validity, field.Nullable, i) {
				continue
			}
			start := i * width
			values[i] = append([]byte(nil), valuesBuf[start:start+width]...)
		}
		return Column{Name: field.Name, Values: values, Nulls: nulls}, 2, nil
	default:
		return Column{}, 0, errors.New("unsupported column type")
	}
}

func decodeListColumn(field Field, node fieldNode, childNodes []fieldNode, buffers []bufferRange, body []byte, dicts map[int64]Column) (Column, int, int, error) {
	if len(field.Children) != 1 {
		return Column{}, 0, 0, errors.New("list field must have exactly one child")
	}
	if len(buffers) < 2 {
		return Column{}, 0, 0, errors.New("list column missing buffers")
	}
	validity := sliceBuffer(buffers[0], body)
	offsets := sliceBuffer(buffers[1], body)
	offsetWidth := field.BitWidth
	if offsetWidth == 0 {
		offsetWidth = 32
	}
	required := int(node.length + 1)
	var lastOffset int64
	switch offsetWidth {
	case 32:
		if len(offsets) < required*4 {
			return Column{}, 0, 0, errors.New("list offsets buffer too short")
		}
		lastOffset = int64(binary.LittleEndian.Uint32(offsets[node.length*4:]))
	case 64:
		if len(offsets) < required*8 {
			return Column{}, 0, 0, errors.New("large list offsets buffer too short")
		}
		lastOffset = int64(binary.LittleEndian.Uint64(offsets[node.length*8:]))
	default:
		return Column{}, 0, 0, fmt.Errorf("unsupported list offset width: %d", offsetWidth)
	}
	childCol, childNodeUsed, childBufUsed, err := decodeFieldColumn(field.Children[0], childNodes, buffers[2:], body, dicts)
	if err != nil {
		return Column{}, 0, 0, err
	}
	values := make([][]any, int(node.length))
	nulls := nullBitmap(validity, field.Nullable, int(node.length))
	for i := 0; i < int(node.length); i++ {
		if isNull(validity, field.Nullable, i) {
			continue
		}
		start, end, err := listOffsetsAt(offsets, offsetWidth, i)
		if err != nil {
			return Column{}, 0, 0, err
		}
		if start < 0 || end < start || end > lastOffset {
			return Column{}, 0, 0, errors.New("list offsets out of bounds")
		}
		row := make([]any, 0, end-start)
		for j := start; j < end; j++ {
			row = append(row, columnValueAt(childCol, int(j)))
		}
		values[i] = row
	}
	return Column{Name: field.Name, Values: values, Nulls: nulls}, 1 + childNodeUsed, 2 + childBufUsed, nil
}

func decodeStructColumn(field Field, node fieldNode, childNodes []fieldNode, buffers []bufferRange, body []byte, dicts map[int64]Column) (Column, int, int, error) {
	if len(buffers) < 1 {
		return Column{}, 0, 0, errors.New("struct column missing validity buffer")
	}
	validity := sliceBuffer(buffers[0], body)
	childCols := make([]Column, 0, len(field.Children))
	nodeUsed := 1
	bufUsed := 1
	for _, child := range field.Children {
		col, usedNodes, usedBuffers, err := decodeFieldColumn(child, childNodes[nodeUsed-1:], buffers[bufUsed:], body, dicts)
		if err != nil {
			return Column{}, 0, 0, err
		}
		nodeUsed += usedNodes
		bufUsed += usedBuffers
		childCols = append(childCols, col)
	}
	values := make([]map[string]any, int(node.length))
	nulls := nullBitmap(validity, field.Nullable, int(node.length))
	for i := 0; i < int(node.length); i++ {
		if isNull(validity, field.Nullable, i) {
			continue
		}
		row := make(map[string]any, len(childCols))
		for _, childCol := range childCols {
			row[childCol.Name] = columnValueAt(childCol, i)
		}
		values[i] = row
	}
	return Column{Name: field.Name, Values: values, Nulls: nulls}, nodeUsed, bufUsed, nil
}

func decodeMapColumn(field Field, node fieldNode, childNodes []fieldNode, buffers []bufferRange, body []byte, dicts map[int64]Column) (Column, int, int, error) {
	if len(field.Children) != 1 {
		return Column{}, 0, 0, errors.New("map field must have exactly one entries child")
	}
	entries := field.Children[0]
	if entries.Type != ColumnTypeStruct || len(entries.Children) < 2 {
		return Column{}, 0, 0, errors.New("map entries must be struct<key, value>")
	}
	col, usedNodes, usedBuffers, err := decodeListColumn(
		Field{
			Name:     field.Name,
			Type:     ColumnTypeList,
			Nullable: field.Nullable,
			BitWidth: field.BitWidth,
			Children: []Field{entries},
		},
		node,
		childNodes,
		buffers,
		body,
		dicts,
	)
	if err != nil {
		return Column{}, 0, 0, err
	}
	listRows, ok := col.Values.([][]any)
	if !ok {
		return Column{}, 0, 0, errors.New("decoded map entries are not list rows")
	}
	values := make([]map[string]any, len(listRows))
	for i, row := range listRows {
		if row == nil {
			continue
		}
		m := make(map[string]any, len(row))
		for _, entry := range row {
			pair, ok := entry.(map[string]any)
			if !ok {
				return Column{}, 0, 0, errors.New("decoded map entry is not a struct map")
			}
			var key any
			var value any
			for k, v := range pair {
				switch k {
				case entries.Children[0].Name:
					key = v
				case entries.Children[1].Name:
					value = v
				}
			}
			m[fmt.Sprint(key)] = value
		}
		values[i] = m
	}
	return Column{Name: field.Name, Values: values, Nulls: col.Nulls}, usedNodes, usedBuffers, nil
}

func decodeDictionaryColumn(field Field, node fieldNode, validity []byte, indicesBufRange bufferRange, body []byte, dict Column) (Column, int, error) {
	enc := field.Dict
	if enc == nil {
		return Column{}, 0, errors.New("dictionary encoding missing")
	}
	indicesBuf := sliceBuffer(indicesBufRange, body)
	width := enc.IndexBitWidth
	if width == 0 {
		width = 32
	}
	byteWidth := int(width / 8)
	if byteWidth <= 0 || len(indicesBuf) < int(node.length)*byteWidth {
		return Column{}, 0, errors.New("dictionary index buffer too short")
	}
	values := make([]any, int(node.length))
	nulls := nullBitmap(validity, field.Nullable, int(node.length))
	for i := range values {
		if isNull(validity, field.Nullable, i) {
			continue
		}
		index, err := dictionaryIndexAt(indicesBuf[i*byteWidth:(i+1)*byteWidth], enc.IndexSigned)
		if err != nil {
			return Column{}, 0, err
		}
		if index < 0 {
			return Column{}, 0, errors.New("dictionary index must be non-negative")
		}
		values[i] = columnValueAt(dict, int(index))
	}
	return Column{Name: field.Name, Values: values, Nulls: nulls}, 2, nil
}

func decodeVariableString(name string, nullable bool, length int64, validity []byte, offsetsBuf bufferRange, dataBuf bufferRange, body []byte) (Column, int) {
	offsets := sliceBuffer(offsetsBuf, body)
	data := sliceBuffer(dataBuf, body)
	values := make([]string, int(length))
	nulls := nullBitmap(validity, nullable, int(length))
	if len(offsets) == int((length+1)*8) {
		for i := 0; i < int(length); i++ {
			if isNull(validity, nullable, i) {
				continue
			}
			start := int(binary.LittleEndian.Uint64(offsets[i*8:]))
			end := int(binary.LittleEndian.Uint64(offsets[(i+1)*8:]))
			values[i] = string(data[start:end])
		}
		return Column{Name: name, Values: values, Nulls: nulls}, 3
	}
	for i := 0; i < int(length); i++ {
		if isNull(validity, nullable, i) {
			continue
		}
		start := int(binary.LittleEndian.Uint32(offsets[i*4:]))
		end := int(binary.LittleEndian.Uint32(offsets[(i+1)*4:]))
		values[i] = string(data[start:end])
	}
	return Column{Name: name, Values: values, Nulls: nulls}, 3
}

func decodeVariableBinary(name string, nullable bool, length int64, validity []byte, offsetsBuf bufferRange, dataBuf bufferRange, body []byte) (Column, int) {
	offsets := sliceBuffer(offsetsBuf, body)
	data := sliceBuffer(dataBuf, body)
	values := make([][]byte, int(length))
	nulls := nullBitmap(validity, nullable, int(length))
	if len(offsets) == int((length+1)*8) {
		for i := 0; i < int(length); i++ {
			if isNull(validity, nullable, i) {
				continue
			}
			start := int(binary.LittleEndian.Uint64(offsets[i*8:]))
			end := int(binary.LittleEndian.Uint64(offsets[(i+1)*8:]))
			values[i] = append([]byte(nil), data[start:end]...)
		}
		return Column{Name: name, Values: values, Nulls: nulls}, 3
	}
	for i := 0; i < int(length); i++ {
		if isNull(validity, nullable, i) {
			continue
		}
		start := int(binary.LittleEndian.Uint32(offsets[i*4:]))
		end := int(binary.LittleEndian.Uint32(offsets[(i+1)*4:]))
		values[i] = append([]byte(nil), data[start:end]...)
	}
	return Column{Name: name, Values: values, Nulls: nulls}, 3
}

func sliceBuffer(br bufferRange, body []byte) []byte {
	start := int(br.offset)
	end := start + int(br.length)
	if start < 0 || end < start || end > len(body) {
		return nil
	}
	return body[start:end]
}

func isNull(validity []byte, nullable bool, idx int) bool {
	if !nullable || len(validity) == 0 {
		return false
	}
	return !bitIsSet(validity, idx)
}

func nullBitmap(validity []byte, nullable bool, length int) []bool {
	if !nullable || len(validity) == 0 || length <= 0 {
		return nil
	}
	nulls := make([]bool, length)
	hasNull := false
	for i := 0; i < length; i++ {
		if !bitIsSet(validity, i) {
			nulls[i] = true
			hasNull = true
		}
	}
	if !hasNull {
		return nil
	}
	return nulls
}

func bitIsSet(buf []byte, idx int) bool {
	if len(buf) == 0 {
		return true
	}
	byteIdx := idx / 8
	if byteIdx >= len(buf) {
		return false
	}
	mask := byte(1 << (idx % 8))
	return buf[byteIdx]&mask != 0
}

func listOffsetsAt(buf []byte, width int32, idx int) (int64, int64, error) {
	switch width {
	case 32:
		start := idx * 4
		end := start + 8
		if end > len(buf) {
			return 0, 0, errors.New("list offsets buffer too short")
		}
		return int64(binary.LittleEndian.Uint32(buf[start:])), int64(binary.LittleEndian.Uint32(buf[start+4:])), nil
	case 64:
		start := idx * 8
		end := start + 16
		if end > len(buf) {
			return 0, 0, errors.New("large list offsets buffer too short")
		}
		return int64(binary.LittleEndian.Uint64(buf[start:])), int64(binary.LittleEndian.Uint64(buf[start+8:])), nil
	default:
		return 0, 0, fmt.Errorf("unsupported list offset width: %d", width)
	}
}

func (t ColumnType) String() string {
	switch t {
	case ColumnTypeList:
		return "list"
	case ColumnTypeStruct:
		return "struct"
	case ColumnTypeMap:
		return "map"
	case ColumnTypeInt8:
		return "int8"
	case ColumnTypeInt16:
		return "int16"
	case ColumnTypeInt64:
		return "int64"
	case ColumnTypeInt32:
		return "int32"
	case ColumnTypeUint8:
		return "uint8"
	case ColumnTypeUint16:
		return "uint16"
	case ColumnTypeUint32:
		return "uint32"
	case ColumnTypeUint64:
		return "uint64"
	case ColumnTypeFloat64:
		return "float64"
	case ColumnTypeFloat32:
		return "float32"
	case ColumnTypeFloat16:
		return "float16"
	case ColumnTypeBool:
		return "bool"
	case ColumnTypeBinary:
		return "binary"
	case ColumnTypeFixedBinary:
		return "fixed-binary"
	case ColumnTypeDate32:
		return "date32"
	case ColumnTypeDate64:
		return "date64"
	case ColumnTypeTime:
		return "time"
	case ColumnTypeTimestamp:
		return "timestamp"
	case ColumnTypeDuration:
		return "duration"
	case ColumnTypeDecimal:
		return "decimal"
	default:
		return "string"
	}
}

func (s *DataStream) DrainBatches() ([]*RecordBatch, error) {
	var batches []*RecordBatch
	for {
		batch, err := s.NextRecordBatch()
		if errors.Is(err, io.EOF) {
			return batches, nil
		}
		if err != nil {
			return nil, err
		}
		batches = append(batches, batch)
	}
}

func valueAt(values any, idx int) any {
	switch v := values.(type) {
	case []any:
		if idx < len(v) {
			return v[idx]
		}
	case [][]any:
		if idx < len(v) {
			return append([]any(nil), v[idx]...)
		}
	case []map[string]any:
		if idx < len(v) {
			if v[idx] == nil {
				return nil
			}
			out := make(map[string]any, len(v[idx]))
			for k, val := range v[idx] {
				out[k] = val
			}
			return out
		}
	case []string:
		if idx < len(v) {
			return v[idx]
		}
	case [][]byte:
		if idx < len(v) {
			if v[idx] == nil {
				return nil
			}
			return append([]byte(nil), v[idx]...)
		}
	case []bool:
		if idx < len(v) {
			return v[idx]
		}
	case []int8:
		if idx < len(v) {
			return v[idx]
		}
	case []int16:
		if idx < len(v) {
			return v[idx]
		}
	case []int64:
		if idx < len(v) {
			return v[idx]
		}
	case []int32:
		if idx < len(v) {
			return v[idx]
		}
	case []uint8:
		if idx < len(v) {
			return v[idx]
		}
	case []uint16:
		if idx < len(v) {
			return v[idx]
		}
	case []uint32:
		if idx < len(v) {
			return v[idx]
		}
	case []uint64:
		if idx < len(v) {
			return v[idx]
		}
	case []float32:
		if idx < len(v) {
			return v[idx]
		}
	case []float64:
		if idx < len(v) {
			return v[idx]
		}
	case []time.Time:
		if idx < len(v) {
			return v[idx]
		}
	case []time.Duration:
		if idx < len(v) {
			return v[idx]
		}
	}
	return nil
}

func columnValueAt(col Column, idx int) any {
	if idx < len(col.Nulls) && col.Nulls[idx] {
		return nil
	}
	return valueAt(col.Values, idx)
}

func (s *DataStream) applyDictionaryBatch(header []byte, body []byte) error {
	id, batchHeader, err := parseDictionaryBatch(header)
	if err != nil {
		return err
	}
	field, ok := s.schema.dictionaryField(id)
	if !ok {
		return fmt.Errorf("dictionary %d not declared in schema", id)
	}
	rb, err := decodeRecordBatch(Schema{Fields: []Field{fieldWithoutDictionary(field)}}, batchHeader, body, nil)
	if err != nil {
		return err
	}
	if len(rb.Columns) != 1 {
		return fmt.Errorf("dictionary %d produced %d columns", id, len(rb.Columns))
	}
	s.dicts[id] = rb.Columns[0]
	return nil
}

func parseDictionaryBatch(buf []byte) (int64, []byte, error) {
	tab := rootTable(buf)
	id := tab.tab.GetInt64Slot(4, 0)
	dataOff := tab.tab.Offset(6)
	if dataOff == 0 {
		return 0, nil, errors.New("arrow dictionary batch missing data")
	}
	dataPos := tab.tab.Pos + flatbuffers.UOffsetT(dataOff)
	dataPos += tab.tab.GetUOffsetT(dataPos)
	return id, tab.buf[dataPos:], nil
}

func (s Schema) dictionaryField(id int64) (Field, bool) {
	for _, field := range s.Fields {
		if field.Dict != nil && field.Dict.ID == id {
			return field, true
		}
	}
	return Field{}, false
}

func fieldWithoutDictionary(field Field) Field {
	field.Dict = nil
	return field
}

func decodeMetadataVector(buf []byte, tab flatbuffers.Table, slot flatbuffers.VOffsetT) map[string]string {
	vecOff := tab.Offset(slot)
	if vecOff == 0 {
		return nil
	}
	n := tab.VectorLen(flatbuffers.UOffsetT(vecOff))
	if n == 0 {
		return nil
	}
	out := make(map[string]string, n)
	for i := 0; i < n; i++ {
		elem := tab.Vector(flatbuffers.UOffsetT(vecOff)) + flatbuffers.UOffsetT(i*4)
		pos := tab.Indirect(elem)
		kv := flatbuffers.Table{Bytes: buf, Pos: pos}
		key := ""
		val := ""
		if keyOff := kv.Offset(4); keyOff != 0 {
			key = string(kv.ByteVector(pos + flatbuffers.UOffsetT(keyOff)))
		}
		if valOff := kv.Offset(6); valOff != 0 {
			val = string(kv.ByteVector(pos + flatbuffers.UOffsetT(valOff)))
		}
		if key != "" {
			out[key] = val
		}
	}
	if len(out) == 0 {
		return nil
	}
	return out
}

func dictionaryIndexAt(buf []byte, signed bool) (int64, error) {
	switch len(buf) {
	case 1:
		if signed {
			return int64(int8(buf[0])), nil
		}
		return int64(buf[0]), nil
	case 2:
		if signed {
			return int64(int16(binary.LittleEndian.Uint16(buf))), nil
		}
		return int64(binary.LittleEndian.Uint16(buf)), nil
	case 4:
		if signed {
			return int64(int32(binary.LittleEndian.Uint32(buf))), nil
		}
		return int64(binary.LittleEndian.Uint32(buf)), nil
	case 8:
		if signed {
			return int64(binary.LittleEndian.Uint64(buf)), nil
		}
		u := binary.LittleEndian.Uint64(buf)
		if u > uint64(^uint64(0)>>1) {
			return 0, errors.New("dictionary index exceeds int64")
		}
		return int64(u), nil
	default:
		return 0, fmt.Errorf("unsupported dictionary index width: %d", len(buf)*8)
	}
}

func timestampValue(raw int64, unit int16) time.Time {
	switch unit {
	case ipcTimeUnitSecond:
		return time.Unix(raw, 0).UTC()
	case ipcTimeUnitMillisecond:
		return time.UnixMilli(raw).UTC()
	case ipcTimeUnitMicrosecond:
		return time.Unix(0, raw*int64(time.Microsecond)).UTC()
	case ipcTimeUnitNanosecond:
		return time.Unix(0, raw).UTC()
	default:
		return time.UnixMilli(raw).UTC()
	}
}

func durationValue(raw int64, unit int16) time.Duration {
	switch unit {
	case ipcTimeUnitSecond:
		return time.Duration(raw) * time.Second
	case ipcTimeUnitMillisecond:
		return time.Duration(raw) * time.Millisecond
	case ipcTimeUnitMicrosecond:
		return time.Duration(raw) * time.Microsecond
	case ipcTimeUnitNanosecond:
		return time.Duration(raw)
	default:
		return time.Duration(raw)
	}
}

func decodeTimeValues(valuesBuf []byte, count int, bitWidth int32, unit int16, validity []byte, nullable bool) ([]time.Duration, error) {
	values := make([]time.Duration, count)
	nulls := nullBitmap(validity, nullable, count)
	_ = nulls
	switch bitWidth {
	case 32:
		if len(valuesBuf) < count*4 {
			return nil, errors.New("time32 buffer too short")
		}
		for i := range values {
			if isNull(validity, nullable, i) {
				continue
			}
			raw := int64(binary.LittleEndian.Uint32(valuesBuf[i*4:]))
			values[i] = durationValue(raw, unit)
		}
	case 64:
		if len(valuesBuf) < count*8 {
			return nil, errors.New("time64 buffer too short")
		}
		for i := range values {
			if isNull(validity, nullable, i) {
				continue
			}
			raw := int64(binary.LittleEndian.Uint64(valuesBuf[i*8:]))
			values[i] = durationValue(raw, unit)
		}
	default:
		return nil, fmt.Errorf("unsupported time bit width: %d", bitWidth)
	}
	return values, nil
}

func float16ToFloat32(bits uint16) float32 {
	sign := uint32(bits>>15) & 0x1
	exp := uint32(bits>>10) & 0x1f
	frac := uint32(bits & 0x03ff)
	switch exp {
	case 0:
		if frac == 0 {
			return math.Float32frombits(sign << 31)
		}
		for frac&0x0400 == 0 {
			frac <<= 1
			exp--
		}
		exp++
		frac &= ^uint32(0x0400)
	case 31:
		return math.Float32frombits((sign << 31) | 0x7f800000 | (frac << 13))
	}
	exp = exp + (127 - 15)
	return math.Float32frombits((sign << 31) | (exp << 23) | (frac << 13))
}

func formatDecimalString(le []byte, scale int32) string {
	if len(le) == 0 {
		return "0"
	}
	negative := le[len(le)-1]&0x80 != 0
	mag := append([]byte(nil), le...)
	if negative {
		twosComplementLE(mag)
	}
	digits := decimalDigitsFromLittleEndian(mag)
	if digits == "" {
		digits = "0"
		negative = false
	}
	formatted := applyDecimalScale(digits, scale)
	if negative && formatted != "0" {
		return "-" + formatted
	}
	return formatted
}

func twosComplementLE(buf []byte) {
	carry := byte(1)
	for i := range buf {
		buf[i] = ^buf[i]
		sum := uint16(buf[i]) + uint16(carry)
		buf[i] = byte(sum)
		carry = byte(sum >> 8)
	}
}

func decimalDigitsFromLittleEndian(le []byte) string {
	last := len(le) - 1
	for last >= 0 && le[last] == 0 {
		last--
	}
	if last < 0 {
		return ""
	}
	be := make([]byte, last+1)
	for i := 0; i <= last; i++ {
		be[last-i] = le[i]
	}
	digits := make([]byte, 0, len(be)*3)
	for len(be) > 0 {
		carry := 0
		for i := 0; i < len(be); i++ {
			value := carry*256 + int(be[i])
			be[i] = byte(value / 10)
			carry = value % 10
		}
		digits = append(digits, byte('0'+carry))
		cut := 0
		for cut < len(be) && be[cut] == 0 {
			cut++
		}
		be = be[cut:]
	}
	for i, j := 0, len(digits)-1; i < j; i, j = i+1, j-1 {
		digits[i], digits[j] = digits[j], digits[i]
	}
	return string(digits)
}

func applyDecimalScale(digits string, scale int32) string {
	if scale == 0 {
		return digits
	}
	if scale < 0 {
		return digits + strings.Repeat("0", int(-scale))
	}
	if len(digits) <= int(scale) {
		return "0." + strings.Repeat("0", int(scale)-len(digits)) + digits
	}
	point := len(digits) - int(scale)
	return digits[:point] + "." + digits[point:]
}
