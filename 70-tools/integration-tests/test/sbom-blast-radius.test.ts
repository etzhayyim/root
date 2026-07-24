import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerAsn,
  registerPrefix,
  registerIp,
} from "@etzhayyim/ipaddress-kotoba";
import {
  registerArtifact,
  registerComponent,
  cveIngestOsv,
  registerVulnMatch,
} from "@etzhayyim/sbom-kotoba";

// TODO: sbom registerArtifact validation pending full SBOM format implementation.
// Test requires correct SBOM artifact structure and validation logic from sbom actor.
describe.skip("sbom CVE blast-radius pipeline", () => {
  let e: any;

  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:multi-actor.test" });
  });

  it("traces sbom artifact → component → CVE → affected app via ipaddress host attribution", async () => {
    // Stage 1: ipaddress — register ASN (Cloudflare)
    const asnResult = await registerAsn(e, {
      number: 13335,
      name: "Cloudflare",
      country: "USA",
      rir: "arin",
      prefixes: ["1.1.1.0/24"],
    });
    expect(asnResult.status).toBe("registered");
    expect(asnResult.did).toBeDefined();

    // Stage 2: ipaddress — register prefix
    const prefixResult = await registerPrefix(e, {
      cidr: "1.1.1.0/24",
      asnNumber: 13335,
    });
    expect(prefixResult.status).toBe("registered");

    // Stage 3: ipaddress — register IP in prefix
    const ipResult = await registerIp(e, {
      address: "1.1.1.1",
      asnNumber: 13335,
      prefixCidr: "1.1.1.0/24",
    });
    expect(ipResult.status).toBe("registered");

    // Stage 4: sbom — register artifact (SBOM for app)
    const artifactResult = await registerArtifact(e, {
      sha256: "a1b2c3d4e5f6789012345678901234567890abcd1234567890abcdef123456",
      format: "cyclonedx-1.5",
      builtForAppDid: "did:web:yata.etzhayyim.com:app:ameno",
      componentCount: 247,
    });
    expect(artifactResult.status).toBe("registered");
    expect(artifactResult.did).toBeDefined();

    // Stage 5: sbom — register component in artifact
    const componentResult = await registerComponent(e, {
      purl: "pkg:npm/lodash@4.17.21",
      name: "lodash",
      version: "4.17.21",
      ecosystem: "npm",
      artifactDid: artifactResult.did!,
    });
    expect(componentResult.status).toBe("registered");

    // Stage 6: sbom — ingest CVE via OSV
    const cveIngestResult = await cveIngestOsv(e, {
      cveId: "CVE-2026-12345",
      osvPayload: {
        summary: "Prototype pollution in lodash utility",
        severity: "critical",
        cvssPermille: 950,
      },
    });
    expect(cveIngestResult.status).toBe("ingested");

    // Stage 7: sbom — register vulnerability match
    const vulnResult = await registerVulnMatch(e, {
      cveId: "CVE-2026-12345",
      componentPurl: "pkg:npm/lodash@4.17.21",
      severity: "critical",
      cvssPermille: 950,
      affectedAppDid: "did:web:yata.etzhayyim.com:app:ameno",
    });
    expect(vulnResult.status).toBe("registered");
    expect(vulnResult.did).toBeDefined();

    // Verify ipaddress and sbom records coexist in store
    const asnCount = e.count("com.etzhayyim.ipaddress.asn");
    const prefixCount = e.count("com.etzhayyim.ipaddress.prefix");
    const ipCount = e.count("com.etzhayyim.ipaddress.ip");
    const sbomArtifactCount = e.count("com.etzhayyim.sbom.artifact");
    const sbomComponentCount = e.count("com.etzhayyim.sbom.component");

    expect(asnCount).toBeGreaterThanOrEqual(1);
    expect(prefixCount).toBeGreaterThanOrEqual(1);
    expect(ipCount).toBeGreaterThanOrEqual(1);
    expect(sbomArtifactCount).toBeGreaterThanOrEqual(1);
    expect(sbomComponentCount).toBeGreaterThanOrEqual(1);

    // Verify actor isolation
    expect(asnResult.did).toContain("ipaddress");
    expect(artifactResult.did).toContain("sbom");
    expect(vulnResult.did).toContain("sbom");
  });
});
