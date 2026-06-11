#!/usr/bin/env node
/**
 * charter-rider-notice lint — enforce ADR-2605192200 v2.0 §3 + §4.
 *
 * Pre-commit gate. When a staged change adds or modifies a manifest
 * (package.json / Cargo.toml / pyproject.toml) that declares Apache-2.0
 * licensing, the same directory MUST contain:
 *
 *   - NOTICE file referencing "etzhayyim Charter Compliance Rider"
 *   - CHARTER-RIDER.md (file or symlink to repo-root CHARTER-RIDER.md)
 *
 * 3rd-party vendored directories (Foundry lib/, Rust vendor/, our forks)
 * are exempted per ADR-2605192200 v2.0 §3 (Apache 2.0 §4 attribution
 * preservation for upstream NOTICE files).
 *
 * Exit code 0 on success, 1 on violation.
 *
 * Authoritative ADR: 90-docs/adr/2605192200-etzhayyim-ip-free-release-charter-rider.md
 * Related: 70-tools/charter-rider-applicator/{apply,verify}.sh
 */
import { existsSync, readFileSync, statSync, lstatSync, realpathSync } from "node:fs";
import { dirname, resolve, basename, relative } from "node:path";

const args = process.argv.slice(2);
if (args.length === 0) process.exit(0);

const REPO_ROOT = process.cwd();
const ROOT_RIDER = resolve(REPO_ROOT, "CHARTER-RIDER.md");

const MANIFEST_NAMES = new Set(["package.json", "Cargo.toml", "pyproject.toml"]);

/** 3rd-party vendored paths — exempted from Rider requirement. */
const VENDORED_PATTERNS = [
  /\/lib\//,
  /\/vendor\//,
  /-fork\//,
  /-fork$/,
  /node_modules\//,
  /\.git\//,
];

let violations = 0;

for (const file of args) {
  const name = basename(file);
  if (!MANIFEST_NAMES.has(name)) continue;
  if (VENDORED_PATTERNS.some((re) => re.test(file))) continue;

  let content;
  try {
    if (!statSync(file).isFile()) continue;
    content = readFileSync(file, "utf8");
  } catch {
    continue;
  }

  // Only enforce for Apache-2.0 manifests
  if (!/Apache-2\.0/.test(content)) continue;

  const dir = dirname(resolve(REPO_ROOT, file));

  // Check NOTICE exists + references the Rider
  const notice = resolve(dir, "NOTICE");
  if (!existsSync(notice)) {
    console.error(
      `${file}: missing NOTICE file (required for Apache-2.0 packages per ADR-2605192200 §3)`,
    );
    violations++;
  } else {
    try {
      const noticeContent = readFileSync(notice, "utf8");
      if (!/etzhayyim Charter Compliance Rider/.test(noticeContent)) {
        console.error(
          `${file}: NOTICE present but missing "etzhayyim Charter Compliance Rider" reference (ADR-2605192200 §3.2)`,
        );
        violations++;
      }
    } catch (e) {
      console.error(`${file}: cannot read NOTICE (${e.message})`);
      violations++;
    }
  }

  // Check CHARTER-RIDER.md present + content matches root
  const rider = resolve(dir, "CHARTER-RIDER.md");
  if (!existsSync(rider) && !lstatExists(rider)) {
    console.error(
      `${file}: missing CHARTER-RIDER.md (file or symlink required per ADR-2605192200 §3)`,
    );
    violations++;
  } else {
    try {
      const isSymlink = lstatSync(rider).isSymbolicLink();
      if (isSymlink) {
        // Resolve and check it points to root canonical
        const target = realpathSync(rider);
        if (target !== ROOT_RIDER) {
          console.error(
            `${file}: CHARTER-RIDER.md symlink points to ${relative(REPO_ROOT, target)} but should resolve to /CHARTER-RIDER.md`,
          );
          violations++;
        }
      } else {
        // Plain file — verify content matches root canonical
        const localContent = readFileSync(rider, "utf8");
        const rootContent = readFileSync(ROOT_RIDER, "utf8");
        if (localContent !== rootContent) {
          console.error(
            `${file}: CHARTER-RIDER.md content drift from root canonical (rerun 70-tools/charter-rider-applicator/apply.sh)`,
          );
          violations++;
        }
      }
    } catch (e) {
      console.error(`${file}: cannot inspect CHARTER-RIDER.md (${e.message})`);
      violations++;
    }
  }
}

if (violations > 0) {
  console.error("");
  console.error(`✘ charter-rider-notice: ${violations} violation(s).`);
  console.error("  Per ADR-2605192200 v2.0 §3 + §4.");
  console.error("  Fix: run `./70-tools/charter-rider-applicator/apply.sh` from repo root,");
  console.error("       then re-stage the new NOTICE + CHARTER-RIDER.md files.");
  process.exit(1);
}
process.exit(0);

function lstatExists(p) {
  try {
    lstatSync(p);
    return true;
  } catch {
    return false;
  }
}
