/**
 * @etzhayyim/etzhayyim-hrse#GenerateGoBDD
 * Generate Go BDD feature files from capabilities.jsonld
 */

import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";

interface Capability {
  "@id": string;
  "@type": string;
  "rdfs:label": Array<{ "@value": string; "@language": string }>;
  "dcterms:description": Array<{ "@value": string; "@language": string }>;
  implementation?: string[];
}

interface CapabilitiesJSONLD {
  "@graph": Capability[];
}

function generateGoBDDFeature(capability: Capability): string {
  const capabilityID = capability["@id"];
  const label = capability["rdfs:label"]?.find(l => l["@language"] === "en")?.["@value"] || capabilityID;
  const description = capability["dcterms:description"]?.find(d => d["@language"] === "en")?.["@value"] || "";

  return `# @etzhayyim/etzhayyim-hrse#${capabilityID}BDD
# BDD Feature: ${label}
# ${description}

Feature: ${label}
  As a system user
  I want to use ${label}
  So that I can achieve the capability

  Background:
    Given the database is available
    And the service is initialized

  Scenario: ${label} should work correctly
    Given I am a valid user
    When I call the ${capabilityID} capability
    Then the operation should succeed
    And the result should be valid

  Scenario: ${label} should handle errors gracefully
    Given I am a valid user
    When I call the ${capabilityID} capability with invalid input
    Then the operation should fail
    And an appropriate error should be returned
`;
}

function main() {
  const capabilitiesPath = join(process.cwd(), "capabilities.jsonld");
  const capabilitiesData = readFileSync(capabilitiesPath, "utf-8");
  const capabilities: CapabilitiesJSONLD = JSON.parse(capabilitiesData);

  const outputDir = join(process.cwd(), "features", "go");
  mkdirSync(outputDir, { recursive: true });

  for (const capability of capabilities["@graph"]) {
    if (capability["@type"] !== "Capability") {
      continue;
    }

    const featureCode = generateGoBDDFeature(capability);
    const featureFileName = `${capability["@id"].toLowerCase().replace("capability", "")}.feature`;
    const featureFilePath = join(outputDir, featureFileName);

    writeFileSync(featureFilePath, featureCode, "utf-8");
    console.log(`Generated: ${featureFilePath}`);
  }
}

main();
