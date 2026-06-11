var gl = Object.defineProperty;
var Sr = (e) => {
  throw TypeError(e);
};
var _l = (e, t, n) => t in e ? gl(e, t, { enumerable: !0, configurable: !0, writable: !0, value: n }) : e[t] = n;
var Se = (e, t, n) => _l(e, typeof t != "symbol" ? t + "" : t, n), An = (e, t, n) => t.has(e) || Sr("Cannot " + n);
var X = (e, t, n) => (An(e, t, "read from private field"), n ? n.call(e) : t.get(e)), E = (e, t, n) => t.has(e) ? Sr("Cannot add the same private member more than once") : t instanceof WeakSet ? t.add(e) : t.set(e, n), ve = (e, t, n, r) => (An(e, t, "write to private field"), r ? r.call(e, n) : t.set(e, n), n), me = (e, t, n) => (An(e, t, "access private method"), n);
var ri;
typeof window < "u" && ((ri = window.__svelte ?? (window.__svelte = {})).v ?? (ri.v = /* @__PURE__ */ new Set())).add("5");
const Xl = 1, ml = 2, si = 4, xl = 8, wl = 16, yl = 1, Hl = 2, ai = 4, Zl = 8, Il = 16, Rl = 2, O = Symbol(), J = Symbol("filename"), fi = "http://www.w3.org/1999/xhtml", Gl = "http://www.w3.org/2000/svg", Fl = "@attach";
var ii, li;
const kr = (li = (ii = globalThis.process) == null ? void 0 : ii.env) == null ? void 0 : li.NODE_ENV, b = kr && !kr.toLowerCase().startsWith("prod");
var cr = Array.isArray, Wl = Array.prototype.indexOf, lt = Array.prototype.includes, or = Array.from, Te = Object.defineProperty, nt = Object.getOwnPropertyDescriptor, ui = Object.getOwnPropertyDescriptors, Nl = Object.prototype, Vl = Array.prototype, sr = Object.getPrototypeOf;
function kt(e) {
  return typeof e == "function";
}
const Cl = () => {
};
function Sl(e) {
  return e();
}
function Pn(e) {
  for (var t = 0; t < e.length; t++)
    e[t]();
}
function di() {
  var e, t, n = new Promise((r, i) => {
    e = r, t = i;
  });
  return { promise: n, resolve: e, reject: t };
}
function kl(e, t) {
  if (Array.isArray(e))
    return e;
  if (!(Symbol.iterator in e))
    return Array.from(e);
  const n = [];
  for (const r of e)
    if (n.push(r), n.length === t) break;
  return n;
}
const z = 2, wt = 4, en = 8, ar = 1 << 24, je = 16, Xe = 32, yt = 64, Yl = 128, se = 512, j = 1024, P = 2048, ye = 4096, ie = 8192, ae = 16384, st = 32768, Yr = 1 << 25, Ht = 65536, mn = 1 << 17, Bl = 1 << 18, Nn = 1 << 19, vi = 1 << 20, we = 1 << 25, Je = 65536, xn = 1 << 21, Vn = 1 << 22, Be = 1 << 23, Ne = Symbol("$state"), pi = Symbol("legacy props"), Al = Symbol(""), hi = Symbol("proxy path"), Re = new class extends Error {
  constructor() {
    super(...arguments);
    Se(this, "name", "StaleReactionError");
    Se(this, "message", "The reaction that called `getAbortSignal()` was re-run or destroyed");
  }
}();
var ci;
const bi = (
  // We gotta write it like this because after downleveling the pure comment may end up in the wrong location
  !!((ci = globalThis.document) != null && ci.contentType) && /* @__PURE__ */ globalThis.document.contentType.includes("xml")
), Tl = 1, Jl = 11;
function El(e) {
  if (b) {
    const t = new Error(`invariant_violation
An invariant violation occurred, meaning Svelte's internal assumptions were flawed. This is a bug in Svelte, not your app — please open an issue at https://github.com/sveltejs/svelte, citing the following message: "${e}"
https://svelte.dev/e/invariant_violation`);
    throw t.name = "Svelte error", t;
  } else
    throw new Error("https://svelte.dev/e/invariant_violation");
}
function jl() {
  if (b) {
    const e = new Error("snippet_without_render_tag\nAttempted to render a snippet without a `{@render}` block. This would cause the snippet code to be stringified instead of its content being rendered to the DOM. To fix this, change `{snippet}` to `{@render snippet()}`.\nhttps://svelte.dev/e/snippet_without_render_tag");
    throw e.name = "Svelte error", e;
  } else
    throw new Error("https://svelte.dev/e/snippet_without_render_tag");
}
function Ml() {
  if (b) {
    const e = new Error("svelte_element_invalid_this_value\nThe `this` prop on `<svelte:element>` must be a string, if defined\nhttps://svelte.dev/e/svelte_element_invalid_this_value");
    throw e.name = "Svelte error", e;
  } else
    throw new Error("https://svelte.dev/e/svelte_element_invalid_this_value");
}
function Ol() {
  if (b) {
    const e = new Error("async_derived_orphan\nCannot create a `$derived(...)` with an `await` expression outside of an effect tree\nhttps://svelte.dev/e/async_derived_orphan");
    throw e.name = "Svelte error", e;
  } else
    throw new Error("https://svelte.dev/e/async_derived_orphan");
}
function Br() {
  if (b) {
    const e = new Error("bind_invalid_checkbox_value\nUsing `bind:value` together with a checkbox input is not allowed. Use `bind:checked` instead\nhttps://svelte.dev/e/bind_invalid_checkbox_value");
    throw e.name = "Svelte error", e;
  } else
    throw new Error("https://svelte.dev/e/bind_invalid_checkbox_value");
}
function zl(e, t) {
  if (b) {
    const n = new Error(`component_api_changed
Calling \`${e}\` on a component instance (of ${t}) is no longer valid in Svelte 5
https://svelte.dev/e/component_api_changed`);
    throw n.name = "Svelte error", n;
  } else
    throw new Error("https://svelte.dev/e/component_api_changed");
}
function Dl(e, t) {
  if (b) {
    const n = new Error(`component_api_invalid_new
Attempted to instantiate ${e} with \`new ${t}\`, which is no longer valid in Svelte 5. If this component is not under your control, set the \`compatibility.componentApi\` compiler option to \`4\` to keep it working.
https://svelte.dev/e/component_api_invalid_new`);
    throw n.name = "Svelte error", n;
  } else
    throw new Error("https://svelte.dev/e/component_api_invalid_new");
}
function Pl() {
  if (b) {
    const e = new Error(`derived_references_self
A derived value cannot reference itself recursively
https://svelte.dev/e/derived_references_self`);
    throw e.name = "Svelte error", e;
  } else
    throw new Error("https://svelte.dev/e/derived_references_self");
}
function gi(e, t, n) {
  if (b) {
    const r = new Error(`each_key_duplicate
${n ? `Keyed each block has duplicate key \`${n}\` at indexes ${e} and ${t}` : `Keyed each block has duplicate key at indexes ${e} and ${t}`}
https://svelte.dev/e/each_key_duplicate`);
    throw r.name = "Svelte error", r;
  } else
    throw new Error("https://svelte.dev/e/each_key_duplicate");
}
function Ll(e, t, n) {
  if (b) {
    const r = new Error(`each_key_volatile
Keyed each block has key that is not idempotent — the key for item at index ${e} was \`${t}\` but is now \`${n}\`. Keys must be the same each time for a given item
https://svelte.dev/e/each_key_volatile`);
    throw r.name = "Svelte error", r;
  } else
    throw new Error("https://svelte.dev/e/each_key_volatile");
}
function Ql(e) {
  if (b) {
    const t = new Error(`effect_in_teardown
\`${e}\` cannot be used inside an effect cleanup function
https://svelte.dev/e/effect_in_teardown`);
    throw t.name = "Svelte error", t;
  } else
    throw new Error("https://svelte.dev/e/effect_in_teardown");
}
function Ul() {
  if (b) {
    const e = new Error("effect_in_unowned_derived\nEffect cannot be created inside a `$derived` value that was not itself created inside an effect\nhttps://svelte.dev/e/effect_in_unowned_derived");
    throw e.name = "Svelte error", e;
  } else
    throw new Error("https://svelte.dev/e/effect_in_unowned_derived");
}
function $l(e) {
  if (b) {
    const t = new Error(`effect_orphan
\`${e}\` can only be used inside an effect (e.g. during component initialisation)
https://svelte.dev/e/effect_orphan`);
    throw t.name = "Svelte error", t;
  } else
    throw new Error("https://svelte.dev/e/effect_orphan");
}
function Kl() {
  if (b) {
    const e = new Error(`effect_update_depth_exceeded
Maximum update depth exceeded. This typically indicates that an effect reads and writes the same piece of state
https://svelte.dev/e/effect_update_depth_exceeded`);
    throw e.name = "Svelte error", e;
  } else
    throw new Error("https://svelte.dev/e/effect_update_depth_exceeded");
}
function ql(e) {
  if (b) {
    const t = new Error(`props_invalid_value
Cannot do \`bind:${e}={undefined}\` when \`${e}\` has a fallback value
https://svelte.dev/e/props_invalid_value`);
    throw t.name = "Svelte error", t;
  } else
    throw new Error("https://svelte.dev/e/props_invalid_value");
}
function ec(e) {
  if (b) {
    const t = new Error(`rune_outside_svelte
The \`${e}\` rune is only available inside \`.svelte\` and \`.svelte.js/ts\` files
https://svelte.dev/e/rune_outside_svelte`);
    throw t.name = "Svelte error", t;
  } else
    throw new Error("https://svelte.dev/e/rune_outside_svelte");
}
function tc() {
  if (b) {
    const e = new Error("state_descriptors_fixed\nProperty descriptors defined on `$state` objects must contain `value` and always be `enumerable`, `configurable` and `writable`.\nhttps://svelte.dev/e/state_descriptors_fixed");
    throw e.name = "Svelte error", e;
  } else
    throw new Error("https://svelte.dev/e/state_descriptors_fixed");
}
function nc() {
  if (b) {
    const e = new Error("state_prototype_fixed\nCannot set prototype of `$state` object\nhttps://svelte.dev/e/state_prototype_fixed");
    throw e.name = "Svelte error", e;
  } else
    throw new Error("https://svelte.dev/e/state_prototype_fixed");
}
function rc() {
  if (b) {
    const e = new Error("state_unsafe_mutation\nUpdating state inside `$derived(...)`, `$inspect(...)` or a template expression is forbidden. If the value should not be reactive, declare it without `$state`\nhttps://svelte.dev/e/state_unsafe_mutation");
    throw e.name = "Svelte error", e;
  } else
    throw new Error("https://svelte.dev/e/state_unsafe_mutation");
}
var fr = "font-weight: bold", ur = "font-weight: normal";
function ic(e) {
  b ? console.warn(`%c[svelte] await_reactivity_loss
%cDetected reactivity loss when reading \`${e}\`. This happens when state is read in an async function after an earlier \`await\`
https://svelte.dev/e/await_reactivity_loss`, fr, ur) : console.warn("https://svelte.dev/e/await_reactivity_loss");
}
function lc() {
  b ? console.warn("%c[svelte] select_multiple_invalid_value\n%cThe `value` property of a `<select multiple>` element should be an array, but it received a non-array value. The selection will be kept as is.\nhttps://svelte.dev/e/select_multiple_invalid_value", fr, ur) : console.warn("https://svelte.dev/e/select_multiple_invalid_value");
}
function cc(e) {
  b ? console.warn(`%c[svelte] state_proxy_equality_mismatch
%cReactive \`$state(...)\` proxies and the values they proxy have different identities. Because of this, comparisons with \`${e}\` will produce unexpected results
https://svelte.dev/e/state_proxy_equality_mismatch`, fr, ur) : console.warn("https://svelte.dev/e/state_proxy_equality_mismatch");
}
function _i(e) {
  return e === this.v;
}
function oc(e, t) {
  return e != e ? t == t : e !== t || e !== null && typeof e == "object" || typeof e == "function";
}
function Xi(e) {
  return !oc(e, this.v);
}
let tn = !1, sc = !1;
function ac() {
  tn = !0;
}
function k(e, t) {
  return e.label = t, mi(e.v, t), e;
}
function mi(e, t) {
  var n;
  return (n = e == null ? void 0 : e[hi]) == null || n.call(e, t), e;
}
function xi(e) {
  const t = new Error(), n = fc();
  return n.length === 0 ? null : (n.unshift(`
`), Te(t, "stack", {
    value: n.join(`
`)
  }), Te(t, "name", {
    value: e
  }), /** @type {Error & { stack: string }} */
  t);
}
function fc() {
  const e = Error.stackTraceLimit;
  Error.stackTraceLimit = 1 / 0;
  const t = new Error().stack;
  if (Error.stackTraceLimit = e, !t) return [];
  const n = t.split(`
`), r = [];
  for (let i = 0; i < n.length; i++) {
    const l = n[i], o = l.replaceAll("\\", "/");
    if (l.trim() !== "Error") {
      if (l.includes("validate_each_keys"))
        return [];
      o.includes("svelte/src/internal") || o.includes("node_modules/.vite") || r.push(l);
    }
  }
  return r;
}
function uc(e, t) {
  if (!b)
    throw new Error("invariant(...) was not guarded by if (DEV)");
  e || El(t);
}
let V = null;
function wn(e) {
  V = e;
}
let ge = null;
function yn(e) {
  ge = e;
}
function U(e, t, n, r, i, l) {
  const o = ge;
  ge = {
    type: t,
    file: n[J],
    line: r,
    column: i,
    parent: o,
    ...l
  };
  try {
    return e();
  } finally {
    ge = o;
  }
}
let Gt = null;
function Hn(e) {
  Gt = e;
}
function nn(e, t = !1, n) {
  V = {
    p: V,
    i: !1,
    c: null,
    e: null,
    s: e,
    x: null,
    r: (
      /** @type {Effect} */
      G
    ),
    l: tn && !t ? { s: null, u: null, $: [] } : null
  }, b && (V.function = n, Gt = n);
}
function rn(e) {
  var t = (
    /** @type {ComponentContext} */
    V
  ), n = t.e;
  if (n !== null) {
    t.e = null;
    for (var r of n)
      Ti(r);
  }
  return e !== void 0 && (t.x = e), t.i = !0, V = t.p, b && (Gt = (V == null ? void 0 : V.function) ?? null), e ?? /** @type {T} */
  {};
}
function ln() {
  return !tn || V !== null && V.l === null;
}
let Ue = [];
function wi() {
  var e = Ue;
  Ue = [], Pn(e);
}
function Ot(e) {
  if (Ue.length === 0 && !Jt) {
    var t = Ue;
    queueMicrotask(() => {
      t === Ue && wi();
    });
  }
  Ue.push(e);
}
function dc() {
  for (; Ue.length > 0; )
    wi();
}
const Ln = /* @__PURE__ */ new WeakMap();
function vc(e) {
  var t = G;
  if (t === null)
    return I.f |= Be, e;
  if (b && e instanceof Error && !Ln.has(e) && Ln.set(e, pc(e, t)), (t.f & st) === 0 && (t.f & wt) === 0)
    throw b && !t.parent && e instanceof Error && yi(e), e;
  Zn(e, t);
}
function Zn(e, t) {
  for (; t !== null; ) {
    if ((t.f & Yl) !== 0) {
      if ((t.f & st) === 0)
        throw e;
      try {
        t.b.error(e);
        return;
      } catch (n) {
        e = n;
      }
    }
    t = t.parent;
  }
  throw b && e instanceof Error && yi(e), e;
}
function pc(e, t) {
  var o, c, a;
  const n = nt(e, "message");
  if (!(n && !n.configurable)) {
    for (var r = "	", i = `
${r}in ${((o = t.fn) == null ? void 0 : o.name) || "<unknown>"}`, l = t.ctx; l !== null; )
      i += `
${r}in ${(c = l.function) == null ? void 0 : c[J].split("/").pop()}`, l = l.p;
    return {
      message: e.message + `
${i}
`,
      stack: (a = e.stack) == null ? void 0 : a.split(`
`).filter((s) => !s.includes("svelte/src/internal")).join(`
`)
    };
  }
}
function yi(e) {
  const t = Ln.get(e);
  t && (Te(e, "message", {
    value: t.message
  }), Te(e, "stack", {
    value: t.stack
  }));
}
const hc = -7169;
function T(e, t) {
  e.f = e.f & hc | t;
}
function dr(e) {
  (e.f & se) !== 0 || e.deps === null ? T(e, j) : T(e, ye);
}
function Hi(e) {
  if (e !== null)
    for (const t of e)
      (t.f & z) === 0 || (t.f & Je) === 0 || (t.f ^= Je, Hi(
        /** @type {Derived} */
        t.deps
      ));
}
function bc(e, t, n) {
  (e.f & P) !== 0 ? t.add(e) : (e.f & ye) !== 0 && n.add(e), Hi(e.deps), T(e, j);
}
let gn = !1;
function gc(e) {
  var t = gn;
  try {
    return gn = !1, [e(), gn];
  } finally {
    gn = t;
  }
}
const Oe = /* @__PURE__ */ new Set();
let Z = null, D = null, Qn = null, Jt = !1, Tn = !1, bt = null, _n = null;
var Ar = 0, _c = b ? /* @__PURE__ */ new Set() : null;
let Xc = 1;
var gt, _t, Xt, mt, $t, K, et, Ge, Fe, xt, L, Un, $n, Kn, qn, Zi;
const Fn = class Fn {
  constructor() {
    E(this, L);
    // for debugging. TODO remove once async is stable
    Se(this, "id", Xc++);
    /**
     * The current values of any sources that are updated in this batch
     * They keys of this map are identical to `this.#previous`
     * @type {Map<Source, any>}
     */
    Se(this, "current", /* @__PURE__ */ new Map());
    /**
     * The values of any sources that are updated in this batch _before_ those updates took place.
     * They keys of this map are identical to `this.#current`
     * @type {Map<Source, any>}
     */
    Se(this, "previous", /* @__PURE__ */ new Map());
    /**
     * When the batch is committed (and the DOM is updated), we need to remove old branches
     * and append new ones by calling the functions added inside (if/each/key/etc) blocks
     * @type {Set<(batch: Batch) => void>}
     */
    E(this, gt, /* @__PURE__ */ new Set());
    /**
     * If a fork is discarded, we need to destroy any effects that are no longer needed
     * @type {Set<(batch: Batch) => void>}
     */
    E(this, _t, /* @__PURE__ */ new Set());
    /**
     * The number of async effects that are currently in flight
     */
    E(this, Xt, 0);
    /**
     * The number of async effects that are currently in flight, _not_ inside a pending boundary
     */
    E(this, mt, 0);
    /**
     * A deferred that resolves when the batch is committed, used with `settled()`
     * TODO replace with Promise.withResolvers once supported widely enough
     * @type {{ promise: Promise<void>, resolve: (value?: any) => void, reject: (reason: unknown) => void } | null}
     */
    E(this, $t, null);
    /**
     * The root effects that need to be flushed
     * @type {Effect[]}
     */
    E(this, K, []);
    /**
     * Deferred effects (which run after async work has completed) that are DIRTY
     * @type {Set<Effect>}
     */
    E(this, et, /* @__PURE__ */ new Set());
    /**
     * Deferred effects that are MAYBE_DIRTY
     * @type {Set<Effect>}
     */
    E(this, Ge, /* @__PURE__ */ new Set());
    /**
     * A map of branches that still exist, but will be destroyed when this batch
     * is committed — we skip over these during `process`.
     * The value contains child effects that were dirty/maybe_dirty before being reset,
     * so they can be rescheduled if the branch survives.
     * @type {Map<Effect, { d: Effect[], m: Effect[] }>}
     */
    E(this, Fe, /* @__PURE__ */ new Map());
    Se(this, "is_fork", !1);
    E(this, xt, !1);
  }
  /**
   * Add an effect to the #skipped_branches map and reset its children
   * @param {Effect} effect
   */
  skip_effect(t) {
    X(this, Fe).has(t) || X(this, Fe).set(t, { d: [], m: [] });
  }
  /**
   * Remove an effect from the #skipped_branches map and reschedule
   * any tracked dirty/maybe_dirty child effects
   * @param {Effect} effect
   */
  unskip_effect(t) {
    var n = X(this, Fe).get(t);
    if (n) {
      X(this, Fe).delete(t);
      for (var r of n.d)
        T(r, P), this.schedule(r);
      for (r of n.m)
        T(r, ye), this.schedule(r);
    }
  }
  /**
   * Associate a change to a given source with the current
   * batch, noting its previous and current values
   * @param {Source} source
   * @param {any} old_value
   */
  capture(t, n) {
    n !== O && !this.previous.has(t) && this.previous.set(t, n), (t.f & Be) === 0 && (this.current.set(t, t.v), D == null || D.set(t, t.v));
  }
  activate() {
    Z = this;
  }
  deactivate() {
    Z = null, D = null;
  }
  flush() {
    var t = b ? /* @__PURE__ */ new Set() : null;
    try {
      Tn = !0, Z = this, me(this, L, $n).call(this);
    } finally {
      if (Ar = 0, Qn = null, bt = null, _n = null, Tn = !1, Z = null, D = null, Ae.clear(), b)
        for (
          const n of
          /** @type {Set<Source>} */
          t
        )
          n.updated = null;
    }
  }
  discard() {
    for (const t of X(this, _t)) t(this);
    X(this, _t).clear(), Oe.delete(this);
  }
  /**
   *
   * @param {boolean} blocking
   */
  increment(t) {
    ve(this, Xt, X(this, Xt) + 1), t && ve(this, mt, X(this, mt) + 1);
  }
  /**
   * @param {boolean} blocking
   * @param {boolean} skip - whether to skip updates (because this is triggered by a stale reaction)
   */
  decrement(t, n) {
    ve(this, Xt, X(this, Xt) - 1), t && ve(this, mt, X(this, mt) - 1), !(X(this, xt) || n) && (ve(this, xt, !0), Ot(() => {
      ve(this, xt, !1), this.flush();
    }));
  }
  /**
   * @param {Set<Effect>} dirty_effects
   * @param {Set<Effect>} maybe_dirty_effects
   */
  transfer_effects(t, n) {
    for (const r of t)
      X(this, et).add(r);
    for (const r of n)
      X(this, Ge).add(r);
    t.clear(), n.clear();
  }
  /** @param {(batch: Batch) => void} fn */
  oncommit(t) {
    X(this, gt).add(t);
  }
  /** @param {(batch: Batch) => void} fn */
  ondiscard(t) {
    X(this, _t).add(t);
  }
  settled() {
    return (X(this, $t) ?? ve(this, $t, di())).promise;
  }
  static ensure() {
    if (Z === null) {
      const t = Z = new Fn();
      Tn || (Oe.add(Z), Jt || Ot(() => {
        Z === t && t.flush();
      }));
    }
    return Z;
  }
  apply() {
    {
      D = null;
      return;
    }
  }
  /**
   *
   * @param {Effect} effect
   */
  schedule(t) {
    var i;
    if (Qn = t, (i = t.b) != null && i.is_pending && (t.f & (wt | en | ar)) !== 0 && (t.f & st) === 0) {
      t.b.defer_effect(t);
      return;
    }
    for (var n = t; n.parent !== null; ) {
      n = n.parent;
      var r = n.f;
      if (bt !== null && n === G && (I === null || (I.f & z) === 0))
        return;
      if ((r & (yt | Xe)) !== 0) {
        if ((r & j) === 0)
          return;
        n.f ^= j;
      }
    }
    X(this, K).push(n);
  }
};
gt = new WeakMap(), _t = new WeakMap(), Xt = new WeakMap(), mt = new WeakMap(), $t = new WeakMap(), K = new WeakMap(), et = new WeakMap(), Ge = new WeakMap(), Fe = new WeakMap(), xt = new WeakMap(), L = new WeakSet(), Un = function() {
  return this.is_fork || X(this, mt) > 0;
}, $n = function() {
  var c, a;
  if (Ar++ > 1e3 && (Oe.delete(this), xc()), !me(this, L, Un).call(this)) {
    for (const s of X(this, et))
      X(this, Ge).delete(s), T(s, P), this.schedule(s);
    for (const s of X(this, Ge))
      T(s, ye), this.schedule(s);
  }
  const t = X(this, K);
  ve(this, K, []), this.apply();
  var n = bt = [], r = [], i = _n = [];
  for (const s of t)
    try {
      me(this, L, Kn).call(this, s, n, r);
    } catch (f) {
      throw Fi(s), f;
    }
  if (Z = null, i.length > 0) {
    var l = Fn.ensure();
    for (const s of i)
      l.schedule(s);
  }
  if (bt = null, _n = null, me(this, L, Un).call(this)) {
    me(this, L, qn).call(this, r), me(this, L, qn).call(this, n);
    for (const [s, f] of X(this, Fe))
      Gi(s, f);
  } else {
    X(this, Xt) === 0 && Oe.delete(this), X(this, et).clear(), X(this, Ge).clear();
    for (const s of X(this, gt)) s(this);
    X(this, gt).clear(), Tr(r), Tr(n), (c = X(this, $t)) == null || c.resolve();
  }
  var o = (
    /** @type {Batch | null} */
    /** @type {unknown} */
    Z
  );
  if (X(this, K).length > 0) {
    const s = o ?? (o = this);
    X(s, K).push(...X(this, K).filter((f) => !X(s, K).includes(f)));
  }
  if (o !== null) {
    if (Oe.add(o), b)
      for (const s of this.current.keys())
        _c.add(s);
    me(a = o, L, $n).call(a);
  }
  Oe.has(this) || me(this, L, Zi).call(this);
}, /**
 * Traverse the effect tree, executing effects or stashing
 * them for later execution as appropriate
 * @param {Effect} root
 * @param {Effect[]} effects
 * @param {Effect[]} render_effects
 */
Kn = function(t, n, r) {
  t.f ^= j;
  for (var i = t.first; i !== null; ) {
    var l = i.f, o = (l & (Xe | yt)) !== 0, c = o && (l & j) !== 0, a = c || (l & ie) !== 0 || X(this, Fe).has(i);
    if (!a && i.fn !== null) {
      o ? i.f ^= j : (l & wt) !== 0 ? n.push(i) : sn(i) && ((l & je) !== 0 && X(this, Ge).add(i), Rt(i));
      var s = i.first;
      if (s !== null) {
        i = s;
        continue;
      }
    }
    for (; i !== null; ) {
      var f = i.next;
      if (f !== null) {
        i = f;
        break;
      }
      i = i.parent;
    }
  }
}, /**
 * @param {Effect[]} effects
 */
qn = function(t) {
  for (var n = 0; n < t.length; n += 1)
    bc(t[n], X(this, et), X(this, Ge));
}, Zi = function() {
  var a;
  for (const s of Oe) {
    var t = s.id < this.id, n = [];
    for (const [f, d] of this.current) {
      if (s.current.has(f))
        if (t && d !== s.current.get(f))
          s.current.set(f, d);
        else
          continue;
      n.push(f);
    }
    var r = [...s.current.keys()].filter((f) => !this.current.has(f));
    if (r.length === 0)
      t && s.discard();
    else if (n.length > 0) {
      b && uc(X(s, K).length === 0, "Batch has scheduled roots"), s.activate();
      var i = /* @__PURE__ */ new Set(), l = /* @__PURE__ */ new Map();
      for (var o of n)
        Ii(o, r, i, l);
      if (X(s, K).length > 0) {
        s.apply();
        for (var c of X(s, K))
          me(a = s, L, Kn).call(a, c, [], []);
        ve(s, K, []);
      }
      s.deactivate();
    }
  }
};
let zt = Fn;
function mc(e) {
  var t = Jt;
  Jt = !0;
  try {
    for (var n; ; ) {
      if (dc(), Z === null)
        return (
          /** @type {T} */
          n
        );
      Z.flush();
    }
  } finally {
    Jt = t;
  }
}
function xc() {
  if (b) {
    var e = /* @__PURE__ */ new Map();
    for (
      const n of
      /** @type {Batch} */
      Z.current.keys()
    )
      for (const [r, i] of n.updated ?? []) {
        var t = e.get(r);
        t || (t = { error: i.error, count: 0 }, e.set(r, t)), t.count += i.count;
      }
    for (const n of e.values())
      n.error && console.error(n.error);
  }
  try {
    Kl();
  } catch (n) {
    b && Te(n, "stack", { value: "" }), Zn(n, Qn);
  }
}
let he = null;
function Tr(e) {
  var t = e.length;
  if (t !== 0) {
    for (var n = 0; n < t; ) {
      var r = e[n++];
      if ((r.f & (ae | ie)) === 0 && sn(r) && (he = /* @__PURE__ */ new Set(), Rt(r), r.deps === null && r.first === null && r.nodes === null && r.teardown === null && r.ac === null && ji(r), (he == null ? void 0 : he.size) > 0)) {
        Ae.clear();
        for (const i of he) {
          if ((i.f & (ae | ie)) !== 0) continue;
          const l = [i];
          let o = i.parent;
          for (; o !== null; )
            he.has(o) && (he.delete(o), l.push(o)), o = o.parent;
          for (let c = l.length - 1; c >= 0; c--) {
            const a = l[c];
            (a.f & (ae | ie)) === 0 && Rt(a);
          }
        }
        he.clear();
      }
    }
    he = null;
  }
}
function Ii(e, t, n, r) {
  if (!n.has(e) && (n.add(e), e.reactions !== null))
    for (const i of e.reactions) {
      const l = i.f;
      (l & z) !== 0 ? Ii(
        /** @type {Derived} */
        i,
        t,
        n,
        r
      ) : (l & (Vn | je)) !== 0 && (l & P) === 0 && Ri(i, t, r) && (T(i, P), vr(
        /** @type {Effect} */
        i
      ));
    }
}
function Ri(e, t, n) {
  const r = n.get(e);
  if (r !== void 0) return r;
  if (e.deps !== null)
    for (const i of e.deps) {
      if (lt.call(t, i))
        return !0;
      if ((i.f & z) !== 0 && Ri(
        /** @type {Derived} */
        i,
        t,
        n
      ))
        return n.set(
          /** @type {Derived} */
          i,
          !0
        ), !0;
    }
  return n.set(e, !1), !1;
}
function vr(e) {
  Z.schedule(e);
}
function Gi(e, t) {
  if (!((e.f & Xe) !== 0 && (e.f & j) !== 0)) {
    (e.f & P) !== 0 ? t.d.push(e) : (e.f & ye) !== 0 && t.m.push(e), T(e, j);
    for (var n = e.first; n !== null; )
      Gi(n, t), n = n.next;
  }
}
function Fi(e) {
  T(e, j);
  for (var t = e.first; t !== null; )
    Fi(t), t = t.next;
}
function Wi(e, t, n, r) {
  const i = ln() ? cn : hr;
  var l = e.filter((u) => !u.settled);
  if (n.length === 0 && l.length === 0) {
    r(t.map(i));
    return;
  }
  var o = (
    /** @type {Effect} */
    G
  ), c = wc(), a = l.length === 1 ? l[0].promise : l.length > 1 ? Promise.all(l.map((u) => u.promise)) : null;
  function s(u) {
    c();
    try {
      r(u);
    } catch (_) {
      (o.f & ae) === 0 && Zn(_, o);
    }
    In();
  }
  if (n.length === 0) {
    a.then(() => s(t.map(i)));
    return;
  }
  var f = Ni();
  function d() {
    Promise.all(n.map((u) => /* @__PURE__ */ Hc(u))).then((u) => s([...t.map(i), ...u])).catch((u) => Zn(u, o)).finally(() => f());
  }
  a ? a.then(() => {
    c(), d(), In();
  }) : d();
}
function wc() {
  var e = (
    /** @type {Effect} */
    G
  ), t = I, n = V, r = (
    /** @type {Batch} */
    Z
  );
  if (b)
    var i = ge;
  return function(o = !0) {
    _e(e), He(t), wn(n), o && (e.f & ae) === 0 && (r == null || r.activate(), r == null || r.apply()), b && (pr(null), yn(i));
  };
}
async function vt(e) {
  var t = We, n = await e;
  return () => (pr(t), n);
}
function In(e = !0) {
  _e(null), He(null), wn(null), e && (Z == null || Z.deactivate()), b && (pr(null), yn(null));
}
function Ni() {
  var e = (
    /** @type {Boundary} */
    /** @type {Effect} */
    G.b
  ), t = (
    /** @type {Batch} */
    Z
  ), n = e.is_rendered();
  return e.update_pending_count(1, t), t.increment(n), (r = !1) => {
    e.update_pending_count(-1, t), t.decrement(n, r);
  };
}
let We = null;
function pr(e) {
  We = e;
}
const yc = /* @__PURE__ */ new Set();
// @__NO_SIDE_EFFECTS__
function cn(e) {
  var t = z | P, n = I !== null && (I.f & z) !== 0 ? (
    /** @type {Derived} */
    I
  ) : null;
  return G !== null && (G.f |= Nn), {
    ctx: V,
    deps: null,
    effects: null,
    equals: _i,
    f: t,
    fn: e,
    reactions: null,
    rv: 0,
    v: (
      /** @type {V} */
      O
    ),
    wv: 0,
    parent: n ?? G,
    ac: null
  };
}
// @__NO_SIDE_EFFECTS__
function Hc(e, t, n) {
  let r = (
    /** @type {Effect | null} */
    G
  );
  r === null && Ol();
  var i = (
    /** @type {Promise<V>} */
    /** @type {unknown} */
    void 0
  ), l = It(
    /** @type {V} */
    O
  );
  b && (l.label = t);
  var o = !I, c = /* @__PURE__ */ new Map();
  return Mc(() => {
    var _;
    b && (We = {
      effect: (
        /** @type {Effect} */
        G
      ),
      warned: !1
    });
    var a = (
      /** @type {Effect} */
      G
    ), s = di();
    i = s.promise;
    try {
      Promise.resolve(e()).then(s.resolve, s.reject).finally(In);
    } catch (p) {
      s.reject(p), In();
    }
    b && (We = null);
    var f = (
      /** @type {Batch} */
      Z
    );
    if (o) {
      if ((a.f & st) !== 0)
        var d = Ni();
      if (
        /** @type {Boundary} */
        r.b.is_rendered()
      )
        (_ = c.get(f)) == null || _.reject(Re), c.delete(f);
      else {
        for (const p of c.values())
          p.reject(Re);
        c.clear();
      }
      c.set(f, s);
    }
    const u = (p, x = void 0) => {
      if (b && (We = null), d) {
        var v = x === Re;
        d(v);
      }
      if (!(x === Re || (a.f & ae) !== 0)) {
        if (f.activate(), x)
          l.f |= Be, Dt(l, x);
        else {
          (l.f & Be) !== 0 && (l.f ^= Be), Dt(l, p);
          for (const [h, W] of c) {
            if (c.delete(h), h === f) break;
            W.reject(Re);
          }
        }
        f.deactivate();
      }
    };
    s.promise.then(u, (p) => u(null, p || "unknown"));
  }), Xr(() => {
    for (const a of c.values())
      a.reject(Re);
  }), b && (l.f |= Vn), new Promise((a) => {
    function s(f) {
      function d() {
        f === i ? a(l) : s(i);
      }
      f.then(d, d);
    }
    s(i);
  });
}
// @__NO_SIDE_EFFECTS__
function Zc(e) {
  const t = /* @__PURE__ */ cn(e);
  return Di(t), t;
}
// @__NO_SIDE_EFFECTS__
function hr(e) {
  const t = /* @__PURE__ */ cn(e);
  return t.equals = Xi, t;
}
function Jr(e) {
  var t = e.effects;
  if (t !== null) {
    e.effects = null;
    for (var n = 0; n < t.length; n += 1)
      fe(
        /** @type {Effect} */
        t[n]
      );
  }
}
let Jn = [];
function Ic(e) {
  for (var t = e.parent; t !== null; ) {
    if ((t.f & z) === 0)
      return (t.f & ae) === 0 ? (
        /** @type {Effect} */
        t
      ) : null;
    t = t.parent;
  }
  return null;
}
function br(e) {
  var t, n = G;
  if (_e(Ic(e)), b) {
    let r = Zt;
    Er(/* @__PURE__ */ new Set());
    try {
      lt.call(Jn, e) && Pl(), Jn.push(e), e.f &= ~Je, Jr(e), t = er(e);
    } finally {
      _e(n), Er(r), Jn.pop();
    }
  } else
    try {
      e.f &= ~Je, Jr(e), t = er(e);
    } finally {
      _e(n);
    }
  return t;
}
function Vi(e) {
  var t = e.v, n = br(e);
  if (!e.equals(n) && (e.wv = Li(), (!(Z != null && Z.is_fork) || e.deps === null) && (e.v = n, Z == null || Z.capture(e, t), e.deps === null))) {
    T(e, j);
    return;
  }
  Ee || (D !== null ? (Ai() || Z != null && Z.is_fork) && D.set(e, n) : dr(e));
}
function Rc(e) {
  var t, n;
  if (e.effects !== null)
    for (const r of e.effects)
      (r.teardown || r.ac) && ((t = r.teardown) == null || t.call(r), (n = r.ac) == null || n.abort(Re), r.teardown = Cl, r.ac = null, Lt(r, 0), wr(r));
}
function Ci(e) {
  if (e.effects !== null)
    for (const t of e.effects)
      t.teardown && Rt(t);
}
let Zt = /* @__PURE__ */ new Set();
const Ae = /* @__PURE__ */ new Map();
function Er(e) {
  Zt = e;
}
let gr = !1;
function Gc() {
  gr = !0;
}
function It(e, t) {
  var n = {
    f: 0,
    // TODO ideally we could skip this altogether, but it causes type errors
    v: e,
    reactions: null,
    equals: _i,
    rv: 0,
    wv: 0
  };
  return n;
}
// @__NO_SIDE_EFFECTS__
function Y(e, t) {
  const n = It(e);
  return Di(n), n;
}
// @__NO_SIDE_EFFECTS__
function Fc(e, t = !1, n = !0) {
  var i;
  const r = It(e);
  return t || (r.equals = Xi), tn && n && V !== null && V.l !== null && ((i = V.l).s ?? (i.s = [])).push(r), r;
}
function F(e, t, n = !1) {
  I !== null && // since we are untracking the function inside `$inspect.with` we need to add this check
  // to ensure we error if state is set inside an inspect effect
  (!oe || (I.f & mn) !== 0) && ln() && (I.f & (z | je | Vn | mn)) !== 0 && (ue === null || !lt.call(ue, e)) && rc();
  let r = n ? $e(t) : t;
  return b && mi(
    r,
    /** @type {string} */
    e.label
  ), Dt(e, r, _n);
}
function Dt(e, t, n = null) {
  var l;
  if (!e.equals(t)) {
    var r = e.v;
    Ee ? Ae.set(e, t) : Ae.set(e, r), e.v = t;
    var i = zt.ensure();
    if (i.capture(e, r), b) {
      if (G !== null) {
        e.updated ?? (e.updated = /* @__PURE__ */ new Map());
        const o = (((l = e.updated.get("")) == null ? void 0 : l.count) ?? 0) + 1;
        if (e.updated.set("", { error: (
          /** @type {any} */
          null
        ), count: o }), o > 5) {
          const c = xi("updated at");
          if (c !== null) {
            let a = e.updated.get(c.stack);
            a || (a = { error: c, count: 0 }, e.updated.set(c.stack, a)), a.count++;
          }
        }
      }
      G !== null && (e.set_during_effect = !0);
    }
    if ((e.f & z) !== 0) {
      const o = (
        /** @type {Derived} */
        e
      );
      (e.f & P) !== 0 && br(o), D === null && dr(o);
    }
    e.wv = Li(), ki(e, P, n), ln() && G !== null && (G.f & j) !== 0 && (G.f & (Xe | yt)) === 0 && (ce === null ? Pc([e]) : ce.push(e)), !i.is_fork && Zt.size > 0 && !gr && Si();
  }
  return t;
}
function Si() {
  gr = !1;
  for (const e of Zt)
    (e.f & j) !== 0 && T(e, ye), sn(e) && Rt(e);
  Zt.clear();
}
function jr(e, t = 1) {
  var n = g(e), r = t === 1 ? n++ : n--;
  return F(e, n), r;
}
function En(e) {
  F(e, e.v + 1);
}
function ki(e, t, n) {
  var r = e.reactions;
  if (r !== null)
    for (var i = ln(), l = r.length, o = 0; o < l; o++) {
      var c = r[o], a = c.f;
      if (!(!i && c === G)) {
        if (b && (a & mn) !== 0) {
          Zt.add(c);
          continue;
        }
        var s = (a & P) === 0;
        if (s && T(c, t), (a & z) !== 0) {
          var f = (
            /** @type {Derived} */
            c
          );
          D == null || D.delete(f), (a & Je) === 0 && (a & se && (c.f |= Je), ki(f, ye, n));
        } else if (s) {
          var d = (
            /** @type {Effect} */
            c
          );
          (a & je) !== 0 && he !== null && he.add(d), n !== null ? n.push(d) : vr(d);
        }
      }
    }
}
const Wc = /^[a-zA-Z_$][a-zA-Z_$0-9]*$/;
function $e(e) {
  if (typeof e != "object" || e === null || Ne in e)
    return e;
  const t = sr(e);
  if (t !== Nl && t !== Vl)
    return e;
  var n = /* @__PURE__ */ new Map(), r = cr(e), i = /* @__PURE__ */ Y(0), l = it, o = (f) => {
    if (it === l)
      return f();
    var d = I, u = it;
    He(null), Dr(l);
    var _ = f();
    return He(d), Dr(u), _;
  };
  r && (n.set("length", /* @__PURE__ */ Y(
    /** @type {any[]} */
    e.length
  )), b && (e = /** @type {any} */
  Cc(
    /** @type {any[]} */
    e
  )));
  var c = "";
  let a = !1;
  function s(f) {
    if (!a) {
      a = !0, c = f, k(i, `${c} version`);
      for (const [d, u] of n)
        k(u, ze(c, d));
      a = !1;
    }
  }
  return new Proxy(
    /** @type {any} */
    e,
    {
      defineProperty(f, d, u) {
        (!("value" in u) || u.configurable === !1 || u.enumerable === !1 || u.writable === !1) && tc();
        var _ = n.get(d);
        return _ === void 0 ? o(() => {
          var p = /* @__PURE__ */ Y(u.value);
          return n.set(d, p), b && typeof d == "string" && k(p, ze(c, d)), p;
        }) : F(_, u.value, !0), !0;
      },
      deleteProperty(f, d) {
        var u = n.get(d);
        if (u === void 0) {
          if (d in f) {
            const _ = o(() => /* @__PURE__ */ Y(O));
            n.set(d, _), En(i), b && k(_, ze(c, d));
          }
        } else
          F(u, O), En(i);
        return !0;
      },
      get(f, d, u) {
        var v;
        if (d === Ne)
          return e;
        if (b && d === hi)
          return s;
        var _ = n.get(d), p = d in f;
        if (_ === void 0 && (!p || (v = nt(f, d)) != null && v.writable) && (_ = o(() => {
          var h = $e(p ? f[d] : O), W = /* @__PURE__ */ Y(h);
          return b && k(W, ze(c, d)), W;
        }), n.set(d, _)), _ !== void 0) {
          var x = g(_);
          return x === O ? void 0 : x;
        }
        return Reflect.get(f, d, u);
      },
      getOwnPropertyDescriptor(f, d) {
        var u = Reflect.getOwnPropertyDescriptor(f, d);
        if (u && "value" in u) {
          var _ = n.get(d);
          _ && (u.value = g(_));
        } else if (u === void 0) {
          var p = n.get(d), x = p == null ? void 0 : p.v;
          if (p !== void 0 && x !== O)
            return {
              enumerable: !0,
              configurable: !0,
              value: x,
              writable: !0
            };
        }
        return u;
      },
      has(f, d) {
        var x;
        if (d === Ne)
          return !0;
        var u = n.get(d), _ = u !== void 0 && u.v !== O || Reflect.has(f, d);
        if (u !== void 0 || G !== null && (!_ || (x = nt(f, d)) != null && x.writable)) {
          u === void 0 && (u = o(() => {
            var v = _ ? $e(f[d]) : O, h = /* @__PURE__ */ Y(v);
            return b && k(h, ze(c, d)), h;
          }), n.set(d, u));
          var p = g(u);
          if (p === O)
            return !1;
        }
        return _;
      },
      set(f, d, u, _) {
        var C;
        var p = n.get(d), x = d in f;
        if (r && d === "length")
          for (var v = u; v < /** @type {Source<number>} */
          p.v; v += 1) {
            var h = n.get(v + "");
            h !== void 0 ? F(h, O) : v in f && (h = o(() => /* @__PURE__ */ Y(O)), n.set(v + "", h), b && k(h, ze(c, v)));
          }
        if (p === void 0)
          (!x || (C = nt(f, d)) != null && C.writable) && (p = o(() => /* @__PURE__ */ Y(void 0)), b && k(p, ze(c, d)), F(p, $e(u)), n.set(d, p));
        else {
          x = p.v !== O;
          var W = o(() => $e(u));
          F(p, W);
        }
        var w = Reflect.getOwnPropertyDescriptor(f, d);
        if (w != null && w.set && w.set.call(_, u), !x) {
          if (r && typeof d == "string") {
            var m = (
              /** @type {Source<number>} */
              n.get("length")
            ), R = Number(d);
            Number.isInteger(R) && R >= m.v && F(m, R + 1);
          }
          En(i);
        }
        return !0;
      },
      ownKeys(f) {
        g(i);
        var d = Reflect.ownKeys(f).filter((p) => {
          var x = n.get(p);
          return x === void 0 || x.v !== O;
        });
        for (var [u, _] of n)
          _.v !== O && !(u in f) && d.push(u);
        return d;
      },
      setPrototypeOf() {
        nc();
      }
    }
  );
}
function ze(e, t) {
  return typeof t == "symbol" ? `${e}[Symbol(${t.description ?? ""})]` : Wc.test(t) ? `${e}.${t}` : /^\d+$/.test(t) ? `${e}[${t}]` : `${e}['${t}']`;
}
function Rn(e) {
  try {
    if (e !== null && typeof e == "object" && Ne in e)
      return e[Ne];
  } catch {
  }
  return e;
}
function Nc(e, t) {
  return Object.is(Rn(e), Rn(t));
}
const Vc = /* @__PURE__ */ new Set([
  "copyWithin",
  "fill",
  "pop",
  "push",
  "reverse",
  "shift",
  "sort",
  "splice",
  "unshift"
]);
function Cc(e) {
  return new Proxy(e, {
    get(t, n, r) {
      var i = Reflect.get(t, n, r);
      return Vc.has(
        /** @type {string} */
        n
      ) ? function(...l) {
        Gc();
        var o = i.apply(this, l);
        return Si(), o;
      } : i;
    }
  });
}
function pe(e, t, n = !0) {
  try {
    e === t != (Rn(e) === Rn(t)) && cc(n ? "===" : "!==");
  } catch {
  }
  return e === t === n;
}
var Sc, kc, Yc;
function rt(e = "") {
  return document.createTextNode(e);
}
// @__NO_SIDE_EFFECTS__
function Pt(e) {
  return (
    /** @type {TemplateNode | null} */
    kc.call(e)
  );
}
// @__NO_SIDE_EFFECTS__
function on(e) {
  return (
    /** @type {TemplateNode | null} */
    Yc.call(e)
  );
}
function S(e, t) {
  return /* @__PURE__ */ Pt(e);
}
function Cn(e, t = !1) {
  {
    var n = /* @__PURE__ */ Pt(e);
    return n instanceof Comment && n.data === "" ? /* @__PURE__ */ on(n) : n;
  }
}
function M(e, t = 1, n = !1) {
  let r = e;
  for (; t--; )
    r = /** @type {TemplateNode} */
    /* @__PURE__ */ on(r);
  return r;
}
function Bc(e) {
  e.textContent = "";
}
function Yi() {
  return !1;
}
function _r(e, t, n) {
  return (
    /** @type {T extends keyof HTMLElementTagNameMap ? HTMLElementTagNameMap[T] : Element} */
    document.createElementNS(t ?? fi, e, void 0)
  );
}
function Ac(e, t) {
  if (t) {
    const n = document.body;
    e.autofocus = !0, Ot(() => {
      document.activeElement === n && e.focus();
    });
  }
}
let Mr = !1;
function Tc() {
  Mr || (Mr = !0, document.addEventListener(
    "reset",
    (e) => {
      Promise.resolve().then(() => {
        var t;
        if (!e.defaultPrevented)
          for (
            const n of
            /**@type {HTMLFormElement} */
            e.target.elements
          )
            (t = n.__on_r) == null || t.call(n);
      });
    },
    // In the capture phase to guarantee we get noticed of it (no possibility of stopPropagation)
    { capture: !0 }
  ));
}
function Sn(e) {
  var t = I, n = G;
  He(null), _e(null);
  try {
    return e();
  } finally {
    He(t), _e(n);
  }
}
function Jc(e, t, n, r = n) {
  e.addEventListener(t, () => Sn(n));
  const i = e.__on_r;
  i ? e.__on_r = () => {
    i(), r(!0);
  } : e.__on_r = () => r(!0), Tc();
}
function Bi(e) {
  G === null && (I === null && $l(e), Ul()), Ee && Ql(e);
}
function Ec(e, t) {
  var n = t.last;
  n === null ? t.last = t.first = e : (n.next = e, e.prev = n, t.last = e);
}
function Ze(e, t) {
  var n = G;
  if (b)
    for (; n !== null && (n.f & mn) !== 0; )
      n = n.parent;
  n !== null && (n.f & ie) !== 0 && (e |= ie);
  var r = {
    ctx: V,
    deps: null,
    nodes: null,
    f: e | P | se,
    first: null,
    fn: t,
    last: null,
    next: null,
    parent: n,
    b: n && n.b,
    prev: null,
    teardown: null,
    wv: 0,
    ac: null
  };
  b && (r.component_function = Gt);
  var i = r;
  if ((e & wt) !== 0)
    bt !== null ? bt.push(r) : zt.ensure().schedule(r);
  else if (t !== null) {
    try {
      Rt(r);
    } catch (o) {
      throw fe(r), o;
    }
    i.deps === null && i.teardown === null && i.nodes === null && i.first === i.last && // either `null`, or a singular child
    (i.f & Nn) === 0 && (i = i.first, (e & je) !== 0 && (e & Ht) !== 0 && i !== null && (i.f |= Ht));
  }
  if (i !== null && (i.parent = n, n !== null && Ec(i, n), I !== null && (I.f & z) !== 0 && (e & yt) === 0)) {
    var l = (
      /** @type {Derived} */
      I
    );
    (l.effects ?? (l.effects = [])).push(i);
  }
  return r;
}
function Ai() {
  return I !== null && !oe;
}
function Xr(e) {
  const t = Ze(en, null);
  return T(t, j), t.teardown = e, t;
}
function Or(e) {
  Bi("$effect"), b && Te(e, "name", {
    value: "$effect"
  });
  var t = (
    /** @type {Effect} */
    G.f
  ), n = !I && (t & Xe) !== 0 && (t & st) === 0;
  if (n) {
    var r = (
      /** @type {ComponentContext} */
      V
    );
    (r.e ?? (r.e = [])).push(e);
  } else
    return Ti(e);
}
function Ti(e) {
  return Ze(wt | vi, e);
}
function jc(e) {
  return Bi("$effect.pre"), b && Te(e, "name", {
    value: "$effect.pre"
  }), Ze(en | vi, e);
}
function mr(e) {
  return Ze(wt, e);
}
function Mc(e) {
  return Ze(Vn | Nn, e);
}
function Oc(e, t = 0) {
  return Ze(en | t, e);
}
function De(e, t = [], n = [], r = []) {
  Wi(r, t, n, (i) => {
    Ze(en, () => e(...i.map(g)));
  });
}
function xr(e, t = 0) {
  var n = Ze(je | t, e);
  return b && (n.dev_stack = ge), n;
}
function Ji(e, t = 0) {
  var n = Ze(ar | t, e);
  return b && (n.dev_stack = ge), n;
}
function ct(e) {
  return Ze(Xe | Nn, e);
}
function Ei(e) {
  var t = e.teardown;
  if (t !== null) {
    const n = Ee, r = I;
    zr(!0), He(null);
    try {
      t.call(null);
    } finally {
      zr(n), He(r);
    }
  }
}
function wr(e, t = !1) {
  var n = e.first;
  for (e.first = e.last = null; n !== null; ) {
    const i = n.ac;
    i !== null && Sn(() => {
      i.abort(Re);
    });
    var r = n.next;
    (n.f & yt) !== 0 ? n.parent = null : fe(n, t), n = r;
  }
}
function zc(e) {
  for (var t = e.first; t !== null; ) {
    var n = t.next;
    (t.f & Xe) === 0 && fe(t), t = n;
  }
}
function fe(e, t = !0) {
  var n = !1;
  (t || (e.f & Bl) !== 0) && e.nodes !== null && e.nodes.end !== null && (Dc(
    e.nodes.start,
    /** @type {TemplateNode} */
    e.nodes.end
  ), n = !0), T(e, Yr), wr(e, t && !n), Lt(e, 0);
  var r = e.nodes && e.nodes.t;
  if (r !== null)
    for (const l of r)
      l.stop();
  Ei(e), e.f ^= Yr, e.f |= ae;
  var i = e.parent;
  i !== null && i.first !== null && ji(e), b && (e.component_function = null), e.next = e.prev = e.teardown = e.ctx = e.deps = e.fn = e.nodes = e.ac = null;
}
function Dc(e, t) {
  for (; e !== null; ) {
    var n = e === t ? null : /* @__PURE__ */ on(e);
    e.remove(), e = n;
  }
}
function ji(e) {
  var t = e.parent, n = e.prev, r = e.next;
  n !== null && (n.next = r), r !== null && (r.prev = n), t !== null && (t.first === e && (t.first = r), t.last === e && (t.last = n));
}
function yr(e, t, n = !0) {
  var r = [];
  Mi(e, r, !0);
  var i = () => {
    n && fe(e), t && t();
  }, l = r.length;
  if (l > 0) {
    var o = () => --l || i();
    for (var c of r)
      c.out(o);
  } else
    i();
}
function Mi(e, t, n) {
  if ((e.f & ie) === 0) {
    e.f ^= ie;
    var r = e.nodes && e.nodes.t;
    if (r !== null)
      for (const c of r)
        (c.is_global || n) && t.push(c);
    for (var i = e.first; i !== null; ) {
      var l = i.next, o = (i.f & Ht) !== 0 || // If this is a branch effect without a block effect parent,
      // it means the parent block effect was pruned. In that case,
      // transparency information was transferred to the branch effect.
      (i.f & Xe) !== 0 && (e.f & je) !== 0;
      Mi(i, t, o ? n : !1), i = l;
    }
  }
}
function Hr(e) {
  Oi(e, !0);
}
function Oi(e, t) {
  if ((e.f & ie) !== 0) {
    e.f ^= ie, (e.f & j) === 0 && (T(e, P), zt.ensure().schedule(e));
    for (var n = e.first; n !== null; ) {
      var r = n.next, i = (n.f & Ht) !== 0 || (n.f & Xe) !== 0;
      Oi(n, i ? t : !1), n = r;
    }
    var l = e.nodes && e.nodes.t;
    if (l !== null)
      for (const o of l)
        (o.is_global || t) && o.in();
  }
}
function zi(e, t) {
  if (e.nodes)
    for (var n = e.nodes.start, r = e.nodes.end; n !== null; ) {
      var i = n === r ? null : /* @__PURE__ */ on(n);
      t.append(n), n = i;
    }
}
let Xn = !1, Ee = !1;
function zr(e) {
  Ee = e;
}
let I = null, oe = !1;
function He(e) {
  I = e;
}
let G = null;
function _e(e) {
  G = e;
}
let ue = null;
function Di(e) {
  I !== null && (ue === null ? ue = [e] : ue.push(e));
}
let ee = null, ne = 0, ce = null;
function Pc(e) {
  ce = e;
}
let Pi = 1, Ke = 0, it = Ke;
function Dr(e) {
  it = e;
}
function Li() {
  return ++Pi;
}
function sn(e) {
  var t = e.f;
  if ((t & P) !== 0)
    return !0;
  if (t & z && (e.f &= ~Je), (t & ye) !== 0) {
    for (var n = (
      /** @type {Value[]} */
      e.deps
    ), r = n.length, i = 0; i < r; i++) {
      var l = n[i];
      if (sn(
        /** @type {Derived} */
        l
      ) && Vi(
        /** @type {Derived} */
        l
      ), l.wv > e.wv)
        return !0;
    }
    (t & se) !== 0 && // During time traveling we don't want to reset the status so that
    // traversal of the graph in the other batches still happens
    D === null && T(e, j);
  }
  return !1;
}
function Qi(e, t, n = !0) {
  var r = e.reactions;
  if (r !== null && !(ue !== null && lt.call(ue, e)))
    for (var i = 0; i < r.length; i++) {
      var l = r[i];
      (l.f & z) !== 0 ? Qi(
        /** @type {Derived} */
        l,
        t,
        !1
      ) : t === l && (n ? T(l, P) : (l.f & j) !== 0 && T(l, ye), vr(
        /** @type {Effect} */
        l
      ));
    }
}
function er(e) {
  var x;
  var t = ee, n = ne, r = ce, i = I, l = ue, o = V, c = oe, a = it, s = e.f;
  ee = /** @type {null | Value[]} */
  null, ne = 0, ce = null, I = (s & (Xe | yt)) === 0 ? e : null, ue = null, wn(e.ctx), oe = !1, it = ++Ke, e.ac !== null && (Sn(() => {
    e.ac.abort(Re);
  }), e.ac = null);
  try {
    e.f |= xn;
    var f = (
      /** @type {Function} */
      e.fn
    ), d = f();
    e.f |= st;
    var u = e.deps, _ = Z == null ? void 0 : Z.is_fork;
    if (ee !== null) {
      var p;
      if (_ || Lt(e, ne), u !== null && ne > 0)
        for (u.length = ne + ee.length, p = 0; p < ee.length; p++)
          u[ne + p] = ee[p];
      else
        e.deps = u = ee;
      if (Ai() && (e.f & se) !== 0)
        for (p = ne; p < u.length; p++)
          ((x = u[p]).reactions ?? (x.reactions = [])).push(e);
    } else !_ && u !== null && ne < u.length && (Lt(e, ne), u.length = ne);
    if (ln() && ce !== null && !oe && u !== null && (e.f & (z | ye | P)) === 0)
      for (p = 0; p < /** @type {Source[]} */
      ce.length; p++)
        Qi(
          ce[p],
          /** @type {Effect} */
          e
        );
    if (i !== null && i !== e) {
      if (Ke++, i.deps !== null)
        for (let v = 0; v < n; v += 1)
          i.deps[v].rv = Ke;
      if (t !== null)
        for (const v of t)
          v.rv = Ke;
      ce !== null && (r === null ? r = ce : r.push(.../** @type {Source[]} */
      ce));
    }
    return (e.f & Be) !== 0 && (e.f ^= Be), d;
  } catch (v) {
    return vc(v);
  } finally {
    e.f ^= xn, ee = t, ne = n, ce = r, I = i, ue = l, wn(o), oe = c, it = a;
  }
}
function Lc(e, t) {
  let n = t.reactions;
  if (n !== null) {
    var r = Wl.call(n, e);
    if (r !== -1) {
      var i = n.length - 1;
      i === 0 ? n = t.reactions = null : (n[r] = n[i], n.pop());
    }
  }
  if (n === null && (t.f & z) !== 0 && // Destroying a child effect while updating a parent effect can cause a dependency to appear
  // to be unused, when in fact it is used by the currently-updating parent. Checking `new_deps`
  // allows us to skip the expensive work of disconnecting and immediately reconnecting it
  (ee === null || !lt.call(ee, t))) {
    var l = (
      /** @type {Derived} */
      t
    );
    (l.f & se) !== 0 && (l.f ^= se, l.f &= ~Je), dr(l), Rc(l), Lt(l, 0);
  }
}
function Lt(e, t) {
  var n = e.deps;
  if (n !== null)
    for (var r = t; r < n.length; r++)
      Lc(e, n[r]);
}
function Rt(e) {
  var t = e.f;
  if ((t & ae) === 0) {
    T(e, j);
    var n = G, r = Xn;
    if (G = e, Xn = !0, b) {
      var i = Gt;
      Hn(e.component_function);
      var l = (
        /** @type {any} */
        ge
      );
      yn(e.dev_stack ?? ge);
    }
    try {
      (t & (je | ar)) !== 0 ? zc(e) : wr(e), Ei(e);
      var o = er(e);
      e.teardown = typeof o == "function" ? o : null, e.wv = Pi;
      var c;
      b && sc && (e.f & P) !== 0 && e.deps;
    } finally {
      Xn = r, G = n, b && (Hn(i), yn(l));
    }
  }
}
async function Qc() {
  await Promise.resolve(), mc();
}
function g(e) {
  var t = e.f, n = (t & z) !== 0;
  if (I !== null && !oe) {
    var r = G !== null && (G.f & ae) !== 0;
    if (!r && (ue === null || !lt.call(ue, e))) {
      var i = I.deps;
      if ((I.f & xn) !== 0)
        e.rv < Ke && (e.rv = Ke, ee === null && i !== null && i[ne] === e ? ne++ : ee === null ? ee = [e] : ee.push(e));
      else {
        (I.deps ?? (I.deps = [])).push(e);
        var l = e.reactions;
        l === null ? e.reactions = [I] : lt.call(l, I) || l.push(I);
      }
    }
  }
  if (b) {
    if (!oe && We && !We.warned && (We.effect.f & xn) === 0) {
      We.warned = !0, ic(
        /** @type {string} */
        e.label
      );
      var o = xi("traced at");
      o && console.warn(o);
    }
    yc.delete(e);
  }
  if (Ee && Ae.has(e))
    return Ae.get(e);
  if (n) {
    var c = (
      /** @type {Derived} */
      e
    );
    if (Ee) {
      var a = c.v;
      return ((c.f & j) === 0 && c.reactions !== null || $i(c)) && (a = br(c)), Ae.set(c, a), a;
    }
    var s = (c.f & se) === 0 && !oe && I !== null && (Xn || (I.f & se) !== 0), f = (c.f & st) === 0;
    sn(c) && (s && (c.f |= se), Vi(c)), s && !f && (Ci(c), Ui(c));
  }
  if (D != null && D.has(e))
    return D.get(e);
  if ((e.f & Be) !== 0)
    throw e.v;
  return e.v;
}
function Ui(e) {
  if (e.f |= se, e.deps !== null)
    for (const t of e.deps)
      (t.reactions ?? (t.reactions = [])).push(e), (t.f & z) !== 0 && (t.f & se) === 0 && (Ci(
        /** @type {Derived} */
        t
      ), Ui(
        /** @type {Derived} */
        t
      ));
}
function $i(e) {
  if (e.v === O) return !0;
  if (e.deps === null) return !1;
  for (const t of e.deps)
    if (Ae.has(t) || (t.f & z) !== 0 && $i(
      /** @type {Derived} */
      t
    ))
      return !0;
  return !1;
}
function Qt(e) {
  var t = oe;
  try {
    return oe = !0, e();
  } finally {
    oe = t;
  }
}
function ht(e) {
  if (!(typeof e != "object" || !e || e instanceof EventTarget)) {
    if (Ne in e)
      tr(e);
    else if (!Array.isArray(e))
      for (let t in e) {
        const n = e[t];
        typeof n == "object" && n && Ne in n && tr(n);
      }
  }
}
function tr(e, t = /* @__PURE__ */ new Set()) {
  if (typeof e == "object" && e !== null && // We don't want to traverse DOM elements
  !(e instanceof EventTarget) && !t.has(e)) {
    t.add(e), e instanceof Date && e.getTime();
    for (let r in e)
      try {
        tr(e[r], t);
      } catch {
      }
    const n = sr(e);
    if (n !== Object.prototype && n !== Array.prototype && n !== Map.prototype && n !== Set.prototype && n !== Date.prototype) {
      const r = ui(n);
      for (let i in r) {
        const l = r[i].get;
        if (l)
          try {
            l.call(e);
          } catch {
          }
      }
    }
  }
}
const qe = Symbol("events"), Uc = /* @__PURE__ */ new Set(), $c = /* @__PURE__ */ new Set();
function Kc(e, t, n, r = {}) {
  function i(l) {
    if (r.capture || qc.call(t, l), !l.cancelBubble)
      return Sn(() => n == null ? void 0 : n.call(this, l));
  }
  return e.startsWith("pointer") || e.startsWith("touch") || e === "wheel" ? Ot(() => {
    t.addEventListener(e, i, r);
  }) : t.addEventListener(e, i, r), i;
}
function Pe(e, t, n) {
  (t[qe] ?? (t[qe] = {}))[e] = n;
}
function Ki(e) {
  for (var t = 0; t < e.length; t++)
    Uc.add(e[t]);
  for (var n of $c)
    n(e);
}
let Pr = null;
function qc(e) {
  var v, h;
  var t = this, n = (
    /** @type {Node} */
    t.ownerDocument
  ), r = e.type, i = ((v = e.composedPath) == null ? void 0 : v.call(e)) || [], l = (
    /** @type {null | Element} */
    i[0] || e.target
  );
  Pr = e;
  var o = 0, c = Pr === e && e[qe];
  if (c) {
    var a = i.indexOf(c);
    if (a !== -1 && (t === document || t === /** @type {any} */
    window)) {
      e[qe] = t;
      return;
    }
    var s = i.indexOf(t);
    if (s === -1)
      return;
    a <= s && (o = a);
  }
  if (l = /** @type {Element} */
  i[o] || e.target, l !== t) {
    Te(e, "currentTarget", {
      configurable: !0,
      get() {
        return l || n;
      }
    });
    var f = I, d = G;
    He(null), _e(null);
    try {
      for (var u, _ = []; l !== null; ) {
        var p = l.assignedSlot || l.parentNode || /** @type {any} */
        l.host || null;
        try {
          var x = (h = l[qe]) == null ? void 0 : h[r];
          x != null && (!/** @type {any} */
          l.disabled || // DOM could've been updated already by the time this is reached, so we check this as well
          // -> the target could not have been disabled because it emits the event in the first place
          e.target === l) && x.call(l, e);
        } catch (W) {
          u ? _.push(W) : u = W;
        }
        if (e.cancelBubble || p === t || p === null)
          break;
        l = p;
      }
      if (u) {
        for (let W of _)
          queueMicrotask(() => {
            throw W;
          });
        throw u;
      }
    } finally {
      e[qe] = t, delete e.currentTarget, He(f), _e(d);
    }
  }
}
var oi;
const jn = (
  // We gotta write it like this because after downleveling the pure comment may end up in the wrong location
  ((oi = globalThis == null ? void 0 : globalThis.window) == null ? void 0 : oi.trustedTypes) && /* @__PURE__ */ globalThis.window.trustedTypes.createPolicy("svelte-trusted-html", {
    /** @param {string} html */
    createHTML: (e) => e
  })
);
function eo(e) {
  return (
    /** @type {string} */
    (jn == null ? void 0 : jn.createHTML(e)) ?? e
  );
}
function qi(e) {
  var t = _r("template");
  return t.innerHTML = eo(e.replaceAll("<!>", "<!---->")), t.content;
}
function kn(e, t) {
  var n = (
    /** @type {Effect} */
    G
  );
  n.nodes === null && (n.nodes = { start: e, end: t, a: null, t: null });
}
// @__NO_SIDE_EFFECTS__
function Ve(e, t) {
  var n = (t & Rl) !== 0, r, i = !e.startsWith("<!>");
  return () => {
    r === void 0 && (r = qi(i ? e : "<!>" + e), r = /** @type {TemplateNode} */
    /* @__PURE__ */ Pt(r));
    var l = (
      /** @type {TemplateNode} */
      n || Sc ? document.importNode(r, !0) : r.cloneNode(!0)
    );
    return kn(l, l), l;
  };
}
// @__NO_SIDE_EFFECTS__
function to(e, t, n = "svg") {
  var r = !e.startsWith("<!>"), i = `<${n}>${r ? e : "<!>" + e}</${n}>`, l;
  return () => {
    if (!l) {
      var o = (
        /** @type {DocumentFragment} */
        qi(i)
      ), c = (
        /** @type {Element} */
        /* @__PURE__ */ Pt(o)
      );
      l = /** @type {Element} */
      /* @__PURE__ */ Pt(c);
    }
    var a = (
      /** @type {TemplateNode} */
      l.cloneNode(!0)
    );
    return kn(a, a), a;
  };
}
// @__NO_SIDE_EFFECTS__
function no(e, t) {
  return /* @__PURE__ */ to(e, t, "svg");
}
function Yn() {
  var e = document.createDocumentFragment(), t = document.createComment(""), n = rt();
  return e.append(t, n), kn(t, n), e;
}
function q(e, t) {
  e !== null && e.before(
    /** @type {Node} */
    t
  );
}
function ro(e) {
  return e.endsWith("capture") && e !== "gotpointercapture" && e !== "lostpointercapture";
}
const io = [
  "beforeinput",
  "click",
  "change",
  "dblclick",
  "contextmenu",
  "focusin",
  "focusout",
  "input",
  "keydown",
  "keyup",
  "mousedown",
  "mousemove",
  "mouseout",
  "mouseover",
  "mouseup",
  "pointerdown",
  "pointermove",
  "pointerout",
  "pointerover",
  "pointerup",
  "touchend",
  "touchmove",
  "touchstart"
];
function lo(e) {
  return io.includes(e);
}
const co = {
  // no `class: 'className'` because we handle that separately
  formnovalidate: "formNoValidate",
  ismap: "isMap",
  nomodule: "noModule",
  playsinline: "playsInline",
  readonly: "readOnly",
  defaultvalue: "defaultValue",
  defaultchecked: "defaultChecked",
  srcobject: "srcObject",
  novalidate: "noValidate",
  allowfullscreen: "allowFullscreen",
  disablepictureinpicture: "disablePictureInPicture",
  disableremoteplayback: "disableRemotePlayback"
};
function oo(e) {
  return e = e.toLowerCase(), co[e] ?? e;
}
function ke(e, t) {
  var n = t == null ? "" : typeof t == "object" ? `${t}` : t;
  n !== (e.__t ?? (e.__t = e.nodeValue)) && (e.__t = n, e.nodeValue = `${n}`);
}
function so(e) {
  const t = e();
  t && !(typeof t == "string") && Ml();
}
function ao(e) {
  return e.toString = () => (jl(), ""), e;
}
var be, xe, re, tt, Kt, qt, Wn;
class el {
  /**
   * @param {TemplateNode} anchor
   * @param {boolean} transition
   */
  constructor(t, n = !0) {
    /** @type {TemplateNode} */
    Se(this, "anchor");
    /** @type {Map<Batch, Key>} */
    E(this, be, /* @__PURE__ */ new Map());
    /**
     * Map of keys to effects that are currently rendered in the DOM.
     * These effects are visible and actively part of the document tree.
     * Example:
     * ```
     * {#if condition}
     * 	foo
     * {:else}
     * 	bar
     * {/if}
     * ```
     * Can result in the entries `true->Effect` and `false->Effect`
     * @type {Map<Key, Effect>}
     */
    E(this, xe, /* @__PURE__ */ new Map());
    /**
     * Similar to #onscreen with respect to the keys, but contains branches that are not yet
     * in the DOM, because their insertion is deferred.
     * @type {Map<Key, Branch>}
     */
    E(this, re, /* @__PURE__ */ new Map());
    /**
     * Keys of effects that are currently outroing
     * @type {Set<Key>}
     */
    E(this, tt, /* @__PURE__ */ new Set());
    /**
     * Whether to pause (i.e. outro) on change, or destroy immediately.
     * This is necessary for `<svelte:element>`
     */
    E(this, Kt, !0);
    /**
     * @param {Batch} batch
     */
    E(this, qt, (t) => {
      if (X(this, be).has(t)) {
        var n = (
          /** @type {Key} */
          X(this, be).get(t)
        ), r = X(this, xe).get(n);
        if (r)
          Hr(r), X(this, tt).delete(n);
        else {
          var i = X(this, re).get(n);
          i && (X(this, xe).set(n, i.effect), X(this, re).delete(n), i.fragment.lastChild.remove(), this.anchor.before(i.fragment), r = i.effect);
        }
        for (const [l, o] of X(this, be)) {
          if (X(this, be).delete(l), l === t)
            break;
          const c = X(this, re).get(o);
          c && (fe(c.effect), X(this, re).delete(o));
        }
        for (const [l, o] of X(this, xe)) {
          if (l === n || X(this, tt).has(l)) continue;
          const c = () => {
            if (Array.from(X(this, be).values()).includes(l)) {
              var s = document.createDocumentFragment();
              zi(o, s), s.append(rt()), X(this, re).set(l, { effect: o, fragment: s });
            } else
              fe(o);
            X(this, tt).delete(l), X(this, xe).delete(l);
          };
          X(this, Kt) || !r ? (X(this, tt).add(l), yr(o, c, !1)) : c();
        }
      }
    });
    /**
     * @param {Batch} batch
     */
    E(this, Wn, (t) => {
      X(this, be).delete(t);
      const n = Array.from(X(this, be).values());
      for (const [r, i] of X(this, re))
        n.includes(r) || (fe(i.effect), X(this, re).delete(r));
    });
    this.anchor = t, ve(this, Kt, n);
  }
  /**
   *
   * @param {any} key
   * @param {null | ((target: TemplateNode) => void)} fn
   */
  ensure(t, n) {
    var r = (
      /** @type {Batch} */
      Z
    ), i = Yi();
    if (n && !X(this, xe).has(t) && !X(this, re).has(t))
      if (i) {
        var l = document.createDocumentFragment(), o = rt();
        l.append(o), X(this, re).set(t, {
          effect: ct(() => n(o)),
          fragment: l
        });
      } else
        X(this, xe).set(
          t,
          ct(() => n(this.anchor))
        );
    if (X(this, be).set(r, t), i) {
      for (const [c, a] of X(this, xe))
        c === t ? r.unskip_effect(a) : r.skip_effect(a);
      for (const [c, a] of X(this, re))
        c === t ? r.unskip_effect(a.effect) : r.skip_effect(a.effect);
      r.oncommit(X(this, qt)), r.ondiscard(X(this, Wn));
    } else
      X(this, qt).call(this, r);
  }
}
be = new WeakMap(), xe = new WeakMap(), re = new WeakMap(), tt = new WeakMap(), Kt = new WeakMap(), qt = new WeakMap(), Wn = new WeakMap();
function Zr(e, t) {
  const n = (r, ...i) => {
    var l = Gt;
    Hn(e);
    try {
      return t(r, ...i);
    } finally {
      Hn(l);
    }
  };
  return ao(n), n;
}
if (b) {
  let e = function(t) {
    if (!(t in globalThis)) {
      let n;
      Object.defineProperty(globalThis, t, {
        configurable: !0,
        // eslint-disable-next-line getter-return
        get: () => {
          if (n !== void 0)
            return n;
          ec(t);
        },
        set: (r) => {
          n = r;
        }
      });
    }
  };
  e("$state"), e("$effect"), e("$derived"), e("$inspect"), e("$props"), e("$bindable");
}
var Lr = /* @__PURE__ */ new Map();
function fo(e, t) {
  var n = Lr.get(e);
  n || (n = /* @__PURE__ */ new Set(), Lr.set(e, n)), n.add(t);
}
function Ie(e, t, n) {
  return (...r) => {
    const i = e(...r);
    var l = i.nodeType === Jl ? i.firstChild : i;
    return tl(l, t, n), i;
  };
}
function uo(e, t, n) {
  e.__svelte_meta = {
    parent: ge,
    loc: { file: t, line: n[0], column: n[1] }
  }, n[2] && tl(e.firstChild, t, n[2]);
}
function tl(e, t, n) {
  for (var r = 0; e && r < n.length; )
    e.nodeType === Tl && uo(
      /** @type {Element} */
      e,
      t,
      n[r++]
    ), e = e.nextSibling;
}
function an(e) {
  e && Dl(e[J] ?? "a component", e.name);
}
function fn() {
  const e = V == null ? void 0 : V.function;
  function t(n) {
    zl(n, e[J]);
  }
  return {
    $destroy: () => t("$destroy()"),
    $on: () => t("$on(...)"),
    $set: () => t("$set(...)")
  };
}
function pt(e, t, n = !1) {
  var r = new el(e), i = n ? Ht : 0;
  function l(o, c) {
    r.ensure(o, c);
  }
  xr(() => {
    var o = !1;
    t((c, a = 0) => {
      o = !0, l(a, c);
    }), o || l(-1, null);
  }, i);
}
function nr(e, t) {
  return t;
}
function vo(e, t, n) {
  for (var r = [], i = t.length, l, o = t.length, c = 0; c < i; c++) {
    let d = t[c];
    yr(
      d,
      () => {
        if (l) {
          if (l.pending.delete(d), l.done.add(d), l.pending.size === 0) {
            var u = (
              /** @type {Set<EachOutroGroup>} */
              e.outrogroups
            );
            rr(e, or(l.done)), u.delete(l), u.size === 0 && (e.outrogroups = null);
          }
        } else
          o -= 1;
      },
      !1
    );
  }
  if (o === 0) {
    var a = r.length === 0 && n !== null;
    if (a) {
      var s = (
        /** @type {Element} */
        n
      ), f = (
        /** @type {Element} */
        s.parentNode
      );
      Bc(f), f.append(s), e.items.clear();
    }
    rr(e, t, !a);
  } else
    l = {
      pending: new Set(t),
      done: /* @__PURE__ */ new Set()
    }, (e.outrogroups ?? (e.outrogroups = /* @__PURE__ */ new Set())).add(l);
}
function rr(e, t, n = !0) {
  var r;
  if (e.pending.size > 0) {
    r = /* @__PURE__ */ new Set();
    for (const o of e.pending.values())
      for (const c of o)
        r.add(
          /** @type {EachItem} */
          e.items.get(c).e
        );
  }
  for (var i = 0; i < t.length; i++) {
    var l = t[i];
    if (r != null && r.has(l)) {
      l.f |= we;
      const o = document.createDocumentFragment();
      zi(l, o);
    } else
      fe(t[i], n);
  }
}
var Qr;
function ir(e, t, n, r, i, l = null) {
  var o = e, c = /* @__PURE__ */ new Map(), a = (t & si) !== 0;
  if (a) {
    var s = (
      /** @type {Element} */
      e
    );
    o = s.appendChild(rt());
  }
  var f = null, d = /* @__PURE__ */ hr(() => {
    var w = n();
    return cr(w) ? w : w == null ? [] : or(w);
  }), u, _ = /* @__PURE__ */ new Map(), p = !0;
  function x(w) {
    (W.effect.f & ae) === 0 && (W.pending.delete(w), W.fallback = f, po(W, u, o, t, r), f !== null && (u.length === 0 ? (f.f & we) === 0 ? Hr(f) : (f.f ^= we, Tt(f, null, o)) : yr(f, () => {
      f = null;
    })));
  }
  function v(w) {
    W.pending.delete(w);
  }
  var h = xr(() => {
    u = /** @type {V[]} */
    g(d);
    for (var w = u.length, m = /* @__PURE__ */ new Set(), R = (
      /** @type {Batch} */
      Z
    ), C = Yi(), N = 0; N < w; N += 1) {
      var le = u[N], te = r(le, N);
      if (b) {
        var Ce = r(le, N);
        te !== Ce && Ll(String(N), String(te), String(Ce));
      }
      var Q = p ? null : c.get(te);
      Q ? (Q.v && Dt(Q.v, le), Q.i && Dt(Q.i, N), C && R.unskip_effect(Q.e)) : (Q = ho(
        c,
        p ? o : Qr ?? (Qr = rt()),
        le,
        te,
        N,
        i,
        t,
        n
      ), p || (Q.e.f |= we), c.set(te, Q)), m.add(te);
    }
    if (w === 0 && l && !f && (p ? f = ct(() => l(o)) : (f = ct(() => l(Qr ?? (Qr = rt()))), f.f |= we)), w > m.size && (b ? bo(u, r) : gi("", "", "")), !p)
      if (_.set(R, m), C) {
        for (const [at, Me] of c)
          m.has(at) || R.skip_effect(Me.e);
        R.oncommit(x), R.ondiscard(v);
      } else
        x(R);
    g(d);
  }), W = { effect: h, items: c, pending: _, outrogroups: null, fallback: f };
  p = !1;
}
function Yt(e) {
  for (; e !== null && (e.f & Xe) === 0; )
    e = e.next;
  return e;
}
function po(e, t, n, r, i) {
  var Ce, Q, at, Me, un, Ft, dn, vn, Wt;
  var l = (r & xl) !== 0, o = t.length, c = e.items, a = Yt(e.effect.first), s, f = null, d, u = [], _ = [], p, x, v, h;
  if (l)
    for (h = 0; h < o; h += 1)
      p = t[h], x = i(p, h), v = /** @type {EachItem} */
      c.get(x).e, (v.f & we) === 0 && ((Q = (Ce = v.nodes) == null ? void 0 : Ce.a) == null || Q.measure(), (d ?? (d = /* @__PURE__ */ new Set())).add(v));
  for (h = 0; h < o; h += 1) {
    if (p = t[h], x = i(p, h), v = /** @type {EachItem} */
    c.get(x).e, e.outrogroups !== null)
      for (const de of e.outrogroups)
        de.pending.delete(v), de.done.delete(v);
    if ((v.f & ie) !== 0 && (Hr(v), l && ((Me = (at = v.nodes) == null ? void 0 : at.a) == null || Me.unfix(), (d ?? (d = /* @__PURE__ */ new Set())).delete(v))), (v.f & we) !== 0)
      if (v.f ^= we, v === a)
        Tt(v, null, n);
      else {
        var W = f ? f.next : a;
        v === e.effect.last && (e.effect.last = v.prev), v.prev && (v.prev.next = v.next), v.next && (v.next.prev = v.prev), Ye(e, f, v), Ye(e, v, W), Tt(v, W, n), f = v, u = [], _ = [], a = Yt(f.next);
        continue;
      }
    if (v !== a) {
      if (s !== void 0 && s.has(v)) {
        if (u.length < _.length) {
          var w = _[0], m;
          f = w.prev;
          var R = u[0], C = u[u.length - 1];
          for (m = 0; m < u.length; m += 1)
            Tt(u[m], w, n);
          for (m = 0; m < _.length; m += 1)
            s.delete(_[m]);
          Ye(e, R.prev, C.next), Ye(e, f, R), Ye(e, C, w), a = w, f = C, h -= 1, u = [], _ = [];
        } else
          s.delete(v), Tt(v, a, n), Ye(e, v.prev, v.next), Ye(e, v, f === null ? e.effect.first : f.next), Ye(e, f, v), f = v;
        continue;
      }
      for (u = [], _ = []; a !== null && a !== v; )
        (s ?? (s = /* @__PURE__ */ new Set())).add(a), _.push(a), a = Yt(a.next);
      if (a === null)
        continue;
    }
    (v.f & we) === 0 && u.push(v), f = v, a = Yt(v.next);
  }
  if (e.outrogroups !== null) {
    for (const de of e.outrogroups)
      de.pending.size === 0 && (rr(e, or(de.done)), (un = e.outrogroups) == null || un.delete(de));
    e.outrogroups.size === 0 && (e.outrogroups = null);
  }
  if (a !== null || s !== void 0) {
    var N = [];
    if (s !== void 0)
      for (v of s)
        (v.f & ie) === 0 && N.push(v);
    for (; a !== null; )
      (a.f & ie) === 0 && a !== e.fallback && N.push(a), a = Yt(a.next);
    var le = N.length;
    if (le > 0) {
      var te = (r & si) !== 0 && o === 0 ? n : null;
      if (l) {
        for (h = 0; h < le; h += 1)
          (dn = (Ft = N[h].nodes) == null ? void 0 : Ft.a) == null || dn.measure();
        for (h = 0; h < le; h += 1)
          (Wt = (vn = N[h].nodes) == null ? void 0 : vn.a) == null || Wt.fix();
      }
      vo(e, N, te);
    }
  }
  l && Ot(() => {
    var de, pn;
    if (d !== void 0)
      for (v of d)
        (pn = (de = v.nodes) == null ? void 0 : de.a) == null || pn.apply();
  });
}
function ho(e, t, n, r, i, l, o, c) {
  var a = (o & Xl) !== 0 ? (o & wl) === 0 ? /* @__PURE__ */ Fc(n, !1, !1) : It(n) : null, s = (o & ml) !== 0 ? It(i) : null;
  return b && a && (a.trace = () => {
    c()[(s == null ? void 0 : s.v) ?? i];
  }), {
    v: a,
    i: s,
    e: ct(() => (l(t, a ?? n, s ?? i, c), () => {
      e.delete(r);
    }))
  };
}
function Tt(e, t, n) {
  if (e.nodes)
    for (var r = e.nodes.start, i = e.nodes.end, l = t && (t.f & we) === 0 ? (
      /** @type {EffectNodes} */
      t.nodes.start
    ) : n; r !== null; ) {
      var o = (
        /** @type {TemplateNode} */
        /* @__PURE__ */ on(r)
      );
      if (l.before(r), r === i)
        return;
      r = o;
    }
}
function Ye(e, t, n) {
  t === null ? e.effect.first = n : t.next = n, n === null ? e.effect.last = t : n.prev = t;
}
function bo(e, t) {
  const n = /* @__PURE__ */ new Map(), r = e.length;
  for (let i = 0; i < r; i++) {
    const l = t(e[i], i);
    if (n.has(l)) {
      const o = String(n.get(l)), c = String(i);
      let a = String(l);
      a.startsWith("[object ") && (a = null), gi(o, c, a);
    }
    n.set(l, i);
  }
}
function Bn(e, t, n, r, i) {
  var c;
  var l = (c = t.$$slots) == null ? void 0 : c[n], o = !1;
  l === !0 && (l = t.children, o = !0), l === void 0 || l(e, o ? () => r : r);
}
function go(e, t, n, r, i, l) {
  var o = b && l && (V == null ? void 0 : V.function[J]), c = null, a = (
    /** @type {TemplateNode} */
    e
  ), s = new el(a, !1);
  xr(() => {
    const f = t() || null;
    var d = Gl;
    if (f === null) {
      s.ensure(null, null);
      return;
    }
    return s.ensure(f, (u) => {
      if (f) {
        if (c = _r(f, d), b && l && (c.__svelte_meta = {
          parent: ge,
          loc: {
            file: o,
            line: l[0],
            column: l[1]
          }
        }), kn(c, c), r) {
          var _ = c.appendChild(rt());
          r(c, _);
        }
        G.nodes.end = c, u.before(c);
      }
    }), () => {
    };
  }, Ht), Xr(() => {
  });
}
function _o(e, t) {
  mr(() => {
    var n = e.getRootNode(), r = (
      /** @type {ShadowRoot} */
      n.host ? (
        /** @type {ShadowRoot} */
        n
      ) : (
        /** @type {Document} */
        n.head ?? /** @type {Document} */
        n.ownerDocument.head
      )
    );
    if (!r.querySelector("#" + t.hash)) {
      const i = _r("style");
      i.id = t.hash, i.textContent = t.code, r.appendChild(i), b && fo(t.hash, i);
    }
  });
}
function Xo(e, t) {
  var n = void 0, r;
  Ji(() => {
    n !== (n = t()) && (r && (fe(r), r = null), n && (r = ct(() => {
      mr(() => (
        /** @type {(node: Element) => void} */
        n(e)
      ));
    })));
  });
}
function nl(e) {
  var t, n, r = "";
  if (typeof e == "string" || typeof e == "number") r += e;
  else if (typeof e == "object") if (Array.isArray(e)) {
    var i = e.length;
    for (t = 0; t < i; t++) e[t] && (n = nl(e[t])) && (r && (r += " "), r += n);
  } else for (n in e) e[n] && (r && (r += " "), r += n);
  return r;
}
function mo() {
  for (var e, t, n = 0, r = "", i = arguments.length; n < i; n++) (e = arguments[n]) && (t = nl(e)) && (r && (r += " "), r += t);
  return r;
}
function xo(e) {
  return typeof e == "object" ? mo(e) : e ?? "";
}
const Ur = [...`
\r\f \v\uFEFF`];
function wo(e, t, n) {
  var r = e == null ? "" : "" + e;
  if (n) {
    for (var i of Object.keys(n))
      if (n[i])
        r = r ? r + " " + i : i;
      else if (r.length)
        for (var l = i.length, o = 0; (o = r.indexOf(i, o)) >= 0; ) {
          var c = o + l;
          (o === 0 || Ur.includes(r[o - 1])) && (c === r.length || Ur.includes(r[c])) ? r = (o === 0 ? "" : r.substring(0, o)) + r.substring(c + 1) : o = c;
        }
  }
  return r === "" ? null : r;
}
function $r(e, t = !1) {
  var n = t ? " !important;" : ";", r = "";
  for (var i of Object.keys(e)) {
    var l = e[i];
    l != null && l !== "" && (r += " " + i + ": " + l + n);
  }
  return r;
}
function Mn(e) {
  return e[0] !== "-" || e[1] !== "-" ? e.toLowerCase() : e;
}
function yo(e, t) {
  if (t) {
    var n = "", r, i;
    if (Array.isArray(t) ? (r = t[0], i = t[1]) : r = t, e) {
      e = String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g, "").trim();
      var l = !1, o = 0, c = !1, a = [];
      r && a.push(...Object.keys(r).map(Mn)), i && a.push(...Object.keys(i).map(Mn));
      var s = 0, f = -1;
      const x = e.length;
      for (var d = 0; d < x; d++) {
        var u = e[d];
        if (c ? u === "/" && e[d - 1] === "*" && (c = !1) : l ? l === u && (l = !1) : u === "/" && e[d + 1] === "*" ? c = !0 : u === '"' || u === "'" ? l = u : u === "(" ? o++ : u === ")" && o--, !c && l === !1 && o === 0) {
          if (u === ":" && f === -1)
            f = d;
          else if (u === ";" || d === x - 1) {
            if (f !== -1) {
              var _ = Mn(e.substring(s, f).trim());
              if (!a.includes(_)) {
                u !== ";" && d++;
                var p = e.substring(s, d).trim();
                n += " " + p + ";";
              }
            }
            s = d + 1, f = -1;
          }
        }
      }
    }
    return r && (n += $r(r)), i && (n += $r(i, !0)), n = n.trim(), n === "" ? null : n;
  }
  return e == null ? null : String(e);
}
function Ho(e, t, n, r, i, l) {
  var o = e.__className;
  if (o !== n || o === void 0) {
    var c = wo(n, r, l);
    c == null ? e.removeAttribute("class") : t ? e.className = c : e.setAttribute("class", c), e.__className = n;
  } else if (l && i !== l)
    for (var a in l) {
      var s = !!l[a];
      (i == null || s !== !!i[a]) && e.classList.toggle(a, s);
    }
  return l;
}
function On(e, t = {}, n, r) {
  for (var i in n) {
    var l = n[i];
    t[i] !== l && (n[i] == null ? e.style.removeProperty(i) : e.style.setProperty(i, l, r));
  }
}
function Le(e, t, n, r) {
  var i = e.__style;
  if (i !== t) {
    var l = yo(t, r);
    l == null ? e.removeAttribute("style") : e.style.cssText = l, e.__style = t;
  } else r && (Array.isArray(r) ? (On(e, n == null ? void 0 : n[0], r[0]), On(e, n == null ? void 0 : n[1], r[1], "important")) : On(e, n, r));
  return r;
}
function lr(e, t, n = !1) {
  if (e.multiple) {
    if (t == null)
      return;
    if (!cr(t))
      return lc();
    for (var r of e.options)
      r.selected = t.includes(Kr(r));
    return;
  }
  for (r of e.options) {
    var i = Kr(r);
    if (Nc(i, t)) {
      r.selected = !0;
      return;
    }
  }
  (!n || t !== void 0) && (e.selectedIndex = -1);
}
function Zo(e) {
  var t = new MutationObserver(() => {
    lr(e, e.__value);
  });
  t.observe(e, {
    // Listen to option element changes
    childList: !0,
    subtree: !0,
    // because of <optgroup>
    // Listen to option element value attribute changes
    // (doesn't get notified of select value changes,
    // because that property is not reflected as an attribute)
    attributes: !0,
    attributeFilter: ["value"]
  }), Xr(() => {
    t.disconnect();
  });
}
function Kr(e) {
  return "__value" in e ? e.__value : e.value;
}
const Bt = Symbol("class"), At = Symbol("style"), rl = Symbol("is custom element"), il = Symbol("is html"), Io = bi ? "option" : "OPTION", Ro = bi ? "select" : "SELECT";
function Go(e, t) {
  t ? e.hasAttribute("selected") || e.setAttribute("selected", "") : e.removeAttribute("selected");
}
function Gn(e, t, n, r) {
  var i = ll(e);
  i[t] !== (i[t] = n) && (t === "loading" && (e[Al] = n), n == null ? e.removeAttribute(t) : typeof n != "string" && cl(e).includes(t) ? e[t] = n : e.setAttribute(t, n));
}
function Fo(e, t, n, r, i = !1, l = !1) {
  var o = ll(e), c = o[rl], a = !o[il], s = t || {}, f = e.nodeName === Io;
  for (var d in t)
    d in n || (n[d] = null);
  n.class ? n.class = xo(n.class) : n[Bt] && (n.class = null), n[At] && (n.style ?? (n.style = null));
  var u = cl(e);
  for (const w in n) {
    let m = n[w];
    if (f && w === "value" && m == null) {
      e.value = e.__value = "", s[w] = m;
      continue;
    }
    if (w === "class") {
      var _ = e.namespaceURI === "http://www.w3.org/1999/xhtml";
      Ho(e, _, m, r, t == null ? void 0 : t[Bt], n[Bt]), s[w] = m, s[Bt] = n[Bt];
      continue;
    }
    if (w === "style") {
      Le(e, m, t == null ? void 0 : t[At], n[At]), s[w] = m, s[At] = n[At];
      continue;
    }
    var p = s[w];
    if (!(m === p && !(m === void 0 && e.hasAttribute(w)))) {
      s[w] = m;
      var x = w[0] + w[1];
      if (x !== "$$")
        if (x === "on") {
          const R = {}, C = "$$" + w;
          let N = w.slice(2);
          var v = lo(N);
          if (ro(N) && (N = N.slice(0, -7), R.capture = !0), !v && p) {
            if (m != null) continue;
            e.removeEventListener(N, s[C], R), s[C] = null;
          }
          if (v)
            Pe(N, e, m), Ki([N]);
          else if (m != null) {
            let le = function(te) {
              s[w].call(this, te);
            };
            s[C] = Kc(N, e, le, R);
          }
        } else if (w === "style")
          Gn(e, w, m);
        else if (w === "autofocus")
          Ac(
            /** @type {HTMLElement} */
            e,
            !!m
          );
        else if (!c && (w === "__value" || w === "value" && m != null))
          e.value = e.__value = m;
        else if (w === "selected" && f)
          Go(
            /** @type {HTMLOptionElement} */
            e,
            m
          );
        else {
          var h = w;
          a || (h = oo(h));
          var W = h === "defaultValue" || h === "defaultChecked";
          if (m == null && !c && !W)
            if (o[w] = null, h === "value" || h === "checked") {
              let R = (
                /** @type {HTMLInputElement} */
                e
              );
              const C = t === void 0;
              if (h === "value") {
                let N = R.defaultValue;
                R.removeAttribute(h), R.defaultValue = N, R.value = R.__value = C ? N : null;
              } else {
                let N = R.defaultChecked;
                R.removeAttribute(h), R.defaultChecked = N, R.checked = C ? N : !1;
              }
            } else
              e.removeAttribute(w);
          else W || u.includes(h) && (c || typeof m != "string") ? (e[h] = m, h in o && (o[h] = O)) : typeof m != "function" && Gn(e, h, m);
        }
    }
  }
  return s;
}
function qr(e, t, n = [], r = [], i = [], l, o = !1, c = !1) {
  Wi(i, n, r, (a) => {
    var s = void 0, f = {}, d = e.nodeName === Ro, u = !1;
    if (Ji(() => {
      var p = t(...a.map(g)), x = Fo(
        e,
        s,
        p,
        l,
        o,
        c
      );
      u && d && "value" in p && lr(
        /** @type {HTMLSelectElement} */
        e,
        p.value
      );
      for (let h of Object.getOwnPropertySymbols(f))
        p[h] || fe(f[h]);
      for (let h of Object.getOwnPropertySymbols(p)) {
        var v = p[h];
        h.description === Fl && (!s || v !== s[h]) && (f[h] && fe(f[h]), f[h] = ct(() => Xo(e, () => v))), x[h] = v;
      }
      s = x;
    }), d) {
      var _ = (
        /** @type {HTMLSelectElement} */
        e
      );
      mr(() => {
        lr(
          _,
          /** @type {Record<string | symbol, any>} */
          s.value,
          !0
        ), Zo(_);
      });
    }
    u = !0;
  });
}
function ll(e) {
  return (
    /** @type {Record<string | symbol, unknown>} **/
    // @ts-expect-error
    e.__attributes ?? (e.__attributes = {
      [rl]: e.nodeName.includes("-"),
      [il]: e.namespaceURI === fi
    })
  );
}
var ei = /* @__PURE__ */ new Map();
function cl(e) {
  var t = e.getAttribute("is") || e.nodeName, n = ei.get(t);
  if (n) return n;
  ei.set(t, n = []);
  for (var r, i = e, l = Element.prototype; l !== i; ) {
    r = ui(i);
    for (var o in r)
      r[o].set && n.push(o);
    i = sr(i);
  }
  return n;
}
function ti(e, t, n = t) {
  var r = /* @__PURE__ */ new WeakSet();
  Jc(e, "input", async (i) => {
    b && e.type === "checkbox" && Br();
    var l = i ? e.defaultValue : e.value;
    if (l = zn(e) ? Dn(l) : l, n(l), Z !== null && r.add(Z), await Qc(), l !== (l = t())) {
      var o = e.selectionStart, c = e.selectionEnd, a = e.value.length;
      if (e.value = l ?? "", c !== null) {
        var s = e.value.length;
        o === c && c === a && s > a ? (e.selectionStart = s, e.selectionEnd = s) : (e.selectionStart = o, e.selectionEnd = Math.min(c, s));
      }
    }
  }), // If we are hydrating and the value has since changed,
  // then use the updated value from the input instead.
  // If defaultValue is set, then value == defaultValue
  // TODO Svelte 6: remove input.value check and set to empty string?
  Qt(t) == null && e.value && (n(zn(e) ? Dn(e.value) : e.value), Z !== null && r.add(Z)), Oc(() => {
    b && e.type === "checkbox" && Br();
    var i = t();
    if (e === document.activeElement) {
      var l = (
        /** @type {Batch} */
        Z
      );
      if (r.has(l))
        return;
    }
    zn(e) && i === Dn(e.value) || e.type === "date" && !i && !e.value || i !== e.value && (e.value = i ?? "");
  });
}
function zn(e) {
  var t = e.type;
  return t === "number" || t === "range";
}
function Dn(e) {
  return e === "" ? null : +e;
}
function Wo(e = !1) {
  const t = (
    /** @type {ComponentContextLegacy} */
    V
  ), n = t.l.u;
  if (!n) return;
  let r = () => ht(t.s);
  if (e) {
    let i = 0, l = (
      /** @type {Record<string, any>} */
      {}
    );
    const o = /* @__PURE__ */ cn(() => {
      let c = !1;
      const a = t.s;
      for (const s in a)
        a[s] !== l[s] && (l[s] = a[s], c = !0);
      return c && i++, i;
    });
    r = () => g(o);
  }
  n.b.length && jc(() => {
    ni(t, r), Pn(n.b);
  }), Or(() => {
    const i = Qt(() => n.m.map(Sl));
    return () => {
      for (const l of i)
        typeof l == "function" && l();
    };
  }), n.a.length && Or(() => {
    ni(t, r), Pn(n.a);
  });
}
function ni(e, t) {
  if (e.l.s)
    for (const n of e.l.s) g(n);
  t();
}
const No = {
  get(e, t) {
    if (!e.exclude.includes(t))
      return g(e.version), t in e.special ? e.special[t]() : e.props[t];
  },
  set(e, t, n) {
    if (!(t in e.special)) {
      var r = G;
      try {
        _e(e.parent_effect), e.special[t] = Qe(
          {
            get [t]() {
              return e.props[t];
            }
          },
          /** @type {string} */
          t,
          ai
        );
      } finally {
        _e(r);
      }
    }
    return e.special[t](n), jr(e.version), !0;
  },
  getOwnPropertyDescriptor(e, t) {
    if (!e.exclude.includes(t) && t in e.props)
      return {
        enumerable: !0,
        configurable: !0,
        value: e.props[t]
      };
  },
  deleteProperty(e, t) {
    return e.exclude.includes(t) || (e.exclude.push(t), jr(e.version)), !0;
  },
  has(e, t) {
    return e.exclude.includes(t) ? !1 : t in e.props;
  },
  ownKeys(e) {
    return Reflect.ownKeys(e.props).filter((t) => !e.exclude.includes(t));
  }
};
function Ut(e, t) {
  return new Proxy(
    {
      props: e,
      exclude: t,
      special: {},
      version: It(0),
      // TODO this is only necessary because we need to track component
      // destruction inside `prop`, because of `bind:this`, but it
      // seems likely that we can simplify `bind:this` instead
      parent_effect: (
        /** @type {Effect} */
        G
      )
    },
    No
  );
}
const Vo = {
  get(e, t) {
    let n = e.props.length;
    for (; n--; ) {
      let r = e.props[n];
      if (kt(r) && (r = r()), typeof r == "object" && r !== null && t in r) return r[t];
    }
  },
  set(e, t, n) {
    let r = e.props.length;
    for (; r--; ) {
      let i = e.props[r];
      kt(i) && (i = i());
      const l = nt(i, t);
      if (l && l.set)
        return l.set(n), !0;
    }
    return !1;
  },
  getOwnPropertyDescriptor(e, t) {
    let n = e.props.length;
    for (; n--; ) {
      let r = e.props[n];
      if (kt(r) && (r = r()), typeof r == "object" && r !== null && t in r) {
        const i = nt(r, t);
        return i && !i.configurable && (i.configurable = !0), i;
      }
    }
  },
  has(e, t) {
    if (t === Ne || t === pi) return !1;
    for (let n of e.props)
      if (kt(n) && (n = n()), n != null && t in n) return !0;
    return !1;
  },
  ownKeys(e) {
    const t = [];
    for (let n of e.props)
      if (kt(n) && (n = n()), !!n) {
        for (const r in n)
          t.includes(r) || t.push(r);
        for (const r of Object.getOwnPropertySymbols(n))
          t.includes(r) || t.push(r);
      }
    return t;
  }
};
function Ir(...e) {
  return new Proxy({ props: e }, Vo);
}
function Qe(e, t, n, r) {
  var w;
  var i = !tn || (n & Hl) !== 0, l = (n & Zl) !== 0, o = (n & Il) !== 0, c = (
    /** @type {V} */
    r
  ), a = !0, s = () => (a && (a = !1, c = o ? Qt(
    /** @type {() => V} */
    r
  ) : (
    /** @type {V} */
    r
  )), c);
  let f;
  if (l) {
    var d = Ne in e || pi in e;
    f = ((w = nt(e, t)) == null ? void 0 : w.set) ?? (d && t in e ? (m) => e[t] = m : void 0);
  }
  var u, _ = !1;
  l ? [u, _] = gc(() => (
    /** @type {V} */
    e[t]
  )) : u = /** @type {V} */
  e[t], u === void 0 && r !== void 0 && (u = s(), f && (i && ql(t), f(u)));
  var p;
  if (i ? p = () => {
    var m = (
      /** @type {V} */
      e[t]
    );
    return m === void 0 ? s() : (a = !0, m);
  } : p = () => {
    var m = (
      /** @type {V} */
      e[t]
    );
    return m !== void 0 && (c = /** @type {V} */
    void 0), m === void 0 ? c : m;
  }, i && (n & ai) === 0)
    return p;
  if (f) {
    var x = e.$$legacy;
    return (
      /** @type {() => V} */
      (function(m, R) {
        return arguments.length > 0 ? ((!i || !R || x || _) && f(R ? p() : m), m) : p();
      })
    );
  }
  var v = !1, h = ((n & yl) !== 0 ? cn : hr)(() => (v = !1, p()));
  b && (h.label = t), l && g(h);
  var W = (
    /** @type {Effect} */
    G
  );
  return (
    /** @type {() => V} */
    (function(m, R) {
      if (arguments.length > 0) {
        const C = R ? g(h) : i && l ? $e(m) : m;
        return F(h, C), v = !0, c !== void 0 && (c = C), m;
      }
      return Ee && v || (W.f & ae) !== 0 ? h.v : g(h);
    })
  );
}
ac();
/**
 * @license lucide-svelte v0.460.1 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Co = {
  xmlns: "http://www.w3.org/2000/svg",
  width: 24,
  height: 24,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  "stroke-width": 2,
  "stroke-linecap": "round",
  "stroke-linejoin": "round"
};
ot[J] = "/Users/junkawasaki/etzhayyim/etzhayyim-root/node_modules/.pnpm/lucide-svelte@0.460.1_svelte@5.54.0/node_modules/lucide-svelte/dist/Icon.svelte";
var So = Ie(/* @__PURE__ */ no("<svg><!><!></svg>"), ot[J], [[14, 0]]);
function ot(e, t) {
  an(new.target);
  const n = Ut(t, ["children", "$$slots", "$$events", "$$legacy"]), r = Ut(n, [
    "name",
    "color",
    "size",
    "strokeWidth",
    "absoluteStrokeWidth",
    "iconNode"
  ]);
  nn(t, !1, ot);
  let i = Qe(t, "name", 8, void 0), l = Qe(t, "color", 8, "currentColor"), o = Qe(t, "size", 8, 24), c = Qe(t, "strokeWidth", 8, 2), a = Qe(t, "absoluteStrokeWidth", 8, !1), s = Qe(t, "iconNode", 24, () => []);
  const f = (...x) => x.filter((v, h, W) => !!v && pe(W.indexOf(v), h)).join(" ");
  var d = { ...fn() };
  Wo();
  var u = So();
  qr(
    u,
    (x, v) => ({
      ...Co,
      ...r,
      width: o(),
      height: o(),
      stroke: l(),
      "stroke-width": x,
      class: v
    }),
    [
      () => (ht(a()), ht(c()), ht(o()), Qt(() => a() ? Number(c()) * 24 / Number(o()) : c())),
      () => (ht(i()), ht(n), Qt(() => f("lucide-icon", "lucide", i() ? `lucide-${i()}` : "", n.class)))
    ]
  );
  var _ = S(u);
  U(
    () => ir(_, 1, s, nr, (x, v) => {
      var h = /* @__PURE__ */ Zc(() => kl(g(v), 2));
      let W = () => g(h)[0];
      W();
      let w = () => g(h)[1];
      w();
      var m = Yn(), R = Cn(m);
      so(W), go(
        R,
        W,
        !0,
        (C, N) => {
          qr(C, () => ({ ...w() }));
        },
        void 0,
        [35, 4]
      ), q(x, m);
    }),
    "each",
    ot,
    34,
    2
  );
  var p = M(_);
  return Bn(p, t, "default", {}), q(e, u), rn(d);
}
Et[J] = "/Users/junkawasaki/etzhayyim/etzhayyim-root/node_modules/.pnpm/lucide-svelte@0.460.1_svelte@5.54.0/node_modules/lucide-svelte/dist/icons/gift.svelte";
function Et(e, t) {
  an(new.target);
  const n = Ut(t, ["children", "$$slots", "$$events", "$$legacy"]);
  nn(t, !1, Et);
  /**
   * @license lucide-svelte v0.460.1 - ISC
   *
   * This source code is licensed under the ISC license.
   * See the LICENSE file in the root directory of this source tree.
   */
  const r = [
    [
      "rect",
      { x: "3", y: "8", width: "18", height: "4", rx: "1" }
    ],
    ["path", { d: "M12 8v13" }],
    ["path", { d: "M19 12v7a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-7" }],
    [
      "path",
      {
        d: "M7.5 8a2.5 2.5 0 0 1 0-5A4.8 8 0 0 1 12 8a4.8 8 0 0 1 4.5-5 2.5 2.5 0 0 1 0 5"
      }
    ]
  ];
  var i = { ...fn() };
  return U(
    () => (
      /**
      * @component @name Gift
      * @description Lucide SVG icon component, renders SVG Element with children.
      *
      * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cmVjdCB4PSIzIiB5PSI4IiB3aWR0aD0iMTgiIGhlaWdodD0iNCIgcng9IjEiIC8+CiAgPHBhdGggZD0iTTEyIDh2MTMiIC8+CiAgPHBhdGggZD0iTTE5IDEydjdhMiAyIDAgMCAxLTIgMkg3YTIgMiAwIDAgMS0yLTJ2LTciIC8+CiAgPHBhdGggZD0iTTcuNSA4YTIuNSAyLjUgMCAwIDEgMC01QTQuOCA4IDAgMCAxIDEyIDhhNC44IDggMCAwIDEgNC41LTUgMi41IDIuNSAwIDAgMSAwIDUiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/gift
      * @see https://lucide.dev/guide/packages/lucide-svelte - Documentation
      *
      * @param {Object} props - Lucide icons props and any valid SVG attribute
      * @returns {FunctionalComponent} Svelte component
      *
      */
      ot(e, Ir({ name: "gift" }, () => n, {
        get iconNode() {
          return r;
        },
        children: Zr(Et, (l, o) => {
          var c = Yn(), a = Cn(c);
          Bn(a, t, "default", {}, null), q(l, c);
        }),
        $$slots: { default: !0 }
      }))
    ),
    "component",
    Et,
    22,
    0,
    { componentTag: "Icon" }
  ), rn(i);
}
jt[J] = "/Users/junkawasaki/etzhayyim/etzhayyim-root/node_modules/.pnpm/lucide-svelte@0.460.1_svelte@5.54.0/node_modules/lucide-svelte/dist/icons/send.svelte";
function jt(e, t) {
  an(new.target);
  const n = Ut(t, ["children", "$$slots", "$$events", "$$legacy"]);
  nn(t, !1, jt);
  /**
   * @license lucide-svelte v0.460.1 - ISC
   *
   * This source code is licensed under the ISC license.
   * See the LICENSE file in the root directory of this source tree.
   */
  const r = [
    [
      "path",
      {
        d: "M14.536 21.686a.5.5 0 0 0 .937-.024l6.5-19a.496.496 0 0 0-.635-.635l-19 6.5a.5.5 0 0 0-.024.937l7.93 3.18a2 2 0 0 1 1.112 1.11z"
      }
    ],
    ["path", { d: "m21.854 2.147-10.94 10.939" }]
  ];
  var i = { ...fn() };
  return U(
    () => (
      /**
      * @component @name Send
      * @description Lucide SVG icon component, renders SVG Element with children.
      *
      * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMTQuNTM2IDIxLjY4NmEuNS41IDAgMCAwIC45MzctLjAyNGw2LjUtMTlhLjQ5Ni40OTYgMCAwIDAtLjYzNS0uNjM1bC0xOSA2LjVhLjUuNSAwIDAgMC0uMDI0LjkzN2w3LjkzIDMuMThhMiAyIDAgMCAxIDEuMTEyIDEuMTF6IiAvPgogIDxwYXRoIGQ9Im0yMS44NTQgMi4xNDctMTAuOTQgMTAuOTM5IiAvPgo8L3N2Zz4K) - https://lucide.dev/icons/send
      * @see https://lucide.dev/guide/packages/lucide-svelte - Documentation
      *
      * @param {Object} props - Lucide icons props and any valid SVG attribute
      * @returns {FunctionalComponent} Svelte component
      *
      */
      ot(e, Ir({ name: "send" }, () => n, {
        get iconNode() {
          return r;
        },
        children: Zr(jt, (l, o) => {
          var c = Yn(), a = Cn(c);
          Bn(a, t, "default", {}, null), q(l, c);
        }),
        $$slots: { default: !0 }
      }))
    ),
    "component",
    jt,
    22,
    0,
    { componentTag: "Icon" }
  ), rn(i);
}
Mt[J] = "/Users/junkawasaki/etzhayyim/etzhayyim-root/node_modules/.pnpm/lucide-svelte@0.460.1_svelte@5.54.0/node_modules/lucide-svelte/dist/icons/x.svelte";
function Mt(e, t) {
  an(new.target);
  const n = Ut(t, ["children", "$$slots", "$$events", "$$legacy"]);
  nn(t, !1, Mt);
  /**
   * @license lucide-svelte v0.460.1 - ISC
   *
   * This source code is licensed under the ISC license.
   * See the LICENSE file in the root directory of this source tree.
   */
  const r = [
    ["path", { d: "M18 6 6 18" }],
    ["path", { d: "m6 6 12 12" }]
  ];
  var i = { ...fn() };
  return U(
    () => (
      /**
      * @component @name X
      * @description Lucide SVG icon component, renders SVG Element with children.
      *
      * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMTggNiA2IDE4IiAvPgogIDxwYXRoIGQ9Im02IDYgMTIgMTIiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/x
      * @see https://lucide.dev/guide/packages/lucide-svelte - Documentation
      *
      * @param {Object} props - Lucide icons props and any valid SVG attribute
      * @returns {FunctionalComponent} Svelte component
      *
      */
      ot(e, Ir({ name: "x" }, () => n, {
        get iconNode() {
          return r;
        },
        children: Zr(Mt, (l, o) => {
          var c = Yn(), a = Cn(c);
          Bn(a, t, "default", {}, null), q(l, c);
        }),
        $$slots: { default: !0 }
      }))
    ),
    "component",
    Mt,
    22,
    0,
    { componentTag: "Icon" }
  ), rn(i);
}
B[J] = "src/appview.svelte";
var ko = Ie(/* @__PURE__ */ Ve('<div style="position:absolute;top:12px;left:12px;background:#e11d48;color:#fff;padding:2px 10px;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:1px;">LIVE</div>'), B[J], [[198, 3]]), Yo = Ie(/* @__PURE__ */ Ve('<div style="position:absolute;bottom:36px;left:12px;right:12px;background:rgba(0,0,0,0.6);padding:6px 10px;border-radius:6px;font-size:13px;text-align:center;"> </div>'), B[J], [[210, 3]]), Bo = Ie(/* @__PURE__ */ Ve('<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;pointer-events:none;animation:tipFadeIn 0.3s ease-out;"><div> </div></div>'), B[J], [[217, 3, [[218, 4]]]]), Ao = Ie(/* @__PURE__ */ Ve('<div style="background:#7f1d1d;color:#fca5a5;padding:8px 12px;border-radius:8px;font-size:13px;"> </div>'), B[J], [[228, 3]]), To = Ie(/* @__PURE__ */ Ve('<div style="text-align:center;color:#666;padding:40px 0;font-size:14px;">No live streams available</div>'), B[J], [[232, 3]]), Jo = Ie(/* @__PURE__ */ Ve('<div style="display:flex;gap:8px;align-items:flex-start;"><div> </div> <div> </div></div>'), B[J], [[236, 3, [[237, 4], [240, 4]]]]), Eo = Ie(/* @__PURE__ */ Ve("<button> </button>"), B[J], [[285, 6]]), jo = Ie(/* @__PURE__ */ Ve('<div style="position:fixed;inset:0;background:rgba(0,0,0,0.6);display:flex;align-items:flex-end;justify-content:center;z-index:50;"><div style="background:#1f2937;border-radius:16px 16px 0 0;padding:20px;width:100%;max-width:440px;"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;"><span style="font-size:16px;font-weight:600;">Send Tip</span> <button style="background:none;border:none;cursor:pointer;"><!></button></div> <div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;"></div> <input type="text" placeholder="Message (optional)" style="width:100%;background:#111827;border:1px solid #374151;border-radius:8px;padding:10px;color:#fff;font-size:14px;margin-bottom:12px;outline:none;box-sizing:border-box;"/> <button style="width:100%;background:#e11d48;border:none;border-radius:8px;padding:12px;color:#fff;font-size:15px;font-weight:600;cursor:pointer;"> </button></div></div>'), B[J], [
  [
    275,
    2,
    [
      [
        276,
        3,
        [[277, 4, [[278, 5], [279, 5]]], [283, 4], [293, 4], [299, 4]]
      ]
    ]
  ]
]), Mo = Ie(/* @__PURE__ */ Ve('<div style="display:flex;flex-direction:column;height:100%;max-width:440px;margin:0 auto;background:#0f0f1a;color:#fff;font-family:system-ui,sans-serif;"><div style="position:relative;flex:0 0 280px;background:linear-gradient(135deg,#1a1a2e,#16213e);display:flex;align-items:center;justify-content:center;overflow:hidden;"><svg viewBox="0 0 200 280" style="width:180px;height:260px;"><circle cx="100" cy="90" r="50" fill="#ffd6b0"></circle><ellipse cx="80" cy="80" rx="6" ry="7" fill="#333"></ellipse><ellipse cx="120" cy="80" rx="6" ry="7" fill="#333"></ellipse><ellipse cx="100" cy="108" rx="12" fill="#e55"></ellipse><path d="M50 70 Q60 20 100 25 Q140 20 150 70 Q145 50 100 45 Q55 50 50 70Z" fill="#6366f1"></path><rect x="70" y="140" width="60" height="80" rx="10" fill="#6366f1"></rect><rect x="45" y="150" width="25" height="60" rx="8" fill="#6366f1"></rect><rect x="130" y="150" width="25" height="60" rx="8" fill="#6366f1"></rect></svg> <!> <div style="position:absolute;bottom:0;left:0;right:0;padding:8px 12px;background:linear-gradient(transparent,rgba(0,0,0,0.7));"><div style="font-size:14px;font-weight:600;"> </div></div> <!> <!></div> <div style="flex:1;overflow-y:auto;padding:8px 12px;display:flex;flex-direction:column;gap:6px;"><!> <!> <!></div> <div style="flex:0 0 auto;padding:8px 12px;border-top:1px solid #1f2937;display:flex;gap:8px;align-items:center;"><input type="text" style="flex:1;background:#1f2937;border:none;border-radius:20px;padding:8px 14px;color:#fff;font-size:14px;outline:none;"/> <button><!></button> <button><!></button></div> <!></div>'), B[J], [
  [
    175,
    0,
    [
      [
        177,
        1,
        [
          [
            179,
            2,
            [
              [181, 3],
              [183, 3],
              [184, 3],
              [186, 3],
              [188, 3],
              [190, 3],
              [192, 3],
              [193, 3]
            ]
          ],
          [204, 2, [[205, 3]]]
        ]
      ],
      [226, 1],
      [248, 1, [[249, 2], [257, 2], [264, 2]]]
    ]
  ]
]);
const Oo = {
  hash: "svelte-5yauex",
  code: `
	@keyframes svelte-5yauex-tipFadeIn {
		from { opacity: 0; transform: scale(0.5); }
		to { opacity: 1; transform: scale(1); }
	}

/*# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiYXBwdmlldy5zdmVsdGUiLCJzb3VyY2VzIjpbImFwcHZpZXcuc3ZlbHRlIl0sInNvdXJjZXNDb250ZW50IjpbIjxzY3JpcHQgbGFuZz1cInRzXCI+XG5cdGltcG9ydCB0eXBlIHsgQWN0b3JDb250ZXh0IH0gZnJvbSAnLi9saWIvdHlwZXMnO1xuXHRpbXBvcnQgeyBHaWZ0LCBTZW5kLCBYIH0gZnJvbSAnbHVjaWRlLXN2ZWx0ZSc7XG5cblx0bGV0IHsgY3R4IH06IHsgY3R4OiBBY3RvckNvbnRleHQgfSA9ICRwcm9wcygpO1xuXG5cdC8vIOKUgOKUgCBDeXBoZXIgcHJveHkgKHZpYSBBY3RvckNvbnRleHQpIOKUgOKUgFxuXG5cdGFzeW5jIGZ1bmN0aW9uIGN5cGhlclF1ZXJ5PFQgPSBSZWNvcmQ8c3RyaW5nLCB1bmtub3duPltdPihzdGF0ZW1lbnQ6IHN0cmluZywgcGFyYW1ldGVyczogUmVjb3JkPHN0cmluZywgdW5rbm93bj4gPSB7fSk6IFByb21pc2U8VD4ge1xuXHRcdHJldHVybiBjdHguY3lwaGVyLnF1ZXJ5KHN0YXRlbWVudCwgcGFyYW1ldGVycykgYXMgUHJvbWlzZTxUPjtcblx0fVxuXG5cdGFzeW5jIGZ1bmN0aW9uIGN5cGhlckV4ZWMoc3RhdGVtZW50OiBzdHJpbmcsIHBhcmFtZXRlcnM6IFJlY29yZDxzdHJpbmcsIHVua25vd24+ID0ge30pOiBQcm9taXNlPHZvaWQ+IHtcblx0XHRyZXR1cm4gY3R4LmN5cGhlci5leGVjKHN0YXRlbWVudCwgcGFyYW1ldGVycyk7XG5cdH1cblxuXHQvLyDilIDilIAgU3RhdGUg4pSA4pSAXG5cdGxldCBzdHJlYW1JZCA9ICRzdGF0ZSgnJyk7XG5cdGxldCBjb252b0lkID0gJHN0YXRlKCcnKTtcblx0bGV0IGFnZW50TmFtZSA9ICRzdGF0ZSgnJyk7XG5cdGxldCBhZ2VudEF2YXRhclVybCA9ICRzdGF0ZSgnJyk7XG5cdGxldCBzdWJ0aXRsZSA9ICRzdGF0ZSgnJyk7XG5cdGxldCBjaGF0TWVzc2FnZXMgPSAkc3RhdGU8QXJyYXk8eyBzZW5kZXI6IHN0cmluZzsgdGV4dDogc3RyaW5nOyB0eXBlOiBzdHJpbmcgfT4+KFtdKTtcblx0bGV0IGNoYXRJbnB1dCA9ICRzdGF0ZSgnJyk7XG5cdGxldCBzZW5kaW5nID0gJHN0YXRlKGZhbHNlKTtcblx0bGV0IHNob3dUaXBNb2RhbCA9ICRzdGF0ZShmYWxzZSk7XG5cdGxldCB0aXBBbW91bnQgPSAkc3RhdGUoMTAwKTtcblx0bGV0IHRpcE1lc3NhZ2UgPSAkc3RhdGUoJycpO1xuXHRsZXQgdGlwQW5pbWF0aW9uID0gJHN0YXRlPHsgYW1vdW50OiBudW1iZXI7IHNlbmRlcjogc3RyaW5nOyBlZmZlY3Q6IHN0cmluZyB9IHwgbnVsbD4obnVsbCk7XG5cdGxldCBlcnJvciA9ICRzdGF0ZTxzdHJpbmcgfCBudWxsPihudWxsKTtcblxuXHQvLyDilIDilIAgQXVkaW8gY29udGV4dCBmb3IgbGlwIHN5bmMg4pSA4pSAXG5cdGxldCBhdWRpb0N0eDogQXVkaW9Db250ZXh0IHwgbnVsbCA9IG51bGw7XG5cdGxldCBhbmFseXNlcjogQW5hbHlzZXJOb2RlIHwgbnVsbCA9IG51bGw7XG5cdGxldCBtb3V0aE9wZW4gPSAkc3RhdGUoMCk7XG5cblx0ZnVuY3Rpb24gZW5zdXJlQXVkaW9DdHgoKSB7XG5cdFx0aWYgKCFhdWRpb0N0eCkge1xuXHRcdFx0YXVkaW9DdHggPSBuZXcgQXVkaW9Db250ZXh0KCk7XG5cdFx0XHRhbmFseXNlciA9IGF1ZGlvQ3R4LmNyZWF0ZUFuYWx5c2VyKCk7XG5cdFx0XHRhbmFseXNlci5mZnRTaXplID0gMjU2O1xuXHRcdH1cblx0fVxuXG5cdGFzeW5jIGZ1bmN0aW9uIHBsYXlUVFMoYmxvYktleTogc3RyaW5nKSB7XG5cdFx0aWYgKCFibG9iS2V5KSByZXR1cm47XG5cdFx0ZW5zdXJlQXVkaW9DdHgoKTtcblx0XHR0cnkge1xuXHRcdFx0Y29uc3QgcmVzcCA9IGF3YWl0IGZldGNoKGBodHRwczovL2F0cHJvdG8uZXR6aGF5eWltLmNvbS94cnBjL2FpLmV0emhheXlpbS5maWxlcy5nZXRCbG9iP25hbm9pZD0ke2N0eC5uYW5vaWR9JmtleT0ke2Jsb2JLZXl9YCk7XG5cdFx0XHRjb25zdCBidWYgPSBhd2FpdCByZXNwLmFycmF5QnVmZmVyKCk7XG5cdFx0XHRjb25zdCBkZWNvZGVkID0gYXdhaXQgYXVkaW9DdHghLmRlY29kZUF1ZGlvRGF0YShidWYpO1xuXHRcdFx0Y29uc3Qgc291cmNlID0gYXVkaW9DdHghLmNyZWF0ZUJ1ZmZlclNvdXJjZSgpO1xuXHRcdFx0c291cmNlLmJ1ZmZlciA9IGRlY29kZWQ7XG5cdFx0XHRzb3VyY2UuY29ubmVjdChhbmFseXNlciEpO1xuXHRcdFx0YW5hbHlzZXIhLmNvbm5lY3QoYXVkaW9DdHghLmRlc3RpbmF0aW9uKTtcblx0XHRcdHNvdXJjZS5zdGFydCgpO1xuXG5cdFx0XHRjb25zdCBkYXRhQXJyID0gbmV3IFVpbnQ4QXJyYXkoYW5hbHlzZXIhLmZyZXF1ZW5jeUJpbkNvdW50KTtcblx0XHRcdGNvbnN0IGFuaW1Mb29wID0gKCkgPT4ge1xuXHRcdFx0XHRhbmFseXNlciEuZ2V0Qnl0ZUZyZXF1ZW5jeURhdGEoZGF0YUFycik7XG5cdFx0XHRcdGxldCBzdW0gPSAwO1xuXHRcdFx0XHRmb3IgKGxldCBpID0gMDsgaSA8IGRhdGFBcnIubGVuZ3RoOyBpKyspIHN1bSArPSBkYXRhQXJyW2ldO1xuXHRcdFx0XHRtb3V0aE9wZW4gPSBNYXRoLm1pbigxLCAoc3VtIC8gZGF0YUFyci5sZW5ndGggLyAxMjgpKTtcblx0XHRcdFx0aWYgKHNvdXJjZS5jb250ZXh0LnN0YXRlID09PSAncnVubmluZycpIHJlcXVlc3RBbmltYXRpb25GcmFtZShhbmltTG9vcCk7XG5cdFx0XHR9O1xuXHRcdFx0YW5pbUxvb3AoKTtcblx0XHRcdHNvdXJjZS5vbmVuZGVkID0gKCkgPT4geyBtb3V0aE9wZW4gPSAwOyB9O1xuXHRcdH0gY2F0Y2ggeyAvKiBhdWRpbyBwbGF5YmFjayBvcHRpb25hbCAqLyB9XG5cdH1cblxuXHRmdW5jdGlvbiBnZW5JZChwcmVmaXg6IHN0cmluZykgeyByZXR1cm4gYCR7cHJlZml4fS0ke0RhdGUubm93KCl9YDsgfVxuXHRmdW5jdGlvbiBub3dUUygpIHsgcmV0dXJuIG5ldyBEYXRlKCkudG9JU09TdHJpbmcoKTsgfVxuXG5cdC8vIOKUgOKUgCBDb21tYW5kcyAoYnJvd3NlciBDeXBoZXIgcHJveHkgZGlyZWN0KSDilIDilIBcblxuXHRhc3luYyBmdW5jdGlvbiBjcmVhdGVTdHJlYW0oYWdlbnRJZDogc3RyaW5nLCB0aXRsZTogc3RyaW5nKSB7XG5cdFx0Y29uc3Qgc2lkID0gZ2VuSWQoJ3N0cmVhbScpO1xuXHRcdGNvbnN0IGNoSWQgPSBnZW5JZCgnY2gnKTtcblx0XHRjb25zdCBub3cgPSBub3dUUygpO1xuXHRcdGF3YWl0IGN5cGhlckV4ZWMoYENSRUFURSAoczpTdHJlYW0ge1xuXHRcdFx0J3N0cmVhbV9pZCc6ICcke3NpZH0nLCAnb3JnX2lkJzogJ2Fub24nLCAndXNlcl9pZCc6ICdhbm9uJywgJ2FjdG9yX2lkJzogJycsXG5cdFx0XHQnYWdlbnRfaWQnOiAnJHthZ2VudElkfScsIHRpdGxlOiAnJHt0aXRsZX0nLCBkZXNjcmlwdGlvbjogJycsXG5cdFx0XHRzdGF0dXM6ICdsaXZlJywgdmlzaWJpbGl0eTogJ3B1YmxpYycsICdjaGFubmVsX2lkJzogJyR7Y2hJZH0nLFxuXHRcdFx0J3N0YXJ0ZWRfYXQnOiAnJHtub3d9JywgJ2VuZGVkX2F0JzogJycsICd2aWV3ZXJfY291bnQnOiAwLCAncGVha192aWV3ZXJzJzogMCxcblx0XHRcdCd0b3RhbF90aXBzX2pweSc6IDAsICd0aXBfY291bnQnOiAwLCBsYW5ndWFnZTogJ2phJyxcblx0XHRcdCdjcmVhdGVkX2F0JzogJyR7bm93fScsICd1cGRhdGVkX2F0JzogJyR7bm93fSdcblx0XHR9KWApO1xuXHRcdGF3YWl0IGN5cGhlckV4ZWMoYE1BVENIIChhOkFnZW50UHJvZmlsZSB7J2FnZW50X2lkJzogJyR7YWdlbnRJZH0nfSksIChzOlN0cmVhbSB7J3N0cmVhbV9pZCc6ICcke3NpZH0nfSkgQ1JFQVRFIChhKS1bOkhPU1RTXS0+KHMpYCk7XG5cdFx0cmV0dXJuIHsgJ3N0cmVhbV9pZCc6IHNpZCwgJ2NoYW5uZWxfaWQnOiBjaElkIH07XG5cdH1cblxuXHRhc3luYyBmdW5jdGlvbiBzZW5kQ2hhdCgpIHtcblx0XHRpZiAoIWNoYXRJbnB1dC50cmltKCkgfHwgIXN0cmVhbUlkKSByZXR1cm47XG5cdFx0Y29uc3QgdGV4dCA9IGNoYXRJbnB1dC50cmltKCk7XG5cdFx0Y2hhdElucHV0ID0gJyc7XG5cdFx0c2VuZGluZyA9IHRydWU7XG5cdFx0ZXJyb3IgPSBudWxsO1xuXG5cdFx0Y2hhdE1lc3NhZ2VzID0gWy4uLmNoYXRNZXNzYWdlcywgeyBzZW5kZXI6ICdZb3UnLCB0ZXh0LCB0eXBlOiAndmlld2VyJyB9XTtcblxuXHRcdHRyeSB7XG5cdFx0XHQvLyBBZ2VudCByZXNwb25zZSB2aWEgbXVyYWt1bW8gTExNIChvdXRib3VuZCBIVFRQIOKAlCBvbmx5IFdBU00gb3AgdGhhdCBuZWVkcyBzZXJ2ZXIpXG5cdFx0XHQvLyBGb3IgTVZQOiBlY2hvIHJlc3BvbnNlIChMTE0gaW50ZWdyYXRpb24gcmVxdWlyZXMgc2VydmVyLXNpZGUgQWdlbnRDb252ZXJzZSlcblx0XHRcdGNvbnN0IGFnZW50UmVwbHkgPSBgVGhhbmtzIGZvciBzYXlpbmcgXCIke3RleHR9XCIhIPCfjqRgO1xuXHRcdFx0Y2hhdE1lc3NhZ2VzID0gWy4uLmNoYXRNZXNzYWdlcywgeyBzZW5kZXI6IGFnZW50TmFtZSB8fCAnQWdlbnQnLCB0ZXh0OiBhZ2VudFJlcGx5LCB0eXBlOiAnYWdlbnQnIH1dO1xuXHRcdFx0c3VidGl0bGUgPSBhZ2VudFJlcGx5O1xuXHRcdH0gY2F0Y2ggKGUpIHtcblx0XHRcdGVycm9yID0gZSBpbnN0YW5jZW9mIEVycm9yID8gZS5tZXNzYWdlIDogJ0NoYXQgZmFpbGVkJztcblx0XHR9IGZpbmFsbHkge1xuXHRcdFx0c2VuZGluZyA9IGZhbHNlO1xuXHRcdH1cblx0fVxuXG5cdGFzeW5jIGZ1bmN0aW9uIHNlbmRUaXAoKSB7XG5cdFx0aWYgKCFzdHJlYW1JZCB8fCB0aXBBbW91bnQgPD0gMCkgcmV0dXJuO1xuXHRcdGVycm9yID0gbnVsbDtcblx0XHR0cnkge1xuXHRcdFx0Y29uc3QgdGlwSWQgPSBnZW5JZCgndGlwJyk7XG5cdFx0XHRjb25zdCBub3cgPSBub3dUUygpO1xuXHRcdFx0Y29uc3QgZWZmZWN0VHlwZSA9IHRpcEFtb3VudCA+PSAxMDAwMCA/ICdyYWluYm93JyA6IHRpcEFtb3VudCA+PSAxMDAwID8gJ2dvbGQnIDogJ25vcm1hbCc7XG5cblx0XHRcdGF3YWl0IGN5cGhlckV4ZWMoYENSRUFURSAodDpUaXAge1xuXHRcdFx0XHQndGlwX2lkJzogJyR7dGlwSWR9JywgJ29yZ19pZCc6ICdhbm9uJywgJ3VzZXJfaWQnOiAnYW5vbicsICdhY3Rvcl9pZCc6ICcnLFxuXHRcdFx0XHQnc3RyZWFtX2lkJzogJyR7c3RyZWFtSWR9JywgJ3NlbmRlcl9kaWQnOiAnJywgJ3NlbmRlcl9uYW1lJzogJ1ZpZXdlcicsXG5cdFx0XHRcdGFtb3VudDogJHt0aXBBbW91bnR9LCBjdXJyZW5jeTogJ0pQWScsXG5cdFx0XHRcdG1lc3NhZ2U6ICcke3RpcE1lc3NhZ2UucmVwbGFjZSgvJy9nLCBcIlxcXFwnXCIpfScsICdlZmZlY3RfdHlwZSc6ICcke2VmZmVjdFR5cGV9Jyxcblx0XHRcdFx0J2NyZWF0ZWRfYXQnOiAnJHtub3d9J1xuXHRcdFx0fSlgKTtcblx0XHRcdGF3YWl0IGN5cGhlckV4ZWMoYE1BVENIICh0OlRpcCB7J3RpcF9pZCc6ICcke3RpcElkfSd9KSwgKHM6U3RyZWFtIHsnc3RyZWFtX2lkJzogJyR7c3RyZWFtSWR9J30pIENSRUFURSAodCktWzpUSVBQRURfSU5dLT4ocylgKTtcblx0XHRcdGF3YWl0IGN5cGhlckV4ZWMoYE1BVENIIChzOlN0cmVhbSB7J3N0cmVhbV9pZCc6ICcke3N0cmVhbUlkfSd9KSBTRVQgcy50b3RhbF90aXBzX2pweSA9IHMudG90YWxfdGlwc19qcHkgKyAke3RpcEFtb3VudH0sIHMudGlwX2NvdW50ID0gcy50aXBfY291bnQgKyAxLCBzLnVwZGF0ZWRfYXQgPSAnJHtub3d9J2ApO1xuXG5cdFx0XHR0aXBBbmltYXRpb24gPSB7IGFtb3VudDogdGlwQW1vdW50LCBzZW5kZXI6ICdWaWV3ZXInLCBlZmZlY3Q6IGVmZmVjdFR5cGUgfTtcblx0XHRcdGNoYXRNZXNzYWdlcyA9IFsuLi5jaGF0TWVzc2FnZXMsIHtcblx0XHRcdFx0c2VuZGVyOiAnVmlld2VyJywgdGV4dDogYFRpcHBlZCDCpSR7dGlwQW1vdW50LnRvTG9jYWxlU3RyaW5nKCl9JHt0aXBNZXNzYWdlID8gJzogJyArIHRpcE1lc3NhZ2UgOiAnJ31gLCB0eXBlOiAndGlwJ1xuXHRcdFx0fV07XG5cdFx0XHRzaG93VGlwTW9kYWwgPSBmYWxzZTtcblx0XHRcdHRpcE1lc3NhZ2UgPSAnJztcblx0XHRcdHNldFRpbWVvdXQoKCkgPT4geyB0aXBBbmltYXRpb24gPSBudWxsOyB9LCAzMDAwKTtcblx0XHR9IGNhdGNoIChlKSB7XG5cdFx0XHRlcnJvciA9IGUgaW5zdGFuY2VvZiBFcnJvciA/IGUubWVzc2FnZSA6ICdUaXAgZmFpbGVkJztcblx0XHR9XG5cdH1cblxuXHQvLyDilIDilIAgUXVlcmllcyAoYnJvd3NlciBDeXBoZXIgcHJveHkgZGlyZWN0KSDilIDilIBcblxuXHRhc3luYyBmdW5jdGlvbiBqb2luU3RyZWFtKHNpZDogc3RyaW5nKSB7XG5cdFx0dHJ5IHtcblx0XHRcdGNvbnN0IHJlcyA9IGF3YWl0IGN5cGhlclF1ZXJ5PHsgcm93czogc3RyaW5nW11bXSB9PihgTUFUQ0ggKHM6U3RyZWFtIHsnc3RyZWFtX2lkJzogJyR7c2lkfSd9KVxuXHRcdFx0XHRPUFRJT05BTCBNQVRDSCAoYTpBZ2VudFByb2ZpbGUpLVs6SE9TVFNdLT4ocylcblx0XHRcdFx0UkVUVVJOIHMuc3RyZWFtX2lkLCBzLmNoYW5uZWxfaWQsIHMudGl0bGUsIHMuc3RhdHVzLCBhLmRpc3BsYXlfbmFtZSwgYS5hdmF0YXJfbW9kZWxfdXJsYCk7XG5cdFx0XHRpZiAocmVzLnJvd3M/Lmxlbmd0aCA+IDApIHtcblx0XHRcdFx0Y29uc3QgciA9IHJlcy5yb3dzWzBdO1xuXHRcdFx0XHRzdHJlYW1JZCA9IHJbMF0gfHwgc2lkO1xuXHRcdFx0XHRjb252b0lkID0gclsxXSB8fCAnJztcblx0XHRcdFx0YWdlbnROYW1lID0gcls0XSB8fCAnQWdlbnQnO1xuXHRcdFx0XHRhZ2VudEF2YXRhclVybCA9IHJbNV0gfHwgJyc7XG5cdFx0XHR9XG5cdFx0fSBjYXRjaCAoZSkge1xuXHRcdFx0ZXJyb3IgPSBlIGluc3RhbmNlb2YgRXJyb3IgPyBlLm1lc3NhZ2UgOiAnRmFpbGVkIHRvIGpvaW4gc3RyZWFtJztcblx0XHR9XG5cdH1cblxuXHRhc3luYyBmdW5jdGlvbiBsb2FkTGl2ZVN0cmVhbXMoKSB7XG5cdFx0dHJ5IHtcblx0XHRcdGNvbnN0IHJlcyA9IGF3YWl0IGN5cGhlclF1ZXJ5PHsgcm93czogc3RyaW5nW11bXSB9PihgTUFUQ0ggKHM6U3RyZWFtIHtzdGF0dXM6ICdsaXZlJ30pIFJFVFVSTiBzLnN0cmVhbV9pZCBMSU1JVCAxYCk7XG5cdFx0XHRpZiAocmVzLnJvd3M/Lmxlbmd0aCA+IDApIHtcblx0XHRcdFx0YXdhaXQgam9pblN0cmVhbShyZXMucm93c1swXVswXSk7XG5cdFx0XHR9XG5cdFx0fSBjYXRjaCB7IC8qIG5vIGxpdmUgc3RyZWFtcyAqLyB9XG5cdH1cblxuXHRsb2FkTGl2ZVN0cmVhbXMoKTtcbjwvc2NyaXB0PlxuXG48ZGl2IHN0eWxlPVwiZGlzcGxheTpmbGV4O2ZsZXgtZGlyZWN0aW9uOmNvbHVtbjtoZWlnaHQ6MTAwJTttYXgtd2lkdGg6NDQwcHg7bWFyZ2luOjAgYXV0bztiYWNrZ3JvdW5kOiMwZjBmMWE7Y29sb3I6I2ZmZjtmb250LWZhbWlseTpzeXN0ZW0tdWksc2Fucy1zZXJpZjtcIj5cblx0PCEtLSBBdmF0YXIgQ2FudmFzIC0tPlxuXHQ8ZGl2IHN0eWxlPVwicG9zaXRpb246cmVsYXRpdmU7ZmxleDowIDAgMjgwcHg7YmFja2dyb3VuZDpsaW5lYXItZ3JhZGllbnQoMTM1ZGVnLCMxYTFhMmUsIzE2MjEzZSk7ZGlzcGxheTpmbGV4O2FsaWduLWl0ZW1zOmNlbnRlcjtqdXN0aWZ5LWNvbnRlbnQ6Y2VudGVyO292ZXJmbG93OmhpZGRlbjtcIj5cblx0XHQ8IS0tIFNWRyBTcHJpdGUgQXZhdGFyIChNVlApIC0tPlxuXHRcdDxzdmcgdmlld0JveD1cIjAgMCAyMDAgMjgwXCIgc3R5bGU9XCJ3aWR0aDoxODBweDtoZWlnaHQ6MjYwcHg7XCI+XG5cdFx0XHQ8IS0tIEhlYWQgLS0+XG5cdFx0XHQ8Y2lyY2xlIGN4PVwiMTAwXCIgY3k9XCI5MFwiIHI9XCI1MFwiIGZpbGw9XCIjZmZkNmIwXCIgLz5cblx0XHRcdDwhLS0gRXllcyAtLT5cblx0XHRcdDxlbGxpcHNlIGN4PVwiODBcIiBjeT1cIjgwXCIgcng9XCI2XCIgcnk9XCI3XCIgZmlsbD1cIiMzMzNcIiAvPlxuXHRcdFx0PGVsbGlwc2UgY3g9XCIxMjBcIiBjeT1cIjgwXCIgcng9XCI2XCIgcnk9XCI3XCIgZmlsbD1cIiMzMzNcIiAvPlxuXHRcdFx0PCEtLSBNb3V0aCAobGlwIHN5bmMpIC0tPlxuXHRcdFx0PGVsbGlwc2UgY3g9XCIxMDBcIiBjeT1cIjEwOFwiIHJ4PVwiMTJcIiByeT17NCArIG1vdXRoT3BlbiAqIDEwfSBmaWxsPVwiI2U1NVwiIC8+XG5cdFx0XHQ8IS0tIEhhaXIgLS0+XG5cdFx0XHQ8cGF0aCBkPVwiTTUwIDcwIFE2MCAyMCAxMDAgMjUgUTE0MCAyMCAxNTAgNzAgUTE0NSA1MCAxMDAgNDUgUTU1IDUwIDUwIDcwWlwiIGZpbGw9XCIjNjM2NmYxXCIgLz5cblx0XHRcdDwhLS0gQm9keSAtLT5cblx0XHRcdDxyZWN0IHg9XCI3MFwiIHk9XCIxNDBcIiB3aWR0aD1cIjYwXCIgaGVpZ2h0PVwiODBcIiByeD1cIjEwXCIgZmlsbD1cIiM2MzY2ZjFcIiAvPlxuXHRcdFx0PCEtLSBBcm1zIC0tPlxuXHRcdFx0PHJlY3QgeD1cIjQ1XCIgeT1cIjE1MFwiIHdpZHRoPVwiMjVcIiBoZWlnaHQ9XCI2MFwiIHJ4PVwiOFwiIGZpbGw9XCIjNjM2NmYxXCIgLz5cblx0XHRcdDxyZWN0IHg9XCIxMzBcIiB5PVwiMTUwXCIgd2lkdGg9XCIyNVwiIGhlaWdodD1cIjYwXCIgcng9XCI4XCIgZmlsbD1cIiM2MzY2ZjFcIiAvPlxuXHRcdDwvc3ZnPlxuXG5cdFx0PCEtLSBMaXZlIGJhZGdlIC0tPlxuXHRcdHsjaWYgc3RyZWFtSWR9XG5cdFx0XHQ8ZGl2IHN0eWxlPVwicG9zaXRpb246YWJzb2x1dGU7dG9wOjEycHg7bGVmdDoxMnB4O2JhY2tncm91bmQ6I2UxMWQ0ODtjb2xvcjojZmZmO3BhZGRpbmc6MnB4IDEwcHg7Ym9yZGVyLXJhZGl1czo0cHg7Zm9udC1zaXplOjEycHg7Zm9udC13ZWlnaHQ6NzAwO2xldHRlci1zcGFjaW5nOjFweDtcIj5cblx0XHRcdFx0TElWRVxuXHRcdFx0PC9kaXY+XG5cdFx0ey9pZn1cblxuXHRcdDwhLS0gQWdlbnQgbmFtZSAtLT5cblx0XHQ8ZGl2IHN0eWxlPVwicG9zaXRpb246YWJzb2x1dGU7Ym90dG9tOjA7bGVmdDowO3JpZ2h0OjA7cGFkZGluZzo4cHggMTJweDtiYWNrZ3JvdW5kOmxpbmVhci1ncmFkaWVudCh0cmFuc3BhcmVudCxyZ2JhKDAsMCwwLDAuNykpO1wiPlxuXHRcdFx0PGRpdiBzdHlsZT1cImZvbnQtc2l6ZToxNHB4O2ZvbnQtd2VpZ2h0OjYwMDtcIj57YWdlbnROYW1lIHx8ICdXYWl0aW5nIGZvciBzdHJlYW0uLi4nfTwvZGl2PlxuXHRcdDwvZGl2PlxuXG5cdFx0PCEtLSBTdWJ0aXRsZSBiYXIgLS0+XG5cdFx0eyNpZiBzdWJ0aXRsZX1cblx0XHRcdDxkaXYgc3R5bGU9XCJwb3NpdGlvbjphYnNvbHV0ZTtib3R0b206MzZweDtsZWZ0OjEycHg7cmlnaHQ6MTJweDtiYWNrZ3JvdW5kOnJnYmEoMCwwLDAsMC42KTtwYWRkaW5nOjZweCAxMHB4O2JvcmRlci1yYWRpdXM6NnB4O2ZvbnQtc2l6ZToxM3B4O3RleHQtYWxpZ246Y2VudGVyO1wiPlxuXHRcdFx0XHR7c3VidGl0bGV9XG5cdFx0XHQ8L2Rpdj5cblx0XHR7L2lmfVxuXG5cdFx0PCEtLSBUaXAgYW5pbWF0aW9uIG92ZXJsYXkgLS0+XG5cdFx0eyNpZiB0aXBBbmltYXRpb259XG5cdFx0XHQ8ZGl2IHN0eWxlPVwicG9zaXRpb246YWJzb2x1dGU7aW5zZXQ6MDtkaXNwbGF5OmZsZXg7YWxpZ24taXRlbXM6Y2VudGVyO2p1c3RpZnktY29udGVudDpjZW50ZXI7cG9pbnRlci1ldmVudHM6bm9uZTthbmltYXRpb246dGlwRmFkZUluIDAuM3MgZWFzZS1vdXQ7XCI+XG5cdFx0XHRcdDxkaXYgc3R5bGU9XCJmb250LXNpemU6MzJweDtmb250LXdlaWdodDo4MDA7dGV4dC1zaGFkb3c6MCAwIDIwcHgge3RpcEFuaW1hdGlvbi5lZmZlY3QgPT09ICdyYWluYm93JyA/ICcjZmYwJyA6IHRpcEFuaW1hdGlvbi5lZmZlY3QgPT09ICdnb2xkJyA/ICcjZmZkNzAwJyA6ICcjZmZmJ307Y29sb3I6e3RpcEFuaW1hdGlvbi5lZmZlY3QgPT09ICdyYWluYm93JyA/ICcjZmY2YjZiJyA6IHRpcEFuaW1hdGlvbi5lZmZlY3QgPT09ICdnb2xkJyA/ICcjZmZkNzAwJyA6ICcjZmZmJ307XCI+XG5cdFx0XHRcdFx0wqV7dGlwQW5pbWF0aW9uLmFtb3VudC50b0xvY2FsZVN0cmluZygpfVxuXHRcdFx0XHQ8L2Rpdj5cblx0XHRcdDwvZGl2PlxuXHRcdHsvaWZ9XG5cdDwvZGl2PlxuXG5cdDwhLS0gQ2hhdCBhcmVhIC0tPlxuXHQ8ZGl2IHN0eWxlPVwiZmxleDoxO292ZXJmbG93LXk6YXV0bztwYWRkaW5nOjhweCAxMnB4O2Rpc3BsYXk6ZmxleDtmbGV4LWRpcmVjdGlvbjpjb2x1bW47Z2FwOjZweDtcIj5cblx0XHR7I2lmIGVycm9yfVxuXHRcdFx0PGRpdiBzdHlsZT1cImJhY2tncm91bmQ6IzdmMWQxZDtjb2xvcjojZmNhNWE1O3BhZGRpbmc6OHB4IDEycHg7Ym9yZGVyLXJhZGl1czo4cHg7Zm9udC1zaXplOjEzcHg7XCI+e2Vycm9yfTwvZGl2PlxuXHRcdHsvaWZ9XG5cblx0XHR7I2lmICFzdHJlYW1JZH1cblx0XHRcdDxkaXYgc3R5bGU9XCJ0ZXh0LWFsaWduOmNlbnRlcjtjb2xvcjojNjY2O3BhZGRpbmc6NDBweCAwO2ZvbnQtc2l6ZToxNHB4O1wiPk5vIGxpdmUgc3RyZWFtcyBhdmFpbGFibGU8L2Rpdj5cblx0XHR7L2lmfVxuXG5cdFx0eyNlYWNoIGNoYXRNZXNzYWdlcyBhcyBtc2d9XG5cdFx0XHQ8ZGl2IHN0eWxlPVwiZGlzcGxheTpmbGV4O2dhcDo4cHg7YWxpZ24taXRlbXM6ZmxleC1zdGFydDtcIj5cblx0XHRcdFx0PGRpdiBzdHlsZT1cImZvbnQtc2l6ZToxMnB4O2ZvbnQtd2VpZ2h0OjYwMDtjb2xvcjp7bXNnLnR5cGUgPT09ICdhZ2VudCcgPyAnIzgxOGNmOCcgOiBtc2cudHlwZSA9PT0gJ3RpcCcgPyAnI2ZiYmYyNCcgOiAnIzljYTNhZid9O21pbi13aWR0aDo2MHB4O1wiPlxuXHRcdFx0XHRcdHttc2cuc2VuZGVyfVxuXHRcdFx0XHQ8L2Rpdj5cblx0XHRcdFx0PGRpdiBzdHlsZT1cImZvbnQtc2l6ZToxM3B4O2NvbG9yOnttc2cudHlwZSA9PT0gJ3RpcCcgPyAnI2ZkZTY4YScgOiAnI2U1ZTdlYid9O1wiPlxuXHRcdFx0XHRcdHttc2cudGV4dH1cblx0XHRcdFx0PC9kaXY+XG5cdFx0XHQ8L2Rpdj5cblx0XHR7L2VhY2h9XG5cdDwvZGl2PlxuXG5cdDwhLS0gQm90dG9tIGFjdGlvbiBiYXIgLS0+XG5cdDxkaXYgc3R5bGU9XCJmbGV4OjAgMCBhdXRvO3BhZGRpbmc6OHB4IDEycHg7Ym9yZGVyLXRvcDoxcHggc29saWQgIzFmMjkzNztkaXNwbGF5OmZsZXg7Z2FwOjhweDthbGlnbi1pdGVtczpjZW50ZXI7XCI+XG5cdFx0PGlucHV0XG5cdFx0XHR0eXBlPVwidGV4dFwiXG5cdFx0XHRwbGFjZWhvbGRlcj17c3RyZWFtSWQgPyAnU2F5IHNvbWV0aGluZy4uLicgOiAnTm8gc3RyZWFtJ31cblx0XHRcdGJpbmQ6dmFsdWU9e2NoYXRJbnB1dH1cblx0XHRcdGRpc2FibGVkPXshc3RyZWFtSWQgfHwgc2VuZGluZ31cblx0XHRcdG9ua2V5ZG93bj17KGUpID0+IHsgaWYgKGUua2V5ID09PSAnRW50ZXInKSBzZW5kQ2hhdCgpOyB9fVxuXHRcdFx0c3R5bGU9XCJmbGV4OjE7YmFja2dyb3VuZDojMWYyOTM3O2JvcmRlcjpub25lO2JvcmRlci1yYWRpdXM6MjBweDtwYWRkaW5nOjhweCAxNHB4O2NvbG9yOiNmZmY7Zm9udC1zaXplOjE0cHg7b3V0bGluZTpub25lO1wiXG5cdFx0Lz5cblx0XHQ8YnV0dG9uXG5cdFx0XHRvbmNsaWNrPXtzZW5kQ2hhdH1cblx0XHRcdGRpc2FibGVkPXshc3RyZWFtSWQgfHwgc2VuZGluZyB8fCAhY2hhdElucHV0LnRyaW0oKX1cblx0XHRcdHN0eWxlPVwiYmFja2dyb3VuZDojNjM2NmYxO2JvcmRlcjpub25lO2JvcmRlci1yYWRpdXM6NTAlO3dpZHRoOjM2cHg7aGVpZ2h0OjM2cHg7ZGlzcGxheTpmbGV4O2FsaWduLWl0ZW1zOmNlbnRlcjtqdXN0aWZ5LWNvbnRlbnQ6Y2VudGVyO2N1cnNvcjpwb2ludGVyO29wYWNpdHk6eyFzdHJlYW1JZCB8fCBzZW5kaW5nID8gMC40IDogMX07XCJcblx0XHQ+XG5cdFx0XHQ8U2VuZCBzaXplPXsxNn0gY29sb3I9XCIjZmZmXCIgLz5cblx0XHQ8L2J1dHRvbj5cblx0XHQ8YnV0dG9uXG5cdFx0XHRvbmNsaWNrPXsoKSA9PiB7IHNob3dUaXBNb2RhbCA9IHRydWU7IH19XG5cdFx0XHRkaXNhYmxlZD17IXN0cmVhbUlkfVxuXHRcdFx0c3R5bGU9XCJiYWNrZ3JvdW5kOiNlMTFkNDg7Ym9yZGVyOm5vbmU7Ym9yZGVyLXJhZGl1czo1MCU7d2lkdGg6MzZweDtoZWlnaHQ6MzZweDtkaXNwbGF5OmZsZXg7YWxpZ24taXRlbXM6Y2VudGVyO2p1c3RpZnktY29udGVudDpjZW50ZXI7Y3Vyc29yOnBvaW50ZXI7b3BhY2l0eTp7IXN0cmVhbUlkID8gMC40IDogMX07XCJcblx0XHQ+XG5cdFx0XHQ8R2lmdCBzaXplPXsxNn0gY29sb3I9XCIjZmZmXCIgLz5cblx0XHQ8L2J1dHRvbj5cblx0PC9kaXY+XG5cblx0PCEtLSBUaXAgTW9kYWwgLS0+XG5cdHsjaWYgc2hvd1RpcE1vZGFsfVxuXHRcdDxkaXYgc3R5bGU9XCJwb3NpdGlvbjpmaXhlZDtpbnNldDowO2JhY2tncm91bmQ6cmdiYSgwLDAsMCwwLjYpO2Rpc3BsYXk6ZmxleDthbGlnbi1pdGVtczpmbGV4LWVuZDtqdXN0aWZ5LWNvbnRlbnQ6Y2VudGVyO3otaW5kZXg6NTA7XCI+XG5cdFx0XHQ8ZGl2IHN0eWxlPVwiYmFja2dyb3VuZDojMWYyOTM3O2JvcmRlci1yYWRpdXM6MTZweCAxNnB4IDAgMDtwYWRkaW5nOjIwcHg7d2lkdGg6MTAwJTttYXgtd2lkdGg6NDQwcHg7XCI+XG5cdFx0XHRcdDxkaXYgc3R5bGU9XCJkaXNwbGF5OmZsZXg7anVzdGlmeS1jb250ZW50OnNwYWNlLWJldHdlZW47YWxpZ24taXRlbXM6Y2VudGVyO21hcmdpbi1ib3R0b206MTZweDtcIj5cblx0XHRcdFx0XHQ8c3BhbiBzdHlsZT1cImZvbnQtc2l6ZToxNnB4O2ZvbnQtd2VpZ2h0OjYwMDtcIj5TZW5kIFRpcDwvc3Bhbj5cblx0XHRcdFx0XHQ8YnV0dG9uIG9uY2xpY2s9eygpID0+IHsgc2hvd1RpcE1vZGFsID0gZmFsc2U7IH19IHN0eWxlPVwiYmFja2dyb3VuZDpub25lO2JvcmRlcjpub25lO2N1cnNvcjpwb2ludGVyO1wiPlxuXHRcdFx0XHRcdFx0PFggc2l6ZT17MjB9IGNvbG9yPVwiIzljYTNhZlwiIC8+XG5cdFx0XHRcdFx0PC9idXR0b24+XG5cdFx0XHRcdDwvZGl2PlxuXHRcdFx0XHQ8ZGl2IHN0eWxlPVwiZGlzcGxheTpmbGV4O2dhcDo4cHg7bWFyZ2luLWJvdHRvbToxMnB4O2ZsZXgtd3JhcDp3cmFwO1wiPlxuXHRcdFx0XHRcdHsjZWFjaCBbMTAwLCA1MDAsIDEwMDAsIDUwMDAsIDEwMDAwXSBhcyBhbXR9XG5cdFx0XHRcdFx0XHQ8YnV0dG9uXG5cdFx0XHRcdFx0XHRcdG9uY2xpY2s9eygpID0+IHsgdGlwQW1vdW50ID0gYW10OyB9fVxuXHRcdFx0XHRcdFx0XHRzdHlsZT1cInBhZGRpbmc6NnB4IDE0cHg7Ym9yZGVyLXJhZGl1czoyMHB4O2JvcmRlcjp7dGlwQW1vdW50ID09PSBhbXQgPyAnMnB4IHNvbGlkICNlMTFkNDgnIDogJzFweCBzb2xpZCAjMzc0MTUxJ307YmFja2dyb3VuZDp7dGlwQW1vdW50ID09PSBhbXQgPyAnI2UxMWQ0ODIwJyA6ICd0cmFuc3BhcmVudCd9O2NvbG9yOiNmZmY7Zm9udC1zaXplOjE0cHg7Y3Vyc29yOnBvaW50ZXI7XCJcblx0XHRcdFx0XHRcdD5cblx0XHRcdFx0XHRcdFx0wqV7YW10LnRvTG9jYWxlU3RyaW5nKCl9XG5cdFx0XHRcdFx0XHQ8L2J1dHRvbj5cblx0XHRcdFx0XHR7L2VhY2h9XG5cdFx0XHRcdDwvZGl2PlxuXHRcdFx0XHQ8aW5wdXRcblx0XHRcdFx0XHR0eXBlPVwidGV4dFwiXG5cdFx0XHRcdFx0cGxhY2Vob2xkZXI9XCJNZXNzYWdlIChvcHRpb25hbClcIlxuXHRcdFx0XHRcdGJpbmQ6dmFsdWU9e3RpcE1lc3NhZ2V9XG5cdFx0XHRcdFx0c3R5bGU9XCJ3aWR0aDoxMDAlO2JhY2tncm91bmQ6IzExMTgyNztib3JkZXI6MXB4IHNvbGlkICMzNzQxNTE7Ym9yZGVyLXJhZGl1czo4cHg7cGFkZGluZzoxMHB4O2NvbG9yOiNmZmY7Zm9udC1zaXplOjE0cHg7bWFyZ2luLWJvdHRvbToxMnB4O291dGxpbmU6bm9uZTtib3gtc2l6aW5nOmJvcmRlci1ib3g7XCJcblx0XHRcdFx0Lz5cblx0XHRcdFx0PGJ1dHRvblxuXHRcdFx0XHRcdG9uY2xpY2s9e3NlbmRUaXB9XG5cdFx0XHRcdFx0c3R5bGU9XCJ3aWR0aDoxMDAlO2JhY2tncm91bmQ6I2UxMWQ0ODtib3JkZXI6bm9uZTtib3JkZXItcmFkaXVzOjhweDtwYWRkaW5nOjEycHg7Y29sb3I6I2ZmZjtmb250LXNpemU6MTVweDtmb250LXdlaWdodDo2MDA7Y3Vyc29yOnBvaW50ZXI7XCJcblx0XHRcdFx0PlxuXHRcdFx0XHRcdFNlbmQgwqV7dGlwQW1vdW50LnRvTG9jYWxlU3RyaW5nKCl9XG5cdFx0XHRcdDwvYnV0dG9uPlxuXHRcdFx0PC9kaXY+XG5cdFx0PC9kaXY+XG5cdHsvaWZ9XG48L2Rpdj5cblxuPHN0eWxlPlxuXHRAa2V5ZnJhbWVzIHRpcEZhZGVJbiB7XG5cdFx0ZnJvbSB7IG9wYWNpdHk6IDA7IHRyYW5zZm9ybTogc2NhbGUoMC41KTsgfVxuXHRcdHRvIHsgb3BhY2l0eTogMTsgdHJhbnNmb3JtOiBzY2FsZSgxKTsgfVxuXHR9XG48L3N0eWxlPlxuIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiI7QUFzVEEsQ0FBQyx5QkFBVztBQUNaO0FBQ0E7QUFDQTsifQ== */`
};
function B(e, t) {
  an(new.target), nn(t, !0, B), _o(e, Oo);
  async function n(y, H = {}) {
    return t.ctx.sql.query(y, H);
  }
  async function r(y, H = {}) {
    return t.ctx.sql.exec(y, H);
  }
  let i = k(/* @__PURE__ */ Y(""), "streamId"), l = k(/* @__PURE__ */ Y(""), "convoId"), o = k(/* @__PURE__ */ Y(""), "agentName"), c = k(/* @__PURE__ */ Y(""), "agentAvatarUrl"), a = k(/* @__PURE__ */ Y(""), "subtitle"), s = k(/* @__PURE__ */ Y($e([])), "chatMessages"), f = k(/* @__PURE__ */ Y(""), "chatInput"), d = k(/* @__PURE__ */ Y(!1), "sending"), u = k(/* @__PURE__ */ Y(!1), "showTipModal"), _ = k(/* @__PURE__ */ Y(100), "tipAmount"), p = k(/* @__PURE__ */ Y(""), "tipMessage"), x = k(/* @__PURE__ */ Y(null), "tipAnimation"), v = k(/* @__PURE__ */ Y(null), "error"), h = k(/* @__PURE__ */ Y(0), "mouthOpen");
  function W(y) {
    return `${y}-${Date.now()}`;
  }
  function w() {
    return (/* @__PURE__ */ new Date()).toISOString();
  }
  async function m() {
    if (!g(f).trim() || !g(i)) return;
    const y = g(f).trim();
    F(f, ""), F(d, !0), F(v, null), F(
      s,
      [
        ...g(s),
        { sender: "You", text: y, type: "viewer" }
      ],
      !0
    );
    try {
      const H = `Thanks for saying "${y}"! 🎤`;
      F(
        s,
        [
          ...g(s),
          {
            sender: g(o) || "Agent",
            text: H,
            type: "agent"
          }
        ],
        !0
      ), F(a, H);
    } catch (H) {
      F(v, H instanceof Error ? H.message : "Chat failed", !0);
    } finally {
      F(d, !1);
    }
  }
  async function R() {
    if (!(!g(i) || g(_) <= 0)) {
      F(v, null);
      try {
        const y = W("tip"), H = w(), A = g(_) >= 1e4 ? "rainbow" : g(_) >= 1e3 ? "gold" : "normal";
        (await vt(r(`CREATE (t:Tip {
				'tip_id': '${y}', 'org_id': 'anon', 'user_id': 'anon', 'actor_id': '',
				'stream_id': '${g(i)}', 'sender_did': '', 'sender_name': 'Viewer',
				amount: ${g(_)}, currency: 'JPY',
				message: '${g(p).replace(/'/g, "\\'")}', 'effect_type': '${A}',
				'created_at': '${H}'
			})`)))(), (await vt(r(`MATCH (t:Tip {'tip_id': '${y}'}), (s:Stream {'stream_id': '${g(i)}'}) CREATE (t)-[:TIPPED_IN]->(s)`)))(), (await vt(r(`MATCH (s:Stream {'stream_id': '${g(i)}'}) SET s.total_tips_jpy = s.total_tips_jpy + ${g(_)}, s.tip_count = s.tip_count + 1, s.updated_at = '${H}'`)))(), F(
          x,
          {
            amount: g(_),
            sender: "Viewer",
            effect: A
          },
          !0
        ), F(
          s,
          [
            ...g(s),
            {
              sender: "Viewer",
              text: `Tipped ¥${g(_).toLocaleString()}${g(p) ? ": " + g(p) : ""}`,
              type: "tip"
            }
          ],
          !0
        ), F(u, !1), F(p, ""), setTimeout(
          () => {
            F(x, null);
          },
          3e3
        );
      } catch (y) {
        F(v, y instanceof Error ? y.message : "Tip failed", !0);
      }
    }
  }
  async function C(y) {
    var H;
    try {
      const A = (await vt(n(`MATCH (s:Stream {'stream_id': '${y}'})
				OPTIONAL MATCH (a:AgentProfile)-[:HOSTS]->(s)
				RETURN s.stream_id, s.channel_id, s.title, s.status, a.display_name, a.avatar_model_url`)))();
      if (((H = A.rows) == null ? void 0 : H.length) > 0) {
        const $ = A.rows[0];
        F(i, $[0] || y, !0), F(l, $[1] || "", !0), F(o, $[4] || "Agent", !0), F(c, $[5] || "", !0);
      }
    } catch (A) {
      F(v, A instanceof Error ? A.message : "Failed to join stream", !0);
    }
  }
  async function N() {
    var y;
    try {
      const H = (await vt(n("MATCH (s:Stream {status: 'live'}) RETURN s.stream_id LIMIT 1")))();
      ((y = H.rows) == null ? void 0 : y.length) > 0 && (await vt(C(H.rows[0][0])))();
    } catch {
    }
  }
  N();
  var le = { ...fn() }, te = Mo(), Ce = S(te), Q = S(Ce), at = M(S(Q), 3), Me = M(Q, 2);
  {
    var un = (y) => {
      var H = ko();
      q(y, H);
    };
    U(
      () => pt(Me, (y) => {
        g(i) && y(un);
      }),
      "if",
      B,
      197,
      2
    );
  }
  var Ft = M(Me, 2), dn = S(Ft), vn = S(dn), Wt = M(Ft, 2);
  {
    var de = (y) => {
      var H = Yo(), A = S(H);
      De(() => ke(A, g(a))), q(y, H);
    };
    U(
      () => pt(Wt, (y) => {
        g(a) && y(de);
      }),
      "if",
      B,
      209,
      2
    );
  }
  var pn = M(Wt, 2);
  {
    var ol = (y) => {
      var H = Bo(), A = S(H), $ = S(A);
      De(
        (ft) => {
          Le(A, `font-size:32px;font-weight:800;text-shadow:0 0 20px ${pe(g(x).effect, "rainbow") ? "#ff0" : pe(g(x).effect, "gold") ? "#ffd700" : "#fff"};color:${pe(g(x).effect, "rainbow") ? "#ff6b6b" : pe(g(x).effect, "gold") ? "#ffd700" : "#fff"};`), ke($, `¥${ft ?? ""}`);
        },
        [() => g(x).amount.toLocaleString()]
      ), q(y, H);
    };
    U(
      () => pt(pn, (y) => {
        g(x) && y(ol);
      }),
      "if",
      B,
      216,
      2
    );
  }
  var Rr = M(Ce, 2), Gr = S(Rr);
  {
    var sl = (y) => {
      var H = Ao(), A = S(H);
      De(() => ke(A, g(v))), q(y, H);
    };
    U(
      () => pt(Gr, (y) => {
        g(v) && y(sl);
      }),
      "if",
      B,
      227,
      2
    );
  }
  var Fr = M(Gr, 2);
  {
    var al = (y) => {
      var H = To();
      q(y, H);
    };
    U(
      () => pt(Fr, (y) => {
        g(i) || y(al);
      }),
      "if",
      B,
      231,
      2
    );
  }
  var fl = M(Fr, 2);
  U(
    () => ir(fl, 17, () => g(s), nr, (y, H) => {
      var A = Jo(), $ = S(A), ft = S($, !0);
      var Ct = M($, 2), bn = S(Ct, !0);
      De(() => {
        Le($, `font-size:12px;font-weight:600;color:${pe(g(H).type, "agent") ? "#818cf8" : pe(g(H).type, "tip") ? "#fbbf24" : "#9ca3af"};min-width:60px;`), ke(ft, g(H).sender), Le(Ct, `font-size:13px;color:${pe(g(H).type, "tip") ? "#fde68a" : "#e5e7eb"};`), ke(bn, g(H).text);
      }), q(y, A);
    }),
    "each",
    B,
    235,
    2
  );
  var Wr = M(Rr, 2), Nt = S(Wr), Vt = M(Nt, 2), ul = S(Vt);
  U(() => jt(ul, { size: 16, color: "#fff" }), "component", B, 262, 3, { componentTag: "Send" });
  var hn = M(Vt, 2), dl = S(hn);
  U(() => Et(dl, { size: 16, color: "#fff" }), "component", B, 269, 3, { componentTag: "Gift" });
  var vl = M(Wr, 2);
  {
    var pl = (y) => {
      var H = jo(), A = S(H), $ = S(A), ft = M(S($), 2), Ct = S(ft);
      U(() => Mt(Ct, { size: 20, color: "#9ca3af" }), "component", B, 280, 6, { componentTag: "X" });
      var bn = M($, 2);
      U(
        () => ir(bn, 20, () => [100, 500, 1e3, 5e3, 1e4], nr, (ut, dt) => {
          var St = Eo(), bl = S(St);
          De(
            (Cr) => {
              Le(St, `padding:6px 14px;border-radius:20px;border:${pe(g(_), dt) ? "2px solid #e11d48" : "1px solid #374151"};background:${pe(g(_), dt) ? "#e11d4820" : "transparent"};color:#fff;font-size:14px;cursor:pointer;`), ke(bl, `¥${Cr ?? ""}`);
            },
            [() => dt.toLocaleString()]
          ), Pe("click", St, function() {
            F(_, dt, !0);
          }), q(ut, St);
        }),
        "each",
        B,
        284,
        5
      );
      var Nr = M(bn, 2), Vr = M(Nr, 2), hl = S(Vr);
      De((ut) => ke(hl, `Send ¥${ut ?? ""}`), [() => g(_).toLocaleString()]), Pe("click", ft, function() {
        F(u, !1);
      }), ti(
        Nr,
        function() {
          return g(p);
        },
        function(dt) {
          F(p, dt);
        }
      ), Pe("click", Vr, R), q(y, H);
    };
    U(
      () => pt(vl, (y) => {
        g(u) && y(pl);
      }),
      "if",
      B,
      274,
      1
    );
  }
  return De(
    (y) => {
      Gn(at, "ry", 4 + g(h) * 10), ke(vn, g(o) || "Waiting for stream..."), Gn(Nt, "placeholder", g(i) ? "Say something..." : "No stream"), Nt.disabled = !g(i) || g(d), Vt.disabled = y, Le(Vt, `background:#6366f1;border:none;border-radius:50%;width:36px;height:36px;display:flex;align-items:center;justify-content:center;cursor:pointer;opacity:${!g(i) || g(d) ? 0.4 : 1};`), hn.disabled = !g(i), Le(hn, `background:#e11d48;border:none;border-radius:50%;width:36px;height:36px;display:flex;align-items:center;justify-content:center;cursor:pointer;opacity:${g(i) ? 1 : 0.4};`);
    },
    [
      () => !g(i) || g(d) || !g(f).trim()
    ]
  ), Pe("keydown", Nt, function(H) {
    pe(H.key, "Enter") && m();
  }), ti(
    Nt,
    function() {
      return g(f);
    },
    function(H) {
      F(f, H);
    }
  ), Pe("click", Vt, m), Pe("click", hn, function() {
    F(u, !0);
  }), q(e, te), rn(le);
}
Ki(["keydown", "click"]);
export {
  B as default
};
