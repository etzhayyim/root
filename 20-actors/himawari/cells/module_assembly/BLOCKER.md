# module_assembly — Port Blocker

**Status**: NOT PORTED (complex logic, defer to next pass)

**Reason**: This cell (434 lines) has 3 load-bearing dependencies that make faithful porting difficult in isolation:

1. **Cryptographic operations** (hashlib/hmac/json): The per-module signature is a deterministic HMAC over a canonical JSON digest. While cljc can do this, the JSON canonicalization must be BYTE-IDENTICAL to Python's `json.dumps(sort_keys=True, separators=(",", ":"))`  — floating-point formatting differences could break reproducibility. This requires either (a) porting the exact JSON canonicalizer or (b) verifying equivalence against Python test vectors.

2. **Lexicon #robotSignature witness objects**: The cell normalizes a complex nested structure (raw robot entries → #robotSignature objects, each with role/timestamp optionals). The grammar is intricate and interleaves with the module signature binding — a faithful port risks silent divergence if witness binding differs.

3. **kotoba datalog query integration** (ADR-2605312345): The cell does a live `datalog.query()` to verify the feedstock lot exists. In local dev this degrades to a no-op, but the production semantics are critical (G11 traceability cannot be faked). The cljc port must preserve the fallback semantics exactly.

**Recommendation**: Port this cell in a dedicated 2nd pass that:
- Includes JSON canonicalization round-trip test vectors (Python ↔ Clojure)
- Verifies HMAC digest equivalence with Python reference signatures
- Ensures fallback modes (no datalog host binding) match the Python behavior exactly
- Tests against the existing Python test suite via a bridge

**Accepted for next wave**: module_assembly (also polysilicon_refine, outbound_logistics, supply_procurement).
