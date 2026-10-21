// Small live pulse for the home page. Every request stays same-origin.
// CSP: script-src 'self'; connect-src 'self'.
(function () {
  const esc = (s) =>
    String(s ?? "").replace(/[&<>"']/g, (c) => {
      if (c === "&") return "&amp;";
      if (c === "<") return "&lt;";
      if (c === ">") return "&gt;";
      if (c === '"') return "&quot;";
      return "&#39;";
    });
  const set = (id, value) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = value;
  };
  const render = async () => {
    try {
      const [pulseRes, healthRes] = await Promise.all([
        fetch("/organism/pulse.json", { cache: "no-store" }),
        fetch("/organism/health.json", { cache: "no-store" }),
      ]);
      const pulse = pulseRes.ok ? await pulseRes.json() : null;
      const health = healthRes.ok ? await healthRes.json() : null;
      const actors = Object.entries((pulse && pulse.actors) || {})
        .sort((a, b) => ((b[1] && b[1].lastAt) || 0) - ((a[1] && a[1].lastAt) || 0))
        .slice(0, 4);
      const actorList = actors.length
        ? actors
            .map(
              ([actor, info]) =>
                "<li><strong>" +
                esc(actor) +
                "</strong><span>" +
                esc(info && info.lastSubject ? info.lastSubject : "activity stream") +
                "</span></li>",
            )
            .join("")
        : "<li>Waiting for the latest actor pulse…</li>";
      const hostState = health && health.anyStale ? "Resting" : "Alive";
      set("murakumo-host-state", hostState);
      set("murakumo-host-meta", "Updated " + esc((health && health.generatedAt) || "unknown"));
      set("murakumo-host-list", actorList);
    } catch (_err) {
      set("murakumo-host-state", "Pulse unavailable");
      set("murakumo-host-meta", "Will retry shortly");
      set("murakumo-host-list", "<li>Live pulse could not be reached.</li>");
    }
  };
  render();
  setInterval(render, 15000);
})();
