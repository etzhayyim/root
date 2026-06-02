import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  createTitle,
  getTitle,
  listTitles,
  createSeason,
  createEpisode,
  listEpisodes,
  submitReview,
} from "../src/index.js";

describe("anime rw-free", () => {
  let e: any;

  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:anime.etzhayyim.com" });
  });

  describe("createTitle", () => {
    it("creates a new anime title with valid input", async () => {
      const result = await createTitle(e, {
        titleId: "naruto",
        title: "Naruto",
        titleJa: "ナルト",
        genre: "action",
      });

      expect(result.status).toBe("registered");
      expect(result.did).toBeDefined();
      expect(result.titleUri).toBeDefined();
      expect(result.titleId).toBe("naruto");
    });

    it("rejects title creation with missing titleId", async () => {
      const result = await createTitle(e, {
        titleId: "",
        title: "Test Anime",
      });

      expect(result.status).toBe("rejected");
      expect(result.error).toBe("invalidTitleId");
    });

    it("is idempotent on titleId", async () => {
      const input = {
        titleId: "bleach",
        title: "Bleach",
        genre: "action",
      };

      const first = await createTitle(e, input);
      expect(first.status).toBe("registered");
      const firstDid = first.did;

      const second = await createTitle(e, input);
      expect(second.status).toBe("alreadyExists");
      expect(second.did).toBe(firstDid);
    });
  });

  describe("createEpisode + submitReview invariants", () => {
    beforeEach(async () => {
      await createTitle(e, {
        titleId: "jjk",
        title: "Jujutsu Kaisen",
      });
      await createSeason(e, {
        seasonId: "jjk-s1",
        titleId: "jjk",
        seasonNum: 1,
        year: 2020,
        episodeCount: 24,
      });
    });

    it("creates episode under existing season", async () => {
      const result = await createEpisode(e, {
        episodeId: "jjk-ep1",
        seasonId: "jjk-s1",
        episodeNum: 1,
        title: "Ep 1",
        durationSec: 1440,
      });

      expect(result.status).toBe("registered");
      expect(result.episodeUri).toBeDefined();
    });

    it("rejects episode creation without seasonId", async () => {
      const result = await createEpisode(e, {
        episodeId: "jjk-ep1",
        seasonId: "",
        episodeNum: 1,
        title: "Ep 1",
        durationSec: 1440,
      });

      expect(result.status).toBe("rejected");
      expect(result.error).toBe("missingSeasonId");
    });

    it("submitReview enforces ratingPermille bounds (0-1000)", async () => {
      const validReview = await submitReview(e, {
        reviewId: "review-1",
        titleId: "jjk",
        seq: 1,
        reviewerDid: "did:plc:reviewer",
        rating: 750,
        body: "Great anime!",
      });

      expect(validReview.status).toBe("registered");

      const invalidHigh = await submitReview(e, {
        reviewId: "review-2",
        titleId: "jjk",
        seq: 2,
        reviewerDid: "did:plc:reviewer2",
        rating: 1001,
        body: "Bad rating",
      });

      expect(invalidHigh.status).toBe("rejected");
      expect(invalidHigh.error).toBe("invalidRating");

      const invalidLow = await submitReview(e, {
        reviewId: "review-3",
        titleId: "jjk",
        seq: 3,
        reviewerDid: "did:plc:reviewer3",
        rating: -1,
        body: "Bad rating",
      });

      expect(invalidLow.status).toBe("rejected");
      expect(invalidLow.error).toBe("invalidRating");
    });
  });

  describe("listEpisodes filter", () => {
    beforeEach(async () => {
      await createTitle(e, {
        titleId: "mha",
        title: "My Hero Academia",
      });
      await createSeason(e, {
        seasonId: "mha-s1",
        titleId: "mha",
        seasonNum: 1,
        year: 2016,
        episodeCount: 13,
      });
      await createEpisode(e, {
        episodeId: "mha-1-1",
        seasonId: "mha-s1",
        episodeNum: 1,
        title: "Ep 1",
        durationSec: 1440,
      });
      await createEpisode(e, {
        episodeId: "mha-1-2",
        seasonId: "mha-s1",
        episodeNum: 2,
        title: "Ep 2",
        durationSec: 1440,
      });
    });

    it("lists episodes by seasonId", async () => {
      const result = await listEpisodes(e, { seasonId: "mha-s1" });
      expect(result.episodes.length).toBe(2);
      expect(result.episodes.every((ep) => ep.seasonId === "mha-s1")).toBe(
        true
      );
    });

    it("respects limit parameter", async () => {
      const result = await listEpisodes(e, { seasonId: "mha-s1", limit: 1 });
      expect(result.episodes.length).toBeLessThanOrEqual(1);
    });
  });
});
