import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260507860000_recruit_real_job_ingest.ts"),
  "utf-8",
);
const recruitManifest = readFileSync(
  resolve(__dirname, "../../../20-actors/recruit/actor-manifest.jsonld"),
  "utf-8",
);
const ingestJobPostingsLexicon = readFileSync(
  resolve(__dirname, "../../../00-contracts/lexicons/ai/gftd/apps/recruit/ingestJobPostings.json"),
  "utf-8",
);
const listJobIngestRunsLexicon = readFileSync(
  resolve(__dirname, "../../../00-contracts/lexicons/ai/gftd/apps/recruit/listJobIngestRuns.json"),
  "utf-8",
);
const atsIngestScript = readFileSync(
  resolve(__dirname, "../../../70-tools/scripts/recruit-ingest-ats-direct.mjs"),
  "utf-8",
);
const ingestRunnerScript = readFileSync(
  resolve(__dirname, "../../../70-tools/scripts/recruit-run-job-ingest.mjs"),
  "utf-8",
);
const ingestWorkerScript = readFileSync(
  resolve(__dirname, "../../../70-tools/scripts/recruit-job-ingest-worker.mjs"),
  "utf-8",
);
const rootPackageJson = readFileSync(
  resolve(__dirname, "../../../package.json"),
  "utf-8",
);
const cronJobManifest = readFileSync(
  resolve(__dirname, "../../../50-infra/k8s/recruit-job-ingester/cronjob.yaml"),
  "utf-8",
);
const deploymentManifest = readFileSync(
  resolve(__dirname, "../../../50-infra/k8s/recruit-job-ingester/deployment.yaml"),
  "utf-8",
);
const cronDockerfile = readFileSync(
  resolve(__dirname, "../../../50-infra/k8s/recruit-job-ingester/Dockerfile"),
  "utf-8",
);
const kustomizationManifest = readFileSync(
  resolve(__dirname, "../../../50-infra/k8s/recruit-job-ingester/kustomization.yaml"),
  "utf-8",
);

describe("Recruit real job ingest", () => {
  it("adds lineage and lookup support for public posting ingest", () => {
    expect(migrationSource).toContain("ADD COLUMN IF NOT EXISTS source_homepage");
    expect(migrationSource).toContain("CREATE TABLE IF NOT EXISTS vertex_recruit_job_ingest_run");
    expect(migrationSource).toContain("idx_vertex_job_posting_source_id");
    expect(migrationSource).toContain("idx_vertex_job_posting_ingested_at");
    expect(migrationSource).toContain("idx_recruit_job_ingest_run_platform_status");
  });

  it("registers an allowlisted ingestJobPostings entrypoint", () => {
    expect(recruitManifest).toContain("ai.gftd.apps.recruit.ingestJobPostings");
    expect(recruitManifest).toContain("ai.gftd.apps.recruit.listJobIngestRuns");
    expect(recruitManifest).toContain("recruitIngestJobPostings");
    expect(recruitManifest).toContain("recruit-job-ingester.recruit-actors.svc.cluster.local");
    expect(recruitManifest).toContain("RecruitJobIngestRun");
    expect(recruitManifest).toContain("boards-api.greenhouse.io");
    expect(recruitManifest).toContain("api.lever.co");
    expect(recruitManifest).toContain("api.ashbyhq.com");
    expect(recruitManifest).not.toContain("RETURN p ORDER BY");
    expect(recruitManifest).not.toContain("RETURN p, e LIMIT");
    expect(ingestJobPostingsLexicon).toContain("public-postings-only");
    expect(ingestJobPostingsLexicon).toContain("greenhouse");
    expect(ingestJobPostingsLexicon).toContain("lever");
    expect(ingestJobPostingsLexicon).toContain("ashby");
    expect(listJobIngestRunsLexicon).toContain("public-postings-only");
  });

  it("keeps the direct ATS ingest idempotent and prohibited-source gated", () => {
    expect(atsIngestScript).toContain("PROHIBITED_HOST_FRAGMENTS");
    expect(atsIngestScript).toContain("assertNotProhibited(appUrl)");
    expect(atsIngestScript).toContain("resolveEmployerAnchor");
    expect(atsIngestScript).toContain("vertex_legal_entity");
    expect(atsIngestScript).toContain("ALLOW_UNANCHORED");
    expect(atsIngestScript).toContain("IGNORE_CHECKPOINT");
    expect(atsIngestScript).toContain("RECRUIT_ENABLE_LIVE_ANCHOR_LOOKUP");
    expect(atsIngestScript).not.toContain("LIKE '%' || lower(name)");
    expect(atsIngestScript).toContain("WHERE NOT EXISTS");
    expect(atsIngestScript).toContain("if (!DRY_RUN)");
    expect(atsIngestScript).toContain("source_homepage");
    expect(atsIngestScript).toContain("source_id");
    expect(atsIngestScript).not.toContain("/Users/");
    expect(atsIngestScript).not.toContain("candidateEmail");
    expect(atsIngestScript).not.toContain("candidatePhone");
  });

  it("provides an operational runner for dry-run, migrate, ingest, and count verification", () => {
    expect(ingestRunnerScript).toContain("recruit-ingest-ats-direct.mjs");
    expect(ingestRunnerScript).toContain("--allow-unanchored");
    expect(ingestRunnerScript).toContain("--ignore-checkpoint");
    expect(ingestRunnerScript).toContain("db:migrate");
    expect(ingestRunnerScript).toContain("DATABASE_URL: process.env.DATABASE_URL ?? RW_CONN");
    expect(ingestRunnerScript).toContain("queryCounts");
    expect(ingestRunnerScript).toContain("persistRun");
    expect(ingestRunnerScript).toContain("vertex_recruit_job_ingest_run");
    expect(ingestRunnerScript).toContain("/tmp/recruit-real-job-ingest-run.json");
    expect(ingestRunnerScript).not.toContain("current_date");
    expect(ingestRunnerScript).not.toContain("/Users/");
    expect(rootPackageJson).toContain("recruit:jobs:ingest");
    expect(rootPackageJson).toContain("recruit:jobs:dry-run");
  });

  it("provides a long-running worker for agent.invoke and health checks", () => {
    expect(ingestWorkerScript).toContain("createServer");
    expect(ingestWorkerScript).toContain("/healthz");
    expect(ingestWorkerScript).toContain("/readyz");
    expect(ingestWorkerScript).toContain("/xrpc/ai.gftd.apps.recruit.ingestJobPostings");
    expect(ingestWorkerScript).toContain("ingest already running");
    expect(ingestWorkerScript).toContain("allowUnanchored");
    expect(ingestWorkerScript).toContain("ignoreCheckpoint");
    expect(deploymentManifest).toContain("kind: Deployment");
    expect(deploymentManifest).toContain("kind: Service");
    expect(deploymentManifest).toContain("readinessProbe");
    expect(deploymentManifest).toContain("livenessProbe");
    expect(deploymentManifest).toContain("INTERNAL_TRUST");
    expect(deploymentManifest).toContain("etzhayyim.com/agent-invoke-command: recruitIngestJobPostings");
  });

  it("defines a scheduled public job ingest CronJob that triggers the worker", () => {
    expect(cronJobManifest).toContain("kind: CronJob");
    expect(cronJobManifest).toContain("concurrencyPolicy: Forbid");
    expect(cronJobManifest).toContain("curlimages/curl");
    expect(cronJobManifest).toContain("recruit-job-ingester.recruit-actors.svc.cluster.local");
    expect(cronJobManifest).toContain("/xrpc/ai.gftd.apps.recruit.ingestJobPostings");
    expect(kustomizationManifest).toContain("deployment.yaml");
    expect(kustomizationManifest).toContain("cronjob.yaml");
    expect(cronDockerfile).toContain("recruit-run-job-ingest.mjs");
    expect(cronDockerfile).toContain("recruit-job-ingest-worker.mjs");
    expect(cronDockerfile).toContain("30-graph/graph-schema");
  });
});
