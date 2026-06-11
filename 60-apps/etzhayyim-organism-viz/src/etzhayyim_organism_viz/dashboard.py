"""Static HTML dashboard — bonsai SVG + dials + pruning candidates + raw notes."""

from __future__ import annotations

from pathlib import Path

from .aliveness import AliveTuple, in_healthy_band


def render(alive: AliveTuple, axis_scores: dict[str, int], bonsai_svg: str) -> str:
    bands = in_healthy_band(alive)
    rows = "".join(
        f"<tr><td>{k}</td><td>{v:.3f}</td><td>{'✅' if bands.get(k.split('_')[0], False) else '❌'}</td></tr>"
        for k, v in alive.as_dict().items()
        if k not in ("timestamp", "notes")
    )
    axis_rows = "".join(
        f"<tr><td>{k}</td><td>{v} / 10</td></tr>" for k, v in axis_scores.items()
    )
    notes = "".join(f"<li>{n}</li>" for n in alive.notes)
    return f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<title>etzhayyim organism — aliveness dashboard</title>
<style>
  body {{ font-family: ui-sans-serif, -apple-system, sans-serif; background:#fffaf2; color:#222; margin:0; padding:24px 32px; }}
  h1 {{ margin:0 0 4px; font-size:22px; }}
  h2 {{ margin:24px 0 8px; font-size:16px; color:#5e4520; }}
  .sub {{ color:#888; font-size:13px; margin-bottom:24px; }}
  table {{ border-collapse: collapse; margin: 8px 0; }}
  th, td {{ text-align:left; padding:4px 14px 4px 0; border-bottom:1px solid #eee; }}
  .pill {{ display:inline-block; padding:2px 8px; border-radius:10px; background:#eee; color:#333; font-size:11px; margin-right:6px; }}
  .ok {{ background:#dcefe2; color:#1f6b3b; }}
  .bad {{ background:#f1d9d9; color:#7a2c2c; }}
  .grid {{ display:grid; grid-template-columns: minmax(300px, 1fr) minmax(420px, 1.4fr); gap:24px; }}
  .card {{ background:#fff; border:1px solid #ece4d4; border-radius:8px; padding:16px 20px; }}
  small {{ color:#888; }}
  svg {{ width:100%; height:auto; }}
</style></head>
<body>
  <h1>etzhayyim Bonsai of Life</h1>
  <div class="sub">{alive.timestamp} · 非終末論 active-inference health surface · ADR-2605192100 §1.15</div>

  <div>
    <span class="pill {'ok' if all(bands.values()) else 'bad'}">A(t) in band: {sum(bands.values())}/5</span>
    <span class="pill">M={alive.M:.2f}</span>
    <span class="pill">D={alive.D:.2f}</span>
    <span class="pill">C={alive.C:.2f}</span>
    <span class="pill">P={alive.P:.2f}</span>
    <span class="pill">G={alive.G:.2f}</span>
  </div>

  <div class="grid">
    <div>
      <h2>Aliveness 5-tuple</h2>
      <div class="card"><table>
        <tr><th>dim</th><th>value</th><th>band</th></tr>
        {rows}
      </table>
      <small>5-tuple, not a scalar — per §1.15 anti-eschatology.</small>
      </div>

      <h2>Axis scores (latest cycle)</h2>
      <div class="card"><table>
        <tr><th>axis</th><th>score</th></tr>
        {axis_rows}
      </table></div>

      <h2>Notes</h2>
      <div class="card"><ul>{notes}</ul></div>
    </div>

    <div>
      <h2>Bonsai</h2>
      <div class="card">{bonsai_svg}</div>
    </div>
  </div>

  <p style="margin-top:32px;color:#888;font-size:12px">
    Constitutional anchor: <a href="../../../90-docs/adr/2605192100-etzhayyim-mission-charter.md">ADR-2605192100 §1</a>
    · Ideal state prior: <a href="../../../90-docs/2605221243-ideal-ecosystem-state-active-inference-prior.md">2605221243</a>
    · Source: <code>60-apps/etzhayyim-organism-viz/</code>
  </p>
</body></html>
"""


def render_to(out_dir: Path, alive: AliveTuple, axis_scores: dict[str, int], bonsai_svg: str) -> Path:
    out = out_dir / "dashboard.html"
    out.write_text(render(alive, axis_scores, bonsai_svg), encoding="utf-8")
    return out
