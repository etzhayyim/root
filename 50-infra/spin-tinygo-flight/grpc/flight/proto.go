package flight

import "errors"

const commandStatementQueryTypeURL = "type.googleapis.com/arrow.flight.protocol.sql.CommandStatementQuery"
const commandPreparedStatementQueryTypeURL = "type.googleapis.com/arrow.flight.protocol.sql.CommandPreparedStatementQuery"

const (
	createPreparedStatementActionType = "CreatePreparedStatement"
	closePreparedStatementActionType  = "ClosePreparedStatement"
)

func marshalHandshakeRequest(req HandshakeRequest) ([]byte, error) {
	buf := make([]byte, 0, 16+len(req.Payload))
	if req.ProtocolVersion != 0 {
		buf = appendVarintField(buf, 1, req.ProtocolVersion)
	}
	if len(req.Payload) > 0 {
		buf = appendBytesField(buf, 2, req.Payload)
	}
	return buf, nil
}

func unmarshalHandshakeResponse(raw []byte) (HandshakeResponse, error) {
	var out HandshakeResponse
	err := consumeMessage(raw, func(fieldNum int, wireType int, value []byte) error {
		switch {
		case fieldNum == 1 && wireType == wireVarint:
			v, _, err := consumeVarint(value)
			if err != nil {
				return err
			}
			out.ProtocolVersion = v
		case fieldNum == 2 && wireType == wireBytes:
			v, _, err := consumeBytes(value)
			if err != nil {
				return err
			}
			out.Payload = append([]byte(nil), v...)
		}
		return nil
	})
	return out, err
}

func marshalCommandStatementQuery(query string) ([]byte, error) {
	return appendBytesField(nil, 1, []byte(query)), nil
}

func marshalCommandPreparedStatementQuery(handle []byte) ([]byte, error) {
	return appendBytesField(nil, 1, handle), nil
}

func marshalCreatePreparedStatementRequest(query string) ([]byte, error) {
	return appendBytesField(nil, 1, []byte(query)), nil
}

func marshalClosePreparedStatementRequest(handle []byte) ([]byte, error) {
	return appendBytesField(nil, 1, handle), nil
}

func marshalAction(action Action) ([]byte, error) {
	buf := make([]byte, 0, len(action.Type)+len(action.Body)+8)
	if action.Type != "" {
		buf = appendBytesField(buf, 1, []byte(action.Type))
	}
	if len(action.Body) > 0 {
		buf = appendBytesField(buf, 2, action.Body)
	}
	return buf, nil
}

func marshalFlightData(msg FlightData) ([]byte, error) {
	buf := make([]byte, 0, len(msg.DataHeader)+len(msg.DataBody)+len(msg.AppMetadata)+16)
	if msg.FlightDescriptor != nil {
		desc, err := marshalFlightDescriptor(*msg.FlightDescriptor)
		if err != nil {
			return nil, err
		}
		buf = appendBytesField(buf, 1, desc)
	}
	if len(msg.DataHeader) > 0 {
		buf = appendBytesField(buf, 2, msg.DataHeader)
	}
	if len(msg.AppMetadata) > 0 {
		buf = appendBytesField(buf, 3, msg.AppMetadata)
	}
	if len(msg.DataBody) > 0 {
		buf = appendBytesField(buf, 1000, msg.DataBody)
	}
	return buf, nil
}

func marshalFlightDescriptor(desc FlightDescriptor) ([]byte, error) {
	buf := make([]byte, 0, len(desc.Cmd)+16)
	if desc.Type != 0 {
		buf = appendVarintField(buf, 1, uint64(desc.Type))
	}
	if len(desc.Cmd) > 0 {
		buf = appendBytesField(buf, 2, desc.Cmd)
	}
	for _, path := range desc.Path {
		buf = appendBytesField(buf, 3, []byte(path))
	}
	return buf, nil
}

func marshalTicket(ticket Ticket) ([]byte, error) {
	return appendBytesField(nil, 1, ticket.Ticket), nil
}

func marshalAny(typeURL string, value []byte) []byte {
	buf := appendBytesField(nil, 1, []byte(typeURL))
	return appendBytesField(buf, 2, value)
}

func unmarshalFlightInfo(raw []byte) (FlightInfo, error) {
	var out FlightInfo
	err := consumeMessage(raw, func(fieldNum int, wireType int, value []byte) error {
		switch {
		case fieldNum == 1 && wireType == wireBytes:
			v, _, err := consumeBytes(value)
			if err != nil {
				return err
			}
			out.Schema = append([]byte(nil), v...)
		case fieldNum == 2 && wireType == wireBytes:
			v, _, err := consumeBytes(value)
			if err != nil {
				return err
			}
			desc, err := unmarshalFlightDescriptor(v)
			if err != nil {
				return err
			}
			out.FlightDescriptor = &desc
		case fieldNum == 3 && wireType == wireBytes:
			v, _, err := consumeBytes(value)
			if err != nil {
				return err
			}
			ep, err := unmarshalFlightEndpoint(v)
			if err != nil {
				return err
			}
			out.Endpoint = append(out.Endpoint, ep)
		case fieldNum == 4 && wireType == wireVarint:
			v, _, err := consumeVarint(value)
			if err != nil {
				return err
			}
			out.TotalRecords = int64(v)
		case fieldNum == 5 && wireType == wireVarint:
			v, _, err := consumeVarint(value)
			if err != nil {
				return err
			}
			out.TotalBytes = int64(v)
		case fieldNum == 6 && wireType == wireVarint:
			v, _, err := consumeVarint(value)
			if err != nil {
				return err
			}
			out.Ordered = v != 0
		case fieldNum == 7 && wireType == wireBytes:
			v, _, err := consumeBytes(value)
			if err != nil {
				return err
			}
			out.AppMetadata = append([]byte(nil), v...)
		}
		return nil
	})
	return out, err
}

func unmarshalFlightDescriptor(raw []byte) (FlightDescriptor, error) {
	var out FlightDescriptor
	err := consumeMessage(raw, func(fieldNum int, wireType int, value []byte) error {
		switch {
		case fieldNum == 1 && wireType == wireVarint:
			v, _, err := consumeVarint(value)
			if err != nil {
				return err
			}
			out.Type = DescriptorType(v)
		case fieldNum == 2 && wireType == wireBytes:
			v, _, err := consumeBytes(value)
			if err != nil {
				return err
			}
			out.Cmd = append([]byte(nil), v...)
		case fieldNum == 3 && wireType == wireBytes:
			v, _, err := consumeBytes(value)
			if err != nil {
				return err
			}
			out.Path = append(out.Path, string(v))
		}
		return nil
	})
	return out, err
}

func unmarshalFlightEndpoint(raw []byte) (FlightEndpoint, error) {
	var out FlightEndpoint
	err := consumeMessage(raw, func(fieldNum int, wireType int, value []byte) error {
		switch {
		case fieldNum == 1 && wireType == wireBytes:
			v, _, err := consumeBytes(value)
			if err != nil {
				return err
			}
			ticket, err := unmarshalTicket(v)
			if err != nil {
				return err
			}
			out.Ticket = ticket
		case fieldNum == 2 && wireType == wireBytes:
			v, _, err := consumeBytes(value)
			if err != nil {
				return err
			}
			loc, err := unmarshalLocation(v)
			if err != nil {
				return err
			}
			out.Location = append(out.Location, loc)
		case fieldNum == 4 && wireType == wireBytes:
			v, _, err := consumeBytes(value)
			if err != nil {
				return err
			}
			out.AppMetadata = append([]byte(nil), v...)
		}
		return nil
	})
	return out, err
}

func unmarshalTicket(raw []byte) (Ticket, error) {
	var out Ticket
	err := consumeMessage(raw, func(fieldNum int, wireType int, value []byte) error {
		if fieldNum == 1 && wireType == wireBytes {
			v, _, err := consumeBytes(value)
			if err != nil {
				return err
			}
			out.Ticket = append([]byte(nil), v...)
		}
		return nil
	})
	return out, err
}

func unmarshalLocation(raw []byte) (Location, error) {
	var out Location
	err := consumeMessage(raw, func(fieldNum int, wireType int, value []byte) error {
		if fieldNum == 1 && wireType == wireBytes {
			v, _, err := consumeBytes(value)
			if err != nil {
				return err
			}
			out.URI = string(v)
		}
		return nil
	})
	return out, err
}

func unmarshalFlightData(raw []byte) (FlightData, error) {
	var out FlightData
	err := consumeMessage(raw, func(fieldNum int, wireType int, value []byte) error {
		switch {
		case fieldNum == 1 && wireType == wireBytes:
			v, _, err := consumeBytes(value)
			if err != nil {
				return err
			}
			desc, err := unmarshalFlightDescriptor(v)
			if err != nil {
				return err
			}
			out.FlightDescriptor = &desc
		case fieldNum == 2 && wireType == wireBytes:
			v, _, err := consumeBytes(value)
			if err != nil {
				return err
			}
			out.DataHeader = append([]byte(nil), v...)
		case fieldNum == 3 && wireType == wireBytes:
			v, _, err := consumeBytes(value)
			if err != nil {
				return err
			}
			out.AppMetadata = append([]byte(nil), v...)
		case fieldNum == 1000 && wireType == wireBytes:
			v, _, err := consumeBytes(value)
			if err != nil {
				return err
			}
			out.DataBody = append([]byte(nil), v...)
		}
		return nil
	})
	return out, err
}

func unmarshalActionResult(raw []byte) (ActionResult, error) {
	var out ActionResult
	err := consumeMessage(raw, func(fieldNum int, wireType int, value []byte) error {
		if fieldNum == 1 && wireType == wireBytes {
			v, _, err := consumeBytes(value)
			if err != nil {
				return err
			}
			out.Body = append([]byte(nil), v...)
		}
		return nil
	})
	return out, err
}

func unmarshalCreatePreparedStatementResult(raw []byte) (CreatePreparedStatementResult, error) {
	var out CreatePreparedStatementResult
	err := consumeMessage(raw, func(fieldNum int, wireType int, value []byte) error {
		if wireType != wireBytes {
			return nil
		}
		v, _, err := consumeBytes(value)
		if err != nil {
			return err
		}
		switch fieldNum {
		case 1:
			out.PreparedStatementHandle = append([]byte(nil), v...)
		case 2:
			out.DatasetSchema = append([]byte(nil), v...)
		case 3:
			out.ParameterSchema = append([]byte(nil), v...)
		}
		return nil
	})
	return out, err
}

func unmarshalPutResult(raw []byte) (PutResult, error) {
	var out PutResult
	err := consumeMessage(raw, func(fieldNum int, wireType int, value []byte) error {
		if fieldNum == 1 && wireType == wireBytes {
			v, _, err := consumeBytes(value)
			if err != nil {
				return err
			}
			out.AppMetadata = append([]byte(nil), v...)
		}
		return nil
	})
	return out, err
}

const (
	wireVarint = 0
	wireBytes  = 2
)

func appendVarintField(dst []byte, fieldNum int, value uint64) []byte {
	dst = appendVarint(dst, uint64(fieldNum<<3|wireVarint))
	return appendVarint(dst, value)
}

func appendBytesField(dst []byte, fieldNum int, value []byte) []byte {
	dst = appendVarint(dst, uint64(fieldNum<<3|wireBytes))
	dst = appendVarint(dst, uint64(len(value)))
	return append(dst, value...)
}

func appendVarint(dst []byte, value uint64) []byte {
	for value >= 0x80 {
		dst = append(dst, byte(value)|0x80)
		value >>= 7
	}
	return append(dst, byte(value))
}

func consumeTag(src []byte) (fieldNum int, wireType int, n int, err error) {
	v, n, err := consumeVarint(src)
	if err != nil {
		return 0, 0, 0, err
	}
	return int(v >> 3), int(v & 0x7), n, nil
}

func consumeVarint(src []byte) (uint64, int, error) {
	var value uint64
	for i := 0; i < len(src) && i < 10; i++ {
		b := src[i]
		value |= uint64(b&0x7f) << (7 * i)
		if b < 0x80 {
			return value, i + 1, nil
		}
	}
	return 0, 0, errors.New("invalid protobuf varint")
}

func consumeBytes(src []byte) ([]byte, int, error) {
	length, n, err := consumeVarint(src)
	if err != nil {
		return nil, 0, err
	}
	start := n
	end := start + int(length)
	if int(length) < 0 || end > len(src) {
		return nil, 0, errors.New("invalid protobuf bytes field")
	}
	return src[start:end], end, nil
}

func skipField(wireType int, src []byte) (int, error) {
	switch wireType {
	case wireVarint:
		_, n, err := consumeVarint(src)
		return n, err
	case wireBytes:
		_, n, err := consumeBytes(src)
		return n, err
	default:
		return 0, errors.New("unsupported protobuf wire type")
	}
}

func consumeMessage(src []byte, fn func(fieldNum int, wireType int, value []byte) error) error {
	for len(src) > 0 {
		fieldNum, wireType, n, err := consumeTag(src)
		if err != nil {
			return err
		}
		src = src[n:]
		if err := fn(fieldNum, wireType, src); err != nil {
			return err
		}
		m, err := skipField(wireType, src)
		if err != nil {
			return err
		}
		src = src[m:]
	}
	return nil
}
