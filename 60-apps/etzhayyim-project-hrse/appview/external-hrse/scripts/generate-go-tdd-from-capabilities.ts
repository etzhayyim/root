/**
 * @etzhayyim/etzhayyim-hrse#GenerateGoTDD
 * Generate Go TDD tests from capabilities.jsonld
 */

import { readFileSync, writeFileSync } from "fs";
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

function generateGoTDDTest(capability: Capability): string {
  const capabilityID = capability["@id"];
  const capabilityName = capabilityID.replace("Capability", "");
  const testName = `${capabilityName}Test`;

  const label = capability["rdfs:label"]?.find(l => l["@language"] === "en")?.["@value"] || capabilityID;
  const description = capability["dcterms:description"]?.find(d => d["@language"] === "en")?.["@value"] || "";

  return `// @etzhayyim/etzhayyim-hrse#${capabilityID}TDD
// TDD Tests for ${label}
// ${description}
package service

import (
	"context"
	"testing"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// Test${testName} tests ${label}
func Test${testName}(t *testing.T) {
	pool := setupTestDB(t)
	if pool == nil {
		return
	}
	defer pool.Close()

	ctx := context.Background()

	t.Run("should implement ${capabilityID}", func(t *testing.T) {
		t.Skip("Test not yet implemented")
	})
}
`;
}

function main() {
  const capabilitiesPath = join(process.cwd(), "capabilities.jsonld");
  const capabilitiesData = readFileSync(capabilitiesPath, "utf-8");
  const capabilities: CapabilitiesJSONLD = JSON.parse(capabilitiesData);

  const outputDir = join(process.cwd(), "pkg", "service");

  for (const capability of capabilities["@graph"]) {
    if (capability["@type"] !== "Capability") {
      continue;
    }

    const testCode = generateGoTDDTest(capability);
    const testFileName = `${capability["@id"].toLowerCase().replace("capability", "")}_test.go`;
    const testFilePath = join(outputDir, testFileName);

    writeFileSync(testFilePath, testCode, "utf-8");
    console.log(`Generated: ${testFilePath}`);
  }
}

main();
