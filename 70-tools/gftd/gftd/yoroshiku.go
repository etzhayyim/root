package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"
)

const (
	yoroshikuDuty = "勤労の義務"
	yoroshikuKPI  = "credits の獲得"
)

type yoroshikuEntry struct {
	Path      string `json:"path"`
	Nanoid    string `json:"nanoid,omitempty"`
	Name      string `json:"name,omitempty"`
	DutyOK    bool   `json:"duty_ok"`
	KPIOK     bool   `json:"kpi_ok"`
	Updated   bool   `json:"updated,omitempty"`
	ParseFail bool   `json:"parse_fail,omitempty"`
}

type yoroshikuReport struct {
	Total         int              `json:"total"`
	DutyOK        int              `json:"duty_ok"`
	KPIOK         int              `json:"kpi_ok"`
	BothOK        int              `json:"both_ok"`
	Updated       int              `json:"updated"`
	ParseFailures int              `json:"parse_failures"`
	Entries       []yoroshikuEntry `json:"entries"`
}

func runYoroshiku(args []string) error {
	fs := flag.NewFlagSet("yoroshiku", flag.ContinueOnError)
	dir := fs.String("dir", "projects", "directory to scan for magatama.jsonld")
	fix := fs.Bool("fix", false, "apply missing duty/KPI to magatama.jsonld files")
	jsonOut := fs.Bool("json", false, "output as JSON")
	onlyMissing := fs.Bool("only-missing", false, "show only missing entries in text mode")
	limit := fs.Int("limit", 100, "max rows in text mode (0 = unlimited)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	var report yoroshikuReport
	if err := filepath.Walk(*dir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		if info.IsDir() || info.Name() != "magatama.jsonld" {
			return nil
		}

		report.Total++
		entry := yoroshikuEntry{Path: path}

		data, readErr := os.ReadFile(path)
		if readErr != nil {
			entry.ParseFail = true
			report.ParseFailures++
			report.Entries = append(report.Entries, entry)
			return nil
		}

		var doc map[string]any
		if err := json.Unmarshal(data, &doc); err != nil {
			entry.ParseFail = true
			report.ParseFailures++
			report.Entries = append(report.Entries, entry)
			return nil
		}

		entry.Nanoid = stringAny(doc["nanoid"])
		entry.Name = stringAny(doc["name"])

		duties, dutiesChanged, dutyOK := ensureStringArrayValue(doc, "duties", yoroshikuDuty)
		if duties != nil {
			doc["duties"] = duties
		}
		kpis, kpiChanged, kpiOK := ensureStringArrayValue(doc, "kpi", yoroshikuKPI)
		if kpis != nil {
			doc["kpi"] = kpis
		}

		entry.DutyOK = dutyOK
		entry.KPIOK = kpiOK
		if dutyOK {
			report.DutyOK++
		}
		if kpiOK {
			report.KPIOK++
		}
		if dutyOK && kpiOK {
			report.BothOK++
		}

		if *fix && (dutiesChanged || kpiChanged) {
			out, err := json.MarshalIndent(doc, "", "  ")
			if err == nil {
				out = append(out, '\n')
				if os.WriteFile(path, out, 0o644) == nil {
					entry.Updated = true
					report.Updated++
					entry.DutyOK = true
					entry.KPIOK = true
				}
			}
		}

		report.Entries = append(report.Entries, entry)
		return nil
	}); err != nil {
		return err
	}

	sort.Slice(report.Entries, func(i, j int) bool { return report.Entries[i].Path < report.Entries[j].Path })

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	fmt.Printf("gftd yoroshiku — Magatama KPI / Duty Check\n\n")
	fmt.Printf("  total apps:      %d\n", report.Total)
	fmt.Printf("  duty ok:         %d\n", report.DutyOK)
	fmt.Printf("  kpi ok:          %d\n", report.KPIOK)
	fmt.Printf("  both ok:         %d\n", report.BothOK)
	fmt.Printf("  updated:         %d\n", report.Updated)
	fmt.Printf("  parse failures:  %d\n", report.ParseFailures)

	rows := make([]yoroshikuEntry, 0, len(report.Entries))
	for _, e := range report.Entries {
		if *onlyMissing && e.DutyOK && e.KPIOK && !e.ParseFail {
			continue
		}
		rows = append(rows, e)
	}

	if *limit > 0 && len(rows) > *limit {
		rows = rows[:*limit]
	}
	if len(rows) == 0 {
		return nil
	}

	fmt.Printf("\n  entries:\n")
	for _, e := range rows {
		status := "ok"
		if e.ParseFail {
			status = "parse_fail"
		} else if !e.DutyOK && !e.KPIOK {
			status = "missing:duty+kpi"
		} else if !e.DutyOK {
			status = "missing:duty"
		} else if !e.KPIOK {
			status = "missing:kpi"
		}
		if e.Updated {
			status += " (updated)"
		}
		fmt.Printf("  - %s [%s]\n", e.Path, status)
	}

	return nil
}

func ensureStringArrayValue(doc map[string]any, key, value string) ([]any, bool, bool) {
	raw, ok := doc[key]
	if !ok {
		return []any{value}, true, true
	}

	arr, ok := raw.([]any)
	if !ok {
		if s, ok := raw.(string); ok {
			if s == value {
				return []any{s}, true, true
			}
			return []any{s, value}, true, true
		}
		return []any{value}, true, true
	}

	found := false
	for _, v := range arr {
		if stringAny(v) == value {
			found = true
			break
		}
	}
	if found {
		return arr, false, true
	}
	return append(arr, value), true, true
}

func stringAny(v any) string {
	s, _ := v.(string)
	return s
}
