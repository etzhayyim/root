/**
 * ipaddress rw-free — barrel.
 *
 * Per ADR-2605203000 Option B Phase E reference implementation.
 * NOT a Worker. Pure TS module to be wired into an XRPC handler
 * (see open-isco rw-free seed.ts/query.ts CLI pattern + tsukuru
 * rw-free for a more complete shape).
 *
 * Initial slice: 2 of 37 ipaddress XRPC commands ported.
 *   registerAsn + getAsn  — ASN tier of the RIR/NIR/Provider/ASN/
 *                            Prefix/IP authority chain
 *
 * Remaining 35 commands follow the same Option B pattern and ship
 * in follow-up slices.
 */

export * from "./types.js";
export { registerAsn, getAsn } from "./asnRegistry.js";
export {
  registerPrefix,
  getPrefix,
  registerProvider,
  getProvider,
} from "./prefixRegistry.js";
export { registerIp, getIp } from "./ipRegistry.js";
export { registerScan, getScan, listScans } from "./scanRegistry.js";
export {
  searchProviders,
  listProviders,
  listPrefixes,
} from "./search.js";
export {
  getDelegationChain,
  getIpTopology,
  getPeering,
} from "./topology.js";
export { getGeolocation, getAbuseContact } from "./geoAbuse.js";
