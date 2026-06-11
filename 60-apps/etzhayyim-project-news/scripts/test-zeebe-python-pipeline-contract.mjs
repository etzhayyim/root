#!/usr/bin/env node
import { readFileSync } from "node:fs";

const checks = [];

function read(path) {
  return readFileSync(path, "utf8");
}

function ok(name, condition, detail = "") {
  checks.push({ name, ok: Boolean(condition), detail });
}

function includesAll(name, text, needles) {
  for (const needle of needles) {
    ok(`${name}: ${needle}`, text.includes(needle), `missing ${needle}`);
  }
}

function excludesAll(name, text, needles) {
  for (const needle of needles) {
    ok(`${name}: no ${needle}`, !text.includes(needle), `unexpected ${needle}`);
  }
}

function json(path) {
  return JSON.parse(read(path));
}

const appTs = read("60-apps/etzhayyim-project-news/appview/news-core-component/src/app.ts");
const workerPy = read("50-infra/k8s/news-social-arbitrage-actor/worker.py");
const manifest = json("70-tools/config/bpmn-coverage-manifest.json");
const deploymentYaml = read("50-infra/k8s/news-social-arbitrage-actor/deployment.yaml");
const articleJson = json(
  "60-apps/etzhayyim-project-news/resources/content/ja/intel/social-arbitrage/news-social-arbitrage-actor-2026.jsonld",
);
const rssBpmn = read("etzhayyim-root/00-contracts/bpmn/com/etzhayyim/news/rssIngest.bpmn");
const socialBpmn = read("etzhayyim-root/00-contracts/bpmn/com/etzhayyim/news/socialArbitrageIntel.bpmn");

includesAll("TS edge commands", appTs, [
  'nsid("com.etzhayyim.apps.news.commitArticle")',
  'processId: "news_rss_ingest"',
  'movedToZeebe: true',
  'pipeline: "zeebe-python-rss"',
]);

excludesAll("TS edge must not own heavy RSS pipeline", appTs, [
  "async function ingestSource",
  "async function translateText",
  "function parseFeed",
  "function qualityScore",
  "const TIER1_LANGS",
  "fetch(source.feedUrl",
]);

includesAll("Python worker tasks", workerPy, [
  '@worker.task(task_type="news.rss.resolveSources")',
  '@worker.task(task_type="news.rss.ingestSource")',
  '@worker.task(task_type="news.socialArbitrage.discover")',
  '@worker.task(task_type="news.socialArbitrage.draft")',
  "NEWS_COMMIT_ARTICLE_URL",
  "build_translations",
  "commit_article",
  "social_post_quality",
  "SOCIAL_POST_FORBIDDEN",
  "SOCIAL_POST_MIN_QUALITY",
  "draft_rss_social_post",
]);

includesAll("Resident Zeebe worker deployment", deploymentYaml, [
  "kind: Deployment",
  "replicas: 1",
  "restartPolicy: Always",
  "rollingUpdate:",
  "maxUnavailable: 0",
  "livenessProbe:",
  "readinessProbe:",
]);

excludesAll("Resident Zeebe worker is not scheduled batch", deploymentYaml, [
  "kind: CronJob",
  "kind: Job",
]);

includesAll("RSS BPMN contract", rssBpmn, [
  'id="news_rss_ingest"',
  'type="news.rss.resolveSources"',
  'type="news.rss.ingestSource"',
  'type="generic.audit.emit"',
]);

includesAll("Social arbitrage BPMN contract", socialBpmn, [
  'id="news_social_arbitrage_intel"',
  'type="news.socialArbitrage.discover"',
  'type="news.socialArbitrage.draft"',
  'type="xrpc.com.etzhayyim.apps.news.analyzeIntel"',
  'type="generic.audit.emit"',
]);

for (const path of [
  "00-contracts/lexicons/com/etzhayyim/apps/news/commitArticle.json",
  "00-contracts/lexicons/com/etzhayyim/apps/news/rssIngest.json",
  "00-contracts/lexicons/com/etzhayyim/apps/news/socialArbitrageIntel.json",
  "00-contracts/lexicons/com/etzhayyim/apps/news/analyzeIntel.json",
]) {
  const doc = json(path);
  ok(`lexicon parses: ${path}`, doc.lexicon === 1 && typeof doc.id === "string");
}

const commitArticle = json("00-contracts/lexicons/com/etzhayyim/apps/news/commitArticle.json");
const commitProps = commitArticle.defs.main.input.schema.properties;
includesAll("commitArticle lexicon props", JSON.stringify(commitProps), [
  "sourceId",
  "translations",
  "socialPost",
  "publish",
]);

const analyzeIntel = json("00-contracts/lexicons/com/etzhayyim/apps/news/analyzeIntel.json");
const analyzeProps = analyzeIntel.defs.main.input.schema.properties;
includesAll("analyzeIntel Python-scored props", JSON.stringify(analyzeProps), [
  "facts",
  "findings",
  "socialArbitrageScore",
  "credibility",
  "priority",
  "bridgeScores",
]);

function socialPostQuality(post, url) {
  const issues = [];
  const compact = post.replace(/\s+/g, " ").trim();
  const lower = compact.toLowerCase();
  if (compact.length < 80) issues.push("too-short");
  if (compact.length > 300) issues.push("too-long");
  if (url && !post.includes(url)) issues.push("missing-url");
  if (!post.includes("Bridge:") && !post.includes("Action:")) {
    issues.push("missing-bridge-or-action");
  }
  if (!/(access|apply|bridge|capacity|community|deadline|eligibility|rights|services)/i.test(post)) {
    issues.push("missing-actionable-public-value");
  }
  if (["shocking", "you won't believe", "must read", "breaking!!!", "衝撃", "絶対見て"].some((term) => lower.includes(term))) {
    issues.push("clickbait");
  }
  return { score: 1 - Math.min(0.9, issues.length * 0.22), issues };
}

const sampleSocialPost =
  "Public signal: City open-data shows unused evening community rooms near high-loneliness districts. Bridge: connect isolated people to trusted community capacity. Action: check eligibility and contact route.\n\nhttps://example.gov/open-data";
const sampleQuality = socialPostQuality(sampleSocialPost, "https://example.gov/open-data");
ok("sample socialpost quality passes", sampleQuality.score >= 0.75 && sampleQuality.issues.length === 0, sampleQuality.issues.join(","));

const articlePost = articleJson.socialPost;
ok("article socialPost exists", typeof articlePost === "string" && articlePost.length > 0);
ok("article socialPost includes URL", articlePost.includes(articleJson.url));
ok("article socialPost stays in post budget", articlePost.length <= 300);

const bindings = manifest.bindings.map((binding) => `${binding.bpmnProcessId}:${binding.nsid}`);
includesAll("BPMN coverage manifest", bindings.join("\n"), [
  "news_rss_ingest:com.etzhayyim.apps.news.rssIngest",
  "news_social_arbitrage_intel:com.etzhayyim.apps.news.socialArbitrageIntel",
]);

const failed = checks.filter((check) => !check.ok);
for (const check of checks) {
  const mark = check.ok ? "ok" : "not ok";
  console.log(`${mark} - ${check.name}${check.ok ? "" : ` (${check.detail})`}`);
}

if (failed.length > 0) {
  console.error(`\n${failed.length}/${checks.length} integration contract checks failed.`);
  process.exit(1);
}

console.log(`\n${checks.length}/${checks.length} integration contract checks passed.`);
