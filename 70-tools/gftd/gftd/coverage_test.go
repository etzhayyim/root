package main

import (
	"bytes"
	"testing"
)

func TestParseRustTestJSON(t *testing.T) {
	input := []byte(`{"type":"suite","event":"started","test_count":5}
{"type":"test","event":"ok","name":"tests::test_one","exec_time":0.001}
{"type":"test","event":"ok","name":"tests::test_two","exec_time":0.002}
{"type":"test","event":"failed","name":"tests::test_three","exec_time":0.003}
{"type":"test","event":"ok","name":"tests::test_four","exec_time":0.001}
{"type":"test","event":"ignored","name":"tests::test_five"}
{"type":"suite","event":"failed","passed":3,"failed":1,"ignored":1,"measured":0,"filtered_out":0,"exec_time":0.1}
`)
	var entry coverageEntry
	parseRustTestJSON(input, &entry)
	if entry.PassCount != 3 {
		t.Errorf("PassCount = %d, want 3", entry.PassCount)
	}
	if entry.FailCount != 1 {
		t.Errorf("FailCount = %d, want 1", entry.FailCount)
	}
	if entry.SkipCount != 1 {
		t.Errorf("SkipCount = %d, want 1", entry.SkipCount)
	}
	if entry.TestCount != 5 {
		t.Errorf("TestCount = %d, want 5", entry.TestCount)
	}
}

func TestParseGoTestJSON(t *testing.T) {
	input := []byte(`{"Time":"2026-03-25T10:00:00Z","Action":"run","Package":"pkg","Test":"TestOne"}
{"Time":"2026-03-25T10:00:01Z","Action":"pass","Package":"pkg","Test":"TestOne","Elapsed":0.5}
{"Time":"2026-03-25T10:00:01Z","Action":"run","Package":"pkg","Test":"TestTwo"}
{"Time":"2026-03-25T10:00:02Z","Action":"fail","Package":"pkg","Test":"TestTwo","Elapsed":0.3}
{"Time":"2026-03-25T10:00:02Z","Action":"run","Package":"pkg","Test":"TestThree"}
{"Time":"2026-03-25T10:00:03Z","Action":"skip","Package":"pkg","Test":"TestThree","Elapsed":0.0}
{"Time":"2026-03-25T10:00:03Z","Action":"pass","Package":"pkg"}
`)
	var entry coverageEntry
	parseGoTestJSON(input, &entry)
	if entry.PassCount != 1 {
		t.Errorf("PassCount = %d, want 1", entry.PassCount)
	}
	if entry.FailCount != 1 {
		t.Errorf("FailCount = %d, want 1", entry.FailCount)
	}
	if entry.SkipCount != 1 {
		t.Errorf("SkipCount = %d, want 1", entry.SkipCount)
	}
	if entry.TestCount != 3 {
		t.Errorf("TestCount = %d, want 3", entry.TestCount)
	}
}

func TestParseVitestJSON(t *testing.T) {
	input := []byte(`some output before json
{"numTotalTests":10,"numPassedTests":8,"numFailedTests":1,"numPendingTests":1,"testResults":[]}
`)
	var entry coverageEntry
	parseVitestJSON(input, &entry)
	if entry.TestCount != 10 {
		t.Errorf("TestCount = %d, want 10", entry.TestCount)
	}
	if entry.PassCount != 8 {
		t.Errorf("PassCount = %d, want 8", entry.PassCount)
	}
	if entry.FailCount != 1 {
		t.Errorf("FailCount = %d, want 1", entry.FailCount)
	}
	if entry.SkipCount != 1 {
		t.Errorf("SkipCount = %d, want 1", entry.SkipCount)
	}
}

func TestExtractJSON(t *testing.T) {
	tests := []struct {
		name  string
		input string
		want  string
	}{
		{"pure json", `{"a":1}`, `{"a":1}`},
		{"prefixed", `output\n{"a":1}\nmore`, `{"a":1}`},
		{"nested", `pre {"a":{"b":2}} post`, `{"a":{"b":2}}`},
		{"empty", `no json here`, ""},
		{"braces in strings", `{"name":"test {foo}","count":5}`, `{"name":"test {foo}","count":5}`},
		{"escaped quotes", `{"a":"val\"ue","b":1}`, `{"a":"val\"ue","b":1}`},
		{"vitest-like", `{"numTotalTests":10,"testResults":[{"fullName":"test {inline}"}]}`, `{"numTotalTests":10,"testResults":[{"fullName":"test {inline}"}]}`},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := extractJSON([]byte(tt.input))
			if tt.want == "" {
				if got != nil {
					t.Errorf("want nil, got %q", string(got))
				}
				return
			}
			if !bytes.Equal(got, []byte(tt.want)) {
				t.Errorf("got %q, want %q", string(got), tt.want)
			}
		})
	}
}

func TestParseRustTestText(t *testing.T) {
	input := []byte(`
running 3 tests
test tests::alpha ... ok
test tests::beta ... ok
test tests::gamma ... FAILED

test result: FAILED. 2 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.01s

running 5 tests
test more::a ... ok
test more::b ... ok
test more::c ... ok
test more::d ... ignored
test more::e ... ok

test result: ok. 3 passed; 0 failed; 1 ignored; 0 measured; 0 filtered out; finished in 0.02s
`)
	var entry coverageEntry
	parseRustTestText(input, &entry)
	if entry.PassCount != 5 {
		t.Errorf("PassCount = %d, want 5", entry.PassCount)
	}
	if entry.FailCount != 1 {
		t.Errorf("FailCount = %d, want 1", entry.FailCount)
	}
	if entry.SkipCount != 1 {
		t.Errorf("SkipCount = %d, want 1", entry.SkipCount)
	}
	if entry.TestCount != 7 {
		t.Errorf("TestCount = %d, want 7", entry.TestCount)
	}
}

func TestTruncateStr(t *testing.T) {
	if got := truncateStr("hello", 10); got != "hello" {
		t.Errorf("got %q", got)
	}
	if got := truncateStr("hello world", 5); got != "hello..." {
		t.Errorf("got %q", got)
	}
}
