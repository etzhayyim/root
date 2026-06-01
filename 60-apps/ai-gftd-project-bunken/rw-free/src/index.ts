/**
 * bunken rw-free — barrel.
 *
 * Per ADR-2605203000 Option B Phase E reference impl. 文献書誌 multi-scheme
 * bibliography on the etzhayyim substrate (AT PDS records; no RW).
 *
 * Slice 1: 4 of 4 canonical lexicons ported.
 *   registerRecord + getRecord + search + stats
 */

export * from "./types.js";
export { registerRecord, getRecord, search, stats } from "./registry.js";
