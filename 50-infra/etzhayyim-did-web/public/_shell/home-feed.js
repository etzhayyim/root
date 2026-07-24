// Home page live feed (same-origin, no inline). Refreshes the Murakumo host
// pulse + kotobase publish stats every 15s from same-origin JSON. CSP:
// script-src 'self'; connect-src 'self'. Extracted from the former inline
// <script> in buildHomeHtml. ADR: etzhayyim-did-web UIUX unification.
(function () {
  const esc = (s) =>
    String(s ?? "").replace(/[&<>"']/g, (c) => {
      if (c === "&") return "&amp;";
      if (c === "<") return "&lt;";
      if (c === ">") return "&gt;";
      if (c === '"') return "&quot;";
      return "&#39;";
    });
  const n = (v) => new Intl.NumberFormat("en-US").format(Number(v || 0));
  const pct = (v, max) =>
    Math.max(0, Math.min(100, (Number(v || 0) / Math.max(1, Number(max || 1))) * 100));
  const ageLabel = (ms) => {
    const s = Math.max(0, Math.round(Number(ms || 0) / 1000));
    if (s < 60) return s + "s ago";
    const m = Math.floor(s / 60);
    if (m < 60) return m + "m ago";
    const h = Math.floor(m / 60);
    return h + "h ago";
  };
  const set = (id, value) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = value;
  };
  const render = async () => {
    try {
      const [pulseRes, healthRes, statsRes] = await Promise.all([
        fetch("/organism/pulse.json", { cache: "no-store" }),
        fetch("/organism/health.json", { cache: "no-store" }),
        fetch("/xrpc/com.etzhayyim.apps.kotoba.stats?graph=yoro-social-v1", {
          cache: "no-store",
        }),
      ]);
      const pulse = pulseRes.ok ? await pulseRes.json() : null;
      const health = healthRes.ok ? await healthRes.json() : null;
      const stats = statsRes.ok ? await statsRes.json() : null;
      const actors = Object.entries((pulse && pulse.actors) || {})
        .sort((a, b) => ((b[1] && b[1].lastAt) || 0) - ((a[1] && a[1].lastAt) || 0))
        .slice(0, 6);
      const actorList = actors.length
        ? actors
            .map(
              ([actor, info]) =>
                "<li><strong>" +
                esc(actor) +
                "</strong><span>" +
                esc(info && info.lastSubject ? info.lastSubject : "activity stream") +
                "</span><small>" +
                n((info && info.commits) || 0) +
                " commits · " +
                ageLabel(Date.now() - Number((info && info.lastAt) || 0)) +
                "</small></li>",
            )
            .join("")
        : "<li><strong>loading</strong><span>no pulse data yet</span><small>waiting for organism feed</small></li>";
      const hostState = health && health.anyStale ? "degraded" : "live";
      set("murakumo-host-state", hostState);
      set(
        "murakumo-host-meta",
        "pulse " +
          esc(hostState) +
          " · updated " +
          esc((health && health.generatedAt) || "unknown"),
      );
      set(
        "murakumo-host-bar",
        "<span style=\"width:" +
          pct(
            ((health && health.layers && health.layers.pulse && health.layers.pulse.cadenceMs) ||
              6000) -
              ((health && health.layers && health.layers.pulse && health.layers.pulse.ageMs) ||
                0),
            (health && health.layers && health.layers.pulse && health.layers.pulse.cadenceMs) ||
              6000,
          ) +
          '%"></span>',
      );
      set("murakumo-host-list", actorList);
      set("kotobase-root", esc((stats && stats.root) || "no published root yet"));
      set(
        "kotobase-meta",
        "advances " +
          n((stats && stats.advances) || 0) +
          " · conflicts " +
          n((stats && stats.conflicts) || 0) +
          " · rate-limited " +
          n((stats && stats.rateLimited) || 0) +
          " · updated " +
          esc((stats && stats.updatedAt) || "unknown"),
      );
    } catch (_err) {
      set("murakumo-host-state", "offline");
      set("murakumo-host-meta", "live feed unavailable");
      set(
        "murakumo-host-list",
        "<li><strong>offline</strong><span>could not load organism feed</span><small>retrying</small></li>",
      );
      set("kotobase-meta", "live publish stats unavailable");
    }
  };
  render();
  setInterval(render, 15000);
})();
