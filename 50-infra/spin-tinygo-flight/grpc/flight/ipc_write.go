package flight

import (
	"encoding/binary"
	"errors"
	"fmt"
	"math"
	"strconv"
	"time"

	flatbuffers "github.com/google/flatbuffers/go"
)

const (
	ipcMetadataVersionV5 = 4
	ipcEndiannessLittle  = 0
)

// BuildPreparedStatementMessages converts row-oriented parameter values into the
// FlightData sequence expected by DoPut for a prepared statement handle.
func BuildPreparedStatementMessages(handle []byte, parameterSchema []byte, rows []map[string]any) ([]FlightData, error) {
	if len(handle) == 0 {
		return nil, errors.New("prepared statement handle is required")
	}
	if len(parameterSchema) == 0 {
		return nil, errors.New("parameter schema is required")
	}
	schema, err := decodeSchema(parameterSchema)
	if err != nil {
		return nil, fmt.Errorf("decode parameter schema: %w", err)
	}
	if err := validateWritableSchema(*schema); err != nil {
		return nil, err
	}
	schemaHeader, err := buildSchemaIPCMessage(*schema)
	if err != nil {
		return nil, err
	}
	batchHeader, batchBody, err := buildRecordBatchIPCMessage(*schema, rows)
	if err != nil {
		return nil, err
	}
	cmd, err := marshalCommandPreparedStatementQuery(handle)
	if err != nil {
		return nil, err
	}
	desc := &FlightDescriptor{
		Type: DescriptorCmd,
		Cmd:  marshalAny(commandPreparedStatementQueryTypeURL, cmd),
	}
	return []FlightData{
		{
			FlightDescriptor: desc,
			DataHeader:       schemaHeader,
		},
		{
			DataHeader: batchHeader,
			DataBody:   batchBody,
		},
	}, nil
}

func validateWritableSchema(schema Schema) error {
	for _, field := range schema.Fields {
		if field.Dict != nil {
			return fmt.Errorf("bind does not support dictionary field %q", field.Name)
		}
		if len(field.Children) > 0 {
			return fmt.Errorf("bind does not support nested field %q", field.Name)
		}
		switch field.Type {
		case ColumnTypeString, ColumnTypeBinary, ColumnTypeBool,
			ColumnTypeInt8, ColumnTypeInt16, ColumnTypeInt32, ColumnTypeInt64,
			ColumnTypeUint8, ColumnTypeUint16, ColumnTypeUint32, ColumnTypeUint64,
			ColumnTypeFloat16, ColumnTypeFloat32, ColumnTypeFloat64,
			ColumnTypeDate32, ColumnTypeDate64, ColumnTypeTime,
			ColumnTypeTimestamp, ColumnTypeDuration, ColumnTypeFixedBinary:
		default:
			return fmt.Errorf("bind does not support field %q of type %s", field.Name, field.Type.String())
		}
	}
	return nil
}

func buildSchemaIPCMessage(schema Schema) ([]byte, error) {
	builder := flatbuffers.NewBuilder(256)
	schemaOffset, err := buildSchemaFlatbuffer(builder, schema)
	if err != nil {
		return nil, err
	}
	builder.StartObject(5)
	builder.PrependInt16Slot(0, ipcMetadataVersionV5, 0)
	builder.PrependByteSlot(1, ipcHeaderSchema, 0)
	builder.PrependUOffsetTSlot(2, schemaOffset, 0)
	builder.PrependInt64Slot(3, 0, 0)
	msg := builder.EndObject()
	builder.Finish(msg)
	return append([]byte(nil), builder.FinishedBytes()...), nil
}

func buildSchemaFlatbuffer(builder *flatbuffers.Builder, schema Schema) (flatbuffers.UOffsetT, error) {
	meta := buildMetadataVector(builder, schema.Metadata)
	fieldOffsets := make([]flatbuffers.UOffsetT, len(schema.Fields))
	for i := len(schema.Fields) - 1; i >= 0; i-- {
		offset, err := buildFieldFlatbuffer(builder, schema.Fields[i])
		if err != nil {
			return 0, err
		}
		fieldOffsets[i] = offset
	}
	var fieldsVec flatbuffers.UOffsetT
	if len(fieldOffsets) > 0 {
		builder.StartVector(4, len(fieldOffsets), 4)
		for i := len(fieldOffsets) - 1; i >= 0; i-- {
			builder.PrependUOffsetT(fieldOffsets[i])
		}
		fieldsVec = builder.EndVector(len(fieldOffsets))
	}
	builder.StartObject(4)
	builder.PrependInt16Slot(0, ipcEndiannessLittle, 0)
	if fieldsVec != 0 {
		builder.PrependUOffsetTSlot(1, fieldsVec, 0)
	}
	if meta != 0 {
		builder.PrependUOffsetTSlot(2, meta, 0)
	}
	return builder.EndObject(), nil
}

func buildFieldFlatbuffer(builder *flatbuffers.Builder, field Field) (flatbuffers.UOffsetT, error) {
	if len(field.Children) > 0 {
		return 0, fmt.Errorf("nested field %q is not writable", field.Name)
	}
	if field.Dict != nil {
		return 0, fmt.Errorf("dictionary field %q is not writable", field.Name)
	}
	name := flatbuffers.UOffsetT(0)
	if field.Name != "" {
		name = builder.CreateString(field.Name)
	}
	meta := buildMetadataVector(builder, field.Metadata)
	typeCode, typeOffset, err := buildTypeFlatbuffer(builder, field)
	if err != nil {
		return 0, err
	}
	builder.StartObject(7)
	if name != 0 {
		builder.PrependUOffsetTSlot(0, name, 0)
	}
	builder.PrependBoolSlot(1, field.Nullable, false)
	builder.PrependByteSlot(2, typeCode, 0)
	builder.PrependUOffsetTSlot(3, typeOffset, 0)
	if meta != 0 {
		builder.PrependUOffsetTSlot(6, meta, 0)
	}
	return builder.EndObject(), nil
}

func buildTypeFlatbuffer(builder *flatbuffers.Builder, field Field) (byte, flatbuffers.UOffsetT, error) {
	switch field.Type {
	case ColumnTypeString:
		builder.StartObject(0)
		return ipcTypeUtf8, builder.EndObject(), nil
	case ColumnTypeBinary:
		builder.StartObject(0)
		return ipcTypeBinary, builder.EndObject(), nil
	case ColumnTypeBool:
		builder.StartObject(0)
		return ipcTypeBool, builder.EndObject(), nil
	case ColumnTypeInt8, ColumnTypeInt16, ColumnTypeInt32, ColumnTypeInt64:
		builder.StartObject(2)
		builder.PrependInt32Slot(0, intBitWidth(field.Type), 0)
		builder.PrependBoolSlot(1, true, false)
		return ipcTypeInt, builder.EndObject(), nil
	case ColumnTypeUint8, ColumnTypeUint16, ColumnTypeUint32, ColumnTypeUint64:
		builder.StartObject(2)
		builder.PrependInt32Slot(0, intBitWidth(field.Type), 0)
		builder.PrependBoolSlot(1, false, false)
		return ipcTypeInt, builder.EndObject(), nil
	case ColumnTypeFloat16:
		builder.StartObject(1)
		builder.PrependInt16Slot(0, ipcPrecisionHalf, 0)
		return ipcTypeFloat, builder.EndObject(), nil
	case ColumnTypeFloat32:
		builder.StartObject(1)
		builder.PrependInt16Slot(0, ipcPrecisionSingle, 0)
		return ipcTypeFloat, builder.EndObject(), nil
	case ColumnTypeFloat64:
		builder.StartObject(1)
		builder.PrependInt16Slot(0, ipcPrecisionDouble, 0)
		return ipcTypeFloat, builder.EndObject(), nil
	case ColumnTypeDate32:
		builder.StartObject(1)
		builder.PrependInt16Slot(0, ipcDateUnitDay, 1)
		return ipcTypeDate, builder.EndObject(), nil
	case ColumnTypeDate64:
		builder.StartObject(1)
		builder.PrependInt16Slot(0, ipcDateUnitMillisecond, 1)
		return ipcTypeDate, builder.EndObject(), nil
	case ColumnTypeTime:
		width := field.BitWidth
		if width == 0 {
			width = 32
		}
		builder.StartObject(2)
		builder.PrependInt16Slot(0, field.TimeUnit, 1)
		builder.PrependInt32Slot(1, width, 32)
		return ipcTypeTime, builder.EndObject(), nil
	case ColumnTypeTimestamp:
		tz := flatbuffers.UOffsetT(0)
		if field.TimeZone != "" {
			tz = builder.CreateString(field.TimeZone)
		}
		builder.StartObject(2)
		builder.PrependInt16Slot(0, field.TimeUnit, 0)
		if tz != 0 {
			builder.PrependUOffsetTSlot(1, tz, 0)
		}
		return ipcTypeTimestamp, builder.EndObject(), nil
	case ColumnTypeDuration:
		builder.StartObject(1)
		builder.PrependInt16Slot(0, field.TimeUnit, 1)
		return ipcTypeDuration, builder.EndObject(), nil
	case ColumnTypeFixedBinary:
		builder.StartObject(1)
		builder.PrependInt32Slot(0, field.BitWidth, 0)
		return ipcTypeFixedBinary, builder.EndObject(), nil
	default:
		return 0, 0, fmt.Errorf("unsupported writable field type %q: %s", field.Name, field.Type.String())
	}
}

func buildMetadataVector(builder *flatbuffers.Builder, meta map[string]string) flatbuffers.UOffsetT {
	if len(meta) == 0 {
		return 0
	}
	type kv struct {
		k string
		v string
	}
	items := make([]kv, 0, len(meta))
	for k, v := range meta {
		items = append(items, kv{k: k, v: v})
	}
	offsets := make([]flatbuffers.UOffsetT, len(items))
	for i := len(items) - 1; i >= 0; i-- {
		key := builder.CreateString(items[i].k)
		val := builder.CreateString(items[i].v)
		builder.StartObject(2)
		builder.PrependUOffsetTSlot(0, key, 0)
		builder.PrependUOffsetTSlot(1, val, 0)
		offsets[i] = builder.EndObject()
	}
	builder.StartVector(4, len(offsets), 4)
	for i := len(offsets) - 1; i >= 0; i-- {
		builder.PrependUOffsetT(offsets[i])
	}
	return builder.EndVector(len(offsets))
}

func buildRecordBatchIPCMessage(schema Schema, rows []map[string]any) ([]byte, []byte, error) {
	nodes, buffers, body, err := encodeRecordBatch(schema, rows)
	if err != nil {
		return nil, nil, err
	}
	builder := flatbuffers.NewBuilder(256)
	var nodesVec flatbuffers.UOffsetT
	if len(nodes) > 0 {
		builder.StartVector(16, len(nodes), 8)
		for i := len(nodes) - 1; i >= 0; i-- {
			builder.Prep(8, 16)
			builder.PrependInt64(nodes[i].nullCount)
			builder.PrependInt64(nodes[i].length)
		}
		nodesVec = builder.EndVector(len(nodes))
	}
	var buffersVec flatbuffers.UOffsetT
	if len(buffers) > 0 {
		builder.StartVector(16, len(buffers), 8)
		for i := len(buffers) - 1; i >= 0; i-- {
			builder.Prep(8, 16)
			builder.PrependInt64(buffers[i].length)
			builder.PrependInt64(buffers[i].offset)
		}
		buffersVec = builder.EndVector(len(buffers))
	}
	builder.StartObject(5)
	builder.PrependInt64Slot(0, int64(len(rows)), 0)
	if nodesVec != 0 {
		builder.PrependUOffsetTSlot(1, nodesVec, 0)
	}
	if buffersVec != 0 {
		builder.PrependUOffsetTSlot(2, buffersVec, 0)
	}
	recordBatch := builder.EndObject()
	builder.StartObject(5)
	builder.PrependInt16Slot(0, ipcMetadataVersionV5, 0)
	builder.PrependByteSlot(1, ipcHeaderRecordBatch, 0)
	builder.PrependUOffsetTSlot(2, recordBatch, 0)
	builder.PrependInt64Slot(3, int64(len(body)), 0)
	msg := builder.EndObject()
	builder.Finish(msg)
	return append([]byte(nil), builder.FinishedBytes()...), body, nil
}

func encodeRecordBatch(schema Schema, rows []map[string]any) ([]fieldNode, []bufferRange, []byte, error) {
	nodes := make([]fieldNode, 0, len(schema.Fields))
	buffers := make([]bufferRange, 0, len(schema.Fields)*3)
	body := make([]byte, 0, len(rows)*len(schema.Fields)*8)
	for _, field := range schema.Fields {
		node, chunks, err := encodeFieldBuffers(field, rows)
		if err != nil {
			return nil, nil, nil, fmt.Errorf("encode field %q: %w", field.Name, err)
		}
		nodes = append(nodes, node)
		for _, chunk := range chunks {
			offset := int64(len(body))
			body = append(body, chunk.data...)
			buffers = append(buffers, bufferRange{
				offset: offset,
				length: int64(len(chunk.data)),
			})
			if chunk.align {
				body = appendAligned(body, 8)
			}
		}
	}
	return nodes, buffers, body, nil
}

type encodedBuffer struct {
	data  []byte
	align bool
}

func encodeFieldBuffers(field Field, rows []map[string]any) (fieldNode, []encodedBuffer, error) {
	length := len(rows)
	values := make([]any, length)
	nullCount := int64(0)
	for i, row := range rows {
		if row == nil {
			if !field.Nullable {
				return fieldNode{}, nil, fmt.Errorf("row %d missing non-nullable field %q", i, field.Name)
			}
			nullCount++
			continue
		}
		value, ok := row[field.Name]
		if !ok || value == nil {
			if !field.Nullable {
				return fieldNode{}, nil, fmt.Errorf("row %d missing non-nullable field %q", i, field.Name)
			}
			nullCount++
			continue
		}
		values[i] = value
	}
	validity := encodeValidityBitmap(values)
	switch field.Type {
	case ColumnTypeBool:
		out := make([]byte, (length+7)/8)
		for i, value := range values {
			if value == nil {
				continue
			}
			b, ok := boolValue(value)
			if !ok {
				return fieldNode{}, nil, valueTypeError(field, i, value)
			}
			if b {
				out[i/8] |= 1 << uint(i%8)
			}
		}
		return fieldNode{length: int64(length), nullCount: nullCount}, []encodedBuffer{{data: validity, align: true}, {data: out, align: true}}, nil
	case ColumnTypeInt8:
		out := make([]byte, length)
		for i, value := range values {
			if value == nil {
				continue
			}
			v, ok := signedValue(value)
			if !ok {
				return fieldNode{}, nil, valueTypeError(field, i, value)
			}
			out[i] = byte(int8(v))
		}
		return fieldNode{length: int64(length), nullCount: nullCount}, []encodedBuffer{{data: validity, align: true}, {data: out, align: true}}, nil
	case ColumnTypeUint8:
		out := make([]byte, length)
		for i, value := range values {
			if value == nil {
				continue
			}
			v, ok := unsignedValue(value)
			if !ok {
				return fieldNode{}, nil, valueTypeError(field, i, value)
			}
			out[i] = byte(v)
		}
		return fieldNode{length: int64(length), nullCount: nullCount}, []encodedBuffer{{data: validity, align: true}, {data: out, align: true}}, nil
	case ColumnTypeInt16:
		out := make([]byte, length*2)
		for i, value := range values {
			if value == nil {
				continue
			}
			v, ok := signedValue(value)
			if !ok {
				return fieldNode{}, nil, valueTypeError(field, i, value)
			}
			binary.LittleEndian.PutUint16(out[i*2:], uint16(int16(v)))
		}
		return fieldNode{length: int64(length), nullCount: nullCount}, []encodedBuffer{{data: validity, align: true}, {data: out, align: true}}, nil
	case ColumnTypeUint16:
		out := make([]byte, length*2)
		for i, value := range values {
			if value == nil {
				continue
			}
			v, ok := unsignedValue(value)
			if !ok {
				return fieldNode{}, nil, valueTypeError(field, i, value)
			}
			binary.LittleEndian.PutUint16(out[i*2:], uint16(v))
		}
		return fieldNode{length: int64(length), nullCount: nullCount}, []encodedBuffer{{data: validity, align: true}, {data: out, align: true}}, nil
	case ColumnTypeInt32, ColumnTypeDate32:
		out := make([]byte, length*4)
		for i, value := range values {
			if value == nil {
				continue
			}
			v, err := int32FieldValue(field, value)
			if err != nil {
				return fieldNode{}, nil, fmt.Errorf("row %d: %w", i, err)
			}
			binary.LittleEndian.PutUint32(out[i*4:], uint32(v))
		}
		return fieldNode{length: int64(length), nullCount: nullCount}, []encodedBuffer{{data: validity, align: true}, {data: out, align: true}}, nil
	case ColumnTypeUint32:
		out := make([]byte, length*4)
		for i, value := range values {
			if value == nil {
				continue
			}
			v, ok := unsignedValue(value)
			if !ok {
				return fieldNode{}, nil, valueTypeError(field, i, value)
			}
			binary.LittleEndian.PutUint32(out[i*4:], uint32(v))
		}
		return fieldNode{length: int64(length), nullCount: nullCount}, []encodedBuffer{{data: validity, align: true}, {data: out, align: true}}, nil
	case ColumnTypeInt64, ColumnTypeDate64, ColumnTypeTimestamp, ColumnTypeDuration:
		out := make([]byte, length*8)
		for i, value := range values {
			if value == nil {
				continue
			}
			v, err := int64FieldValue(field, value)
			if err != nil {
				return fieldNode{}, nil, fmt.Errorf("row %d: %w", i, err)
			}
			binary.LittleEndian.PutUint64(out[i*8:], uint64(v))
		}
		return fieldNode{length: int64(length), nullCount: nullCount}, []encodedBuffer{{data: validity, align: true}, {data: out, align: true}}, nil
	case ColumnTypeUint64:
		out := make([]byte, length*8)
		for i, value := range values {
			if value == nil {
				continue
			}
			v, ok := unsignedValue(value)
			if !ok {
				return fieldNode{}, nil, valueTypeError(field, i, value)
			}
			binary.LittleEndian.PutUint64(out[i*8:], v)
		}
		return fieldNode{length: int64(length), nullCount: nullCount}, []encodedBuffer{{data: validity, align: true}, {data: out, align: true}}, nil
	case ColumnTypeFloat16:
		out := make([]byte, length*2)
		for i, value := range values {
			if value == nil {
				continue
			}
			v, ok := floatValue(value)
			if !ok {
				return fieldNode{}, nil, valueTypeError(field, i, value)
			}
			binary.LittleEndian.PutUint16(out[i*2:], float32ToFloat16(float32(v)))
		}
		return fieldNode{length: int64(length), nullCount: nullCount}, []encodedBuffer{{data: validity, align: true}, {data: out, align: true}}, nil
	case ColumnTypeFloat32:
		out := make([]byte, length*4)
		for i, value := range values {
			if value == nil {
				continue
			}
			v, ok := floatValue(value)
			if !ok {
				return fieldNode{}, nil, valueTypeError(field, i, value)
			}
			binary.LittleEndian.PutUint32(out[i*4:], math.Float32bits(float32(v)))
		}
		return fieldNode{length: int64(length), nullCount: nullCount}, []encodedBuffer{{data: validity, align: true}, {data: out, align: true}}, nil
	case ColumnTypeFloat64:
		out := make([]byte, length*8)
		for i, value := range values {
			if value == nil {
				continue
			}
			v, ok := floatValue(value)
			if !ok {
				return fieldNode{}, nil, valueTypeError(field, i, value)
			}
			binary.LittleEndian.PutUint64(out[i*8:], math.Float64bits(v))
		}
		return fieldNode{length: int64(length), nullCount: nullCount}, []encodedBuffer{{data: validity, align: true}, {data: out, align: true}}, nil
	case ColumnTypeTime:
		width := field.BitWidth
		if width == 0 {
			width = 32
		}
		switch width {
		case 32:
			out := make([]byte, length*4)
			for i, value := range values {
				if value == nil {
					continue
				}
				v, err := timeFieldValue(field, value)
				if err != nil {
					return fieldNode{}, nil, fmt.Errorf("row %d: %w", i, err)
				}
				binary.LittleEndian.PutUint32(out[i*4:], uint32(v))
			}
			return fieldNode{length: int64(length), nullCount: nullCount}, []encodedBuffer{{data: validity, align: true}, {data: out, align: true}}, nil
		case 64:
			out := make([]byte, length*8)
			for i, value := range values {
				if value == nil {
					continue
				}
				v, err := timeFieldValue(field, value)
				if err != nil {
					return fieldNode{}, nil, fmt.Errorf("row %d: %w", i, err)
				}
				binary.LittleEndian.PutUint64(out[i*8:], uint64(v))
			}
			return fieldNode{length: int64(length), nullCount: nullCount}, []encodedBuffer{{data: validity, align: true}, {data: out, align: true}}, nil
		default:
			return fieldNode{}, nil, fmt.Errorf("unsupported time width %d", width)
		}
	case ColumnTypeString:
		offsets := make([]byte, (length+1)*4)
		data := make([]byte, 0, length*8)
		for i, value := range values {
			binary.LittleEndian.PutUint32(offsets[i*4:], uint32(len(data)))
			if value == nil {
				continue
			}
			s, ok := stringValue(value)
			if !ok {
				return fieldNode{}, nil, valueTypeError(field, i, value)
			}
			data = append(data, s...)
		}
		binary.LittleEndian.PutUint32(offsets[length*4:], uint32(len(data)))
		return fieldNode{length: int64(length), nullCount: nullCount}, []encodedBuffer{{data: validity, align: true}, {data: offsets, align: true}, {data: data, align: true}}, nil
	case ColumnTypeBinary:
		offsets := make([]byte, (length+1)*4)
		data := make([]byte, 0, length*8)
		for i, value := range values {
			binary.LittleEndian.PutUint32(offsets[i*4:], uint32(len(data)))
			if value == nil {
				continue
			}
			b, ok := binaryValue(value)
			if !ok {
				return fieldNode{}, nil, valueTypeError(field, i, value)
			}
			data = append(data, b...)
		}
		binary.LittleEndian.PutUint32(offsets[length*4:], uint32(len(data)))
		return fieldNode{length: int64(length), nullCount: nullCount}, []encodedBuffer{{data: validity, align: true}, {data: offsets, align: true}, {data: data, align: true}}, nil
	case ColumnTypeFixedBinary:
		width := int(field.BitWidth)
		if width <= 0 {
			return fieldNode{}, nil, errors.New("fixed-size binary width is invalid")
		}
		out := make([]byte, length*width)
		for i, value := range values {
			if value == nil {
				continue
			}
			b, ok := binaryValue(value)
			if !ok || len(b) != width {
				return fieldNode{}, nil, fmt.Errorf("row %d: field %q expects []byte of length %d", i, field.Name, width)
			}
			copy(out[i*width:], b)
		}
		return fieldNode{length: int64(length), nullCount: nullCount}, []encodedBuffer{{data: validity, align: true}, {data: out, align: true}}, nil
	default:
		return fieldNode{}, nil, fmt.Errorf("unsupported writable field type %s", field.Type.String())
	}
}

func encodeValidityBitmap(values []any) []byte {
	hasNull := false
	out := make([]byte, (len(values)+7)/8)
	for i, value := range values {
		if value == nil {
			hasNull = true
			continue
		}
		out[i/8] |= 1 << uint(i%8)
	}
	if !hasNull {
		return nil
	}
	return out
}

func appendAligned(dst []byte, alignment int) []byte {
	if alignment <= 1 {
		return dst
	}
	padding := alignment - (len(dst) % alignment)
	if padding == alignment {
		return dst
	}
	for i := 0; i < padding; i++ {
		dst = append(dst, 0)
	}
	return dst
}

func intBitWidth(typ ColumnType) int32 {
	switch typ {
	case ColumnTypeInt8, ColumnTypeUint8:
		return 8
	case ColumnTypeInt16, ColumnTypeUint16:
		return 16
	case ColumnTypeInt32, ColumnTypeUint32:
		return 32
	default:
		return 64
	}
}

func boolValue(v any) (bool, bool) {
	b, ok := v.(bool)
	return b, ok
}

func signedValue(v any) (int64, bool) {
	switch n := v.(type) {
	case int:
		return int64(n), true
	case int8:
		return int64(n), true
	case int16:
		return int64(n), true
	case int32:
		return int64(n), true
	case int64:
		return n, true
	}
	return 0, false
}

func unsignedValue(v any) (uint64, bool) {
	switch n := v.(type) {
	case uint:
		return uint64(n), true
	case uint8:
		return uint64(n), true
	case uint16:
		return uint64(n), true
	case uint32:
		return uint64(n), true
	case uint64:
		return n, true
	}
	return 0, false
}

func floatValue(v any) (float64, bool) {
	switch n := v.(type) {
	case float32:
		return float64(n), true
	case float64:
		return n, true
	}
	return 0, false
}

func stringValue(v any) (string, bool) {
	switch s := v.(type) {
	case string:
		return s, true
	case []byte:
		return string(s), true
	}
	return "", false
}

func binaryValue(v any) ([]byte, bool) {
	switch b := v.(type) {
	case []byte:
		return append([]byte(nil), b...), true
	case string:
		return []byte(b), true
	}
	return nil, false
}

func int32FieldValue(field Field, value any) (int32, error) {
	switch field.Type {
	case ColumnTypeDate32:
		switch v := value.(type) {
		case time.Time:
			return int32(v.UTC().Unix() / 86400), nil
		}
	}
	if v, ok := signedValue(value); ok {
		return int32(v), nil
	}
	return 0, fmt.Errorf("field %q expects int32-compatible value", field.Name)
}

func int64FieldValue(field Field, value any) (int64, error) {
	switch field.Type {
	case ColumnTypeDate64:
		switch v := value.(type) {
		case time.Time:
			return v.UTC().UnixMilli(), nil
		}
	case ColumnTypeTimestamp:
		switch v := value.(type) {
		case time.Time:
			return encodeTimestampValue(v, field.TimeUnit), nil
		}
	case ColumnTypeDuration:
		switch v := value.(type) {
		case time.Duration:
			return encodeDurationValue(v, field.TimeUnit), nil
		}
	}
	if v, ok := signedValue(value); ok {
		return v, nil
	}
	return 0, fmt.Errorf("field %q expects int64-compatible value", field.Name)
}

func timeFieldValue(field Field, value any) (int64, error) {
	switch v := value.(type) {
	case time.Duration:
		return encodeDurationValue(v, field.TimeUnit), nil
	}
	if raw, ok := signedValue(value); ok {
		return raw, nil
	}
	return 0, fmt.Errorf("field %q expects time.Duration-compatible value", field.Name)
}

func encodeTimestampValue(t time.Time, unit int16) int64 {
	t = t.UTC()
	switch unit {
	case ipcTimeUnitSecond:
		return t.Unix()
	case ipcTimeUnitMillisecond:
		return t.UnixMilli()
	case ipcTimeUnitMicrosecond:
		return t.UnixMicro()
	default:
		return t.UnixNano()
	}
}

func encodeDurationValue(d time.Duration, unit int16) int64 {
	switch unit {
	case ipcTimeUnitSecond:
		return int64(d / time.Second)
	case ipcTimeUnitMillisecond:
		return int64(d / time.Millisecond)
	case ipcTimeUnitMicrosecond:
		return int64(d / time.Microsecond)
	default:
		return int64(d)
	}
}

func valueTypeError(field Field, row int, value any) error {
	return fmt.Errorf("row %d: field %q expects %s-compatible value, got %T", row, field.Name, field.Type.String(), value)
}

func float32ToFloat16(v float32) uint16 {
	bits := math.Float32bits(v)
	sign := uint16((bits >> 16) & 0x8000)
	exp := int32((bits>>23)&0xff) - 127 + 15
	mant := bits & 0x7fffff
	switch {
	case exp <= 0:
		if exp < -10 {
			return sign
		}
		mant = (mant | 0x800000) >> uint32(1-exp)
		if mant&0x1000 != 0 {
			mant += 0x2000
		}
		return sign | uint16(mant>>13)
	case exp >= 31:
		return sign | 0x7c00
	default:
		if mant&0x1000 != 0 {
			mant += 0x2000
			if mant&0x800000 != 0 {
				mant = 0
				exp++
				if exp >= 31 {
					return sign | 0x7c00
				}
			}
		}
		return sign | uint16(exp<<10) | uint16(mant>>13)
	}
}

func parseInt64String(value string) (int64, bool) {
	v, err := strconv.ParseInt(value, 10, 64)
	return v, err == nil
}
