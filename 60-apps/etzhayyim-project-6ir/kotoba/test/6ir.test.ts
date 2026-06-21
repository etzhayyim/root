import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  defineCompany,
  getCompany,
  listCompanies,
  addFiling,
  getFiling,
  listFilings,
  recordEarnings,
  listEarnings,
  submitAnalysis,
  listAnalyses,
  coverage,
} from "../src/index.js";

const ANALYST = "did:web:analyst.example.com";

describe("6ir kotoba", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:6ir.etzhayyim.com" });
  });

  describe("company directory", () => {
    it("defines, reads, idempotent, app-layer search, rejects bad ticker", async () => {
      expect((await defineCompany(e, { ticker: "aapl", name: "Apple Inc.", exchange: "NASDAQ", sector: "Tech" })).status).toBe("defined");
      expect((await getCompany(e, { ticker: "AAPL" })).company?.name).toBe("Apple Inc.");
      expect((await defineCompany(e, { ticker: "AAPL", name: "dup" })).status).toBe("alreadyExists");
      await defineCompany(e, { ticker: "MSFT", name: "Microsoft Corp.", exchange: "NASDAQ", sector: "Tech" });
      expect((await listCompanies(e, { sector: "Tech" })).total).toBe(2);
      expect((await listCompanies(e, { q: "micro" })).total).toBe(1);
      expect((await defineCompany(e, { ticker: "bad ticker!", name: "x" })).status).toBe("rejected");
    });
  });

  describe("filings / earnings / coverage against a company", () => {
    beforeEach(async () => {
      await defineCompany(e, { ticker: "AAPL", name: "Apple Inc." });
    });
    it("adds filings (FK), validates form type + missing company", async () => {
      expect((await addFiling(e, { filingId: "F-1", ticker: "AAPL", formType: "10-K", filedAt: "2026-01-31" })).status).toBe("added");
      expect((await getFiling(e, { filingId: "F-1" })).filing?.formType).toBe("10-K");
      expect((await addFiling(e, { filingId: "F-2", ticker: "AAPL", formType: "BOGUS" as any, filedAt: "2026-01-31" })).status).toBe("rejected");
      expect((await addFiling(e, { filingId: "F-3", ticker: "GHOST", formType: "8-K", filedAt: "2026-01-31" })).status).toBe("companyNotFound");
      await addFiling(e, { filingId: "F-4", ticker: "AAPL", formType: "10-Q", filedAt: "2026-04-30" });
      expect((await listFilings(e, { ticker: "AAPL", formType: "10-Q" })).total).toBe(1);
      expect((await listFilings(e, { since: "2026-03-01" })).total).toBe(1);
    });
    it("records earnings with signed EPS micros; rejects bad amounts + missing company", async () => {
      expect((await recordEarnings(e, { earningsId: "Q-1", ticker: "AAPL", fiscalPeriod: "2026Q1", reportedAt: "2026-01-31", epsMicros: "1230000", revenueMicros: "94000000000000" })).status).toBe("recorded");
      // negative EPS allowed
      expect((await recordEarnings(e, { earningsId: "Q-2", ticker: "AAPL", fiscalPeriod: "2026Q2", reportedAt: "2026-04-30", epsMicros: "-50000", revenueMicros: "80000000000000" })).status).toBe("recorded");
      // negative revenue rejected
      expect((await recordEarnings(e, { earningsId: "Q-3", ticker: "AAPL", fiscalPeriod: "2026Q3", reportedAt: "2026-07-31", epsMicros: "1", revenueMicros: "-1" })).status).toBe("rejected");
      // float rejected
      expect((await recordEarnings(e, { earningsId: "Q-4", ticker: "AAPL", fiscalPeriod: "2026Q4", reportedAt: "2026-10-31", epsMicros: "1.5", revenueMicros: "1" })).status).toBe("rejected");
      expect((await recordEarnings(e, { earningsId: "Q-5", ticker: "GHOST", fiscalPeriod: "2026Q1", reportedAt: "x", epsMicros: "1", revenueMicros: "1" })).status).toBe("companyNotFound");
      expect((await listEarnings(e, { ticker: "AAPL" })).total).toBe(2);
    });
    it("submits analyst coverage (FK + rating + analyst DID) and rolls up coverage", async () => {
      expect((await submitAnalysis(e, { analysisId: "A-1", ticker: "AAPL", analystDid: ANALYST, rating: "buy", priceTargetMicros: "250000000" })).status).toBe("submitted");
      expect((await submitAnalysis(e, { analysisId: "A-2", ticker: "AAPL", analystDid: ANALYST, rating: "hold" })).status).toBe("submitted");
      expect((await submitAnalysis(e, { analysisId: "A-X", ticker: "AAPL", analystDid: ANALYST, rating: "moon" as any })).status).toBe("rejected");
      expect((await submitAnalysis(e, { analysisId: "A-Y", ticker: "AAPL", analystDid: "nope", rating: "buy" })).status).toBe("rejected");
      expect((await listAnalyses(e, { ticker: "AAPL", rating: "buy" })).total).toBe(1);

      await addFiling(e, { filingId: "F-1", ticker: "AAPL", formType: "10-K", filedAt: "2026-01-31" });
      await recordEarnings(e, { earningsId: "Q-1", ticker: "AAPL", fiscalPeriod: "2026Q1", reportedAt: "2026-01-31", epsMicros: "1230000", revenueMicros: "94000000000000" });
      const cov = await coverage(e);
      expect(cov.companyCount).toBe(1);
      expect(cov.filingCount).toBe(1);
      expect(cov.earningsCount).toBe(1);
      expect(cov.analysisCount).toBe(2);
      expect(cov.filingsByForm?.["10-K"]).toBe(1);
      expect(cov.analysesByRating?.buy).toBe(1);
      expect(cov.analysesByRating?.hold).toBe(1);
    });
  });
});
