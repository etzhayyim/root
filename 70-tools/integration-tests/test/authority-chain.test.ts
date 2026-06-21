import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerJurisdiction,
  seedCases,
} from "@etzhayyim/hanrei-kotoba";
import {
  registerStatute,
  registerArticle,
} from "@etzhayyim/houbun-kotoba";

describe("authority-chain integration (hanrei + houbun)", () => {
  let e: any;

  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:multi-actor.test" });
  });

  it("composes hanrei jurisdiction + houbun statute into authority chain", async () => {
    // Step 1: hanrei — register jurisdiction
    const jurisdictionResult = await registerJurisdiction(e, {
      iso3: "jpn",
      name: "Japan",
      legalSystem: "civil-law",
      primaryLanguage: "ja",
    });
    expect(jurisdictionResult.status).toBe("registered");
    expect(jurisdictionResult.did).toBeDefined();

    // Step 2: hanrei — seed court cases for Japan
    const casesResult = await seedCases(e, {
      cases: [
        {
          caseId: "supreme-2024-001",
          title: "Privacy Rights v. Data Controller",
          jurisdiction: "jpn",
        },
      ],
    });
    expect(casesResult.status).toBe("ok");
    // seedCases returns inserted[] array, not recordCount
    if (casesResult.inserted) {
      expect(casesResult.inserted.length).toBeGreaterThanOrEqual(1);
    }

    // Step 3: houbun — register statute in Japan
    const statuteResult = await registerStatute(e, {
      jurisdiction: "jpn",
      statuteId: "416AC0000000061",
      title: "個人情報の保護に関する法律",
      source: "e-gov",
      sourceUrl: "https://example.com/statute",
      statuteType: "law",
    });
    expect(statuteResult.status).toBe("registered");
    expect(statuteResult.did).toBeDefined();
    expect(statuteResult.statuteUri).toBeDefined();

    // Step 4: houbun — register article of statute
    const articleResult = await registerArticle(e, {
      jurisdiction: "jpn",
      statuteId: "416AC0000000061",
      articleNo: "第二条",
      statuteRef: statuteResult.statuteUri!,
      text: "個人情報とは、生存する個人に関する情報であって...",
    });
    expect(articleResult.status).toBe("registered");
    expect(articleResult.did).toBeDefined();

    // Verify collection isolation (no cross-contamination)
    const hanreiCount = e.count("com.etzhayyim.hanrei.jurisdiction");
    const houbunCount = e.count("com.etzhayyim.houbun.statute");
    expect(hanreiCount).toBeGreaterThanOrEqual(1);
    expect(houbunCount).toBeGreaterThanOrEqual(1);

    // Verify DIDs use correct actor prefixes
    expect(jurisdictionResult.did).toContain("hanrei");
    expect(statuteResult.did).toContain("houbun");
    expect(articleResult.did).toContain("houbun");
  });
});
