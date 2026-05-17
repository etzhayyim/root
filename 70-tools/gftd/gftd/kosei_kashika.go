// kosei_kashika.go — HTML visualization for gftd kosei
//
// Generates an interactive HTML dashboard showing:
//   - Tier distribution bar chart + system η
//   - Per-app table with tier badges, sortable/filterable
//   - Tier transition diagram (T1→T2→T3 flow)
//
// Output: temp HTML file, auto-opened in browser.
package main

import (
	"flag"
	"fmt"
	"html"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
	"time"
)

func runKoseiKashika(args []string) error {
	fs := flag.NewFlagSet("kosei kashika", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root")
	dataDir := fs.String("data-dir", "", "data directory")
	outFile := fs.String("out", "", "output HTML file (default: temp file)")
	noOpen := fs.Bool("no-open", false, "do not open browser")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot, dDir, err := koseiResolveRoots(*workspaceDir, *dataDir)
	if err != nil {
		return err
	}

	states, err := koseiLoadStates(wsRoot, dDir)
	if err != nil {
		return err
	}

	htmlContent := buildKoseiHTML(states)

	outPath := *outFile
	if outPath == "" {
		tmp, err := os.CreateTemp("", "kosei-*.html")
		if err != nil {
			return fmt.Errorf("create temp: %w", err)
		}
		outPath = tmp.Name()
		tmp.Close()
	}

	if err := os.WriteFile(outPath, []byte(htmlContent), 0644); err != nil {
		return fmt.Errorf("write html: %w", err)
	}

	fmt.Fprintf(os.Stderr, "kosei kashika: %s\n", outPath)

	if !*noOpen {
		koseiOpenBrowser(outPath)
	}
	return nil
}

func koseiOpenBrowser(path string) {
	absPath, _ := filepath.Abs(path)
	url := "file://" + absPath
	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "darwin":
		cmd = exec.Command("open", url)
	case "linux":
		cmd = exec.Command("xdg-open", url)
	case "windows":
		cmd = exec.Command("cmd", "/c", "start", url)
	default:
		fmt.Fprintf(os.Stderr, "open browser: %s\n", url)
		return
	}
	_ = cmd.Start()
}

func buildKoseiHTML(states []koseiAppState) string {
	counts := map[string]int{"T1": 0, "T2": 0, "T3": 0, "?": 0}
	for _, s := range states {
		if _, ok := counts[s.Tier]; ok {
			counts[s.Tier]++
		} else {
			counts["?"]++
		}
	}
	total := len(states)
	systemEta := koseiSystemEta(states)

	pct := func(tier string) float64 {
		if total == 0 {
			return 0
		}
		return float64(counts[tier]) / float64(total) * 100
	}

	// Sort states for table display
	sorted := make([]koseiAppState, len(states))
	copy(sorted, states)
	sort.Slice(sorted, func(i, j int) bool {
		if sorted[i].Tier != sorted[j].Tier {
			return sorted[i].Tier < sorted[j].Tier
		}
		return sorted[i].Nanoid < sorted[j].Nanoid
	})

	// Build rows HTML
	var rowsHTML strings.Builder
	for _, s := range sorted {
		tierClass := map[string]string{
			"T1": "badge-t1",
			"T2": "badge-t2",
			"T3": "badge-t3",
			"?":  "badge-unknown",
		}[s.Tier]
		if tierClass == "" {
			tierClass = "badge-unknown"
		}
		etaStr := "—"
		if s.Efficiency > 0 {
			etaStr = fmt.Sprintf("%.3f", s.Efficiency)
		}
		notes := html.EscapeString(s.Notes)
		name := html.EscapeString(s.Name)
		desc := html.EscapeString(truncStr(s.Description, 80))

		rowsHTML.WriteString(fmt.Sprintf(`
    <tr data-tier="%s">
      <td class="col-nanoid">%s</td>
      <td class="col-name" title="%s">%s</td>
      <td class="col-tier"><span class="badge %s">%s</span></td>
      <td class="col-eta">%s</td>
      <td class="col-by">%s</td>
      <td class="col-notes" title="%s">%s</td>
    </tr>`,
			html.EscapeString(s.Tier),
			html.EscapeString(s.Nanoid),
			desc, name,
			tierClass, s.Tier,
			etaStr,
			html.EscapeString(s.AssignedBy),
			notes, truncStr(s.Notes, 50),
		))
	}

	generatedAt := time.Now().UTC().Format("2006-01-02 15:04:05 UTC")

	return fmt.Sprintf(`<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>gftd kosei — Project Configuration</title>
<style>
  :root {
    --t1: #4ade80; --t1-bg: #052e16;
    --t2: #60a5fa; --t2-bg: #172554;
    --t3: #f97316; --t3-bg: #431407;
    --un: #94a3b8; --un-bg: #1e293b;
    --bg: #0f172a; --surface: #1e293b; --border: #334155;
    --text: #e2e8f0; --muted: #94a3b8;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'JetBrains Mono', 'Fira Code', monospace; background: var(--bg); color: var(--text); padding: 24px; }
  h1 { font-size: 1.4rem; font-weight: 700; margin-bottom: 4px; }
  .subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 24px; }

  /* Summary cards */
  .cards { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 24px; }
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 20px; min-width: 140px; }
  .card-label { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
  .card-value { font-size: 1.6rem; font-weight: 700; }
  .card-sub { font-size: 0.75rem; color: var(--muted); margin-top: 2px; }

  /* Distribution bar */
  .dist-section { margin-bottom: 24px; }
  .dist-section h2 { font-size: 0.9rem; color: var(--muted); margin-bottom: 12px; }
  .dist-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; font-size: 0.82rem; }
  .dist-label { width: 120px; color: var(--muted); }
  .dist-bar-wrap { flex: 1; background: var(--surface); border-radius: 4px; height: 18px; overflow: hidden; }
  .dist-bar { height: 100%%; border-radius: 4px; transition: width 0.3s; }
  .bar-t1 { background: var(--t1); }
  .bar-t2 { background: var(--t2); }
  .bar-t3 { background: var(--t3); }
  .bar-un { background: var(--un); }
  .dist-count { width: 80px; text-align: right; }
  .dist-pct { width: 50px; text-align: right; color: var(--muted); }

  /* Filter controls */
  .controls { display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; align-items: center; }
  .controls input { background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 6px 10px; border-radius: 6px; font-size: 0.82rem; width: 220px; outline: none; }
  .controls input:focus { border-color: var(--t1); }
  .filter-btn { background: var(--surface); border: 1px solid var(--border); color: var(--muted); padding: 5px 12px; border-radius: 6px; cursor: pointer; font-size: 0.8rem; }
  .filter-btn.active { color: var(--text); border-color: var(--text); }
  .filter-btn[data-tier="T1"].active { border-color: var(--t1); color: var(--t1); }
  .filter-btn[data-tier="T2"].active { border-color: var(--t2); color: var(--t2); }
  .filter-btn[data-tier="T3"].active { border-color: var(--t3); color: var(--t3); }

  /* Table */
  .table-wrap { overflow-x: auto; }
  table { width: 100%%; border-collapse: collapse; font-size: 0.8rem; }
  th { background: var(--surface); color: var(--muted); padding: 8px 10px; text-align: left; border-bottom: 1px solid var(--border); cursor: pointer; user-select: none; white-space: nowrap; }
  th:hover { color: var(--text); }
  td { padding: 7px 10px; border-bottom: 1px solid #1e293b; vertical-align: middle; white-space: nowrap; }
  tr:hover td { background: #1e293b88; }
  tr.hidden { display: none; }

  .col-nanoid { font-family: monospace; color: var(--muted); }
  .col-name { max-width: 200px; overflow: hidden; text-overflow: ellipsis; }
  .col-eta { text-align: right; font-variant-numeric: tabular-nums; }
  .col-notes { max-width: 200px; overflow: hidden; text-overflow: ellipsis; color: var(--muted); font-size: 0.75rem; }

  /* Badges */
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
  .badge-t1 { background: var(--t1-bg); color: var(--t1); border: 1px solid var(--t1); }
  .badge-t2 { background: var(--t2-bg); color: var(--t2); border: 1px solid var(--t2); }
  .badge-t3 { background: var(--t3-bg); color: var(--t3); border: 1px solid var(--t3); }
  .badge-unknown { background: var(--un-bg); color: var(--un); border: 1px solid var(--un); }

  /* Tier legend */
  .legend { display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 20px; font-size: 0.78rem; }
  .legend-item { display: flex; align-items: center; gap: 6px; }
  .legend-dot { width: 10px; height: 10px; border-radius: 50%%; }

  .footer { margin-top: 20px; font-size: 0.72rem; color: var(--muted); }
</style>
</head>
<body>

<h1>gftd kosei — Project Configuration (構成)</h1>
<p class="subtitle">Execution tier management for App components · Generated %s</p>

<!-- Summary cards -->
<div class="cards">
  <div class="card">
    <div class="card-label">Total Apps</div>
    <div class="card-value">%d</div>
    <div class="card-sub">App components</div>
  </div>
  <div class="card">
    <div class="card-label">System η</div>
    <div class="card-value" style="color:var(--t1)">%.3f</div>
    <div class="card-sub">weighted avg efficiency</div>
  </div>
  <div class="card">
    <div class="card-label">T1 Shared Executor</div>
    <div class="card-value" style="color:var(--t1)">%d</div>
    <div class="card-sub">η=0.667  mitama + primitives</div>
  </div>
  <div class="card">
    <div class="card-label">T2 App Worker</div>
    <div class="card-value" style="color:var(--t2)">%d</div>
    <div class="card-sub">η=0.500  product UI/UX worker</div>
  </div>
  <div class="card">
    <div class="card-label">T3 Infra Worker</div>
    <div class="card-value" style="color:var(--t3)">%d</div>
    <div class="card-sub">η=0.910  platform infrastructure</div>
  </div>
  <div class="card">
    <div class="card-label">Unassigned</div>
    <div class="card-value" style="color:var(--un)">%d</div>
    <div class="card-sub">run: gftd kosei suggest</div>
  </div>
</div>

<!-- Distribution -->
<div class="dist-section">
  <h2>TIER DISTRIBUTION</h2>
  <div class="dist-row">
    <div class="dist-label">T1 Shared Executor</div>
    <div class="dist-bar-wrap"><div class="dist-bar bar-t1" style="width:%.1f%%"></div></div>
    <div class="dist-count">%d apps</div>
    <div class="dist-pct">%.0f%%</div>
  </div>
  <div class="dist-row">
    <div class="dist-label">T2 App Worker</div>
    <div class="dist-bar-wrap"><div class="dist-bar bar-t2" style="width:%.1f%%"></div></div>
    <div class="dist-count">%d apps</div>
    <div class="dist-pct">%.0f%%</div>
  </div>
  <div class="dist-row">
    <div class="dist-label">T3 Infra Worker</div>
    <div class="dist-bar-wrap"><div class="dist-bar bar-t3" style="width:%.1f%%"></div></div>
    <div class="dist-count">%d apps</div>
    <div class="dist-pct">%.0f%%</div>
  </div>
  <div class="dist-row">
    <div class="dist-label">Unassigned</div>
    <div class="dist-bar-wrap"><div class="dist-bar bar-un" style="width:%.1f%%"></div></div>
    <div class="dist-count">%d apps</div>
    <div class="dist-pct">%.0f%%</div>
  </div>
</div>

<!-- Filter controls -->
<div class="controls">
  <input type="text" id="search" placeholder="Search nanoid or name..." oninput="filterTable()">
  <button class="filter-btn active" data-tier="ALL" onclick="setTierFilter('ALL', this)">All</button>
  <button class="filter-btn" data-tier="T1" onclick="setTierFilter('T1', this)">T1</button>
  <button class="filter-btn" data-tier="T2" onclick="setTierFilter('T2', this)">T2</button>
  <button class="filter-btn" data-tier="T3" onclick="setTierFilter('T3', this)">T3</button>
  <button class="filter-btn" data-tier="?" onclick="setTierFilter('?', this)">Unassigned</button>
</div>

<!-- App table -->
<div class="table-wrap">
  <table id="app-table">
    <thead>
      <tr>
        <th onclick="sortTable(0)">NANOID ↕</th>
        <th onclick="sortTable(1)">NAME ↕</th>
        <th onclick="sortTable(2)">TIER ↕</th>
        <th onclick="sortTable(3)">η ↕</th>
        <th>BY</th>
        <th>NOTES</th>
      </tr>
    </thead>
    <tbody id="table-body">
%s
    </tbody>
  </table>
</div>
<div id="row-count" style="font-size:0.78rem;color:var(--muted);margin-top:8px;"></div>

<div class="footer">
  gftd kosei kashika · %s · Run <code>gftd kosei suggest --apply</code> to assign missing tiers
</div>

<script>
let tierFilter = 'ALL';
let sortCol = -1;
let sortAsc = true;

function filterTable() {
  const q = document.getElementById('search').value.toLowerCase();
  const rows = document.querySelectorAll('#table-body tr');
  let visible = 0;
  rows.forEach(row => {
    const nanoid = row.cells[0].textContent.toLowerCase();
    const name = row.cells[1].textContent.toLowerCase();
    const tier = row.dataset.tier;
    const matchSearch = !q || nanoid.includes(q) || name.includes(q);
    const matchTier = tierFilter === 'ALL' || tier === tierFilter;
    if (matchSearch && matchTier) { row.classList.remove('hidden'); visible++; }
    else { row.classList.add('hidden'); }
  });
  document.getElementById('row-count').textContent = visible + ' app(s) shown';
}

function setTierFilter(tier, btn) {
  tierFilter = tier;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  filterTable();
}

function sortTable(col) {
  if (sortCol === col) sortAsc = !sortAsc;
  else { sortCol = col; sortAsc = true; }
  const tbody = document.getElementById('table-body');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  rows.sort((a, b) => {
    const av = a.cells[col].textContent.trim();
    const bv = b.cells[col].textContent.trim();
    const cmp = av.localeCompare(bv, undefined, {numeric: true});
    return sortAsc ? cmp : -cmp;
  });
  rows.forEach(r => tbody.appendChild(r));
}

// Initial count
window.onload = () => filterTable();
</script>
</body>
</html>`,
		generatedAt,
		total, systemEta,
		counts["T1"], counts["T2"], counts["T3"], counts["?"],
		pct("T1"), counts["T1"], pct("T1"),
		pct("T2"), counts["T2"], pct("T2"),
		pct("T3"), counts["T3"], pct("T3"),
		pct("?"), counts["?"], pct("?"),
		rowsHTML.String(),
		generatedAt,
	)
}
