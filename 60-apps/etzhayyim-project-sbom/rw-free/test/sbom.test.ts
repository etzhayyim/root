import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerArtifact,
  getArtifact,
  registerComponent,
  listComponents,
  registerVulnMatch,
  listVulnMatches,
} from "../src/index.js";

describe("sbom rw-free", () => {
  let e: any;

  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:sbom.etzhayyim.com" });
  });

  describe("registerArtifact", () => {
    it("registers an artifact with valid sha256", async () => {
      const sha256 =
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
      const result = await registerArtifact(e, {
        artifactId: "app-1.0",
        sha256,
        artifactType: "container",
        name: "MyApp",
      });

      expect(result.status).toBe("created");
      expect(result.artifactUri).toBeDefined();
    });

    it("rejects artifact with invalid sha256 (not 64 hex chars)", async () => {
      const result = await registerArtifact(e, {
        artifactId: "app-1.0",
        sha256: "invalid-sha256",
        artifactType: "container",
        name: "MyApp",
      });

      expect(result.status).toBe("rejected");
      expect(result.error).toBe("invalidSha256");
    });

    it("is idempotent on artifactId", async () => {
      const input = {
        artifactId: "app-1.0",
        sha256:
          "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        artifactType: "container",
        name: "MyApp",
      };

      const first = await registerArtifact(e, input);
      expect(first.status).toBe("created");

      const second = await registerArtifact(e, input);
      expect(second.status).toBe("alreadyExists");
    });
  });

  describe("registerComponent", () => {
    beforeEach(async () => {
      await registerArtifact(e, {
        artifactId: "app-1.0",
        sha256:
          "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        artifactType: "container",
        name: "MyApp",
      });
    });

    it("registers a component with valid artifactId", async () => {
      const result = await registerComponent(e, {
        componentId: "openssl-1.1.1",
        artifactId: "app-1.0",
        componentType: "library",
        name: "OpenSSL",
        version: "1.1.1w",
      });

      expect(result.status).toBe("created");
      expect(result.componentUri).toBeDefined();
    });

    it("rejects component without existing artifactId", async () => {
      const result = await registerComponent(e, {
        componentId: "openssl-1.1.1",
        artifactId: "nonexistent-artifact",
        componentType: "library",
        name: "OpenSSL",
        version: "1.1.1w",
      });

      expect(result.status).toBe("rejected");
      expect(result.error).toBe("artifactNotFound");
    });
  });

  describe("registerVulnMatch", () => {
    beforeEach(async () => {
      await registerArtifact(e, {
        artifactId: "app-1.0",
        sha256:
          "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        artifactType: "container",
        name: "MyApp",
      });
      await registerComponent(e, {
        componentId: "openssl-1.1.1",
        artifactId: "app-1.0",
        componentType: "library",
        name: "OpenSSL",
        version: "1.1.1w",
      });
    });

    it("registers vuln match with valid component", async () => {
      const result = await registerVulnMatch(e, {
        vulnMatchId: "vuln-1",
        componentId: "openssl-1.1.1",
        cvId: "CVE-2024-1234",
        severity: "critical",
      });

      expect(result.status).toBe("created");
      expect(result.vulnMatchUri).toBeDefined();
    });

    it("rejects vuln match for non-existent component", async () => {
      const result = await registerVulnMatch(e, {
        vulnMatchId: "vuln-1",
        componentId: "nonexistent",
        cvId: "CVE-2024-1234",
        severity: "critical",
      });

      expect(result.status).toBe("rejected");
      expect(result.error).toBe("vulnMatchNotFound");
    });
  });

  describe("listComponents", () => {
    beforeEach(async () => {
      await registerArtifact(e, {
        artifactId: "app-1.0",
        sha256:
          "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        artifactType: "container",
        name: "MyApp",
      });
      await registerComponent(e, {
        componentId: "openssl-1.1.1",
        artifactId: "app-1.0",
        componentType: "library",
        name: "OpenSSL",
        version: "1.1.1w",
      });
      await registerComponent(e, {
        componentId: "curl-7.68",
        artifactId: "app-1.0",
        componentType: "library",
        name: "curl",
        version: "7.68.0",
      });
    });

    it("lists components for artifact", async () => {
      const result = await listComponents(e, { artifactId: "app-1.0" });

      expect(result.items.length).toBe(2);
      expect(result.total).toBe(2);
    });

    it("filters by componentType", async () => {
      const result = await listComponents(e, {
        artifactId: "app-1.0",
        componentType: "library",
      });

      expect(result.items.length).toBe(2);
      expect(result.items.every((c) => c.componentType === "library")).toBe(
        true
      );
    });
  });

  describe("listVulnMatches", () => {
    beforeEach(async () => {
      await registerArtifact(e, {
        artifactId: "app-1.0",
        sha256:
          "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        artifactType: "container",
        name: "MyApp",
      });
      await registerComponent(e, {
        componentId: "openssl-1.1.1",
        artifactId: "app-1.0",
        componentType: "library",
        name: "OpenSSL",
        version: "1.1.1w",
      });
      await registerVulnMatch(e, {
        vulnMatchId: "vuln-1",
        componentId: "openssl-1.1.1",
        cvId: "CVE-2024-1234",
        severity: "critical",
      });
    });

    it("lists all vuln matches", async () => {
      const result = await listVulnMatches(e, {});

      expect(result.items.length).toBeGreaterThan(0);
    });

    it("filters vuln matches by severity", async () => {
      const result = await listVulnMatches(e, { severity: "critical" });

      expect(result.items.every((v) => v.severity === "critical")).toBe(true);
    });
  });
});
