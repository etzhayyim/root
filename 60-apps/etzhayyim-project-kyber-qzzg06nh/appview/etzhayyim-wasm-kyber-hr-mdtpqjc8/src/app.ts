import {
  asAgentTool,
  createWorkerExport,
  createKyselyDb,
  nowISO,
  str,
  withCapabilityTags,
  type ComAtprotoSyncSubscribeReposCommit,
  type HostSDK,
  resolveHeartbeatCadence,
  createCadenceState,
  createInboxBuffer,
  decodeJson,
  genID,
  nsid,
  parseLexiconInput,
} from "@etzhayyim/kotodama-host-sdk";

const cadenceState = createCadenceState();
const inbox = createInboxBuffer();

let appId = "";
let actorDID = "";

// ─── Graph Labels ───
// HrEmployee    — employee profile (department, role, skills, lifecycle status)
// HrPosition    — job position with required competencies and salary range
// HrSkill       — skill/competency definition with proficiency levels
// HrEvaluation  — performance evaluation with multi-dimensional scoring
// HrTraining    — training program enrollment and completion tracking

// ─── Collection Kinds (AT Protocol camelCase) ───
// employee, position, skill, evaluation, training

const PROBATION_MONTHS = 3;
const PERFORMANCE_SCORE_MIN = 1;
const PERFORMANCE_SCORE_MAX = 5;
const SKILL_PROFICIENCY_MAX = 5;
const ANNUAL_LEAVE_DEFAULT_DAYS = 20;

// ─── Helpers ───

async function write(_sdk: HostSDK, kind: string, rec: Record<string, unknown>): Promise<void> {
  function camelToSnake(s: string): string { return s.replace(/[A-Z]/g, c => `_${c.toLowerCase()}`); }
  const tableMap: Record<string, string> = {
    employee: "vertex_hr_employee",
    position: "vertex_hr_position",
    skill: "vertex_hr_skill",
    evaluation: "vertex_hr_evaluation",
    training: "vertex_hr_training",
  };
  const table = tableMap[kind] ?? `vertex_hr_${camelToSnake(kind)}`;
  const ownerDid = actorDID || "did:web:mdtpqjc8.etzhayyim.com";
  const rkey = str(rec.employeeId ?? rec.positionId ?? rec.skillId ?? rec.assignmentId ?? rec.evaluationId ?? rec.enrollmentId ?? "") || genID();
  const vertex_id = `at://${ownerDid}/com.etzhayyim.app.kyber.hr.${kind}/${rkey}`;
  const snakeRec = Object.fromEntries(Object.entries(rec).map(([k, v]) => [camelToSnake(k), v]));
  await createKyselyDb().insertInto(table as any).values({ vertex_id, sensitivity_ord: 2, owner_did: ownerDid, actor_id: appId, ...snakeRec }).execute();
}

function post(_sdk: HostSDK, _text: string): void {
  // derive rule handles actual social posting
}

// ─── Domain Entity DIDs ───

interface DomainEntity { path: string; displayName: string; description: string; category: string }

const domainEntities: DomainEntity[] = [
  { path: "actor:recruiter", displayName: "Recruiter", description: "Talent acquisition and hiring agent", category: "hr" },
  { path: "actor:evaluator", displayName: "Performance Evaluator", description: "Employee performance review agent", category: "hr" },
  { path: "actor:trainer", displayName: "Training Coordinator", description: "Learning and development agent", category: "hr" },
  { path: "actor:succession-planner", displayName: "Succession Planner", description: "Career path and succession planning agent", category: "hr" },
  { path: "actor:compensation", displayName: "Compensation Analyst", description: "Salary and benefits management agent", category: "hr" },
];

let entitiesRegistered = false;

function registerDomainEntities(sdk: HostSDK): void {
  if (entitiesRegistered) return;
  for (const de of domainEntities) {
    try {
      sdk.hostImports.comAtprotoIdentityCreate(de.path, JSON.stringify({
        displayName: de.displayName,
        description: de.description,
        category: de.category,
      }));
    } catch (e) { console.warn(`DID create ${de.path}:`, e); }
  }
  entitiesRegistered = true;
}

// ─── Health & Describe ───

function cmdHealth(): Record<string, unknown> {
  return { status: "healthy", app: "Kyber HR", nanoid: appId, did: actorDID, now: nowISO() };
}

function cmdDescribe(): Record<string, unknown> {
  return {
    name: "Kyber HR",
    did: actorDID,
    nanoid: appId,
    capabilities: [
      "health", "describe",
      "registerEmployee", "updateEmployeeStatus", "listEmployees",
      "createPosition", "listPositions",
      "registerSkill", "assignSkill", "skillGapAnalysis",
      "createEvaluation", "listEvaluations",
      "enrollTraining", "completeTraining",
      "coverageStats",
    ],
    protocols: ["xrpc", "w-protocol", "mcp"],
  };
}

// ─── HR: Employee Management ───

async function cmdRegisterEmployee(sdk: HostSDK, body: Uint8Array): Promise<Record<string, unknown>> {
  const args = parseLexiconInput("com.etzhayyim.app.kyber.hr.registerEmployee", body);
  const fullName = str(args.fullName ?? "");
  const department = str(args.department ?? "");
  const role = str(args.role ?? "");
  const positionId = str(args.positionId ?? "");
  const employmentType = str(args.employmentType ?? "fullTime") as "fullTime" | "partTime" | "contract" | "intern";
  const startDate = str(args.startDate ?? nowISO());
  const salary = Number(args.salary ?? 0);
  const managerId = str(args.managerId ?? "");
  const email = str(args.email ?? "");

  if (!fullName || !department || !role) {
    return { ok: false, error: "missing_params", detail: "fullName, department, role required" };
  }

  if (employmentType === "fullTime" && salary <= 0) {
    return { ok: false, error: "invalid_salary", detail: "Full-time employees must have a positive salary" };
  }

  let probationStatus: "on_probation" | "confirmed" | "not_applicable";
  if (employmentType === "fullTime" || employmentType === "partTime") {
    probationStatus = "on_probation";
  } else if (employmentType === "contract") {
    probationStatus = "confirmed";
  } else {
    probationStatus = "not_applicable";
  }

  const probationEndDate = probationStatus === "on_probation"
    ? new Date(new Date(startDate).getTime() + PROBATION_MONTHS * 30 * 24 * 60 * 60 * 1000).toISOString()
    : "";

  const employeeId = genID("emp");
  await write(sdk, "employee", {
    employeeId,
    fullName,
    department,
    role,
    positionId,
    employmentType,
    startDate,
    salary,
    managerId,
    email,
    probationStatus,
    probationEndDate,
    annualLeaveDays: ANNUAL_LEAVE_DEFAULT_DAYS,
    usedLeaveDays: 0,
    status: "active",
    registeredAt: nowISO(),
    org_id: "anon",
    user_id: "anon",
    actor_id: appId,
    created_at: nowISO(),
  });

  post(sdk, `Employee ${fullName} registered in ${department} as ${role} (${employmentType}, ${probationStatus})`);

  return { ok: true, employeeId, fullName, department, role, probationStatus, probationEndDate };
}

async function cmdUpdateEmployeeStatus(sdk: HostSDK, body: Uint8Array): Promise<Record<string, unknown>> {
  const args = parseLexiconInput("com.etzhayyim.app.kyber.hr.updateEmployeeStatus", body);
  const employeeId = str(args.employeeId ?? "");
  const newStatus = str(args.status ?? "") as "active" | "on_leave" | "terminated" | "retired";
  const reason = str(args.reason ?? "");

  if (!employeeId || !newStatus) {
    return { ok: false, error: "missing_params", detail: "employeeId and status required" };
  }

  const validStatuses = ["active", "on_leave", "terminated", "retired"];
  if (!validStatuses.includes(newStatus)) {
    return { ok: false, error: "invalid_status", detail: `status must be one of: ${validStatuses.join(", ")}` };
  }

  const employees = ([] as Record<string, unknown>[]);

  if (employees.length === 0) {
    return { ok: false, error: "employee_not_found", detail: `Employee ${employeeId} not found` };
  }

  const currentStatus = str(employees[0].status as string);
  if (currentStatus === "terminated") {
    return { ok: false, error: "already_terminated", detail: "Cannot update terminated employee" };
  }

  await write(sdk, "employee", {
    employeeId,
    status: newStatus,
    reason,
    statusChangedAt: nowISO(),
    previousStatus: currentStatus,
    org_id: "anon",
    user_id: "anon",
    actor_id: appId,
    created_at: nowISO(),
  });

  post(sdk, `Employee ${employees[0].fullName} status: ${currentStatus} -> ${newStatus}`);

  return { ok: true, employeeId, previousStatus: currentStatus, newStatus, reason };
}

async function cmdListEmployees(_sdk: HostSDK, body: Uint8Array): Promise<Record<string, unknown>> {
  const args = parseLexiconInput("com.etzhayyim.app.kyber.hr.listEmployees", body);
  const limit = Number(args.limit ?? 50);
  const offset = Number(args.offset ?? 0);
  // TODO(kyber-hr): vertex_hr_employee not in @etzhayyim/graph-schema — reads return empty
  const rows = ([] as Record<string, unknown>[]);
  return { ok: true, employees: rows, total: rows.length, offset, limit };
}

// ─── Position Management ───

async function cmdCreatePosition(sdk: HostSDK, body: Uint8Array): Promise<Record<string, unknown>> {
  const args = parseLexiconInput("com.etzhayyim.app.kyber.hr.createPosition", body);
  const title = str(args.title ?? "");
  const department = str(args.department ?? "");
  const level = str(args.level ?? "staff") as "intern" | "staff" | "senior" | "lead" | "manager" | "director" | "executive";
  const requiredSkills = (args.requiredSkills ?? []) as Array<{ skillId: string; minProficiency: number }>;
  const headcount = Number(args.headcount ?? 1);
  const salaryRangeMin = Number(args.salaryRangeMin ?? 0);
  const salaryRangeMax = Number(args.salaryRangeMax ?? 0);
  const description = str(args.description ?? "");

  if (!title || !department) {
    return { ok: false, error: "missing_params", detail: "title and department required" };
  }

  if (salaryRangeMax > 0 && salaryRangeMin > salaryRangeMax) {
    return { ok: false, error: "invalid_salary_range", detail: "salaryRangeMin must not exceed salaryRangeMax" };
  }

  const positionId = genID("pos");
  await write(sdk, "position", {
    positionId,
    title,
    department,
    level,
    requiredSkills: JSON.stringify(requiredSkills),
    headcount,
    filledCount: 0,
    salaryRangeMin,
    salaryRangeMax,
    description,
    status: "open",
    createdAt: nowISO(),
    org_id: "anon",
    user_id: "anon",
    actor_id: appId,
    created_at: nowISO(),
  });

  return { ok: true, positionId, title, department, level, headcount };
}

async function cmdListPositions(_sdk: HostSDK, _body: Uint8Array): Promise<Record<string, unknown>> {
  // TODO(kyber-hr): vertex_hr_position not in @etzhayyim/graph-schema — reads return empty
  const rows = ([] as Record<string, unknown>[]);
  return { ok: true, positions: rows, total: rows.length };
}

// ─── Skill / Competency Management ───

async function cmdRegisterSkill(sdk: HostSDK, body: Uint8Array): Promise<Record<string, unknown>> {
  const args = parseLexiconInput("com.etzhayyim.app.kyber.hr.registerSkill", body);
  const name = str(args.name ?? "");
  const category = str(args.category ?? "technical") as "technical" | "leadership" | "communication" | "analytical" | "domain";
  const description = str(args.description ?? "");
  const maxProficiency = Number(args.maxProficiency ?? SKILL_PROFICIENCY_MAX);

  if (!name) {
    return { ok: false, error: "missing_params", detail: "name required" };
  }

  const skillId = genID("skl");
  await write(sdk, "skill", {
    skillId,
    name,
    category,
    description,
    maxProficiency,
    createdAt: nowISO(),
    org_id: "anon",
    user_id: "anon",
    actor_id: appId,
    created_at: nowISO(),
  });

  return { ok: true, skillId, name, category };
}

async function cmdAssignSkill(sdk: HostSDK, body: Uint8Array): Promise<Record<string, unknown>> {
  const args = parseLexiconInput("com.etzhayyim.app.kyber.hr.assignSkill", body);
  const employeeId = str(args.employeeId ?? "");
  const skillId = str(args.skillId ?? "");
  const proficiency = Number(args.proficiency ?? 1);
  const certifiedBy = str(args.certifiedBy ?? "");
  const certifiedAt = str(args.certifiedAt ?? nowISO());

  if (!employeeId || !skillId) {
    return { ok: false, error: "missing_params", detail: "employeeId and skillId required" };
  }

  if (proficiency < 1 || proficiency > SKILL_PROFICIENCY_MAX) {
    return { ok: false, error: "invalid_proficiency", detail: `proficiency must be between 1 and ${SKILL_PROFICIENCY_MAX}` };
  }

  const assignmentId = genID("ska");
  await write(sdk, "skill", {
    assignmentId,
    employeeId,
    skillId,
    proficiency,
    certifiedBy,
    certifiedAt,
    type: "assignment",
    org_id: "anon",
    user_id: "anon",
    actor_id: appId,
    created_at: nowISO(),
  });

  return { ok: true, assignmentId, employeeId, skillId, proficiency };
}

async function cmdSkillGapAnalysis(_sdk: HostSDK, body: Uint8Array): Promise<Record<string, unknown>> {
  const args = parseLexiconInput("com.etzhayyim.app.kyber.hr.skillGapAnalysis", body);
  const positionId = str(args.positionId ?? "");
  const employeeId = str(args.employeeId ?? "");

  if (!positionId || !employeeId) {
    return { ok: false, error: "missing_params", detail: "positionId and employeeId required" };
  }

  const positions = ([] as Record<string, unknown>[]);

  if (positions.length === 0) {
    return { ok: false, error: "position_not_found" };
  }

  const employeeSkills = ([] as Record<string, unknown>[]);

  const empSkillMap = new Map<string, number>();
  for (const s of employeeSkills) {
    empSkillMap.set(str(s.skillId as string), Number(s.proficiency ?? 0));
  }

  let requiredSkills: Array<{ skillId: string; minProficiency: number }> = [];
  try {
    requiredSkills = JSON.parse(str(positions[0].requiredSkills as string ?? "[]"));
  } catch { /* empty */ }

  const gaps: Array<{ skillId: string; required: number; current: number; gap: number }> = [];
  let totalGap = 0;

  for (const req of requiredSkills) {
    const current = empSkillMap.get(req.skillId) ?? 0;
    const gap = Math.max(0, req.minProficiency - current);
    if (gap > 0) {
      gaps.push({ skillId: req.skillId, required: req.minProficiency, current, gap });
      totalGap += gap;
    }
  }

  const readiness = requiredSkills.length > 0
    ? Math.round((1 - totalGap / (requiredSkills.length * SKILL_PROFICIENCY_MAX)) * 100)
    : 100;

  return {
    ok: true,
    positionId,
    positionTitle: positions[0].title,
    employeeId,
    gaps,
    readinessPercent: readiness,
    totalGapPoints: totalGap,
  };
}

// ─── Performance Evaluation ───

async function cmdCreateEvaluation(sdk: HostSDK, body: Uint8Array): Promise<Record<string, unknown>> {
  const args = parseLexiconInput("com.etzhayyim.app.kyber.hr.createEvaluation", body);
  const employeeId = str(args.employeeId ?? "");
  const evaluatorId = str(args.evaluatorId ?? "");
  const period = str(args.period ?? "");
  const performanceScore = Number(args.performanceScore ?? 0);
  const competencyScore = Number(args.competencyScore ?? 0);
  const leadershipScore = Number(args.leadershipScore ?? 0);
  const goals = (args.goals ?? []) as Array<{ description: string; achieved: boolean; weight: number }>;
  const strengths = str(args.strengths ?? "");
  const improvements = str(args.improvements ?? "");
  const comments = str(args.comments ?? "");

  if (!employeeId || !evaluatorId || !period) {
    return { ok: false, error: "missing_params", detail: "employeeId, evaluatorId, period required" };
  }

  for (const score of [performanceScore, competencyScore, leadershipScore]) {
    if (score < PERFORMANCE_SCORE_MIN || score > PERFORMANCE_SCORE_MAX) {
      return { ok: false, error: "invalid_score", detail: `scores must be between ${PERFORMANCE_SCORE_MIN} and ${PERFORMANCE_SCORE_MAX}` };
    }
  }

  const goalAchievement = goals.length > 0
    ? goals.reduce((sum, g) => sum + (g.achieved ? g.weight : 0), 0) / goals.reduce((sum, g) => sum + g.weight, 0) * PERFORMANCE_SCORE_MAX
    : performanceScore;

  const overallScore = Math.round(
    (performanceScore * 0.3 + competencyScore * 0.25 + leadershipScore * 0.2 + goalAchievement * 0.25) * 100
  ) / 100;

  let rating: "exceptional" | "exceeds" | "meets" | "below" | "unsatisfactory";
  if (overallScore >= 4.5) rating = "exceptional";
  else if (overallScore >= 3.5) rating = "exceeds";
  else if (overallScore >= 2.5) rating = "meets";
  else if (overallScore >= 1.5) rating = "below";
  else rating = "unsatisfactory";

  const evaluationId = genID("eval");
  await write(sdk, "evaluation", {
    evaluationId,
    employeeId,
    evaluatorId,
    period,
    performanceScore,
    competencyScore,
    leadershipScore,
    goalAchievement: Math.round(goalAchievement * 100) / 100,
    overallScore,
    rating,
    goals: JSON.stringify(goals),
    strengths,
    improvements,
    comments,
    evaluatedAt: nowISO(),
    org_id: "anon",
    user_id: "anon",
    actor_id: appId,
    created_at: nowISO(),
  });

  return { ok: true, evaluationId, employeeId, overallScore, rating };
}

async function cmdListEvaluations(_sdk: HostSDK, _body: Uint8Array): Promise<Record<string, unknown>> {
  // TODO(kyber-hr): vertex_hr_evaluation not in @etzhayyim/graph-schema — reads return empty
  const rows = ([] as Record<string, unknown>[]);
  return { ok: true, evaluations: rows, total: rows.length };
}

// ─── Training & Development ───

async function cmdEnrollTraining(sdk: HostSDK, body: Uint8Array): Promise<Record<string, unknown>> {
  const args = parseLexiconInput("com.etzhayyim.app.kyber.hr.enrollTraining", body);
  const employeeId = str(args.employeeId ?? "");
  const programName = str(args.programName ?? "");
  const skillIds = (args.skillIds ?? []) as string[];
  const startDate = str(args.startDate ?? nowISO());
  const durationDays = Number(args.durationDays ?? 1);
  const provider = str(args.provider ?? "internal");
  const cost = Number(args.cost ?? 0);

  if (!employeeId || !programName) {
    return { ok: false, error: "missing_params", detail: "employeeId and programName required" };
  }

  if (durationDays <= 0) {
    return { ok: false, error: "invalid_duration", detail: "durationDays must be positive" };
  }

  const endDate = new Date(new Date(startDate).getTime() + durationDays * 24 * 60 * 60 * 1000).toISOString();

  const enrollmentId = genID("trn");
  await write(sdk, "training", {
    enrollmentId,
    employeeId,
    programName,
    skillIds: JSON.stringify(skillIds),
    startDate,
    endDate,
    durationDays,
    provider,
    cost,
    status: "enrolled",
    enrolledAt: nowISO(),
    org_id: "anon",
    user_id: "anon",
    actor_id: appId,
    created_at: nowISO(),
  });

  post(sdk, `Employee ${employeeId} enrolled in training: ${programName} (${durationDays} days)`);

  return { ok: true, enrollmentId, employeeId, programName, startDate, endDate };
}

async function cmdCompleteTraining(sdk: HostSDK, body: Uint8Array): Promise<Record<string, unknown>> {
  const args = parseLexiconInput("com.etzhayyim.app.kyber.hr.completeTraining", body);
  const enrollmentId = str(args.enrollmentId ?? "");
  const score = Number(args.score ?? 0);
  const certificateId = str(args.certificateId ?? "");
  const feedback = str(args.feedback ?? "");

  if (!enrollmentId) {
    return { ok: false, error: "missing_params", detail: "enrollmentId required" };
  }

  const enrollments = ([] as Record<string, unknown>[]);

  if (enrollments.length === 0) {
    return { ok: false, error: "enrollment_not_found" };
  }

  if (str(enrollments[0].status as string) === "completed") {
    return { ok: false, error: "already_completed", detail: "Training already completed" };
  }

  const passed = score >= 60;

  await write(sdk, "training", {
    enrollmentId,
    status: passed ? "completed" : "failed",
    score,
    certificateId,
    feedback,
    completedAt: nowISO(),
    org_id: "anon",
    user_id: "anon",
    actor_id: appId,
    created_at: nowISO(),
  });

  const programName = str(enrollments[0].programName as string);
  post(sdk, `Training ${programName}: ${passed ? "completed" : "not passed"} (score: ${score})`);

  return { ok: true, enrollmentId, passed, score };
}

// ─── Coverage Stats ───

async function cmdCoverageStats(): Promise<Record<string, unknown>> {
  // SQL deprecated 2026-04-12 — return zero counts
  const [employees, positions, skills, evaluations, trainings] = [[], [], [], [], []] as Record<string, unknown>[][];

  return {
    ok: true,
    activeEmployees: Number(employees[0]?.cnt ?? 0),
    positions: Number(positions[0]?.cnt ?? 0),
    skillDefinitions: Number(skills[0]?.cnt ?? 0),
    evaluations: Number(evaluations[0]?.cnt ?? 0),
    activeTrainings: Number(trainings[0]?.cnt ?? 0),
  };
}

// ─── Reactive Pipeline ───

export function handleComAtprotoSyncSubscribeReposCommit(
  _sdk: HostSDK,
  commit: ComAtprotoSyncSubscribeReposCommit,
): { ok: true; detail: string } {
  if (commit.action !== "create") return { ok: true, detail: "skip non-create" };

  const collection = str(commit.collection ?? "");

  if (collection === "com.etzhayyim.app.kyber.hr.employee") {
    inbox.inboundCommits.push({ collection, action: "create", ts: Date.now() });
    return { ok: true, detail: `employee: ${collection}` };
  }
  if (collection === "com.etzhayyim.app.kyber.hr.evaluation") {
    inbox.inboundCommits.push({ collection, action: "create", ts: Date.now() });
    return { ok: true, detail: `evaluation: ${collection}` };
  }
  if (collection === "com.etzhayyim.app.kyber.hr.training") {
    inbox.inboundCommits.push({ collection, action: "create", ts: Date.now() });
    return { ok: true, detail: `training: ${collection}` };
  }
  if (collection === "com.etzhayyim.app.kyber.hr.position") {
    return { ok: true, detail: `position: ${collection}` };
  }
  if (collection === "com.etzhayyim.app.kyber.hr.skill") {
    return { ok: true, detail: `skill: ${collection}` };
  }

  return { ok: true, detail: `accepted ${collection}` };
}

// ─── Heartbeat ───

export async function runHeartbeat(sdk: HostSDK): Promise<{ ok: boolean; actions: Array<Record<string, unknown>> }> {
  const actions: Array<Record<string, unknown>> = [];
  const ts = nowISO();
  const cadence = await resolveHeartbeatCadence(actorDID, cadenceState, inbox);
  actions.push({ action: "cadenceResolved", mood: cadence.mood, shouldPost: cadence.shouldPost, reason: cadence.reason, ts });

  if (cadence.shouldPost && cadence.contentSource.type !== "none") {
    try {
      const stats = await cmdCoverageStats();
      const text = `Kyber HR: ${stats.activeEmployees} employees, ${stats.positions} positions, ${stats.skillDefinitions} skills, ${stats.evaluations} evaluations, ${stats.activeTrainings} active trainings`;
      post(sdk, text);
      actions.push({ action: "post", source: "coverageStats", ts });
    } catch (e) {
      console.warn("heartbeat post:", e);
      actions.push({ action: "postFailed", error: String(e), ts });
    }
  }

  if (actions.length === 1) actions.push({ action: "noop", mood: cadence.mood, ts });
  return { ok: true, actions };
}

// ─── App Configuration ───

const configuredApps = new WeakSet<object>();

function configureApp(sdk: HostSDK): void {
  const app = sdk.app;
  if (configuredApps.has(app as object)) return;

  app
    .command(nsid("com.etzhayyim.app.kyber.hr.health"), async () => cmdHealth(), asAgentTool("Kyber HR health check"), withCapabilityTags("diagnostics", "hr"))
    .command(nsid("com.etzhayyim.app.kyber.hr.describe"), async () => cmdDescribe(), asAgentTool("Describe Kyber HR capabilities"), withCapabilityTags("meta", "hr"));

  app
    .command(nsid("com.etzhayyim.app.kyber.hr.registerEmployee"), async (_ctx, body) => cmdRegisterEmployee(sdk, body), asAgentTool("Register new employee with probation and leave tracking"), withCapabilityTags("hr", "employee", "talent"))
    .command(nsid("com.etzhayyim.app.kyber.hr.updateEmployeeStatus"), async (_ctx, body) => cmdUpdateEmployeeStatus(sdk, body), asAgentTool("Update employee status (active/on_leave/terminated/retired)"), withCapabilityTags("hr", "employee", "lifecycle"))
    .command(nsid("com.etzhayyim.app.kyber.hr.listEmployees"), async (_ctx, body) => cmdListEmployees(sdk, body), asAgentTool("List employees by department and status"), withCapabilityTags("hr", "employee", "query"));

  app
    .command(nsid("com.etzhayyim.app.kyber.hr.createPosition"), async (_ctx, body) => cmdCreatePosition(sdk, body), asAgentTool("Create job position with required skills and salary range"), withCapabilityTags("hr", "position", "talent"))
    .command(nsid("com.etzhayyim.app.kyber.hr.listPositions"), async (_ctx, body) => cmdListPositions(sdk, body), asAgentTool("List open positions by department"), withCapabilityTags("hr", "position", "query"));

  app
    .command(nsid("com.etzhayyim.app.kyber.hr.registerSkill"), async (_ctx, body) => cmdRegisterSkill(sdk, body), asAgentTool("Register skill/competency definition"), withCapabilityTags("hr", "skill", "competency"))
    .command(nsid("com.etzhayyim.app.kyber.hr.assignSkill"), async (_ctx, body) => cmdAssignSkill(sdk, body), asAgentTool("Assign skill proficiency to employee"), withCapabilityTags("hr", "skill", "talent"))
    .command(nsid("com.etzhayyim.app.kyber.hr.skillGapAnalysis"), async (_ctx, body) => cmdSkillGapAnalysis(sdk, body), asAgentTool("Analyze skill gaps between employee and position requirements"), withCapabilityTags("hr", "skill", "analytics"));

  app
    .command(nsid("com.etzhayyim.app.kyber.hr.createEvaluation"), async (_ctx, body) => cmdCreateEvaluation(sdk, body), asAgentTool("Create performance evaluation with multi-dimensional scoring"), withCapabilityTags("hr", "evaluation", "performance"))
    .command(nsid("com.etzhayyim.app.kyber.hr.listEvaluations"), async (_ctx, body) => cmdListEvaluations(sdk, body), asAgentTool("List evaluations by employee or period"), withCapabilityTags("hr", "evaluation", "query"));

  app
    .command(nsid("com.etzhayyim.app.kyber.hr.enrollTraining"), async (_ctx, body) => cmdEnrollTraining(sdk, body), asAgentTool("Enroll employee in training program"), withCapabilityTags("hr", "training", "development"))
    .command(nsid("com.etzhayyim.app.kyber.hr.completeTraining"), async (_ctx, body) => cmdCompleteTraining(sdk, body), asAgentTool("Record training completion with score and certificate"), withCapabilityTags("hr", "training", "development"));

  app
    .command(nsid("com.etzhayyim.app.kyber.hr.coverageStats"), async () => cmdCoverageStats(), asAgentTool("Kyber HR coverage statistics"), withCapabilityTags("coverage", "stats", "hr"));

  configuredApps.add(app as object);
}

export default createWorkerExport((sdk) => {
  appId = sdk.pds.selfNanoid ?? "";
  actorDID = sdk.pds.selfRepo ?? "";
  registerDomainEntities(sdk);
  configureApp(sdk);
});
