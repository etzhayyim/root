// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 etzhayyim Japan株式会社 / etzhayyim. All rights reserved.
// Licensed under the Apache License, Version 2.0 — see LICENSE at repo root.

export type Plan = {
  planId: string;
  name: string;
  priceJpyMonthly: number;
  includedSeats: number;
  includedUsageUnits: number;
  overageUnitPriceJpy: number;
  supportTier: "community" | "standard" | "priority";
  features: string[];
};

export type TenantStatus = "trial" | "active" | "grace" | "paused" | "churn-risk";
export type WorkspaceEnvironment = "production" | "staging" | "sandbox";
export type MembershipRole = "owner" | "billing-admin" | "operator" | "member";
export type SubscriptionStatus = "trial" | "active" | "grace" | "paused" | "canceled";

export type Tenant = {
  tenantId: string;
  name: string;
  slug: string;
  planId: string;
  primaryOwnerEmail: string;
  status: TenantStatus;
  createdAt: string;
  renewalAt: string;
};

export type Workspace = {
  workspaceId: string;
  tenantId: string;
  name: string;
  region: string;
  environment: WorkspaceEnvironment;
  seatLimit: number;
  createdAt: string;
};

export type Membership = {
  membershipId: string;
  tenantId: string;
  workspaceId: string;
  email: string;
  role: MembershipRole;
  invitedAt: string;
};

export type Subscription = {
  subscriptionId: string;
  tenantId: string;
  planId: string;
  status: SubscriptionStatus;
  startedAt: string;
  renewalAt: string;
  mrrJpy: number;
  contractMode: "self-serve" | "invoice" | "annual";
};

export type UsageRecord = {
  usageId: string;
  tenantId: string;
  workspaceId: string;
  metric: "automation-runs" | "seats" | "api-calls";
  quantity: number;
  recordedAt: string;
  source: "seed" | "ui" | "system";
};

export type AuditEvent = {
  auditId: string;
  tenantId: string;
  actor: string;
  action: string;
  resourceType: string;
  resourceId: string;
  summary: string;
  createdAt: string;
};

export type OpenSaasState = {
  plans: Plan[];
  tenants: Tenant[];
  workspaces: Workspace[];
  memberships: Membership[];
  subscriptions: Subscription[];
  usage: UsageRecord[];
  audit: AuditEvent[];
};

export type TenantSnapshot = {
  tenant: Tenant;
  plan: Plan | null;
  workspaces: Workspace[];
  memberships: Membership[];
  subscription: Subscription | null;
  usageSummary: {
    totalUnits: number;
    usagePct: number;
    usageByMetric: Record<string, number>;
  };
  seatSummary: {
    assignedSeats: number;
    seatLimit: number;
  };
  riskLevel: "stable" | "watch" | "action";
};

type CreateTenantInput = {
  name: string;
  ownerEmail: string;
  planId: string;
  workspaceName?: string;
};

type AddWorkspaceInput = {
  name: string;
  region: string;
  environment: WorkspaceEnvironment;
  seatLimit: number;
};

type AddMembershipInput = {
  workspaceId: string;
  email: string;
  role: MembershipRole;
};

type RecordUsageInput = {
  tenantId: string;
  workspaceId: string;
  metric: UsageRecord["metric"];
  quantity: number;
  source?: UsageRecord["source"];
};

type TransitionSubscriptionInput = {
  subscriptionId: string;
  status: SubscriptionStatus;
  actor: string;
  reason: string;
};

function iso(offsetDays = 0): string {
  const date = new Date();
  date.setUTCDate(date.getUTCDate() + offsetDays);
  return date.toISOString();
}

function nextId(prefix: string): string {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

function slugify(name: string): string {
  return name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 48);
}

function sumUsage(records: UsageRecord[]): number {
  return records.reduce((sum, record) => sum + record.quantity, 0);
}

const initialState: OpenSaasState = {
  plans: [
    {
      planId: "starter",
      name: "Starter",
      priceJpyMonthly: 78000,
      includedSeats: 10,
      includedUsageUnits: 1000,
      overageUnitPriceJpy: 42,
      supportTier: "community",
      features: ["tenant registry", "workspace control", "usage ledger"],
    },
    {
      planId: "growth",
      name: "Growth",
      priceJpyMonthly: 240000,
      includedSeats: 30,
      includedUsageUnits: 5000,
      overageUnitPriceJpy: 36,
      supportTier: "standard",
      features: ["audit stream", "billing ops", "role policy"],
    },
    {
      planId: "enterprise",
      name: "Enterprise",
      priceJpyMonthly: 1260000,
      includedSeats: 120,
      includedUsageUnits: 25000,
      overageUnitPriceJpy: 28,
      supportTier: "priority",
      features: ["sso ready contract", "annual billing", "operator escalation"],
    },
  ],
  tenants: [
    {
      tenantId: "tn_azuma",
      name: "Azuma Research",
      slug: "azuma-research",
      planId: "growth",
      primaryOwnerEmail: "owner@azuma.example",
      status: "active",
      createdAt: iso(-84),
      renewalAt: iso(18),
    },
    {
      tenantId: "tn_kitahoshi",
      name: "Kitahoshi Logistics",
      slug: "kitahoshi-logistics",
      planId: "starter",
      primaryOwnerEmail: "ops@kitahoshi.example",
      status: "churn-risk",
      createdAt: iso(-31),
      renewalAt: iso(6),
    },
    {
      tenantId: "tn_yoroi",
      name: "Yoroi Systems",
      slug: "yoroi-systems",
      planId: "enterprise",
      primaryOwnerEmail: "cio@yoroi.example",
      status: "active",
      createdAt: iso(-190),
      renewalAt: iso(42),
    },
  ],
  workspaces: [
    { workspaceId: "ws_azuma_prod", tenantId: "tn_azuma", name: "Azuma Core", region: "apac", environment: "production", seatLimit: 18, createdAt: iso(-82) },
    { workspaceId: "ws_azuma_lab", tenantId: "tn_azuma", name: "Azuma Lab", region: "apac", environment: "staging", seatLimit: 8, createdAt: iso(-54) },
    { workspaceId: "ws_kitahoshi_ops", tenantId: "tn_kitahoshi", name: "Kitahoshi Ops", region: "japan", environment: "production", seatLimit: 10, createdAt: iso(-30) },
    { workspaceId: "ws_yoroi_prod", tenantId: "tn_yoroi", name: "Yoroi Main", region: "global", environment: "production", seatLimit: 64, createdAt: iso(-188) },
    { workspaceId: "ws_yoroi_sbx", tenantId: "tn_yoroi", name: "Yoroi Sandbox", region: "global", environment: "sandbox", seatLimit: 32, createdAt: iso(-170) },
  ],
  memberships: [
    { membershipId: "mb_azuma_1", tenantId: "tn_azuma", workspaceId: "ws_azuma_prod", email: "owner@azuma.example", role: "owner", invitedAt: iso(-84) },
    { membershipId: "mb_azuma_2", tenantId: "tn_azuma", workspaceId: "ws_azuma_prod", email: "billing@azuma.example", role: "billing-admin", invitedAt: iso(-70) },
    { membershipId: "mb_azuma_3", tenantId: "tn_azuma", workspaceId: "ws_azuma_lab", email: "ops@azuma.example", role: "operator", invitedAt: iso(-52) },
    { membershipId: "mb_kitahoshi_1", tenantId: "tn_kitahoshi", workspaceId: "ws_kitahoshi_ops", email: "ops@kitahoshi.example", role: "owner", invitedAt: iso(-31) },
    { membershipId: "mb_kitahoshi_2", tenantId: "tn_kitahoshi", workspaceId: "ws_kitahoshi_ops", email: "dispatch@kitahoshi.example", role: "member", invitedAt: iso(-26) },
    { membershipId: "mb_yoroi_1", tenantId: "tn_yoroi", workspaceId: "ws_yoroi_prod", email: "cio@yoroi.example", role: "owner", invitedAt: iso(-190) },
    { membershipId: "mb_yoroi_2", tenantId: "tn_yoroi", workspaceId: "ws_yoroi_prod", email: "platform@yoroi.example", role: "operator", invitedAt: iso(-150) },
    { membershipId: "mb_yoroi_3", tenantId: "tn_yoroi", workspaceId: "ws_yoroi_sbx", email: "finance@yoroi.example", role: "billing-admin", invitedAt: iso(-120) },
  ],
  subscriptions: [
    { subscriptionId: "sub_azuma", tenantId: "tn_azuma", planId: "growth", status: "active", startedAt: iso(-84), renewalAt: iso(18), mrrJpy: 240000, contractMode: "self-serve" },
    { subscriptionId: "sub_kitahoshi", tenantId: "tn_kitahoshi", planId: "starter", status: "trial", startedAt: iso(-31), renewalAt: iso(6), mrrJpy: 78000, contractMode: "self-serve" },
    { subscriptionId: "sub_yoroi", tenantId: "tn_yoroi", planId: "enterprise", status: "active", startedAt: iso(-190), renewalAt: iso(42), mrrJpy: 1260000, contractMode: "annual" },
  ],
  usage: [
    { usageId: "usg_1", tenantId: "tn_azuma", workspaceId: "ws_azuma_prod", metric: "automation-runs", quantity: 2200, recordedAt: iso(-2), source: "seed" },
    { usageId: "usg_2", tenantId: "tn_azuma", workspaceId: "ws_azuma_lab", metric: "api-calls", quantity: 1200, recordedAt: iso(-1), source: "seed" },
    { usageId: "usg_3", tenantId: "tn_azuma", workspaceId: "ws_azuma_prod", metric: "seats", quantity: 24, recordedAt: iso(-1), source: "seed" },
    { usageId: "usg_4", tenantId: "tn_kitahoshi", workspaceId: "ws_kitahoshi_ops", metric: "automation-runs", quantity: 710, recordedAt: iso(-1), source: "seed" },
    { usageId: "usg_5", tenantId: "tn_kitahoshi", workspaceId: "ws_kitahoshi_ops", metric: "seats", quantity: 8, recordedAt: iso(-1), source: "seed" },
    { usageId: "usg_6", tenantId: "tn_yoroi", workspaceId: "ws_yoroi_prod", metric: "automation-runs", quantity: 9800, recordedAt: iso(-1), source: "seed" },
    { usageId: "usg_7", tenantId: "tn_yoroi", workspaceId: "ws_yoroi_prod", metric: "api-calls", quantity: 3600, recordedAt: iso(-1), source: "seed" },
    { usageId: "usg_8", tenantId: "tn_yoroi", workspaceId: "ws_yoroi_sbx", metric: "seats", quantity: 87, recordedAt: iso(-1), source: "seed" },
  ],
  audit: [
    { auditId: "aud_1", tenantId: "tn_azuma", actor: "system", action: "seeded", resourceType: "tenant", resourceId: "tn_azuma", summary: "Seeded tenant baseline for Azuma Research", createdAt: iso(-84) },
    { auditId: "aud_2", tenantId: "tn_kitahoshi", actor: "system", action: "seeded", resourceType: "tenant", resourceId: "tn_kitahoshi", summary: "Seeded tenant baseline for Kitahoshi Logistics", createdAt: iso(-31) },
    { auditId: "aud_3", tenantId: "tn_yoroi", actor: "system", action: "seeded", resourceType: "tenant", resourceId: "tn_yoroi", summary: "Seeded tenant baseline for Yoroi Systems", createdAt: iso(-190) },
  ],
};

const state: OpenSaasState = structuredClone(initialState);

function findPlan(planId: string): Plan | null {
  return state.plans.find((plan) => plan.planId === planId) ?? null;
}

function pushAudit(event: Omit<AuditEvent, "auditId" | "createdAt">): AuditEvent {
  const audit = {
    auditId: nextId("aud"),
    createdAt: new Date().toISOString(),
    ...event,
  };
  state.audit.unshift(audit);
  return audit;
}

export function getBlueprint() {
  return {
    name: "etzhayyim-project-open-saas",
    posture: "open-source-first",
    thesis:
      "Ship an auditable SaaS baseline where tenancy, billing, auditability, and extension APIs are first-class from day one.",
    priorities: [
      "tenant onboarding",
      "workspace and seat governance",
      "subscription visibility",
      "usage ledger and audit history",
    ],
    principles: [
      "Control plane is open and inspectable.",
      "Billing events are reproducible from usage ledgers.",
      "Every operator action yields an audit event.",
      "Self-hosted and managed deployment share the same contract.",
    ],
    apiDomains: [
      { path: "/api/open-saas/overview", purpose: "High-signal SaaS health and demand metrics" },
      { path: "/api/open-saas/tenants", purpose: "Tenant onboarding and lifecycle" },
      { path: "/api/open-saas/subscriptions", purpose: "Plan and subscription state transitions" },
      { path: "/api/open-saas/usage", purpose: "Usage ingestion and metering" },
      { path: "/api/open-saas/audit", purpose: "Operator and system change history" },
    ],
  };
}

export function listPlans(): Plan[] {
  return state.plans;
}

export function getUsageSummary(tenantId: string) {
  const tenantRecords = state.usage.filter((record) => record.tenantId === tenantId);
  const usageByMetric = tenantRecords.reduce<Record<string, number>>((acc, record) => {
    acc[record.metric] = (acc[record.metric] ?? 0) + record.quantity;
    return acc;
  }, {});
  const totalUnits = sumUsage(tenantRecords);
  const tenant = state.tenants.find((item) => item.tenantId === tenantId) ?? null;
  const plan = tenant ? findPlan(tenant.planId) : null;
  const included = plan?.includedUsageUnits ?? 1;
  const usagePct = Math.round((totalUnits / included) * 100);
  return { totalUnits, usagePct, usageByMetric };
}

function getSeatSummary(tenantId: string) {
  const assignedSeats = state.memberships.filter((membership) => membership.tenantId === tenantId).length;
  const seatLimit = state.workspaces
    .filter((workspace) => workspace.tenantId === tenantId)
    .reduce((sum, workspace) => sum + workspace.seatLimit, 0);
  return { assignedSeats, seatLimit };
}

export function getTenantSnapshot(tenantId: string): TenantSnapshot | null {
  const tenant = state.tenants.find((item) => item.tenantId === tenantId);
  if (!tenant) return null;
  const plan = findPlan(tenant.planId);
  const workspaces = state.workspaces.filter((workspace) => workspace.tenantId === tenantId);
  const memberships = state.memberships.filter((membership) => membership.tenantId === tenantId);
  const subscription = state.subscriptions.find((item) => item.tenantId === tenantId) ?? null;
  const usageSummary = getUsageSummary(tenantId);
  const seatSummary = getSeatSummary(tenantId);
  const riskLevel =
    usageSummary.usagePct > 90 || tenant.status === "churn-risk"
      ? "action"
      : usageSummary.usagePct > 70
        ? "watch"
        : "stable";
  return { tenant, plan, workspaces, memberships, subscription, usageSummary, seatSummary, riskLevel };
}

export function listTenantSnapshots(): TenantSnapshot[] {
  return state.tenants.map((tenant) => getTenantSnapshot(tenant.tenantId)).filter(Boolean) as TenantSnapshot[];
}

export function listSubscriptions() {
  return state.subscriptions.map((subscription) => ({
    ...subscription,
    tenant: state.tenants.find((tenant) => tenant.tenantId === subscription.tenantId) ?? null,
    plan: findPlan(subscription.planId),
  }));
}

export function listUsage(tenantId?: string) {
  return state.usage
    .filter((record) => (tenantId ? record.tenantId === tenantId : true))
    .sort((a, b) => b.recordedAt.localeCompare(a.recordedAt));
}

export function listAudit(tenantId?: string, limit = 20) {
  return state.audit
    .filter((record) => (tenantId ? record.tenantId === tenantId : true))
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
    .slice(0, limit);
}

export function getOverview() {
  const snapshots = listTenantSnapshots();
  const totalMrrJpy = state.subscriptions
    .filter((subscription) => subscription.status !== "canceled")
    .reduce((sum, subscription) => sum + subscription.mrrJpy, 0);
  const overloadedTenants = snapshots.filter((snapshot) => snapshot.usageSummary.usagePct > 85).length;
  const totalAssignedSeats = snapshots.reduce((sum, snapshot) => sum + snapshot.seatSummary.assignedSeats, 0);
  return {
    generatedAt: new Date().toISOString(),
    totalTenants: snapshots.length,
    activeTenants: snapshots.filter((snapshot) => snapshot.tenant.status === "active").length,
    totalMrrJpy,
    totalAssignedSeats,
    overloadedTenants,
    trialTenants: snapshots.filter((snapshot) => snapshot.subscription?.status === "trial").length,
    highestNeedAreas: [
      {
        key: "tenant-onboarding",
        name: "Tenant onboarding",
        reason: "Every SaaS needs fast provisioning, ownership, and workspace bootstrap before any advanced feature matters.",
      },
      {
        key: "usage-audit",
        name: "Usage and audit",
        reason: "Without usage and audit, billing and support both become manual and unverifiable.",
      },
      {
        key: "subscription-ops",
        name: "Subscription operations",
        reason: "Plan changes, renewals, and grace states are the main revenue-control path.",
      },
    ],
    tenants: snapshots,
  };
}

export function createTenant(input: CreateTenantInput) {
  const name = input.name.trim();
  const ownerEmail = input.ownerEmail.trim().toLowerCase();
  if (!name) throw new Error("name is required");
  if (!ownerEmail.includes("@")) throw new Error("ownerEmail must be a valid email");
  const plan = findPlan(input.planId);
  if (!plan) throw new Error("planId not found");

  const tenantId = nextId("tn");
  const workspaceId = nextId("ws");
  const membershipId = nextId("mb");
  const subscriptionId = nextId("sub");
  const now = new Date().toISOString();

  const tenant: Tenant = {
    tenantId,
    name,
    slug: slugify(name),
    planId: plan.planId,
    primaryOwnerEmail: ownerEmail,
    status: "trial",
    createdAt: now,
    renewalAt: iso(14),
  };
  const workspace: Workspace = {
    workspaceId,
    tenantId,
    name: input.workspaceName?.trim() || `${name} Workspace`,
    region: "japan",
    environment: "production",
    seatLimit: Math.max(plan.includedSeats, 5),
    createdAt: now,
  };
  const membership: Membership = {
    membershipId,
    tenantId,
    workspaceId,
    email: ownerEmail,
    role: "owner",
    invitedAt: now,
  };
  const subscription: Subscription = {
    subscriptionId,
    tenantId,
    planId: plan.planId,
    status: "trial",
    startedAt: now,
    renewalAt: iso(14),
    mrrJpy: plan.priceJpyMonthly,
    contractMode: "self-serve",
  };

  state.tenants.unshift(tenant);
  state.workspaces.unshift(workspace);
  state.memberships.unshift(membership);
  state.subscriptions.unshift(subscription);
  pushAudit({
    tenantId,
    actor: ownerEmail,
    action: "tenant.created",
    resourceType: "tenant",
    resourceId: tenantId,
    summary: `Created tenant ${name} on ${plan.name} plan`,
  });

  return getTenantSnapshot(tenantId);
}

export function addWorkspace(tenantId: string, input: AddWorkspaceInput) {
  const tenant = state.tenants.find((item) => item.tenantId === tenantId);
  if (!tenant) throw new Error("tenant not found");
  const name = input.name.trim();
  if (!name) throw new Error("workspace name is required");
  const workspace: Workspace = {
    workspaceId: nextId("ws"),
    tenantId,
    name,
    region: input.region.trim() || "japan",
    environment: input.environment,
    seatLimit: input.seatLimit,
    createdAt: new Date().toISOString(),
  };
  state.workspaces.unshift(workspace);
  pushAudit({
    tenantId,
    actor: "operator-console",
    action: "workspace.created",
    resourceType: "workspace",
    resourceId: workspace.workspaceId,
    summary: `Created ${workspace.environment} workspace ${workspace.name}`,
  });
  return workspace;
}

export function addMembership(tenantId: string, input: AddMembershipInput) {
  const workspace = state.workspaces.find((item) => item.workspaceId === input.workspaceId && item.tenantId === tenantId);
  if (!workspace) throw new Error("workspace not found");
  const email = input.email.trim().toLowerCase();
  if (!email.includes("@")) throw new Error("email must be valid");
  const membership: Membership = {
    membershipId: nextId("mb"),
    tenantId,
    workspaceId: workspace.workspaceId,
    email,
    role: input.role,
    invitedAt: new Date().toISOString(),
  };
  state.memberships.unshift(membership);
  pushAudit({
    tenantId,
    actor: "operator-console",
    action: "membership.invited",
    resourceType: "membership",
    resourceId: membership.membershipId,
    summary: `Invited ${email} as ${input.role} into ${workspace.name}`,
  });
  return membership;
}

export function recordUsage(input: RecordUsageInput) {
  const workspace = state.workspaces.find(
    (item) => item.workspaceId === input.workspaceId && item.tenantId === input.tenantId,
  );
  if (!workspace) throw new Error("workspace not found");
  if (!Number.isFinite(input.quantity) || input.quantity <= 0) throw new Error("quantity must be > 0");
  const usage: UsageRecord = {
    usageId: nextId("usg"),
    tenantId: input.tenantId,
    workspaceId: input.workspaceId,
    metric: input.metric,
    quantity: input.quantity,
    recordedAt: new Date().toISOString(),
    source: input.source ?? "ui",
  };
  state.usage.unshift(usage);
  pushAudit({
    tenantId: input.tenantId,
    actor: "operator-console",
    action: "usage.recorded",
    resourceType: "usage",
    resourceId: usage.usageId,
    summary: `Recorded ${input.quantity} ${input.metric} for ${workspace.name}`,
  });
  return usage;
}

export function transitionSubscription(input: TransitionSubscriptionInput) {
  const subscription = state.subscriptions.find((item) => item.subscriptionId === input.subscriptionId);
  if (!subscription) throw new Error("subscription not found");
  subscription.status = input.status;
  if (input.status === "active") {
    const tenant = state.tenants.find((item) => item.tenantId === subscription.tenantId);
    if (tenant) tenant.status = "active";
  }
  pushAudit({
    tenantId: subscription.tenantId,
    actor: input.actor,
    action: "subscription.transitioned",
    resourceType: "subscription",
    resourceId: subscription.subscriptionId,
    summary: `Subscription moved to ${input.status}: ${input.reason}`,
  });
  return subscription;
}
