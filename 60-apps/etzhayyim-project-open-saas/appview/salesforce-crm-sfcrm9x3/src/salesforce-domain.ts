// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 etzhayyim Japan株式会社 / etzhayyim. All rights reserved.
// Licensed under the Apache License, Version 2.0 — see LICENSE at repo root.

export type OpportunityStage =
  | "prospecting"
  | "qualification"
  | "needs-analysis"
  | "proposal"
  | "negotiation"
  | "closed-won"
  | "closed-lost";

export type ForecastCategory = "pipeline" | "best-case" | "commit" | "closed" | "omitted";

export type LeadStatus = "new" | "contacted" | "qualifying" | "qualified" | "unqualified" | "converted";

export type CaseStatus =
  | "new"
  | "in-progress"
  | "waiting-on-customer"
  | "waiting-on-internal"
  | "resolved"
  | "closed";

export type Account = {
  uri: string;
  tenantDid: string;
  ownerDid: string;
  name: string;
  type: "prospect" | "customer-direct" | "customer-channel" | "partner" | "other";
  industry?: string;
  region?: string;
  annualRevenueJpyBand?: "u100m" | "u1b" | "u10b" | "u100b" | "o100b";
  employeeCountBand?: "1-10" | "11-50" | "51-200" | "201-1000" | "1001-5000" | "5000+";
  createdAt: string;
};

export type Contact = {
  uri: string;
  tenantDid: string;
  accountDid: string;
  emailHash: string;
  displayLabel?: string;
  role?: string;
  title?: string;
  optOutStatus: "none" | "email" | "phone" | "all";
  createdAt: string;
};

export type Lead = {
  uri: string;
  tenantDid: string;
  ownerDid?: string;
  companyLabel?: string;
  displayLabel?: string;
  emailHash: string;
  source: "web-form" | "inbound-call" | "referral" | "event" | "partner" | "outbound" | "other";
  status: LeadStatus;
  rating?: "hot" | "warm" | "cold";
  scoreBand?: "0-20" | "21-40" | "41-60" | "61-80" | "81-100";
  convertedAt?: string;
  convertedAccountDid?: string;
  convertedContactDid?: string;
  convertedOpportunityDid?: string;
  createdAt: string;
};

export type Opportunity = {
  uri: string;
  tenantDid: string;
  accountDid: string;
  primaryContactDid?: string;
  ownerDid?: string;
  name: string;
  stage: OpportunityStage;
  probability: number;
  amountJpy: number;
  amountBand?: "u1m" | "u10m" | "u100m" | "u1b" | "o1b";
  forecastCategory: ForecastCategory;
  closeDate: string;
  createdAt: string;
  lastStageChangeAt: string;
};

export type Case = {
  uri: string;
  tenantDid: string;
  accountDid: string;
  contactDid?: string;
  ownerDid?: string;
  subject: string;
  status: CaseStatus;
  priority: "low" | "medium" | "high" | "critical";
  origin: "email" | "phone" | "web" | "chat" | "api" | "social";
  caseType: "question" | "bug" | "feature-request" | "incident" | "billing" | "other";
  createdAt: string;
};

export type Activity = {
  uri: string;
  tenantDid: string;
  accountDid?: string;
  contactDid?: string;
  leadDid?: string;
  opportunityDid?: string;
  caseDid?: string;
  actorDid?: string;
  kind:
    | "call"
    | "email"
    | "meeting"
    | "task"
    | "note"
    | "stage-change"
    | "status-change"
    | "conversion";
  subject: string;
  summary?: string;
  source:
    | "derived-stage-change"
    | "derived-status-change"
    | "derived-convo"
    | "derived-conversion"
    | "manual-ui"
    | "import";
  occurredAt: string;
};

const STAGE_PROBABILITY: Record<OpportunityStage, number> = {
  prospecting: 10,
  qualification: 20,
  "needs-analysis": 40,
  proposal: 60,
  negotiation: 80,
  "closed-won": 100,
  "closed-lost": 0,
};

const STAGE_FORECAST: Record<OpportunityStage, ForecastCategory> = {
  prospecting: "pipeline",
  qualification: "pipeline",
  "needs-analysis": "best-case",
  proposal: "best-case",
  negotiation: "commit",
  "closed-won": "closed",
  "closed-lost": "omitted",
};

function iso(offsetHours = 0): string {
  return new Date(Date.now() + offsetHours * 3600 * 1000).toISOString();
}

function amountBandOf(amountJpy: number): Opportunity["amountBand"] {
  if (amountJpy < 1_000_000) return "u1m";
  if (amountJpy < 10_000_000) return "u10m";
  if (amountJpy < 100_000_000) return "u100m";
  if (amountJpy < 1_000_000_000) return "u1b";
  return "o1b";
}

type State = {
  accounts: Account[];
  contacts: Contact[];
  leads: Lead[];
  opportunities: Opportunity[];
  cases: Case[];
  activities: Activity[];
};

const TENANT_DID = "did:web:demo-opensaas.etzhayyim.com";
const OWNER_DID = "did:web:demo-opensaas.etzhayyim.com:seat:ae-01";

function seed(): State {
  const acctA: Account = {
    uri: "at://demo-opensaas.etzhayyim.com/com.etzhayyim.apps.opensaas.salesforce.account/acct-acme",
    tenantDid: TENANT_DID,
    ownerDid: OWNER_DID,
    name: "Acme Robotics K.K.",
    type: "prospect",
    industry: "C-28",
    region: "JPN",
    annualRevenueJpyBand: "u10b",
    employeeCountBand: "201-1000",
    createdAt: iso(-72),
  };
  const contactA: Contact = {
    uri: "at://demo-opensaas.etzhayyim.com/com.etzhayyim.apps.opensaas.salesforce.contact/ctc-acme-cto",
    tenantDid: TENANT_DID,
    accountDid: acctA.uri,
    emailHash: "sha256:demo-cto-hash",
    displayLabel: "CTO, Acme Robotics",
    role: "technical-evaluator",
    title: "Chief Technology Officer",
    optOutStatus: "none",
    createdAt: iso(-72),
  };
  const oppA: Opportunity = {
    uri: "at://demo-opensaas.etzhayyim.com/com.etzhayyim.apps.opensaas.salesforce.opportunity/opp-acme-q2",
    tenantDid: TENANT_DID,
    accountDid: acctA.uri,
    primaryContactDid: contactA.uri,
    ownerDid: OWNER_DID,
    name: "Acme FY26 Q2 Platform Expansion",
    stage: "proposal",
    probability: STAGE_PROBABILITY.proposal,
    amountJpy: 24_000_000,
    amountBand: amountBandOf(24_000_000),
    forecastCategory: STAGE_FORECAST.proposal,
    closeDate: iso(24 * 30),
    createdAt: iso(-30 * 24),
    lastStageChangeAt: iso(-3 * 24),
  };
  const leadA: Lead = {
    uri: "at://demo-opensaas.etzhayyim.com/com.etzhayyim.apps.opensaas.salesforce.lead/lead-inbound-001",
    tenantDid: TENANT_DID,
    ownerDid: OWNER_DID,
    companyLabel: "Nihon MegaMaker Inc.",
    displayLabel: "VP Ops, Nihon MegaMaker",
    emailHash: "sha256:demo-lead-hash",
    source: "web-form",
    status: "qualifying",
    rating: "warm",
    scoreBand: "61-80",
    createdAt: iso(-5 * 24),
  };
  const caseA: Case = {
    uri: "at://demo-opensaas.etzhayyim.com/com.etzhayyim.apps.opensaas.salesforce.case/case-acme-0001",
    tenantDid: TENANT_DID,
    accountDid: acctA.uri,
    contactDid: contactA.uri,
    ownerDid: OWNER_DID,
    subject: "SSO SAML metadata rotation",
    status: "in-progress",
    priority: "high",
    origin: "email",
    caseType: "incident",
    createdAt: iso(-6),
  };
  return {
    accounts: [acctA],
    contacts: [contactA],
    leads: [leadA],
    opportunities: [oppA],
    cases: [caseA],
    activities: [],
  };
}

let state: State = seed();

export function getBlueprint() {
  return {
    project: "etzhayyim-project-open-saas",
    app: "salesforce-crm-sfcrm9x3",
    tenancy: {
      model: "actor-did-per-tenant",
      tenantDidFormat: "did:web:<slug>.opensaas.etzhayyim.com",
      seatDidFormat: "did:web:<slug>.opensaas.etzhayyim.com:seat:<role>-<nn>",
    },
    lexicons: [
      "com.etzhayyim.apps.opensaas.salesforce.account",
      "com.etzhayyim.apps.opensaas.salesforce.contact",
      "com.etzhayyim.apps.opensaas.salesforce.lead",
      "com.etzhayyim.apps.opensaas.salesforce.opportunity",
      "com.etzhayyim.apps.opensaas.salesforce.case",
      "com.etzhayyim.apps.opensaas.salesforce.activity",
      "com.etzhayyim.apps.opensaas.salesforce.createLead",
      "com.etzhayyim.apps.opensaas.salesforce.convertLead",
      "com.etzhayyim.apps.opensaas.salesforce.listPipeline",
    ],
    piiTier: {
      tier1Public: ["emailHash", "phoneHash", "amountBand", "displayLabel"],
      tier3Preferences: ["rawEmail", "rawPhone", "fullName", "exactAnnualRevenue"],
      fieldEncrypted: ["case.description", "activity.summary"],
    },
    deriveRules: [
      "opportunity.stage change → activity(kind=stage-change)",
      "case.status change → activity(kind=status-change)",
      "lead.status→converted → activity(kind=conversion)",
    ],
  };
}

export function listAccounts(): Account[] {
  return state.accounts;
}

export function listContacts(accountDid?: string): Contact[] {
  return accountDid ? state.contacts.filter((c) => c.accountDid === accountDid) : state.contacts;
}

export function listLeads(status?: LeadStatus): Lead[] {
  return status ? state.leads.filter((l) => l.status === status) : state.leads;
}

export function listCases(status?: CaseStatus): Case[] {
  return status ? state.cases.filter((c) => c.status === status) : state.cases;
}

export function listActivities(limit = 50): Activity[] {
  return state.activities.slice(-limit).reverse();
}

export type CreateLeadInput = {
  tenantDid: string;
  ownerDid?: string;
  companyLabel?: string;
  displayLabel?: string;
  emailHash: string;
  phoneHash?: string;
  source: Lead["source"];
  rating?: Lead["rating"];
  scoreBand?: Lead["scoreBand"];
};

export function createLead(input: CreateLeadInput): Lead {
  if (!input.tenantDid || !input.emailHash || !input.source) {
    throw new Error("tenantDid, emailHash, source are required");
  }
  if (!input.emailHash.startsWith("sha256:")) {
    throw new Error("emailHash must be 'sha256:<hex>' — raw PII is rejected");
  }
  const rkey = `lead-${Math.random().toString(36).slice(2, 10)}`;
  const lead: Lead = {
    uri: `at://${input.tenantDid.replace("did:web:", "")}/com.etzhayyim.apps.opensaas.salesforce.lead/${rkey}`,
    tenantDid: input.tenantDid,
    ownerDid: input.ownerDid,
    companyLabel: input.companyLabel,
    displayLabel: input.displayLabel,
    emailHash: input.emailHash,
    source: input.source,
    status: "new",
    rating: input.rating,
    scoreBand: input.scoreBand,
    createdAt: iso(),
  };
  state.leads.push(lead);
  return lead;
}

export type ConvertLeadInput = {
  leadUri: string;
  accountName?: string;
  existingAccountDid?: string;
  createOpportunity?: boolean;
  opportunityName?: string;
  opportunityAmountJpy?: number;
  opportunityCloseDate?: string;
  opportunityStage?: Exclude<OpportunityStage, "closed-won" | "closed-lost">;
};

export function convertLead(input: ConvertLeadInput): {
  account: Account;
  contact: Contact;
  opportunity?: Opportunity;
  lead: Lead;
  activity: Activity;
} {
  const lead = state.leads.find((l) => l.uri === input.leadUri);
  if (!lead) throw new Error("LeadNotFound");
  if (lead.status === "converted") throw new Error("LeadAlreadyConverted");

  const account: Account =
    (input.existingAccountDid && state.accounts.find((a) => a.uri === input.existingAccountDid)) || {
      uri: `at://${lead.tenantDid.replace("did:web:", "")}/com.etzhayyim.apps.opensaas.salesforce.account/${`acct-${Math.random().toString(36).slice(2, 10)}`}`,
      tenantDid: lead.tenantDid,
      ownerDid: lead.ownerDid || OWNER_DID,
      name: input.accountName || lead.companyLabel || "Unnamed Account",
      type: "customer-direct",
      createdAt: iso(),
    };
  if (!state.accounts.some((a) => a.uri === account.uri)) state.accounts.push(account);

  const contact: Contact = {
    uri: `at://${lead.tenantDid.replace("did:web:", "")}/com.etzhayyim.apps.opensaas.salesforce.contact/${`ctc-${Math.random().toString(36).slice(2, 10)}`}`,
    tenantDid: lead.tenantDid,
    accountDid: account.uri,
    emailHash: lead.emailHash,
    displayLabel: lead.displayLabel,
    optOutStatus: "none",
    createdAt: iso(),
  };
  state.contacts.push(contact);

  let opportunity: Opportunity | undefined;
  if (input.createOpportunity !== false) {
    const stage = input.opportunityStage || "qualification";
    const amountJpy = input.opportunityAmountJpy || 0;
    opportunity = {
      uri: `at://${lead.tenantDid.replace("did:web:", "")}/com.etzhayyim.apps.opensaas.salesforce.opportunity/${`opp-${Math.random().toString(36).slice(2, 10)}`}`,
      tenantDid: lead.tenantDid,
      accountDid: account.uri,
      primaryContactDid: contact.uri,
      ownerDid: lead.ownerDid,
      name: input.opportunityName || `${account.name} — new deal`,
      stage,
      probability: STAGE_PROBABILITY[stage],
      amountJpy,
      amountBand: amountBandOf(amountJpy),
      forecastCategory: STAGE_FORECAST[stage],
      closeDate: input.opportunityCloseDate || iso(24 * 60),
      createdAt: iso(),
      lastStageChangeAt: iso(),
    };
    state.opportunities.push(opportunity);
  }

  lead.status = "converted";
  lead.convertedAt = iso();
  lead.convertedAccountDid = account.uri;
  lead.convertedContactDid = contact.uri;
  lead.convertedOpportunityDid = opportunity?.uri;

  const activity: Activity = {
    uri: `at://${lead.tenantDid.replace("did:web:", "")}/com.etzhayyim.apps.opensaas.salesforce.activity/${`act-${Math.random().toString(36).slice(2, 10)}`}`,
    tenantDid: lead.tenantDid,
    accountDid: account.uri,
    contactDid: contact.uri,
    leadDid: lead.uri,
    opportunityDid: opportunity?.uri,
    actorDid: lead.ownerDid,
    kind: "conversion",
    subject: "Lead converted",
    source: "derived-conversion",
    occurredAt: iso(),
  };
  state.activities.push(activity);

  return { account, contact, opportunity, lead, activity };
}

export type AdvanceStageInput = { opportunityUri: string; stage: OpportunityStage; actorDid?: string };

export function advanceStage(input: AdvanceStageInput): { opportunity: Opportunity; activity: Activity } {
  const opp = state.opportunities.find((o) => o.uri === input.opportunityUri);
  if (!opp) throw new Error("OpportunityNotFound");
  const prevStage = opp.stage;
  opp.stage = input.stage;
  opp.probability = STAGE_PROBABILITY[input.stage];
  opp.forecastCategory = STAGE_FORECAST[input.stage];
  opp.lastStageChangeAt = iso();
  const activity: Activity = {
    uri: `at://${opp.tenantDid.replace("did:web:", "")}/com.etzhayyim.apps.opensaas.salesforce.activity/${`act-${Math.random().toString(36).slice(2, 10)}`}`,
    tenantDid: opp.tenantDid,
    accountDid: opp.accountDid,
    opportunityDid: opp.uri,
    actorDid: input.actorDid,
    kind: "stage-change",
    subject: `Stage: ${prevStage} → ${input.stage}`,
    source: "derived-stage-change",
    occurredAt: iso(),
  };
  state.activities.push(activity);
  return { opportunity: opp, activity };
}

export type PipelineFilter = {
  tenantDid: string;
  ownerDid?: string;
  stage?: OpportunityStage;
  forecastCategory?: ForecastCategory;
  limit?: number;
  offset?: number;
};

export function listPipeline(filter: PipelineFilter) {
  const limit = filter.limit ?? 50;
  const offset = filter.offset ?? 0;
  const filtered = state.opportunities.filter(
    (o) =>
      o.tenantDid === filter.tenantDid &&
      (!filter.ownerDid || o.ownerDid === filter.ownerDid) &&
      (!filter.stage || o.stage === filter.stage) &&
      (!filter.forecastCategory || o.forecastCategory === filter.forecastCategory),
  );
  const page = filtered.slice(offset, offset + limit);
  const stageRollup = (Object.keys(STAGE_PROBABILITY) as OpportunityStage[]).map((stage) => {
    const rows = filtered.filter((o) => o.stage === stage);
    const amountJpy = rows.reduce((s, o) => s + o.amountJpy, 0);
    const weightedAmountJpy = rows.reduce((s, o) => s + Math.round((o.amountJpy * o.probability) / 100), 0);
    return { stage, count: rows.length, amountJpy, weightedAmountJpy };
  });
  return {
    items: page.map((o) => ({
      uri: o.uri,
      accountDid: o.accountDid,
      accountName: state.accounts.find((a) => a.uri === o.accountDid)?.name,
      ownerDid: o.ownerDid,
      name: o.name,
      stage: o.stage,
      probability: o.probability,
      amountJpy: o.amountJpy,
      amountBand: o.amountBand,
      forecastCategory: o.forecastCategory,
      closeDate: o.closeDate,
      lastStageChangeAt: o.lastStageChangeAt,
    })),
    total: filtered.length,
    offset,
    limit,
    stageRollup,
  };
}

export function getOverview() {
  return {
    tenantDid: TENANT_DID,
    counts: {
      accounts: state.accounts.length,
      contacts: state.contacts.length,
      leads: state.leads.length,
      opportunities: state.opportunities.length,
      cases: state.cases.length,
      activities: state.activities.length,
    },
    openPipelineJpy: state.opportunities
      .filter((o) => o.stage !== "closed-won" && o.stage !== "closed-lost")
      .reduce((s, o) => s + o.amountJpy, 0),
    weightedPipelineJpy: state.opportunities
      .filter((o) => o.stage !== "closed-won" && o.stage !== "closed-lost")
      .reduce((s, o) => s + Math.round((o.amountJpy * o.probability) / 100), 0),
  };
}
