/**
 * AT Protocol Lexicon to OpenAPI 3.0 converter
 */

import type {
  LexiconDoc,
  LexiconObjectDef,
  LexiconProperty,
  LexiconProcedureDef,
  LexiconQueryDef,
  LexiconRecordDef,
} from "./types.js";

export interface OpenAPIGenOpts {
  /** OpenAPI info.title */
  title: string;
  /** OpenAPI info.version */
  version: string;
  /** Server base URL, e.g., "https://kiyo.etzhayyim.com" */
  baseUrl: string;
}

/**
 * Convert AT Protocol Lexicon documents to OpenAPI 3.0 specification
 */
export function lexiconsToOpenApi(
  lexicons: LexiconDoc[],
  opts: OpenAPIGenOpts
): Record<string, unknown> {
  const paths: Record<string, unknown> = {};
  const components: Record<string, Record<string, unknown>> = { schemas: {} };

  for (const lex of lexicons) {
    const main = lex.defs.main as
      | LexiconQueryDef
      | LexiconProcedureDef
      | LexiconRecordDef
      | undefined;
    if (!main) continue;

    const pathKey = `/xrpc/${lex.id}`;

    if (main.type === "query") {
      const queryDef = main as LexiconQueryDef;
      paths[pathKey] = {
        get: {
          summary: queryDef.description ?? lex.id,
          operationId: lex.id,
          parameters: queryDef.parameters
            ? Object.entries(queryDef.parameters.properties ?? {}).map(
                ([name, prop]) => ({
                  name,
                  in: "query",
                  required: (queryDef.parameters?.required ?? []).includes(
                    name
                  ),
                  description: prop.description,
                  schema: propertyToSchema(prop, components.schemas),
                })
              )
            : [],
          responses: {
            "200": {
              description: "OK",
              content: queryDef.output
                ? {
                    [queryDef.output.encoding]:
                      queryDef.output.schema instanceof Object &&
                      "type" in queryDef.output.schema
                        ? {
                            schema: objectToSchema(
                              queryDef.output.schema as LexiconObjectDef,
                              components.schemas
                            ),
                          }
                        : { schema: {} },
                  }
                : {},
            },
            default: {
              description: "Error",
            },
          },
        },
      };
    } else if (main.type === "procedure") {
      const procDef = main as LexiconProcedureDef;
      paths[pathKey] = {
        post: {
          summary: procDef.description ?? lex.id,
          operationId: lex.id,
          requestBody: procDef.input
            ? {
                required: true,
                content: {
                  [procDef.input.encoding]:
                    procDef.input.schema instanceof Object &&
                    "type" in procDef.input.schema
                      ? {
                          schema: objectToSchema(
                            procDef.input.schema as LexiconObjectDef,
                            components.schemas
                          ),
                        }
                      : { schema: {} },
                },
              }
            : undefined,
          responses: {
            "200": {
              description: "OK",
              content: procDef.output
                ? {
                    [procDef.output.encoding]:
                      procDef.output.schema instanceof Object &&
                      "type" in procDef.output.schema
                        ? {
                            schema: objectToSchema(
                              procDef.output.schema as LexiconObjectDef,
                              components.schemas
                            ),
                          }
                        : { schema: {} },
                  }
                : {},
            },
            default: {
              description: "Error",
            },
          },
        },
      };
    } else if (main.type === "record") {
      // Records aren't endpoints — register as component schemas
      const recDef = main as LexiconRecordDef;
      if (recDef.record instanceof Object && "type" in recDef.record) {
        components.schemas[sanitize(lex.id)] = objectToSchema(
          recDef.record as LexiconObjectDef,
          components.schemas
        );
      }
    }
  }

  return {
    openapi: "3.0.3",
    info: { title: opts.title, version: opts.version },
    servers: [{ url: opts.baseUrl }],
    paths,
    components,
  };
}

/**
 * Convert a Lexicon object definition to OpenAPI schema
 */
function objectToSchema(
  obj: LexiconObjectDef | Record<string, unknown>,
  schemas: Record<string, unknown>
): Record<string, unknown> {
  if (!obj || typeof obj !== "object") {
    return { type: "object" };
  }

  const objDef = obj as Partial<LexiconObjectDef>;
  const props: Record<string, unknown> = {};

  for (const [k, p] of Object.entries(objDef.properties ?? {})) {
    props[k] = propertyToSchema(p as LexiconProperty, schemas);
  }

  const schema: Record<string, unknown> = {
    type: "object",
  };

  if (objDef.description) {
    schema.description = objDef.description;
  }

  if (Object.keys(props).length > 0) {
    schema.properties = props;
  }

  if (objDef.required && objDef.required.length > 0) {
    schema.required = objDef.required;
  }

  return schema;
}

/**
 * Convert a Lexicon property to OpenAPI schema
 */
function propertyToSchema(
  p: LexiconProperty | undefined,
  schemas: Record<string, unknown>
): Record<string, unknown> {
  if (!p || typeof p !== "object") {
    return {};
  }

  const prop = p as Partial<LexiconProperty>;

  // Handle references
  if (prop.type === "ref" && prop.ref) {
    return { $ref: `#/components/schemas/${sanitize(prop.ref)}` };
  }

  // Handle unions
  if (prop.type === "union" || (prop.refs && prop.refs.length > 0)) {
    return {
      oneOf: (prop.refs ?? []).map((r) => ({
        $ref: `#/components/schemas/${sanitize(r)}`,
      })),
    };
  }

  // Handle arrays
  if (prop.type === "array") {
    const schema: Record<string, unknown> = {
      type: "array",
    };
    if (prop.items) {
      schema.items = propertyToSchema(prop.items, schemas);
    }
    if (prop.maxLength !== undefined) {
      schema.maxItems = prop.maxLength;
    }
    return schema;
  }

  // Handle objects
  if (prop.type === "object") {
    return objectToSchema(prop as LexiconObjectDef, schemas);
  }

  // Handle unknown/untyped
  if (prop.type === "unknown" || !prop.type) {
    return {};
  }

  // Build standard schema
  const schema: Record<string, unknown> = {
    type: prop.type,
  };

  if (prop.description) {
    schema.description = prop.description;
  }

  if (prop.format) {
    schema.format = prop.format;
  }

  if (prop.enum && prop.enum.length > 0) {
    schema.enum = prop.enum;
  }

  if (prop.knownValues && prop.knownValues.length > 0) {
    schema["x-knownValues"] = prop.knownValues;
  }

  if (prop.pattern) {
    schema.pattern = prop.pattern;
  }

  if (prop.maxLength !== undefined) {
    schema.maxLength = prop.maxLength;
  }

  if (prop.minLength !== undefined) {
    schema.minLength = prop.minLength;
  }

  if (prop.minimum !== undefined) {
    schema.minimum = prop.minimum;
  }

  if (prop.maximum !== undefined) {
    schema.maximum = prop.maximum;
  }

  if (prop.default !== undefined) {
    schema.default = prop.default;
  }

  return schema;
}

/**
 * Sanitize identifiers to valid OpenAPI schema names (alphanumeric + underscore)
 */
function sanitize(id: string): string {
  return id.replace(/[^a-zA-Z0-9_]/g, "_");
}
