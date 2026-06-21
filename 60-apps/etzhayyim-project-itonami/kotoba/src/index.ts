/**
 * itonami kotoba — barrel.
 *
 * Per ADR-2606011400. Aircraft-engine lifecycle SIMULATION (engine designs +
 * assembly + procurement + tests) on the etzhayyim substrate (AT PDS records;
 * no RW).
 *
 *   engine      : defineEngine / setCertification / getEngine / listEngines
 *   assembly    : recordAssembly (FK→engine, per-mille progress) / listAssemblies
 *   procurement : addProcurement (FK→engine, UNSPSC/ISIC) / listProcurement
 *   test        : recordTest (FK→engine) / listTests
 *   coverage
 *
 * Engineering simulation data; all values integerized (thrust kN×100, per-mille).
 */

export * from "./types.js";
export {
  defineEngine,
  setCertification,
  getEngine,
  listEngines,
  recordAssembly,
  listAssemblies,
  addProcurement,
  listProcurement,
  recordTest,
  listTests,
  coverage,
} from "./registry.js";
