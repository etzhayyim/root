// Spirit tensegrity matching — Kawasaki et al. 2026
// P(w_O|w_I) = exp(w_I·w_O) × r^α × exp(γ·ΔSP/λ) × exp(η·F) / Z

import type { SpiritType } from "./spirit-types";

// 5D positive emotion basis projected from Hume 10D:
// [joy, calm, focus, awe, surprise] — growth & resonance axes
// Input values expected in permille [0, 1000]; normalized to [0, 1] internally.
export type EmotionVec5 = [number, number, number, number, number];

// Archetype prototypes in 5D emotion space (derived from Jung analytical psychology)
export const SPIRIT_PROTOTYPES: Record<SpiritType, EmotionVec5> = {
  Hero:      [0.72, 0.50, 0.88, 0.62, 0.74],
  Sage:      [0.42, 0.88, 0.82, 0.78, 0.33],
  Lover:     [0.84, 0.54, 0.44, 0.72, 0.68],
  Caregiver: [0.68, 0.82, 0.48, 0.64, 0.38],
};

// Complementary pairs: Hero↔Caregiver (protection↔nurture), Sage↔Lover (thought↔feeling)
const COMPLEMENT: Partial<Record<SpiritType, SpiritType>> = {
  Hero: "Caregiver", Caregiver: "Hero",
  Sage: "Lover",     Lover: "Sage",
};

// RBF kernel: W_ij = exp(-||e_i - e_j||² / 2σ²)
function rbf(a: EmotionVec5, b: EmotionVec5, sigma: number): number {
  const distSq = a.reduce((sum, v, i) => sum + (v - b[i]) ** 2, 0);
  return Math.exp(-distSq / (2 * sigma * sigma));
}

export interface MatchBreakdown {
  total: number;       // 0–1, clamped
  uSpirit: number;     // archetype proximity (RBF σ=0.8)
  uResonance: number;  // emotion vector resonance (RBF σ=0.4)
  complementBonus: number; // 1.25 if complementary types, 1.0 otherwise
  score1000: number;   // total × 1000, rounded
}

export function computeMatch(
  typeA: SpiritType, emotionA: EmotionVec5,
  typeB: SpiritType, emotionB: EmotionVec5,
): MatchBreakdown {
  const uSpirit    = rbf(SPIRIT_PROTOTYPES[typeA], SPIRIT_PROTOTYPES[typeB], 0.8);
  const uResonance = rbf(emotionA, emotionB, 0.4);
  const complementBonus = COMPLEMENT[typeA] === typeB ? 1.25 : 1.0;
  const total = Math.min(1, uSpirit * uResonance * complementBonus);
  return { total, uSpirit, uResonance, complementBonus, score1000: Math.round(total * 1000) };
}

// Convert 10D Hume permille centroid → 5D emotion basis [joy, calm, focus, awe, surprise]
export function toVec5(centroid10d: number[]): EmotionVec5 {
  const get = (i: number) => (centroid10d[i] ?? 0) / 1000;
  // indices per HUME_EMOTION_KEYS: joy=0, calm=5, focus=6, awe=9, surprise=7
  return [get(0), get(5), get(6), get(9), get(7)];
}

// Generate a plausible demo emotion vector for a given Spirit type (±15% jitter)
export function demoVec(type: SpiritType, seed = 0): EmotionVec5 {
  const proto = SPIRIT_PROTOTYPES[type];
  return proto.map((v, i) => {
    const jitter = Math.sin(seed * 7.3 + i * 3.1) * 0.12;
    return Math.max(0.05, Math.min(0.98, v + jitter));
  }) as EmotionVec5;
}

// Pentagon SVG path for a 5D emotion vector (r = radius, cx/cy = center)
export function pentagonPath(vec: EmotionVec5, r: number, cx: number, cy: number): string {
  const points = vec.map((v, i) => {
    const angle = (i * 2 * Math.PI) / 5 - Math.PI / 2;
    const d = v * r;
    return `${(cx + d * Math.cos(angle)).toFixed(2)},${(cy + d * Math.sin(angle)).toFixed(2)}`;
  });
  return `M ${points.join(" L ")} Z`;
}

// Grid ring paths (3 rings at 33%, 66%, 100%)
export function gridRings(r: number, cx: number, cy: number): string[] {
  return [0.33, 0.66, 1.0].map((frac) => {
    const pts = Array.from({ length: 5 }, (_, i) => {
      const angle = (i * 2 * Math.PI) / 5 - Math.PI / 2;
      const d = frac * r;
      return `${(cx + d * Math.cos(angle)).toFixed(2)},${(cy + d * Math.sin(angle)).toFixed(2)}`;
    });
    return `M ${pts.join(" L ")} Z`;
  });
}
