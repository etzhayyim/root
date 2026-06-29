// Gov atlas client-side search (same-origin, no inline). Fetches
// /.well-known/gov-units.json once and filters client-side (no per-keystroke
// server call, cookie-free, same-origin only). CSP: script-src 'self';
// connect-src 'self'. Extracted from the former inline <script> in the TS /gov
// handler. ADR: did-web UIUX unification.
(async () => {
  const d = await (await fetch("/.well-known/gov-units.json")).json();
  const U = d.units || [];
  const q = document.getElementById("q"),
    lvl = document.getElementById("lvl"),
    src = document.getElementById("src"),
    out = document.getElementById("out"),
    stats = document.getElementById("stats");
  for (const l of Object.keys(d.byLevel || {}).sort()) {
    const o = document.createElement("option");
    o.value = l;
    o.textContent = l + " (" + d.byLevel[l] + ")";
    lvl.appendChild(o);
  }
  const esc = (s) =>
    String(s || "").replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  function render() {
    const t = q.value.trim().toLowerCase(),
      fl = lvl.value,
      fs = src.value;
    const r = U.filter(
      (u) =>
        (!fl || u.level === fl) &&
        (!fs || u.sourcing === fs) &&
        (!t ||
          (u.name || "").toLowerCase().includes(t) ||
          (u.nameEn || "").toLowerCase().includes(t) ||
          (u.nameRomanized || "").toLowerCase().includes(t) ||
          (u.id || "").toLowerCase().includes(t) ||
          (u.jurisdiction || "").toLowerCase().includes(t)),
    ).slice(0, 300);
    stats.textContent =
      r.length +
      " shown · " +
      d.count +
      " units / " +
      d.countries +
      " jurisdictions · " +
      (d.withNameLocal || 0) +
      " endonyms · " +
      (d.withCoords || 0) +
      " located";
    const geo = (u) =>
      typeof u.lat === "number" && typeof u.lon === "number"
        ? ' · <a href="geo:' + u.lat + "," + u.lon + '" rel="noopener">map</a>'
        : "";
    out.innerHTML = r
      .map(
        (u) =>
          '<li><span class="gov-nm">' +
          esc(u.name) +
          "</span>" +
          (u.nameRomanized && u.nameRomanized !== u.name
            ? ' <span class="gov-ro">' + esc(u.nameRomanized) + "</span>"
            : "") +
          (u.nameEn && u.nameEn !== u.name ? ' <span class="gov-en">' + esc(u.nameEn) + "</span>" : "") +
          ' <span class="gov-lv">' +
          esc(u.level) +
          '</span> <span class="gov-lv ' +
          (u.sourcing === "authoritative" ? "gov-au" : "gov-re") +
          '">' +
          esc(u.sourcing) +
          "</span> <span class=\"gov-en\">" +
          esc(u.jurisdiction) +
          "</span>" +
          (u.url
            ? ' · <a href="' + esc(u.url) + '" rel="noopener noreferrer nofollow">site</a>'
            : "") +
          geo(u) +
          "</li>",
      )
      .join("");
  }
  q.oninput = lvl.onchange = src.onchange = render;
  render();
})();
