// Shared HTML shell for etzhayyim.com public pages. Single source of truth for
// the header/nav/footer envelope + the same-origin /_shell/shell.css link.
// Page builders pass <main> inner content; this wraps it in a full document so
// every page shares one layout, one nav, one footer, one stylesheet
// (style-src 'self', no inline <style>, no third-party CDN).
// ADR: etzhayyim-did-web UIUX unification.

const NAV: ReadonlyArray<readonly [string, string]> = [
  ["/organism", "organism"],
  ["/system-dynamics", "system dynamics"],
  ["/actors", "actors"],
  ["/tomoshibi", "灯 tomoshibi"],
  ["/murakumo", "murakumo"],
  ["/gov", "gov atlas"],
  ["/donate", "donate"],
  ["/.well-known/did.json", "DID"],
];

export interface ShellOpts {
  title: string;
  lang?: string; // default "en"
  description?: string;
  active?: string; // nav href that is current (aria-current=page)
  main: string; // <main> inner HTML
  wrapClass?: string; // extra class on .wrap (page-specific width)
  extraCss?: string[]; // additional same-origin css hrefs
  scriptSrc?: string; // same-origin script src (deferred to end of body)
  scriptType?: "module" | "text/javascript";
  footerHtml?: string; // page-specific footer inner (replaces default)
}

function navHtml(active?: string): string {
  return NAV.map(([href, label]) => {
    const cur = href === active ? ' aria-current="page"' : "";
    return `<a href="${href}"${cur}>${label}</a>`;
  }).join("");
}

export function renderShell(o: ShellOpts): string {
  const lang = o.lang ?? "en";
  const css = [
    "/_shell/shell.css",
    "/_shell/liquid-glass.css",
    "/_shell/liquid-glass-adapter.css",
    ...(o.extraCss ?? []),
  ]
    .map((h) => `<link rel="stylesheet" href="${h}">`)
    .join("");
  const script = o.scriptSrc
    ? `<script${o.scriptType ? ` type="${o.scriptType}"` : ""} src="${o.scriptSrc}"></script>`
    : "";
  return `<!DOCTYPE html>
<html lang="${lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${o.title}</title>
${o.description ? `<meta name="description" content="${o.description}">` : ""}
${css}
</head>
<body>
<div class="wrap ${o.wrapClass ?? ""}">
<header class="site-hd">
<a class="brand" href="/">etzhayyim</a>
<nav class="site-nav" aria-label="Primary">
${navHtml(o.active)}
</nav>
</header>
<main class="site-main">
${o.main}
</main>
<footer class="site-ft">
${
  o.footerHtml ??
  `Machine roots: <a href="/.well-known/did.json">/.well-known/did.json</a> · <a href="/.well-known/actors.json">/.well-known/actors.json</a> · <a href="/.well-known/donation.json">/.well-known/donation.json</a>. No ads, no trackers, no cookies.`
}
</footer>
</div>
${script}
</body>
</html>`;
}
