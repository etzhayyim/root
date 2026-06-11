# @etzhayyim/lexicon-to-zod

Generate Zod runtime validators from AT Protocol Lexicon JSON files.

This tool provides two capabilities:

1. **Runtime Validators**: Convert AT Protocol Lexicon schemas into Zod validators for input/output validation in XRPC handlers.
2. **Code Generation**: CLI tool to pre-generate validator modules from all lexicons under `00-contracts/lexicons/com/etzhayyim/<actor>/`.

## Installation

```bash
npm install @etzhayyim/lexicon-to-zod zod
```

## Usage

### Runtime API

```typescript
import { buildValidatorMap, validateInput } from "@etzhayyim/lexicon-to-zod";
import type { LexiconDoc } from "@etzhayyim/lexicon-to-zod";

// Load lexicons (either from JSON or pre-built generated module)
const lexicons: LexiconDoc[] = [
  {
    lexicon: 1,
    id: "com.etzhayyim.apps.openBanking.transfer",
    defs: {
      main: {
        type: "procedure",
        input: {
          encoding: "application/json",
          schema: {
            type: "object",
            properties: {
              transferId: { type: "string" },
              amount: { type: "integer", minimum: 0 },
            },
            required: ["transferId", "amount"],
          },
        },
      },
    },
  },
];

const validators = buildValidatorMap(lexicons);

// Validate input
const input = { transferId: "tx123", amount: 1000 };
const result = validateInput(validators, "com.etzhayyim.apps.openBanking.transfer", input);

if ("error" in result) {
  console.error("Validation failed:", result.error.issues);
} else {
  console.log("Valid input:", result.data);
}
```

### XRPC Handler Integration

In a Cloudflare Worker XRPC adapter:

```typescript
import { z } from "zod";

// Inline for single endpoint, or import from generated module
const transferInputSchema = z.object({
  transferId: z.string().min(1),
  clientRequestId: z.string().min(1),
  fromAccountId: z.string().min(1),
  toAccountId: z.string().min(1),
  amountMinor: z.number().int().positive(),
  currency: z.string().min(1),
  memo: z.string().optional(),
});

// In fetch handler, before calling business logic:
if (nsid === `${NSID_BASE}.transfer`) {
  const parsed = transferInputSchema.safeParse(input);
  if (!parsed.success) {
    return new Response(
      JSON.stringify({ error: "InvalidInput", issues: parsed.error.issues }),
      { status: 400, headers: { "content-type": "application/json" } }
    );
  }
  input = parsed.data;
}

// Now input is type-safe
const result = await transfer(e, input);
```

### Code Generation (CLI)

Generate validator modules from all lexicons:

```bash
node src/cli.ts 00-contracts/lexicons/com/etzhayyim 70-tools/lexicon-to-zod/generated
```

This produces one `.ts` file per actor directory (e.g., `openBanking.validators.ts`), containing:

```typescript
export const openBankingValidators = buildValidatorMap([...]);
```

Import and use in your handler:

```typescript
import { openBankingValidators } from "@etzhayyim/lexicon-to-zod/generated/openBanking.validators.js";
import { validateInput } from "@etzhayyim/lexicon-to-zod";

const v = validateInput(openBankingValidators, "com.etzhayyim.apps.openBanking.transfer", input);
```

## Supported Lexicon Features

- **Primitives**: string, integer, boolean, bytes
- **Containers**: array, object
- **Constraints**: minLength, maxLength, minimum, maximum
- **Formats**: uri, datetime
- **Enums**: enum (string) and knownValues

Note: `ref` and `union` types are passed through as `z.unknown()`. Schema resolution across lexicon references is the consumer's responsibility.

## Design

The tool maintains independence from `lexicon-to-openapi` by copying the type definitions verbatim. This allows both tools to evolve separately while staying synchronized with the AT Protocol Lexicon spec.

## References

- ADR-2605091400: MCP-as-Cell-Membrane — Lexicon = Dual-Wire SSoT
- ADR-2605210000: Execution Layer Demonstration (open-banking)
