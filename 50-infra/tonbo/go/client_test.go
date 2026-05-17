package lancedbrest

import "testing"

func TestMarshalJSONBodyColumns(t *testing.T) {
	raw, err := marshalJSONBody(map[string]any{
		"columns": [][]string{{"connection_id"}},
		"limit":   1,
		"offset":  0,
	})
	if err != nil {
		t.Fatalf("marshalJSONBody: %v", err)
	}
	t.Log(string(raw))
}
