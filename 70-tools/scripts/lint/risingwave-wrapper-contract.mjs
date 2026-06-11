#!/usr/bin/env node
/**
 * Contract checks for the approved RisingWave operation wrappers.
 *
 * The control-plane guard blocks direct operations; this file checks the
 * approved path itself still has the required lock and health-gate structure.
 */
import { readFileSync } from "node:fs";
import path from "node:path";

const repoRoot = process.cwd();

function read(relPath) {
  return readFileSync(path.join(repoRoot, relPath), "utf8");
}

const checks = [
  {
    file: "70-tools/scripts/risingwave/rw-run-migration-single.sh",
    assertions: [
      {
        id: "migration-uses-lock",
        pattern: /rw-op-lock\.sh/,
        message: "migration wrapper must call rw-op-lock.sh",
      },
      {
        id: "migration-uses-health-gate",
        pattern: /rw-health-gate\.sh/,
        message: "migration wrapper must call rw-health-gate.sh",
      },
      {
        id: "migration-health-purpose-ddl",
        pattern: /RW_GATE_PURPOSE=ddl/,
        message: "migration wrapper must set RW_GATE_PURPOSE=ddl",
      },
      {
        id: "migration-single-apply-only",
        pattern: /node\s+scripts\/apply-single\.mjs\s+"\$migration_name"/,
        message: "migration wrapper must apply exactly the requested single migration",
      },
      {
        id: "migration-requires-dsn",
        pattern: /DATABASE_URL or KOTOBA_URL is required/,
        message: "migration wrapper must refuse missing DATABASE_URL/KOTOBA_URL",
      },
      {
        id: "migration-writes-ledger",
        pattern: /rw-ledger-write\.mjs[\s\S]*write_ledger running[\s\S]*write_ledger succeeded/,
        message: "migration wrapper must write running and succeeded ledger states",
      },
      {
        id: "migration-ledger-failed-trap",
        pattern: /on_exit\(\)[\s\S]*write_ledger failed[\s\S]*trap on_exit EXIT/,
        message: "migration wrapper must record failed state from an EXIT trap",
      },
      {
        id: "migration-ledger-kind",
        pattern: /--operation-kind migration_apply/,
        message: "migration wrapper must write operation_kind=migration_apply",
      },
    ],
  },
  {
    file: "70-tools/scripts/risingwave/rw-helm-upgrade-single.sh",
    assertions: [
      {
        id: "helm-uses-lock",
        pattern: /rw-op-lock\.sh/,
        message: "helm wrapper must call rw-op-lock.sh",
      },
      {
        id: "helm-requires-explicit-mode",
        pattern: /"\$mode" != "--dry-run" && "\$mode" != "--apply"/,
        message: "helm wrapper must reject modes other than --dry-run or --apply",
      },
      {
        id: "helm-dry-run-is-explicit",
        pattern: /helm_args\+=\(--dry-run=client\)/,
        message: "helm wrapper must add --dry-run only for explicit dry-run mode",
      },
      {
        id: "helm-upgrade-install",
        pattern: /upgrade[\s\S]*--install[\s\S]*"\$release_name"[\s\S]*"\$chart"/,
        message: "helm wrapper must run helm upgrade --install against configured release/chart",
      },
      {
        id: "helm-health-gate-scaling-when-dsn-present",
        pattern: /RW_GATE_PURPOSE=scaling/,
        message: "helm wrapper must use RW_GATE_PURPOSE=scaling when a DB health gate is available",
      },
      {
        id: "helm-writes-ledger",
        pattern: /rw-ledger-write\.mjs[\s\S]*write_ledger running[\s\S]*write_ledger succeeded/,
        message: "helm wrapper must write running and succeeded ledger states",
      },
      {
        id: "helm-ledger-failed-trap",
        pattern: /on_exit\(\)[\s\S]*write_ledger failed[\s\S]*trap on_exit EXIT/,
        message: "helm wrapper must record failed state from an EXIT trap",
      },
    ],
  },
  {
    file: "70-tools/scripts/risingwave/rw-op-lock.sh",
    assertions: [
      {
        id: "lock-uses-kubernetes-lease",
        pattern: /apiVersion: coordination\.k8s\.io\/v1[\s\S]*kind: Lease/,
        message: "lock wrapper must use Kubernetes Lease resources",
      },
      {
        id: "lock-has-ttl",
        pattern: /RW_OP_TTL_SECONDS/,
        message: "lock wrapper must expose a TTL",
      },
      {
        id: "lock-renews",
        pattern: /renew_loop\(\)/,
        message: "lock wrapper must renew the lease while the command runs",
      },
      {
        id: "lock-releases-owned-lease",
        pattern: /current_holder.*==.*holder[\s\S]*delete lease/,
        message: "lock wrapper must release only the lease it owns",
      },
    ],
  },
];

const failures = [];

for (const check of checks) {
  const text = read(check.file);
  for (const assertion of check.assertions) {
    if (!assertion.pattern.test(text)) {
      failures.push({
        file: check.file,
        id: assertion.id,
        message: assertion.message,
      });
    }
  }
}

if (failures.length > 0) {
  console.error("[risingwave-wrapper-contract] failed");
  for (const failure of failures) {
    console.error(`\n${failure.file} ${failure.id}`);
    console.error(`  ${failure.message}`);
  }
  process.exit(1);
}

console.log("[risingwave-wrapper-contract] OK");
