/**
 * Unit tests for session-topology.svelte.ts (P4).
 *
 * Invariants:
 *   - echoPersistence = 1 - distinct/total
 *   - Buffer is bounded to BUFFER_SIZE (50).
 *   - Empty buffer → echoPersistence = 0, distinctTopics = 0.
 *   - Doom-scroll threshold tightens at night (20 min) vs day (45 min).
 *   - Raw topics are NOT exposed in the snapshot.
 */
import { describe, expect, it, beforeEach } from "vitest";
import {
  recordTopicVisit,
  resetSessionTopology,
  getSessionTopology,
  isDoomScrolling,
  _testing,
} from "./session-topology.svelte";

beforeEach(() => {
  resetSessionTopology();
});

describe("getSessionTopology", () => {
  it("returns zeroes on an empty session", () => {
    const s = getSessionTopology();
    expect(s.echoPersistence).toBe(0);
    expect(s.distinctTopics).toBe(0);
    expect(s.sampleSize).toBe(0);
    expect(s.dwellMs).toBeGreaterThanOrEqual(0);
  });

  it("echoPersistence = 0 for all-distinct topics", () => {
    recordTopicVisit("tag:a");
    recordTopicVisit("tag:b");
    recordTopicVisit("tag:c");
    const s = getSessionTopology();
    expect(s.distinctTopics).toBe(3);
    expect(s.sampleSize).toBe(3);
    expect(s.echoPersistence).toBeCloseTo(0, 5);
  });

  it("echoPersistence > 0 when topics repeat", () => {
    for (let i = 0; i < 5; i++) recordTopicVisit("tag:cat");
    recordTopicVisit("tag:dog");
    const s = getSessionTopology();
    expect(s.sampleSize).toBe(6);
    expect(s.distinctTopics).toBe(2);
    // echo = 1 - 2/6 = 0.6666...
    expect(s.echoPersistence).toBeCloseTo(2 / 3, 5);
  });

  it("ignores null / empty / nullable inputs", () => {
    recordTopicVisit(null);
    recordTopicVisit(undefined);
    recordTopicVisit("");
    const s = getSessionTopology();
    expect(s.sampleSize).toBe(0);
  });

  it("caps internal buffer at BUFFER_SIZE", () => {
    for (let i = 0; i < 200; i++) recordTopicVisit(`tag:t${i}`);
    const s = getSessionTopology();
    expect(s.sampleSize).toBeLessThanOrEqual(50);
  });

  it("does not leak raw topic history through the public snapshot", () => {
    recordTopicVisit("tag:sensitive");
    const s = getSessionTopology();
    expect(Object.keys(s).sort()).toEqual([
      "distinctTopics", "dwellMs", "echoPersistence", "sampleSize",
    ]);
  });
});

describe("isDoomScrolling", () => {
  it("returns false on a fresh session", () => {
    expect(isDoomScrolling()).toBe(false);
    expect(isDoomScrolling({ stressIdx: 90 })).toBe(false);
  });

  it("triggers at 45 min during the day when stress is high", () => {
    _testing.setState({ sessionStart: Date.now() - 46 * 60 * 1000, topics: ["tag:a"] });
    expect(isDoomScrolling({ stressIdx: 80 })).toBe(true);
    expect(isDoomScrolling({ stressIdx: 50 })).toBe(false);
  });

  it("tightens to 20 min at night regardless of stress", () => {
    _testing.setState({ sessionStart: Date.now() - 21 * 60 * 1000, topics: ["tag:a"] });
    expect(isDoomScrolling({ nightMode: true, stressIdx: 0 })).toBe(true);
    expect(isDoomScrolling({ nightMode: false, stressIdx: 0 })).toBe(false);
  });
});
