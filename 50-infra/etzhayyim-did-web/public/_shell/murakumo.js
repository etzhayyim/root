// /murakumo — Murakumo host / kotoba-wasm resident-actor visualizer.
// Same-origin, no inline (CSP: script-src 'self'; connect-src 'self'; style-src
// 'self'). Fetches the live registry (/.well-known/actors.json) + the Murakumo
// pulse (/organism/pulse.json), joins them, and renders three views — grid,
// commit timeline (字 markers placed by last-commit time, sized by activity),
// and same-glyph "lineage" families — with shared search + filter.
// ADR: etzhayyim-did-web UIUX unification.
(function () {
  "use strict";
  var root = document.getElementById("mk-app");
  if (!root) return;

  var esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return c === "&" ? "&amp;" : c === "<" ? "&lt;" : c === ">" ? "&gt;"
        : c === '"' ? "&quot;" : "&#39;";
    });
  };
  var nf = function (v) { return new Intl.NumberFormat("en-US").format(Number(v || 0)); };

  var D = null, all = [], NOW = 0, WIN = 0;
  var view = "grid", filter = "live", sort = "commits", q = "";

  var fmtAgo = function (t) {
    if (!t) return "";
    var s = (NOW - t) / 1000; if (s < 0) s = 0;
    var h = s / 3600;
    if (h < 1) return Math.round(s / 60) + "m";
    if (h < 48) return h.toFixed(0) + "h";
    return (h / 24).toFixed(0) + "d";
  };
  var fmtClock = function (t) {
    var d = new Date(t), p = function (n) { return String(n).padStart(2, "0"); };
    return p(d.getHours()) + ":" + p(d.getMinutes());
  };
  var kindClass = function (k) {
    return k === "substrate-service" ? "svc" : k === "pulse-only" ? "pulse" : "";
  };

  function build(reg, pulse, rad) {
    var pa = (pulse && pulse.actors) || {};
    var regActors = (reg && reg.actors) || [];
    var actors = regActors.map(function (a) {
      var p = pa[a.handle];
      return {
        handle: a.handle, glyph: a.glyph || "", name: a.displayName || a.handle,
        kind: a.kind, desc: a.description || "", adr: a.adr || [],
        live: !!p, commits: (p && p.commits) || 0, lastAt: p && p.lastAt,
        lastSubject: (p && p.lastSubject) || ""
      };
    });
    var regHandles = {};
    regActors.forEach(function (a) { regHandles[a.handle] = 1; });
    var extra = Object.keys(pa).filter(function (h) { return !regHandles[h]; }).map(function (h) {
      var p = pa[h];
      return {
        handle: h, glyph: "", name: h, kind: "pulse-only", desc: "", adr: [],
        live: true, commits: p.commits || 0, lastAt: p.lastAt, lastSubject: p.lastSubject || ""
      };
    });
    D = {
      meta: {
        entity: reg.entity, entityDid: reg.entityDid, namedCount: regActors.length,
        totalResolvable: reg.totalResolvableActors, entityActorCount: reg.entityActorCount,
        unispscActorCount: reg.unispscActorCount, liveCount: Object.keys(pa).length,
        generatedAt: pulse.generatedAt, sinceHours: pulse.sinceHours || 48,
        store: pulse.store || "kotoba-datom-log", snapshot: pulse.snapshot,
        head: pulse.head, now: pulse.now
      },
      namespaces: (reg.entityNamespaces || []).map(function (n) {
        return { ns: n.ns, glyph: n.glyph, count: n.count, kindLabel: n.kindLabel, owners: n.owners || [] };
      }),
      stream: (pulse.stream || []).map(function (s) { return { at: s.at, actor: s.actor, subj: s.subj || "" }; })
    };
    all = actors.concat(extra);
    D.rad = (rad && rad.actors) || {};
    D.mono = {};
    ((rad && rad.monorepoDirs) || []).forEach(function (h) { D.mono[h] = 1; });
    NOW = D.meta.now || Date.parse(D.meta.generatedAt);
    WIN = D.meta.sinceHours * 3600 * 1000;
  }

  // Per-actor identity links, joined by handle to the kotoba-rad ledger
  // (/_shell/actor-rad.json, generated from 80-data/kotoba-rad/*.identity.journal.edn).
  // Only links backed by real data are shown; GitHub falls back to the monorepo
  // 20-actors dir for registered actors with no child-repo identity yet.
  var GH = "https://github.com/etzhayyim/";
  function actorLinks(a) {
    var h = a.handle, r = D.rad[h], out = [];
    // gh: prefer the always-public monorepo source dir; fall back to the child
    // repo (:rad/repo) only when there is no monorepo dir.
    if (D.mono[h]) out.push(["gh", GH + "root/tree/main/20-actors/" + h, "GitHub (public monorepo): 20-actors/" + h]);
    else if (r && r.repo) out.push(["gh", "https://" + r.repo, "GitHub: " + r.repo]);
    if (r && r.didWeb) out.push(["rad", "https://etzhayyim.github.io/com-etzhayyim-" + h + "/.well-known/did.json", "RAD identity (did:web): " + r.didWeb]);
    if (r) out.push(["k-rad", GH + "root/blob/main/80-data/kotoba-rad/" + h + ".identity.journal.edn", "kotoba-rad ledger" + (r.rid ? " · RID " + r.rid.slice(0, 14) + "…" : "")]);
    return out;
  }
  function linksHtml(a) {
    var lk = actorLinks(a);
    if (!lk.length) return "";
    return '<div class="mk-links">' + lk.map(function (l) {
      return '<a href="' + l[1] + '" target="_blank" rel="noopener noreferrer" title="' + esc(l[2]) + '">' + l[0] + '</a>';
    }).join("") + '</div>';
  }

  function filtered() {
    return all.filter(function (a) {
      if (filter === "live" && !a.live) return false;
      if (filter === "svc" && a.kind !== "substrate-service") return false;
      if (q) {
        var s = (a.handle + " " + a.name + " " + a.desc + " " + a.kind + " " + a.glyph).toLowerCase();
        if (s.indexOf(q) < 0) return false;
      }
      return true;
    });
  }
  function sortRows(rows) {
    return rows.slice().sort(function (a, b) {
      if (sort === "commits") return (b.commits - a.commits) || ((b.lastAt || 0) - (a.lastAt || 0)) || a.handle.localeCompare(b.handle);
      if (sort === "recent") return ((b.lastAt || 0) - (a.lastAt || 0)) || a.handle.localeCompare(b.handle);
      return a.handle.localeCompare(b.handle);
    });
  }

  function renderGrid(rows) {
    return '<div class="mk-grid">' + sortRows(rows).map(function (a) {
      return '<div class="mk-card ' + (a.live ? "live" : "") + '">' +
        '<div class="top"><span class="mk-glyph">' + esc(a.glyph || "·") + '</span>' +
        '<span class="mk-handle">' + esc(a.handle) + '</span>' +
        '<span class="mk-kind ' + kindClass(a.kind) + '">' + esc(a.kind) + '</span></div>' +
        (a.desc ? '<div class="mk-desc" title="' + esc(a.desc) + '">' + esc(a.desc) + '</div>' : '') +
        '<div class="mk-meta">' +
        (a.live ? '<span class="mk-commits">● ' + a.commits + ' commit' + (a.commits === 1 ? '' : 's') + '</span>' : '<span>idle</span>') +
        (a.lastAt ? '<span>last ' + fmtAgo(a.lastAt) + ' ago</span>' : '') +
        (a.adr && a.adr.length ? '<span>ADR ' + a.adr.join(", ") + '</span>' : '') +
        '</div>' + linksHtml(a) + '</div>';
    }).join("") + '</div>';
  }

  function renderTimeline(rows) {
    var live = rows.filter(function (a) { return a.lastAt; });
    var W = Math.max(820, root.clientWidth - 8), padL = 14, padR = 14, top = 30;
    var hours = D.meta.sinceHours, t0 = NOW - WIN, t1 = NOW;
    var x = function (t) { return padL + (t - t0) / (t1 - t0) * (W - padL - padR); };
    var items = live.map(function (a) {
      var fs = Math.min(34, 12 + a.commits * 3);
      var lab = a.glyph || a.handle.slice(0, 4);
      var hw = fs * lab.length * 0.30 + 3;
      return { a: a, fs: fs, lab: lab, xx: x(a.lastAt), hw: hw, row: 0 };
    }).sort(function (p, r) { return p.xx - r.xx; });
    var rowsArr = [];
    items.forEach(function (it) {
      var rr = 0;
      for (; ;) {
        var occ = rowsArr[rr] || (rowsArr[rr] = []);
        var ok = occ.every(function (o) { return Math.abs(o.xx - it.xx) >= o.hw + it.hw + 2; });
        if (ok) { occ.push(it); it.row = rr; break; }
        rr++;
      }
    });
    var nRows = rowsArr.length, rowH = 30, plotH = nRows * rowH, H = top + plotH + 34;
    var yOf = function (r) { return top + plotH - r * rowH - 4; };
    var grid = "";
    for (var h = 0; h <= hours; h += 12) {
      var t = t1 - (hours - h) * 3600 * 1000, gx = x(t);
      grid += '<line class="mk-tl-grid" x1="' + gx + '" y1="' + (top - 6) + '" x2="' + gx + '" y2="' + (top + plotH + 2) + '"/>' +
        '<text class="mk-tl-tick" x="' + gx + '" y="' + (top + plotH + 18) + '" text-anchor="middle">' +
        (h === hours ? "now" : "-" + (hours - h) + "h") + '</text>';
    }
    var marks = items.map(function (it) {
      var a = it.a, gx = it.xx, gy = yOf(it.row);
      var title = a.handle + " · " + a.commits + " commit" + (a.commits === 1 ? "" : "s") +
        " · last " + fmtAgo(a.lastAt) + " ago\n" + (a.lastSubject || "");
      var op = (0.55 + Math.min(0.45, a.commits * 0.08)).toFixed(2);
      return '<text class="mk-tl-glyph" x="' + gx + '" y="' + gy + '" font-size="' + it.fs +
        '" text-anchor="middle" opacity="' + op + '"><title>' + esc(title) + '</title>' + esc(it.lab) + '</text>';
    }).join("");
    var svg = '<div class="mk-tlwrap"><svg class="mk-tlsvg" width="100%" viewBox="0 0 ' + W + ' ' + H +
      '" preserveAspectRatio="xMinYMin meet">' +
      '<text class="mk-tl-tick" x="' + padL + '" y="16" text-anchor="start">commit活動 時系列 — 各アクターを最終 commit 時刻に配置（字サイズ ∝ commit数, ' +
      live.length + ' actors / ' + hours + 'h window）</text>' +
      '<line class="mk-tl-axis" x1="' + padL + '" y1="' + (top + plotH + 2) + '" x2="' + (W - padR) + '" y2="' + (top + plotH + 2) + '"/>' +
      grid + marks + '</svg></div>';
    var feed = D.stream.map(function (s) {
      var merge = !s.actor;
      return '<div class="row"><span class="t">' + fmtClock(s.at) + '</span>' +
        '<span class="a ' + (merge ? "merge" : "") + '">' + (merge ? "⎇ merge" : esc(s.actor)) + '</span>' +
        '<span class="s" title="' + esc(s.subj) + '">' + esc(s.subj) + '</span></div>';
    }).join("");
    return svg + '<h2 class="mk-h2">最新コミット ストリーム <span class="c">— pulse.stream（直近 ' +
      D.stream.length + ' 件）</span></h2><div class="mk-feed">' + feed + '</div>';
  }

  function renderLineage(rows) {
    var fams = {};
    rows.forEach(function (a) {
      var key = a.glyph ? Array.from(a.glyph)[0] : "∅";
      (fams[key] = fams[key] || []).push(a);
    });
    var arr = Object.keys(fams).map(function (k) {
      var v = fams[k];
      return { k: k, v: v, live: v.some(function (a) { return a.live; }) };
    });
    arr.sort(function (a, b) { return (b.v.length - a.v.length) || (b.live - a.live) || a.k.localeCompare(b.k); });
    var multi = arr.filter(function (f) { return f.v.length > 1; });
    var solo = arr.filter(function (f) { return f.v.length === 1; });
    var chip = function (a) {
      return '<div class="mk-chip ' + (a.live ? "live" : "") + '" title="' + esc(a.name + " — " + (a.desc || a.kind)) + '">' +
        '<div class="mk-chip-top"><span class="cg">' + esc(a.glyph || "·") + '</span><span class="ch">' + esc(a.handle) + '</span>' +
        (a.live ? '<span class="cc">●' + a.commits + '</span>' : '<span class="ck">' + esc(a.kind) + '</span>') + '</div>' +
        linksHtml(a) + '</div>';
    };
    var famHtml = function (f) {
      return '<div class="mk-fam ' + (f.live ? "has-live" : "") + '"><div class="mk-fam-h">' +
        '<span class="mk-fam-root">' + esc(f.k) + '</span><span class="mk-fam-meta">' + f.v.length + ' actors' +
        (f.live ? ' · ' + f.v.filter(function (a) { return a.live; }).length + ' live' : '') + '</span></div>' +
        '<div class="mk-members">' + f.v.slice().sort(function (a, b) {
          return b.commits - a.commits || a.handle.localeCompare(b.handle);
        }).map(chip).join("") + '</div></div>';
    };
    var html = '<h2 class="mk-h2">同字 家系 <span class="c">— glyph 先頭字を共有する系統（' + multi.length + ' families）</span></h2>';
    html += multi.map(famHtml).join("");
    if (solo.length) {
      html += '<h2 class="mk-h2">単独系統 <span class="c">— 固有字（' + solo.length + '）</span></h2>' +
        '<div class="mk-fam solo"><div class="mk-members">' + solo.map(function (f) { return chip(f.v[0]); }).join("") + '</div></div>';
    }
    return html;
  }

  function renderViews() {
    var rows = filtered();
    var cnt = document.getElementById("mk-count");
    if (cnt) cnt.textContent = rows.length + " actors";
    var sortSeg = document.getElementById("mk-sort");
    if (sortSeg) sortSeg.style.display = view === "grid" ? "" : "none";
    var host = document.getElementById("mk-views");
    host.innerHTML = view === "grid" ? renderGrid(rows)
      : view === "timeline" ? renderTimeline(rows) : renderLineage(rows);
  }

  function seg(id, items, current, onpick) {
    return '<div class="mk-seg ' + (id === "mk-view" ? "view" : "") + '" id="' + id + '">' +
      items.map(function (it) {
        return '<button data-k="' + it[0] + '" class="' + (it[0] === current ? "on" : "") + '">' + it[1] + '</button>';
      }).join("") + '</div>';
  }

  function shell() {
    var m = D.meta;
    var stats = [
      ["live", m.liveCount, "稼働中アクター (Murakumo, " + m.sinceHours + "h)", true],
      ["", m.namedCount, "登録ネームドアクター", false],
      ["", nf(m.totalResolvable), "resolvable actors 総数", false],
      ["", nf(m.entityActorCount), "entity actors", false],
      ["", nf(m.unispscActorCount), "UNSPSC commodity agents", false]
    ];
    var statHtml = stats.map(function (s) {
      return '<div class="mk-stat ' + (s[3] ? "live" : "") + '"><div class="n">' + s[1] + '</div><div class="l">' + s[2] + '</div></div>';
    }).join("");
    var nsHtml = D.namespaces.map(function (n) {
      return '<div class="mk-ns"><div class="g">' + esc(n.glyph) + '</div><div class="cnt">' + nf(n.count) + '</div>' +
        '<div class="lbl">' + esc(n.ns) + ' · ' + esc(n.kindLabel) + (n.owners.length ? ' · owners: ' + esc(n.owners.join(", ")) : "") + '</div></div>';
    }).join("");
    var ageH = (Date.now() - NOW) / 3600000;
    var stale = ageH > m.sinceHours;
    var ageLbl = ageH < 48 ? Math.max(0, ageH).toFixed(0) + "h" : (ageH / 24).toFixed(1) + "d";
    root.innerHTML =
      (stale ? '<div class="mk-stale">⚠ pulse スナップショットは約' + ageLbl + '前（generated ' + esc(m.generatedAt) +
        '）。pulse.json を再生成する常駐 heartbeat（organism daemon）が更新を停止している可能性があります。下の「稼働」はこのスナップショット時点（その直近' + m.sinceHours +
        'h）の commit 活動であり、現在のプロセス死活ではありません。</div>' : '') +
      '<div class="mk-bound"><span class="dot"></span>Murakumo メッシュ上で <b>kotoba-wasm</b> として常駐稼働 — <code>' + esc(m.store) +
      '</code> store · snapshot <code>' + esc(m.snapshot || "pulse") + '</code> · generated ' + esc(m.generatedAt) +
      ' (window ' + m.sinceHours + 'h) · <b class="live">緑＝直近' + m.sinceHours + 'hに commit したアクター</b>（＝開発 pulse。DID/プロセスの死活ではない）</div>' +
      '<div class="mk-stats">' + statHtml + '</div>' +
      '<div class="mk-bar">' +
      '<input id="mk-q" placeholder="検索: handle / 説明 / kind / glyph …" autocomplete="off">' +
      seg("mk-view", [["grid", "グリッド"], ["timeline", "時系列"], ["lineage", "家系"]], view) +
      seg("mk-filter", [["live", "稼働中"], ["all", "全件"], ["svc", "substrate"]], filter) +
      seg("mk-sort", [["commits", "活動量順"], ["recent", "最終稼働順"], ["name", "名前順"]], sort) +
      '<span class="mk-count" id="mk-count"></span>' +
      '</div>' +
      '<div id="mk-views"></div>' +
      '<h2 class="mk-h2">society-scale mirror actors <span class="c">— keyless 観測ミラー（namespace単位で集計）</span></h2>' +
      '<div class="mk-ns-grid">' + nsHtml + '</div>' +
      '<div class="mk-foot">Sources (same-origin JSON): <a href="/.well-known/actors.json">/.well-known/actors.json</a> (registry, ' +
      m.namedCount + ' named) · <a href="/organism/pulse.json">/organism/pulse.json</a> (live pulse, ' + m.liveCount +
      ' running) · head <code>' + esc((m.head || "").slice(0, 9)) + '</code></div>';

    var bindSeg = function (id, set) {
      var el = document.getElementById(id);
      el.addEventListener("click", function (e) {
        var b = e.target.closest("button"); if (!b) return;
        set(b.getAttribute("data-k"));
        Array.prototype.forEach.call(el.querySelectorAll("button"), function (x) { x.classList.toggle("on", x === b); });
        renderViews();
      });
    };
    bindSeg("mk-view", function (k) { view = k; });
    bindSeg("mk-filter", function (k) { filter = k; });
    bindSeg("mk-sort", function (k) { sort = k; });
    document.getElementById("mk-q").addEventListener("input", function (e) {
      q = e.target.value.toLowerCase().trim(); renderViews();
    });
    var rt;
    window.addEventListener("resize", function () {
      if (view !== "timeline") return;
      clearTimeout(rt); rt = setTimeout(renderViews, 150);
    });
    renderViews();
  }

  Promise.all([
    fetch("/.well-known/actors.json", { cache: "no-store" }).then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); }),
    fetch("/organism/pulse.json", { cache: "no-store" }).then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); }),
    fetch("/_shell/actor-rad.json", { cache: "no-store" }).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; })
  ]).then(function (res) {
    build(res[0], res[1], res[2]);
    shell();
  }).catch(function (err) {
    root.innerHTML = '<p class="mk-loading">live pulse を読み込めませんでした（' + esc(String(err)) +
      '）。<a href="/.well-known/actors.json">actors.json</a> / <a href="/organism/pulse.json">pulse.json</a> を確認してください。</p>';
  });
})();
