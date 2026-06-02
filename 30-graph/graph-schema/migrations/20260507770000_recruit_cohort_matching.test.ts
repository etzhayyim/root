import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260507770000_recruit_cohort_matching.ts"),
  "utf-8",
);
const recruitManifest = readFileSync(
  resolve(__dirname, "../../../20-actors/recruit/actor-manifest.jsonld"),
  "utf-8",
);
const recommendCohortsLexicon = readFileSync(
  resolve(__dirname, "../../../00-contracts/lexicons/com/etzhayyim/apps/recruit/recommendCohorts.json"),
  "utf-8",
);
const matchStatsLexicon = readFileSync(
  resolve(__dirname, "../../../00-contracts/lexicons/com/etzhayyim/apps/recruit/matchStats.json"),
  "utf-8",
);
const proposeCohortMatchLexicon = readFileSync(
  resolve(__dirname, "../../../00-contracts/lexicons/com/etzhayyim/apps/recruit/proposeCohortMatch.json"),
  "utf-8",
);
const listMatchProposalsLexicon = readFileSync(
  resolve(__dirname, "../../../00-contracts/lexicons/com/etzhayyim/apps/recruit/listMatchProposals.json"),
  "utf-8",
);
const getMatchProposalLexicon = readFileSync(
  resolve(__dirname, "../../../00-contracts/lexicons/com/etzhayyim/apps/recruit/getMatchProposal.json"),
  "utf-8",
);
const decideMatchProposalLexicon = readFileSync(
  resolve(__dirname, "../../../00-contracts/lexicons/com/etzhayyim/apps/recruit/decideMatchProposal.json"),
  "utf-8",
);
const listMatchDecisionEventsLexicon = readFileSync(
  resolve(__dirname, "../../../00-contracts/lexicons/com/etzhayyim/apps/recruit/listMatchDecisionEvents.json"),
  "utf-8",
);

describe("Recruit cohort matching migration", () => {
  it("creates a proposal table and cohort candidate materialized view", () => {
    expect(migrationSource).toContain("CREATE TABLE IF NOT EXISTS vertex_recruit_match_proposal");
    expect(migrationSource).toContain("CREATE TABLE IF NOT EXISTS vertex_recruit_match_decision_event");
    expect(migrationSource).toContain("CREATE TABLE IF NOT EXISTS edge_recruit_match_for_posting");
    expect(migrationSource).toContain("CREATE TABLE IF NOT EXISTS edge_recruit_match_for_cohort");
    expect(migrationSource).toContain("CREATE MATERIALIZED VIEW IF NOT EXISTS mv_recruit_cohort_match_candidate");
    expect(migrationSource).toContain("decision_reason");
    expect(migrationSource).toContain("idx_recruit_match_proposal_posting");
    expect(migrationSource).toContain("idx_recruit_match_decision_event_proposal");
    expect(migrationSource).toContain("idx_edge_recruit_match_for_posting");
    expect(migrationSource).toContain("idx_edge_recruit_match_for_cohort");
    expect(migrationSource).toContain("idx_mv_recruit_cohort_match_filter");
  });

  it("joins only public postings, aggregate cohorts, and aggregate demand forecasts", () => {
    expect(migrationSource).toContain("FROM vertex_job_posting p");
    expect(migrationSource).toContain("JOIN vertex_talent_cohort c");
    expect(migrationSource).toContain("LEFT JOIN vertex_demand_forecast d");
    expect(migrationSource).not.toContain("TalentProfile");
    expect(migrationSource).not.toContain("identifying");
    expect(migrationSource).not.toContain("email");
    expect(migrationSource).not.toContain("phone");
  });

  it("registers read, write, and list NSIDs on the recruit actor", () => {
    expect(recruitManifest).toContain("com.etzhayyim.apps.recruit.recommendCohorts");
    expect(recruitManifest).toContain("com.etzhayyim.apps.recruit.matchStats");
    expect(recruitManifest).toContain("com.etzhayyim.apps.recruit.proposeCohortMatch");
    expect(recruitManifest).toContain("com.etzhayyim.apps.recruit.listMatchProposals");
    expect(recruitManifest).toContain("com.etzhayyim.apps.recruit.getMatchProposal");
    expect(recruitManifest).toContain("com.etzhayyim.apps.recruit.decideMatchProposal");
    expect(recruitManifest).toContain("com.etzhayyim.apps.recruit.listMatchDecisionEvents");
    expect(recruitManifest).toContain("RecruitCohortMatchCandidate");
    expect(recruitManifest).toContain("RecruitMatchProposal");
    expect(recruitManifest).toContain("RecruitMatchDecisionEvent");
    expect(recruitManifest).toContain("count(m) AS candidateCount");
    expect(recruitManifest).toContain("count(e) AS decisionEventCount");
    expect(recruitManifest).toContain("MERGE (p)-[:FOR_POSTING]->(jp)");
    expect(recruitManifest).toContain("MERGE (p)-[:FOR_COHORT]->(tc)");
    expect(recruitManifest).toContain("MATCH (p:RecruitMatchProposal {proposalId: $proposalId})");
    expect(recruitManifest).toContain("e.privacyMode = 'cohort-first'");
    expect(recruitManifest).toContain("p.decisionReason AS decisionReason");
  });

  it("keeps lexicons cohort-first and PII-free", () => {
    for (const source of [
      recommendCohortsLexicon,
      matchStatsLexicon,
      proposeCohortMatchLexicon,
      listMatchProposalsLexicon,
      getMatchProposalLexicon,
      decideMatchProposalLexicon,
      listMatchDecisionEventsLexicon,
    ]) {
      expect(source).toContain("cohort-first");
      expect(source).not.toContain("candidateEmail");
      expect(source).not.toContain("candidatePhone");
      expect(source).not.toContain("fullName");
      expect(source).not.toContain("dateOfBirth");
    }
  });
});
