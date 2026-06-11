// Minimal Web API polyfill for SvelteKit SSR in Boa/QuickJS
// These are the minimum APIs SvelteKit's server bundle requires

class Headers {
  constructor(init) {
    this._map = {};
    if (init) {
      if (typeof init === 'object' && !Array.isArray(init)) {
        for (const [k, v] of Object.entries(init)) {
          this._map[k.toLowerCase()] = String(v);
        }
      }
    }
  }
  get(name) { return this._map[name.toLowerCase()] || null; }
  set(name, value) { this._map[name.toLowerCase()] = String(value); }
  has(name) { return name.toLowerCase() in this._map; }
  delete(name) { delete this._map[name.toLowerCase()]; }
  forEach(cb) { for (const [k, v] of Object.entries(this._map)) cb(v, k, this); }
  entries() { return Object.entries(this._map)[Symbol.iterator](); }
  keys() { return Object.keys(this._map)[Symbol.iterator](); }
  values() { return Object.values(this._map)[Symbol.iterator](); }
  [Symbol.iterator]() { return this.entries(); }
}

class URLSearchParams {
  constructor(init) {
    this._params = [];
    if (typeof init === 'string') {
      const s = init.startsWith('?') ? init.slice(1) : init;
      for (const pair of s.split('&')) {
        if (!pair) continue;
        const [k, ...rest] = pair.split('=');
        this._params.push([decodeURIComponent(k), decodeURIComponent(rest.join('='))]);
      }
    }
  }
  get(name) { const p = this._params.find(([k]) => k === name); return p ? p[1] : null; }
  getAll(name) { return this._params.filter(([k]) => k === name).map(([, v]) => v); }
  has(name) { return this._params.some(([k]) => k === name); }
  set(name, value) {
    let found = false;
    this._params = this._params.filter(([k]) => { if (k === name && !found) { found = true; return true; } return k !== name; });
    if (found) { this._params.find(([k]) => k === name)[1] = String(value); }
    else { this._params.push([name, String(value)]); }
  }
  append(name, value) { this._params.push([name, String(value)]); }
  delete(name) { this._params = this._params.filter(([k]) => k !== name); }
  toString() { return this._params.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join('&'); }
  forEach(cb) { for (const [k, v] of this._params) cb(v, k, this); }
  entries() { return this._params[Symbol.iterator](); }
  [Symbol.iterator]() { return this.entries(); }
}

class URL {
  constructor(url, base) {
    let full = url;
    if (base && !url.match(/^https?:\/\//)) {
      if (typeof base === 'string') {
        full = base.replace(/\/$/, '') + (url.startsWith('/') ? '' : '/') + url;
      } else {
        full = base.href.replace(/\/$/, '') + (url.startsWith('/') ? '' : '/') + url;
      }
    }
    const m = full.match(/^(https?):\/\/([^/?#]+)(\/[^?#]*)?\??([^#]*)#?(.*)/);
    if (!m) throw new TypeError('Invalid URL: ' + url);
    this.protocol = m[1] + ':';
    this.host = m[2];
    this.hostname = m[2].split(':')[0];
    this.port = m[2].includes(':') ? m[2].split(':')[1] : '';
    this.pathname = m[3] || '/';
    this.search = m[4] ? '?' + m[4] : '';
    this.hash = m[5] ? '#' + m[5] : '';
    this.searchParams = new URLSearchParams(m[4] || '');
    this.origin = this.protocol + '//' + this.host;
    this.href = this.origin + this.pathname + this.search + this.hash;
  }
  toString() { return this.href; }
}

class Request {
  constructor(input, init) {
    if (typeof input === 'string' || input instanceof URL) {
      this.url = String(input);
    } else {
      this.url = input.url;
    }
    init = init || {};
    this.method = (init.method || 'GET').toUpperCase();
    this.headers = init.headers instanceof Headers ? init.headers : new Headers(init.headers || {});
    this._body = init.body || null;
  }
  async text() { return this._body || ''; }
  async json() { return JSON.parse(this._body || '{}'); }
  async arrayBuffer() { return new ArrayBuffer(0); }
}

class Response {
  constructor(body, init) {
    init = init || {};
    this._body = body || '';
    this.status = init.status || 200;
    this.statusText = init.statusText || 'OK';
    this.headers = init.headers instanceof Headers ? init.headers : new Headers(init.headers || {});
    this.ok = this.status >= 200 && this.status < 300;
  }
  async text() { return String(this._body); }
  async json() { return JSON.parse(String(this._body)); }
  async arrayBuffer() { return new ArrayBuffer(0); }
  static redirect(url, status) { return new Response('', { status: status || 302, headers: { location: url } }); }
  static json(data, init) {
    init = init || {};
    init.headers = init.headers || {};
    init.headers['content-type'] = 'application/json';
    return new Response(JSON.stringify(data), init);
  }
}

class TextEncoder {
  encode(str) {
    const arr = [];
    for (let i = 0; i < str.length; i++) {
      const c = str.charCodeAt(i);
      if (c < 0x80) arr.push(c);
      else if (c < 0x800) { arr.push(0xc0 | (c >> 6), 0x80 | (c & 0x3f)); }
      else { arr.push(0xe0 | (c >> 12), 0x80 | ((c >> 6) & 0x3f), 0x80 | (c & 0x3f)); }
    }
    return new Uint8Array(arr);
  }
}

class TextDecoder {
  decode(arr) {
    if (!arr) return '';
    const bytes = new Uint8Array(arr);
    let result = '';
    for (let i = 0; i < bytes.length; ) {
      const b = bytes[i];
      if (b < 0x80) { result += String.fromCharCode(b); i++; }
      else if ((b & 0xe0) === 0xc0) { result += String.fromCharCode(((b & 0x1f) << 6) | (bytes[i+1] & 0x3f)); i += 2; }
      else { result += String.fromCharCode(((b & 0x0f) << 12) | ((bytes[i+1] & 0x3f) << 6) | (bytes[i+2] & 0x3f)); i += 3; }
    }
    return result;
  }
}

// Stub crypto
if (typeof globalThis.crypto === 'undefined') {
  globalThis.crypto = {
    getRandomValues(arr) { for (let i = 0; i < arr.length; i++) arr[i] = Math.floor(Math.random() * 256); return arr; },
    randomUUID() {
      const h = '0123456789abcdef';
      let u = '';
      for (let i = 0; i < 36; i++) {
        if (i === 8 || i === 13 || i === 18 || i === 23) u += '-';
        else if (i === 14) u += '4';
        else if (i === 19) u += h[(Math.random() * 4 | 0) + 8];
        else u += h[Math.random() * 16 | 0];
      }
      return u;
    }
  };
}

// Stub console
if (typeof globalThis.console === 'undefined') {
  globalThis.console = { log() {}, warn() {}, error() {}, info() {}, debug() {} };
}

// Stub setTimeout/setInterval (sync no-ops for SSR)
if (typeof globalThis.setTimeout === 'undefined') {
  globalThis.setTimeout = (fn) => { fn(); return 0; };
  globalThis.clearTimeout = () => {};
  globalThis.setInterval = () => 0;
  globalThis.clearInterval = () => {};
}

// Stub fetch
if (typeof globalThis.fetch === 'undefined') {
  globalThis.fetch = async () => new Response('', { status: 503, statusText: 'fetch not available in SSR' });
}

// Expose globals
globalThis.URL = URL;
globalThis.URLSearchParams = URLSearchParams;
globalThis.Headers = Headers;
globalThis.Request = Request;
globalThis.Response = Response;
globalThis.TextEncoder = TextEncoder;
globalThis.TextDecoder = TextDecoder;
