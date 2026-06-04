#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

export const DEFAULT_POLICY = {
  policyId: "cf.pipelines.limits",
  provider: "cloudflare",
  product: "pipelines",
  version: "2026-03-27",
  sourceDate: "2026-03-27",
  limits: {
    maxStreams: 20,
    maxSinks: 20,
    maxPipelines: 20,
    maxPayloadBytes: 5_000_000,
    maxIngestRateBps: 5_000_000,
  },
};

const I18N = {
  ja: {
    summaryFail: "Seigen 検証失敗",
    summaryPass: "Seigen 検証成功",
    missingConfig: "設定ファイルが存在しません",
    notCloudflarePipelines: "provider/product が cloudflare/pipelines ではありません",
    streamsLimit: "streams が上限を超過",
    sinksLimit: "sinks が上限を超過",
    pipelinesLimit: "pipelines が上限を超過",
    payloadLimit: "payloadBytes が上限を超過",
    ingestRateLimit: "ingestRateBps が上限を超過",
    pipelineSqlImmutable: "pipeline.sqlMutable=true は違反（作成後 SQL 変更不可）",
    sinkImmutable: "sink.mutable=true は違反（作成後 sink 変更不可）",
    r2CatalogJurisdiction: "r2-data-catalog の crossJurisdictionWrite=true は未対応",
    streamSchemaImmutable: "structured stream の schemaMutable=true は違反",
    streamMismatchDrop: "structured stream の expectNoDropOnSchemaMismatch=true は違反（不一致イベントは drop）",
    cueMissing: "cue コマンドが見つからないため CUE 検証をスキップ",
    cueFailed: "CUE 検証に失敗",
  },
  en: {
    summaryFail: "Seigen validation failed",
    summaryPass: "Seigen validation passed",
    missingConfig: "Config file does not exist",
    notCloudflarePipelines: "provider/product must be cloudflare/pipelines",
    streamsLimit: "streams exceeds platform limit",
    sinksLimit: "sinks exceeds platform limit",
    pipelinesLimit: "pipelines exceeds platform limit",
    payloadLimit: "payloadBytes exceeds platform limit",
    ingestRateLimit: "ingestRateBps exceeds platform limit",
    pipelineSqlImmutable: "pipeline.sqlMutable=true violates immutability",
    sinkImmutable: "sink.mutable=true violates sink immutability",
    r2CatalogJurisdiction: "r2-data-catalog with crossJurisdictionWrite=true is unsupported",
    streamSchemaImmutable: "structured stream schemaMutable=true violates immutability",
    streamMismatchDrop: "structured stream expectNoDropOnSchemaMismatch=true violates platform behavior",
    cueMissing: "cue binary not found; skipping CUE validation",
    cueFailed: "CUE validation failed",
  },
};

function t(locale, key) {
  const table = I18N[locale] ?? I18N.en;
  return table[key] ?? I18N.en[key] ?? key;
}

export function parseJsonFile(filePath, locale = "en") {
  const abs = path.resolve(filePath);
  if (!fs.existsSync(abs)) throw new Error(`${t(locale, "missingConfig")}: ${abs}`);
  return JSON.parse(fs.readFileSync(abs, "utf8"));
}

export function validateCloudflarePipelines(input, options = {}) {
  const locale = options.locale === "ja" ? "ja" : "en";
  const p = options.policy ?? DEFAULT_POLICY;
  const diagnostics = [];

  function err(code, message, pathValue, actual, expected) {
    diagnostics.push({
      severity: "error",
      code,
      message,
      path: pathValue,
      actual,
      expected,
    });
  }

  if (input?.provider !== p.provider || input?.product !== p.product) {
    err(
      "SEIGEN_PROVIDER_PRODUCT",
      t(locale, "notCloudflarePipelines"),
      "$.provider|$.product",
      { provider: input?.provider, product: input?.product },
      { provider: p.provider, product: p.product },
    );
  }

  const usage = input?.usage ?? {};

  if ((usage.streams ?? 0) > p.limits.maxStreams) {
    err("SEIGEN_LIMIT_STREAMS", t(locale, "streamsLimit"), "$.usage.streams", usage.streams, `<= ${p.limits.maxStreams}`);
  }
  if ((usage.sinks ?? 0) > p.limits.maxSinks) {
    err("SEIGEN_LIMIT_SINKS", t(locale, "sinksLimit"), "$.usage.sinks", usage.sinks, `<= ${p.limits.maxSinks}`);
  }
  if ((usage.pipelines ?? 0) > p.limits.maxPipelines) {
    err("SEIGEN_LIMIT_PIPELINES", t(locale, "pipelinesLimit"), "$.usage.pipelines", usage.pipelines, `<= ${p.limits.maxPipelines}`);
  }
  if ((usage.payloadBytes ?? 0) > p.limits.maxPayloadBytes) {
    err("SEIGEN_LIMIT_PAYLOAD", t(locale, "payloadLimit"), "$.usage.payloadBytes", usage.payloadBytes, `<= ${p.limits.maxPayloadBytes}`);
  }
  if ((usage.ingestRateBps ?? 0) > p.limits.maxIngestRateBps) {
    err("SEIGEN_LIMIT_INGEST_RATE", t(locale, "ingestRateLimit"), "$.usage.ingestRateBps", usage.ingestRateBps, `<= ${p.limits.maxIngestRateBps}`);
  }

  if (input?.pipeline?.sqlMutable === true) {
    err("SEIGEN_PIPELINE_SQL_IMMUTABLE", t(locale, "pipelineSqlImmutable"), "$.pipeline.sqlMutable", true, false);
  }

  const sinks = Array.isArray(input?.sinks) ? input.sinks : [];
  for (let i = 0; i < sinks.length; i += 1) {
    const sink = sinks[i] ?? {};
    if (sink.mutable === true) {
      err("SEIGEN_SINK_IMMUTABLE", t(locale, "sinkImmutable"), `$.sinks[${i}].mutable`, true, false);
    }
    if (String(sink.type).toLowerCase() === "r2-data-catalog" && sink.crossJurisdictionWrite === true) {
      err(
        "SEIGEN_R2_CATALOG_JURISDICTION",
        t(locale, "r2CatalogJurisdiction"),
        `$.sinks[${i}].crossJurisdictionWrite`,
        true,
        false,
      );
    }
  }

  const streams = Array.isArray(input?.streams) ? input.streams : [];
  for (let i = 0; i < streams.length; i += 1) {
    const stream = streams[i] ?? {};
    if (stream.mode === "structured" && stream.schemaMutable === true) {
      err("SEIGEN_STREAM_SCHEMA_IMMUTABLE", t(locale, "streamSchemaImmutable"), `$.streams[${i}].schemaMutable`, true, false);
    }
    if (stream.mode === "structured" && stream.expectNoDropOnSchemaMismatch === true) {
      err(
        "SEIGEN_STREAM_SCHEMA_MISMATCH_DROP",
        t(locale, "streamMismatchDrop"),
        `$.streams[${i}].expectNoDropOnSchemaMismatch`,
        true,
        false,
      );
    }
  }

  return {
    ok: diagnostics.length === 0,
    locale,
    policy: {
      policyId: p.policyId,
      version: p.version,
      sourceDate: p.sourceDate,
      provider: p.provider,
      product: p.product,
    },
    diagnostics,
    summary: diagnostics.length === 0 ? t(locale, "summaryPass") : t(locale, "summaryFail"),
  };
}

export function tryCueVet(configPath, options = {}) {
  const locale = options.locale === "ja" ? "ja" : "en";
  const cuePath = options.cuePath ?? "projects/etzhayyim-project-seigen-cue/policy/cue/cloudflare-pipelines-limits.cue";
  const whichCue = spawnSync("command -v cue", { encoding: "utf8", shell: true });

  if (whichCue.status !== 0) {
    return { ok: true, skipped: true, message: t(locale, "cueMissing") };
  }

  const result = spawnSync("cue", ["vet", configPath, cuePath], { encoding: "utf8" });
  if (result.status === 0) {
    return { ok: true, skipped: false, message: "cue vet ok" };
  }

  return {
    ok: false,
    skipped: false,
    message: t(locale, "cueFailed"),
    stderr: (result.stderr || "").trim(),
    stdout: (result.stdout || "").trim(),
  };
}

export function buildSqlUpsertPayload(options = {}) {
  const policyId = options.policyId || DEFAULT_POLICY.policyId;
  const version = options.version || DEFAULT_POLICY.version;
  const sourceDate = options.sourceDate || DEFAULT_POLICY.sourceDate;
  const actorDid = options.actorDid || "did:web:seigen.etzhayyim.com";
  const locale = options.locale === "ja" ? "ja" : "en";

  const cuePath = path.resolve("projects/etzhayyim-project-seigen-cue/policy/cue/cloudflare-pipelines-limits.cue");
  const cueSource = fs.readFileSync(cuePath, "utf8");

  const sql = [
    "MERGE (p:SeigenPolicy {policyId: $policyId})",
    "SET p.provider = $provider,",
    "    p.product = $product,",
    "    p.version = $version,",
    "    p.sourceDate = $sourceDate,",
    "    p.cueSource = $cueSource,",
    "    p.updatedAt = datetime(),",
    "    p.actorDid = $actorDid,",
    "    p.locale = $locale",
    "RETURN p.policyId AS policyId, p.version AS version, p.updatedAt AS updatedAt;",
  ].join("\n");

  return {
    sql,
    params: {
      policyId,
      provider: DEFAULT_POLICY.provider,
      product: DEFAULT_POLICY.product,
      version,
      sourceDate,
      cueSource,
      actorDid,
      locale,
    },
  };
}
