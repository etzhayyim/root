# Coach AI-agent Chat App Design

## Product Definition

- Product: `etzhayyim-project-coach`
- Primary Device: iPad (portrait/landscape)
- Interaction Model: conversational coaching with structured session states

## Domain Model

- Session
  - id, org_id, user_id, title, phase, created_at, updated_at
- Message
  - session_id, role(user|coach), text, timestamp
- ActionItem
  - session_id, id, title, due_date, status(todo|doing|done)

## Coaching State Machine

- `intake`: context intake
- `goal`: concrete goal definition
- `reality`: current state & blockers
- `options`: option generation
- `will`: commitment and next actions
- `review`: reflection + follow-up

## Prompt Strategy

- coach persona: direct, non-judgmental, evidence-oriented
- response format:
  1. Reflection summary
  2. 1-3 coaching questions
  3. Optional next step proposal

## Safety Guardrails

- no diagnosis / legal determination
- risk phrase detection -> immediate escalation guidance
- store only minimum session data

## API Contracts

- `tools/list`
- `tools/call`
- tool names:
  - `coach.session.create`
  - `coach.session.list`
  - `coach.chat.send`
  - `coach.chat.reply`
  - `coach.action.upsert`
  - `coach.action.list`
  - `coach.session.summary`

## Deployment

- Runtime: kotodama runtime (`core.kotodama-runtime.dev/v1alpha1`)
- Image: `ghcr.io/etzhayyim/coach-chat-mcp-component:kotodama-runtime-0.1.0`
- Route: `https://coach.etzhayyim.com/xrpc`
