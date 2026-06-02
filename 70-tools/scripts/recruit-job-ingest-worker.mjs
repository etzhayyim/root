#!/usr/bin/env node
/**
 * Long-running Recruit job ingest worker.
 *
 * Exposes an HTTP XRPC-compatible endpoint for agent.invoke and CronJob
 * triggers. The worker serializes ingest runs so public ATS fetches and
 * RisingWave writes do not overlap.
 */
import http from "node:http";
import { spawn } from "node:child_process";

const PORT = Number(process.env.PORT ?? "8080");
const INTERNAL_TRUST = process.env.INTERNAL_TRUST ?? "";
const INGEST_NSID = "com.etzhayyim.apps.recruit.ingestJobPostings";
const XRPC_PATH = "/xrpc/com.etzhayyim.apps.recruit.ingestJobPostings";
const MAX_BODY_BYTES = 64 * 1024;

let currentRun = null;
let latestReport = null;

function sendJson(res, status, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(body),
  });
  res.end(body);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on("data", (chunk) => {
      size += chunk.length;
      if (size > MAX_BODY_BYTES) {
        reject(new Error("request body too large"));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", () => {
      const raw = Buffer.concat(chunks).toString("utf8");
      if (!raw) {
        resolve({});
        return;
      }
      try {
        resolve(JSON.parse(raw));
      } catch {
        reject(new Error("invalid JSON body"));
      }
    });
    req.on("error", reject);
  });
}

function bool(value) {
  return value === true || value === "true";
}

function ingestArgs(input) {
  const platform = input.platform ?? "lever";
  const limit = String(input.limit ?? 100);
  const batchSize = String(input.batchSize ?? input.batch_size ?? 50);
  const args = [
    "70-tools/scripts/recruit-run-job-ingest.mjs",
    "--platform",
    platform,
    "--limit",
    limit,
    "--batch-size",
    batchSize,
  ];
  if (bool(input.dryRun)) args.push("--dry-run");
  if (bool(input.skipMigrate)) args.push("--skip-migrate");
  if (bool(input.allowUnanchored)) args.push("--allow-unanchored");
  if (bool(input.ignoreCheckpoint)) args.push("--ignore-checkpoint");
  return args;
}

function runIngest(input) {
  if (currentRun) return currentRun;
  const startedAt = new Date().toISOString();
  currentRun = new Promise((resolve) => {
    const child = spawn("node", ingestArgs(input), {
      stdio: ["ignore", "pipe", "pipe"],
      env: process.env,
    });
    const stdout = [];
    const stderr = [];
    child.stdout.on("data", (chunk) => {
      process.stdout.write(chunk);
      stdout.push(chunk.toString("utf8"));
    });
    child.stderr.on("data", (chunk) => {
      process.stderr.write(chunk);
      stderr.push(chunk.toString("utf8"));
    });
    child.on("exit", (code) => {
      const finishedAt = new Date().toISOString();
      latestReport = {
        status: code === 0 ? "succeeded" : "failed",
        exitCode: code,
        startedAt,
        finishedAt,
        durationMs: Date.parse(finishedAt) - Date.parse(startedAt),
        stdout: stdout.join("").slice(-4000),
        stderr: stderr.join("").slice(-4000),
      };
      currentRun = null;
      resolve(latestReport);
    });
    child.on("error", (error) => {
      const finishedAt = new Date().toISOString();
      latestReport = {
        status: "failed",
        exitCode: 1,
        startedAt,
        finishedAt,
        durationMs: Date.parse(finishedAt) - Date.parse(startedAt),
        error: error.message,
      };
      currentRun = null;
      resolve(latestReport);
    });
  });
  return currentRun;
}

function authorized(req) {
  if (!INTERNAL_TRUST) return true;
  return req.headers["x-internal-trust"] === INTERNAL_TRUST;
}

async function handle(req, res) {
  const url = new URL(req.url ?? "/", `http://${req.headers.host ?? "localhost"}`);
  if (req.method === "GET" && url.pathname === "/healthz") {
    sendJson(res, 200, { ok: true });
    return;
  }
  if (req.method === "GET" && url.pathname === "/readyz") {
    sendJson(res, 200, { ok: true, busy: Boolean(currentRun), latestReport });
    return;
  }
  if (req.method === "POST" && url.pathname === XRPC_PATH) {
    if (!authorized(req)) {
      sendJson(res, 401, { error: "unauthorized" });
      return;
    }
    if (currentRun) {
      sendJson(res, 409, { error: "ingest already running" });
      return;
    }
    try {
      const input = await readBody(req);
      const report = await runIngest(input);
      sendJson(res, report.status === "succeeded" ? 200 : 500, {
        ...report,
        privacyMode: "public-postings-only",
      });
    } catch (error) {
      sendJson(res, 400, { error: error.message });
    }
    return;
  }
  sendJson(res, 404, { error: "not found" });
}

const server = http.createServer((req, res) => {
  handle(req, res).catch((error) => {
    sendJson(res, 500, { error: error.message });
  });
});

server.listen(PORT, () => {
  console.log(`[recruit-worker] listening on :${PORT}`);
});
