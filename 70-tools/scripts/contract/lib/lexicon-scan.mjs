// lexicon-scan.mjs — Shared library for Lexicon JSON codegen scripts.
//
// F-Plan 2026-04-13: D step. Shared between gen-host-client-from-lexicon.mjs and
// gen-service-from-lexicon.mjs to avoid duplicating scan + JSON schema → TS emission.
//
// Each consumer script handles its own output template (host: BindingTransport dispatcher;
// service: atQuery/atProcedure XRPC transport) and any script-specific naming rules.

import { existsSync, readFileSync, readdirSync } from "node:fs";
import path from "node:path";

/**
 * Recursively scan a directory for AT Protocol Lexicon JSON files.
 * Returns lexicons sorted by id (NSID).
 *
 * Lexicon files are JSON with `{ lexicon: 1, id: "...", defs: { main: { type: "..." } } }`.
 * Files that don't match this shape are silently skipped (allows registry/schema files
 * to coexist in the same tree).
 *
 * @param {string} dir Absolute or relative directory to walk.
 * @returns {Array<{ path: string, id: string, lexicon: number, defs: object }>}
 */
export function scanLexicons(dir) {
	const results = [];
	if (!existsSync(dir)) return results;
	function walk(d) {
		for (const entry of readdirSync(d, { withFileTypes: true })) {
			const full = path.join(d, entry.name);
			if (entry.isDirectory()) {
				if (entry.name === "archive" || entry.name === "_archive") continue;
				walk(full);
			} else if (entry.name.endsWith(".json")) {
				try {
					const json = JSON.parse(readFileSync(full, "utf8"));
					if (json.lexicon === 1 && json.id && json.defs?.main?.type) {
						results.push({ path: full, ...json });
					}
				} catch {
					// skip invalid JSON
				}
			}
		}
	}
	walk(dir);
	return results.sort((a, b) => a.id.localeCompare(b.id));
}

/**
 * Convert a JSON schema fragment into a TypeScript type literal.
 * Bounded recursion (depth ≤ 2) to keep generated types readable.
 *
 * - object → `{ k: T; ... }` with `?` on non-required keys
 * - array  → `T[]`
 * - string/number/integer/boolean → primitive
 * - $ref / unknown → `unknown`
 *
 * @param {object|null|undefined} schema
 * @param {number} depth
 * @returns {string}
 */
export function jsonSchemaToTs(schema, depth = 0) {
	if (!schema) return "unknown";
	if (schema.$ref) return "unknown";
	switch (schema.type) {
		case "string":
			return "string";
		case "integer":
		case "number":
			return "number";
		case "boolean":
			return "boolean";
		case "array":
			if (schema.items) return `${jsonSchemaToTs(schema.items, depth + 1)}[]`;
			return "unknown[]";
		case "object": {
			if (!schema.properties) return "Record<string, unknown>";
			if (depth > 2) return "Record<string, unknown>";
			const props = Object.entries(schema.properties).map(([key, val]) => {
				const optional = !(schema.required || []).includes(key) ? "?" : "";
				const safeKey = /^[A-Za-z_$][\w$]*$/.test(key) ? key : JSON.stringify(key);
				return `${safeKey}${optional}: ${jsonSchemaToTs(val, depth + 1)}`;
			});
			return `{ ${props.join("; ")} }`;
		}
		default:
			return "unknown";
	}
}

/** Returns true if the given JSON schema fragment has at least one property defined. */
export function hasProperties(schema) {
	return schema?.properties && Object.keys(schema.properties).length > 0;
}

/**
 * Filter scanned lexicons down to XRPC-callable types (query / procedure).
 * Drops record / subscription / object-only definitions.
 */
export function filterXrpcLexicons(lexicons) {
	return lexicons.filter(
		(l) => l.defs.main.type === "query" || l.defs.main.type === "procedure",
	);
}
