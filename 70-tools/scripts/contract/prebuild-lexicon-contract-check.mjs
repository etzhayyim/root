#!/usr/bin/env node

import { execFileSync } from "node:child_process";

function runCheck(label, scriptPath) {
  try {
    execFileSync("node", [scriptPath], { stdio: "inherit" });
  } catch (error) {
    console.error(`\nBUILD BLOCKER: ${label} failed`);
    process.exit(1);
  }
}

runCheck("lexicon nsid type generation", "70-tools/scripts/contract/gen-lexicon-nsid-types.mjs");
runCheck("lexicon primary type validation", "70-tools/scripts/lint/lexicon-primary-types.mjs");
runCheck("NSID/Lexicon registration validation", "70-tools/scripts/lint/nsid-lexicon-registration.mjs");
runCheck("legacy PDS/graph NSID validation", "70-tools/scripts/lint/no-legacy-pds-nsid.mjs");
runCheck("dependency boundary type-check", "70-tools/scripts/contract/prebuild-dependency-boundary-type-check.mjs");

console.log("prebuild lexicon contract checks: OK");
