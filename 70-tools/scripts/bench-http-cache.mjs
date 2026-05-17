#!/usr/bin/env node
import { performance } from "node:perf_hooks";

function parseArgs(argv) {
  const args = { base: "http://127.0.0.1:8787", rounds: 3, paths: [] };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--base" && argv[i + 1]) args.base = argv[++i];
    else if (a === "--rounds" && argv[i + 1]) args.rounds = Math.max(1, Number(argv[++i]) || 3);
    else if (a === "--paths" && argv[i + 1]) args.paths = argv[++i].split(",").map(s => s.trim()).filter(Boolean);
  }
  if (args.paths.length === 0) {
    args.paths = [
      "/.well-known/did.json",
      "/.well-known/oauth-authorization-server",
      "/.well-known/oauth-protected-resource",
      "/oauth/client-metadata.json",
    ];
  }
  return args;
}

async function timedFetch(url, headers = {}) {
  const started = performance.now();
  const res = await fetch(url, { headers });
  const body = await res.arrayBuffer();
  const ended = performance.now();
  return {
    status: res.status,
    ms: +(ended - started).toFixed(1),
    etag: res.headers.get("etag") || "",
    cacheControl: res.headers.get("cache-control") || "",
    contentEncoding: res.headers.get("content-encoding") || "",
    bytes: body.byteLength,
  };
}

function printRow(row) {
  const fields = [
    row.path.padEnd(44),
    String(row.first.status).padStart(3),
    String(row.second.status).padStart(3),
    String(row.avgMs).padStart(7),
    String(row.first.ms).padStart(7),
    String(row.second.ms).padStart(7),
    String(row.first.bytes).padStart(8),
    (row.first.etag ? "yes" : "no").padStart(4),
    (row.first.contentEncoding || "-").padEnd(8),
    row.first.cacheControl || "-",
  ];
  console.log(fields.join("  "));
}

async function run() {
  const { base, rounds, paths } = parseArgs(process.argv);
  const prefix = base.endsWith("/") ? base.slice(0, -1) : base;

  console.log(`base=${prefix} rounds=${rounds}`);
  console.log("path".padEnd(44), "1st", "304", "avg(ms)", "1st(ms)", "304(ms)", "bytes", "etag", "encoding", "cache-control");

  for (const path of paths) {
    const url = `${prefix}${path}`;
    const first = await timedFetch(url, { "Accept-Encoding": "gzip, br" });
    let second;
    if (first.etag) second = await timedFetch(url, { "If-None-Match": first.etag, "Accept-Encoding": "gzip, br" });
    else second = await timedFetch(url, { "Accept-Encoding": "gzip, br" });

    const extra = [];
    for (let i = 0; i < rounds - 2; i++) extra.push(await timedFetch(url, { "Accept-Encoding": "gzip, br" }));
    const samples = [first, second, ...extra];
    const avgMs = +(samples.reduce((s, x) => s + x.ms, 0) / samples.length).toFixed(1);

    printRow({ path, first, second, avgMs });
  }
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
