/**
 * robot kotoba — barrel. kotoba-E2E split: public robot product catalog
 * plaintext + confidential customer orders sealed via kotoba E2E
 * (sdk.encryptedWrite/Read, ADR-2605181100). Fiat settlement / robot motion /
 * KAMI inference EXECUTION stay etzhayyim via consent-capability.
 */
export * from "./types.js";
export {
  registerProduct,
  getProduct,
  listProducts,
  placeOrder,
  listOrders,
  getOrder,
  coverage,
} from "./registry.js";
