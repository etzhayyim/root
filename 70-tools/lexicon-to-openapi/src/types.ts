/**
 * AT Protocol Lexicon type definitions (subset for OpenAPI generation)
 */

export interface LexiconDoc {
  lexicon: 1;
  id: string;
  description?: string;
  defs: Record<string, LexiconDef>;
}

export type LexiconDef =
  | LexiconQueryDef
  | LexiconProcedureDef
  | LexiconRecordDef
  | LexiconObjectDef
  | LexiconTypeDef;

export interface LexiconQueryDef {
  type: "query";
  description?: string;
  parameters?: {
    type: "params";
    properties: Record<string, LexiconProperty>;
    required?: string[];
  };
  output?: {
    encoding: string;
    schema?: LexiconObjectDef | Record<string, unknown>;
  };
}

export interface LexiconProcedureDef {
  type: "procedure";
  description?: string;
  input?: {
    encoding: string;
    schema?: LexiconObjectDef | Record<string, unknown>;
  };
  output?: {
    encoding: string;
    schema?: LexiconObjectDef | Record<string, unknown>;
  };
  errors?: Array<{
    name: string;
    description?: string;
  }>;
}

export interface LexiconRecordDef {
  type: "record";
  description?: string;
  key?: string;
  record: LexiconObjectDef | Record<string, unknown>;
}

export interface LexiconObjectDef {
  type: "object";
  description?: string;
  properties?: Record<string, LexiconProperty>;
  required?: string[];
}

export interface LexiconTypeDef {
  type: "string" | "integer" | "boolean" | "array" | "object" | "bytes";
  description?: string;
  enum?: (string | number)[];
  knownValues?: string[];
  format?: string;
  items?: LexiconProperty;
  maxLength?: number;
  minLength?: number;
  pattern?: string;
  minimum?: number;
  maximum?: number;
  default?: unknown;
  properties?: Record<string, LexiconProperty>;
  required?: string[];
  ref?: string;
  refs?: string[];
}

export interface LexiconProperty {
  type?:
    | "string"
    | "integer"
    | "boolean"
    | "array"
    | "object"
    | "unknown"
    | "ref"
    | "union"
    | "bytes";
  description?: string;
  enum?: (string | number)[];
  knownValues?: string[];
  format?: string;
  items?: LexiconProperty;
  maxLength?: number;
  minLength?: number;
  pattern?: string;
  minimum?: number;
  maximum?: number;
  default?: unknown;
  properties?: Record<string, LexiconProperty>;
  required?: string[];
  ref?: string;
  refs?: string[];
  [key: string]: unknown;
}
