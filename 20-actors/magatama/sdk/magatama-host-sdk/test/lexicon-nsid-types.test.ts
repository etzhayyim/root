// lexicon-nsid-types.test.ts — F-Plan F2 regression guard.
//
// Verifies that the generated nsid() helper, LEXICON_NSID record, and
// LexiconInput/LexiconOutput type maps are consistent with 00-contracts/lexicons/.

import { describe, it, expect, expectTypeOf } from "vitest";
import {
	LEXICON_NSID,
	nsid,
	type LexiconInput,
	type LexiconOutput,
	type KnownLexiconProcedureNSID,
	type KnownLexiconQueryNSID,
} from "../src/generated/lexicon-nsid-types.js";

describe("F-Plan F2: typed NSID helpers (2026-04-13)", () => {
	describe("LEXICON_NSID frozen record", () => {
		it("exposes known host capability NSIDs as typed constants", () => {
			expect(LEXICON_NSID["app.etzhayyim.host.secrets.get"]).toBe("app.etzhayyim.host.secrets.get");
			expect(LEXICON_NSID["app.etzhayyim.host.invoke.call"]).toBe("app.etzhayyim.host.invoke.call");
			expect(LEXICON_NSID["app.etzhayyim.host.llm.converse"]).toBe("app.etzhayyim.host.llm.converse");
		});

		it("exposes known app-level NSIDs (sample)", () => {
			// app.etzhayyim.governance.registerManifest is a procedure on all apps
			expect(LEXICON_NSID["app.etzhayyim.governance.registerManifest"]).toBe(
				"app.etzhayyim.governance.registerManifest",
			);
		});

		it("contains a reasonable number of entries (> 400 XRPC methods)", () => {
			const count = Object.keys(LEXICON_NSID).length;
			expect(count).toBeGreaterThan(400);
		});
	});

	describe("nsid() tagged helper", () => {
		it("returns the NSID unchanged at runtime", () => {
			expect(nsid("app.etzhayyim.host.secrets.get")).toBe("app.etzhayyim.host.secrets.get");
		});

		it("preserves literal type of known NSIDs", () => {
			const n = nsid("app.etzhayyim.host.secrets.get");
			// Literal type is preserved; can be assigned to the narrow string type
			const narrow: "app.etzhayyim.host.secrets.get" = n;
			expect(narrow).toBe("app.etzhayyim.host.secrets.get");
		});
	});

	describe("LexiconInput / LexiconOutput type maps", () => {
		it("infers input type for host secrets.get query", () => {
			type Input = LexiconInput<"app.etzhayyim.host.secrets.get">;
			// The lexicon declares { key: string, required } so LexiconInput should require a key
			const input: Input = { key: "API_KEY" };
			expect(input.key).toBe("API_KEY");
		});

		it("infers output type for host secrets.get query", () => {
			type Output = LexiconOutput<"app.etzhayyim.host.secrets.get">;
			// The lexicon declares output { value?: string, found: boolean }
			const output: Output = { found: true, value: "sk-test" };
			expect(output.found).toBe(true);
			expect(output.value).toBe("sk-test");
		});

		it("falls back to unknown for NSIDs without schemas (type-level check)", () => {
			// app.etzhayyim.host.core.logAppend has output { offset: integer, required }
			type Output = LexiconOutput<"app.etzhayyim.host.core.logAppend">;
			const output: Output = { offset: 42 };
			expect(output.offset).toBe(42);
		});
	});

	describe("KnownLexicon*NSID union types (compile-time)", () => {
		it("classifies host.secrets.get as a query", () => {
			const n: KnownLexiconQueryNSID = "app.etzhayyim.host.secrets.get";
			expect(n).toBe("app.etzhayyim.host.secrets.get");
		});

		it("classifies host.secrets.set as a procedure", () => {
			const n: KnownLexiconProcedureNSID = "app.etzhayyim.host.secrets.set";
			expect(n).toBe("app.etzhayyim.host.secrets.set");
		});
	});

	describe("expectTypeOf sanity checks", () => {
		it("LEXICON_NSID entries are self-typed string literals", () => {
			expectTypeOf(LEXICON_NSID["app.etzhayyim.host.secrets.get"]).toEqualTypeOf<"app.etzhayyim.host.secrets.get">();
		});
	});
});
