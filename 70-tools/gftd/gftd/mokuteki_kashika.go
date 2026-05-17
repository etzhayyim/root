package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strings"
)

// runMokutekiKashika renders the mokuteki report as a visual output.
func runMokutekiKashika(args []string) error {
	fs := flag.NewFlagSet("mokuteki kashika", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	format := fs.String("format", "html", "output format: terminal|html|svg|dot|json")
	output := fs.String("output", "", "output file path (default: stdout, html: auto-open)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot, err := resolveShannonRoot(*workspaceDir)
	if err != nil {
		return err
	}

	report := buildMokutekiReport(wsRoot)

	switch strings.ToLower(strings.TrimSpace(*format)) {
	case "terminal":
		printMokutekiText(report)
		return nil
	case "json":
		buf, err := json.MarshalIndent(report, "", "  ")
		if err != nil {
			return err
		}
		return kashikaWriteOutput(*output, append(buf, '\n'))
	case "dot":
		dot := mokutekiKashikaDot(report)
		return kashikaWriteOutput(*output, []byte(dot))
	case "svg":
		dot := mokutekiKashikaDot(report)
		svg, err := kashikaGraphviz("svg", dot)
		if err != nil {
			return err
		}
		return kashikaWriteOutput(*output, svg)
	case "html":
		html := mokutekiKashikaHTML(report)
		if *output == "" {
			// Write to temp file and auto-open in browser
			tmpFile := "/tmp/mokuteki-kashika.html"
			if err := kashikaWriteOutput(tmpFile, []byte(html)); err != nil {
				return err
			}
			fmt.Fprintf(os.Stderr, "wrote %s\n", tmpFile)
			openBrowser(tmpFile)
			return nil
		}
		return kashikaWriteOutput(*output, []byte(html))
	default:
		return fmt.Errorf("unknown format: %s (available: terminal, html, svg, dot, json)", *format)
	}
}

// mokutekiKashikaDot generates Graphviz DOT for the 4-layer framework.
func mokutekiKashikaDot(r *mokutekiReport) string {
	var b strings.Builder
	b.WriteString("digraph mokuteki {\n")
	b.WriteString("  rankdir=TB;\n")
	b.WriteString("  node [shape=record, fontname=\"Helvetica\", fontsize=11];\n")
	b.WriteString("  edge [fontname=\"Helvetica\", fontsize=9];\n")
	b.WriteString(fmt.Sprintf("  labelloc=t; label=\"mokuteki: %s\\n%s — Score: %d/%d\";\n",
		r.Mokuteki, r.Rank.Name, r.TotalScore, r.MaxScore))
	b.WriteString("\n")

	// Layers as subgraphs
	for _, l := range r.Layers {
		color := dotLayerColor(l.Score)
		b.WriteString(fmt.Sprintf("  subgraph cluster_%s {\n", l.ID))
		b.WriteString(fmt.Sprintf("    label=\"Layer %s: %s (%.0f)\";\n", l.ID, l.NameJP, l.Score))
		b.WriteString(fmt.Sprintf("    style=filled; color=\"%s\"; fillcolor=\"%s20\";\n", color, color))
		for _, c := range l.Components {
			nodeID := fmt.Sprintf("%s_%s", l.ID, dotSafeID(c.Name))
			cColor := dotLayerColor(c.Score)
			b.WriteString(fmt.Sprintf("    %s [label=\"{%s|%.0f}\" color=\"%s\"];\n", nodeID, dotEscape(c.Name), c.Score, cColor))
		}
		b.WriteString("  }\n\n")
	}

	// Layer flow edges: A → B → C → D
	layerIDs := []string{"A", "B", "C", "D"}
	for i := 0; i < len(layerIDs)-1; i++ {
		fromL := findLayer(r.Layers, layerIDs[i])
		toL := findLayer(r.Layers, layerIDs[i+1])
		if fromL != nil && toL != nil && len(fromL.Components) > 0 && len(toL.Components) > 0 {
			fromNode := fmt.Sprintf("%s_%s", fromL.ID, dotSafeID(fromL.Components[0].Name))
			toNode := fmt.Sprintf("%s_%s", toL.ID, dotSafeID(toL.Components[0].Name))
			labels := []string{"A→B: 依存→不確実性", "B→C: 不確実性→制御", "C→D: 制御→実装"}
			b.WriteString(fmt.Sprintf("  %s -> %s [label=\"%s\" style=dashed color=\"#666666\"];\n", fromNode, toNode, labels[i]))
		}
	}

	// Well-Being nodes
	b.WriteString("\n  // Well-Becoming Axes\n")
	b.WriteString("  subgraph cluster_wellbeing {\n")
	b.WriteString("    label=\"Well-Becoming\";\n")
	b.WriteString("    style=rounded; color=\"#333333\";\n")
	for _, a := range r.Axes {
		nodeID := "wb_" + dotSafeID(a.Name)
		color := dotLayerColor(a.Score)
		b.WriteString(fmt.Sprintf("    %s [label=\"{%s|%.0f pts}\" shape=Mrecord color=\"%s\"];\n",
			nodeID, dotEscape(a.Name), a.Score, color))
	}
	b.WriteString("  }\n")

	b.WriteString("}\n")
	return b.String()
}

func findLayer(layers []mokutekiLayer, id string) *mokutekiLayer {
	for i := range layers {
		if layers[i].ID == id {
			return &layers[i]
		}
	}
	return nil
}

func dotLayerColor(score float64) string {
	if score >= 80 {
		return "#22C55E"
	} else if score >= 60 {
		return "#3B82F6"
	} else if score >= 40 {
		return "#FF8C00"
	}
	return "#EF4444"
}

func dotSafeID(s string) string {
	r := strings.NewReplacer(
		" ", "_", "(", "", ")", "", "/", "_", ".", "_",
		"-", "_", "+", "_", ",", "_", ":", "_",
	)
	return r.Replace(s)
}

func dotEscape(s string) string {
	s = strings.ReplaceAll(s, "\"", "\\\"")
	s = strings.ReplaceAll(s, "<", "\\<")
	s = strings.ReplaceAll(s, ">", "\\>")
	return s
}

// mokutekiKashikaHTML generates a self-contained HTML dashboard.
func mokutekiKashikaHTML(r *mokutekiReport) string {
	jsonData, _ := json.Marshal(r)

	return fmt.Sprintf(`<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>mokuteki (目的) — %s</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; background: #0a0a0a; color: #e0e0e0; padding: 24px; max-width: 1400px; margin: 0 auto; }
h1 { font-size: 1.4em; margin-bottom: 4px; }
h2 { font-size: 1.1em; color: #888; margin-bottom: 16px; }
.rank-box { background: linear-gradient(135deg, #1a1a2e, #16213e); border: 2px solid %s; border-radius: 12px; padding: 24px; text-align: center; margin: 20px 0; }
.rank-name { font-size: 2.2em; font-weight: bold; color: %s; }
.rank-score { font-size: 1.4em; color: #aaa; margin-top: 8px; }
.principle { font-size: 0.85em; color: #666; margin: 8px 0 20px 0; font-style: italic; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin: 20px 0; }
.layer-card { background: #111; border-radius: 8px; padding: 16px; border-left: 4px solid; }
.layer-card h3 { font-size: 1em; margin-bottom: 12px; }
.check-row { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; font-size: 0.85em; cursor: pointer; border-radius: 4px; padding: 4px 6px; }
.check-row:hover { background: #1a1a1a; }
.check-row.has-data::after { content: '▸'; margin-left: 6px; color: #555; font-size: 0.7em; }
.check-row.has-data.open::after { content: '▾'; }
.check-name { flex: 1; }
.bar-bg { width: 80px; height: 8px; background: #222; border-radius: 4px; overflow: hidden; margin: 0 8px; }
.bar-fill { height: 100%%; border-radius: 4px; }
.check-score { width: 40px; text-align: right; font-variant-numeric: tabular-nums; }
.detail-panel { display: none; margin: 8px 0; padding: 12px; background: #0d0d0d; border: 1px solid #222; border-radius: 6px; overflow-x: auto; }
.detail-panel.open { display: block; }
.wb-section { margin: 24px 0; }
.wb-row { display: flex; align-items: center; padding: 6px 0; }
.wb-name { width: 200px; font-size: 0.9em; }
.wb-bar-bg { flex: 1; height: 12px; background: #222; border-radius: 6px; overflow: hidden; margin: 0 12px; }
.wb-bar-fill { height: 100%%; border-radius: 6px; }
.wb-score { width: 60px; text-align: right; font-size: 0.9em; }
.diag { margin: 20px 0; padding: 16px; background: #111; border-radius: 8px; }
.diag-item { padding: 4px 0; font-size: 0.85em; font-family: monospace; }
.diag-item.critical { color: #EF4444; }
.diag-item.improve { color: #FF8C00; }
.diag-item.wellbeing { color: #3B82F6; }
.diag-item.next { color: #22C55E; }
/* DSM matrix */
.dsm-matrix { border-collapse: collapse; font-size: 0.7em; font-family: monospace; }
.dsm-matrix th, .dsm-matrix td { width: 22px; height: 22px; text-align: center; border: 1px solid #1a1a1a; padding: 0; }
.dsm-matrix th { background: #1a1a1a; color: #888; font-weight: normal; max-width: 22px; overflow: hidden; }
.dsm-matrix td.cell-zero { background: #0a0a0a; }
.dsm-matrix td.cell-diag { background: #111; color: #333; }
.dsm-matrix td.cell-hit { background: #22C55E33; color: #22C55E; font-weight: bold; }
.dsm-stats { display: flex; gap: 24px; margin: 12px 0; font-size: 0.85em; }
.dsm-stats span { color: #888; }
.dsm-stats b { color: #e0e0e0; }
.dsm-cluster { display: inline-block; background: #1a1a2e; border: 1px solid #2a2a4e; border-radius: 4px; padding: 4px 8px; margin: 4px; font-size: 0.8em; }
.dsm-cycle { font-family: monospace; font-size: 0.8em; color: #EF4444; padding: 2px 0; }
</style>
</head>
<body>
<h1>mokuteki (目的)</h1>
<h2>%s</h2>
<p class="principle">%s</p>
<p style="font-size:0.8em;color:#555;">apps: %d, edges: %d, evaluated: %s</p>

<div class="rank-box">
  <div class="rank-name">%s</div>
  <div class="rank-score">%d / %d</div>
</div>

<div class="grid" id="layers"></div>

<div class="wb-section">
  <h3 style="margin-bottom:12px;">Well-Becoming (5軸)</h3>
  <div id="wellbeing"></div>
</div>

<div class="diag" id="diagnosis"></div>

<script>
const data = %s;

function barColor(score) {
  if (score >= 80) return '#22C55E';
  if (score >= 60) return '#3B82F6';
  if (score >= 40) return '#FF8C00';
  return '#EF4444';
}

// --- DSM detail renderer ---
function renderDSMDetail(dsm) {
  if (!dsm || !dsm.apps) return '<p style="color:#555">No DSM data</p>';
  let html = '';

  // Stats bar
  html += '<div class="dsm-stats">';
  html += '<span>Size: <b>' + dsm.size + '×' + dsm.size + '</b></span>';
  html += '<span>Bandwidth: <b>' + dsm.bandwidth + '</b></span>';
  html += '<span>Clusters: <b>' + (dsm.clusters||[]).length + '</b></span>';
  html += '<span>Cycles: <b>' + (dsm.cycles||[]).length + '</b></span>';
  html += '<span>Score: <b>' + dsm.score.toFixed(1) + '</b></span>';
  html += '</div>';

  // Matrix (cap at 50 for readability)
  const n = Math.min(dsm.apps.length, 50);
  if (n > 0 && dsm.matrix) {
    html += '<div style="overflow-x:auto;margin:8px 0"><table class="dsm-matrix"><tr><th></th>';
    for (let j = 0; j < n; j++) {
      const abbr = dsm.apps[j].length > 3 ? dsm.apps[j].substring(0,3) : dsm.apps[j];
      html += '<th title="' + dsm.apps[j] + '">' + abbr + '</th>';
    }
    html += '</tr>';
    for (let i = 0; i < n; i++) {
      const abbr = dsm.apps[i].length > 8 ? dsm.apps[i].substring(0,8) : dsm.apps[i];
      html += '<tr><th title="' + dsm.apps[i] + '" style="text-align:right;padding-right:4px;">' + abbr + '</th>';
      for (let j = 0; j < n; j++) {
        const v = dsm.matrix[i][j];
        if (i === j) {
          html += '<td class="cell-diag">·</td>';
        } else if (v > 0) {
          html += '<td class="cell-hit">' + v + '</td>';
        } else {
          html += '<td class="cell-zero"></td>';
        }
      }
      html += '</tr>';
    }
    html += '</table></div>';
    if (dsm.apps.length > 50) {
      html += '<p style="color:#555;font-size:0.8em">Showing 50/' + dsm.apps.length + ' apps (Cuthill-McKee reordered)</p>';
    }
  }

  // Clusters
  if (dsm.clusters && dsm.clusters.length > 0) {
    html += '<div style="margin-top:12px"><b style="font-size:0.85em">Clusters</b><div style="margin-top:4px">';
    dsm.clusters.forEach(cl => {
      const members = cl.members.length <= 6 ? cl.members.join(', ') : cl.members.slice(0,6).join(', ') + ' +' + (cl.members.length-6);
      html += '<div class="dsm-cluster" title="' + cl.members.join(', ') + '">' + cl.name + ' (' + cl.members.length + ') int:' + cl.internal_deps + ' ext:' + cl.external_deps + '<br><span style="color:#888;font-size:0.85em">' + members + '</span></div>';
    });
    html += '</div></div>';
  }

  // Cycles
  if (dsm.cycles && dsm.cycles.length > 0) {
    html += '<div style="margin-top:12px"><b style="font-size:0.85em;color:#EF4444">Cycles (' + dsm.cycles.length + ')</b>';
    const maxShow = Math.min(dsm.cycles.length, 10);
    for (let i = 0; i < maxShow; i++) {
      html += '<div class="dsm-cycle">[len=' + dsm.cycles[i].length + '] ' + dsm.cycles[i].path.join(' → ') + '</div>';
    }
    if (dsm.cycles.length > maxShow) {
      html += '<div style="color:#555;font-size:0.8em">... and ' + (dsm.cycles.length - maxShow) + ' more</div>';
    }
    html += '</div>';
  }

  return html;
}

// --- Detail renderer dispatch ---
function renderDetail(check) {
  if (!check.data) return null;
  // DSM bandwidth check
  if (check.name.includes('DSM')) return renderDSMDetail(check.data);
  // Fallback: raw JSON
  return '<pre style="font-size:0.75em;color:#888;max-height:300px;overflow:auto">' + JSON.stringify(check.data, null, 2) + '</pre>';
}

// Layers
const layersEl = document.getElementById('layers');
data.layers.forEach(l => {
  const card = document.createElement('div');
  card.className = 'layer-card';
  card.style.borderColor = barColor(l.score);
  let checksHTML = '';
  (l.components || []).forEach((c, ci) => {
    const col = barColor(c.score);
    const hasData = c.data ? ' has-data' : '';
    const rowId = 'check_' + l.id + '_' + ci;
    checksHTML += '<div class="check-row' + hasData + '" id="row_' + rowId + '" onclick="toggleDetail(\'' + rowId + '\')">' +
      '<span class="check-name">' + c.name + '</span>' +
      '<div class="bar-bg"><div class="bar-fill" style="width:' + c.score + '%%;background:' + col + '"></div></div>' +
      '<span class="check-score">' + c.score.toFixed(0) + '</span></div>';
    if (c.data) {
      checksHTML += '<div class="detail-panel" id="detail_' + rowId + '"></div>';
    }
  });
  card.innerHTML = '<h3>Layer ' + l.id + ': ' + l.name_jp + ' (' + l.score.toFixed(0) + ' pts)</h3>' + checksHTML;
  layersEl.appendChild(card);
});

function toggleDetail(rowId) {
  const row = document.getElementById('row_' + rowId);
  const panel = document.getElementById('detail_' + rowId);
  if (!row || !panel) return;
  const isOpen = panel.classList.contains('open');
  if (isOpen) {
    panel.classList.remove('open');
    row.classList.remove('open');
  } else {
    // Find the check data
    const parts = rowId.split('_');
    const layerId = parts[1];
    const ci = parseInt(parts[2]);
    const layer = data.layers.find(l => l.id === layerId);
    if (layer && layer.components[ci]) {
      const content = renderDetail(layer.components[ci]);
      if (content) panel.innerHTML = content;
    }
    panel.classList.add('open');
    row.classList.add('open');
  }
}

// Well-Becoming
const wbEl = document.getElementById('wellbeing');
data.axes.forEach(a => {
  const col = barColor(a.score);
  const row = document.createElement('div');
  row.className = 'wb-row';
  row.innerHTML = '<span class="wb-name">' + a.name + '</span>' +
    '<div class="wb-bar-bg"><div class="wb-bar-fill" style="width:' + a.score + '%%;background:' + col + '"></div></div>' +
    '<span class="wb-score">' + a.score.toFixed(0) + ' (' + a.points + ' pts)</span>';
  wbEl.appendChild(row);
});

// Diagnosis
const diagEl = document.getElementById('diagnosis');
diagEl.innerHTML = '<h3 style="margin-bottom:8px;">Diagnosis</h3>';
data.diagnosis.forEach(d => {
  const item = document.createElement('div');
  item.className = 'diag-item';
  if (d.includes('[CRITICAL]')) item.className += ' critical';
  else if (d.includes('[IMPROVE]')) item.className += ' improve';
  else if (d.includes('[WELLBEING]')) item.className += ' wellbeing';
  else if (d.includes('[NEXT]')) item.className += ' next';
  item.textContent = d;
  diagEl.appendChild(item);
});
</script>
</body>
</html>`,
		r.Mokuteki,
		rankBorderColor(r.Rank),
		rankTextColor(r.Rank),
		r.Mokuteki,
		r.Principle,
		r.TotalApps, r.TotalEdges, r.GeneratedAt,
		r.Rank.Name,
		r.TotalScore, r.MaxScore,
		string(jsonData),
	)
}

func rankBorderColor(rank mokutekiRank) string {
	switch {
	case strings.HasPrefix(rank.Name, "Dan"):
		return "#FFD700"
	case rank.Name == "Kyu 1":
		return "#8B4513"
	case rank.Name == "Kyu 2":
		return "#3B82F6"
	case rank.Name == "Kyu 3":
		return "#22C55E"
	default:
		return "#666666"
	}
}

func rankTextColor(rank mokutekiRank) string {
	switch {
	case strings.HasPrefix(rank.Name, "Dan"):
		return "#FFD700"
	case rank.Name == "Kyu 1":
		return "#CD853F"
	case rank.Name == "Kyu 2":
		return "#60A5FA"
	case rank.Name == "Kyu 3":
		return "#4ADE80"
	default:
		return "#CCCCCC"
	}
}
