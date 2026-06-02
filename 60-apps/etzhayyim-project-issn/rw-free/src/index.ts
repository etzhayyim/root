/**
 * issn rw-free — barrel.
 *
 * Per ADR-2605203000 Option B Phase E reference impl. ISO 3297 ISSN serial
 * registry with mod-11 check-digit validation. Sibling of isbn rw-free.
 *
 * Slice 1: 4 of 4 canonical lexicons ported.
 *   registerSerial + lookup + listSerials + coverage
 */

export * from "./types.js";
export {
  registerSerial,
  lookup,
  listSerials,
  coverage,
} from "./registry.js";
