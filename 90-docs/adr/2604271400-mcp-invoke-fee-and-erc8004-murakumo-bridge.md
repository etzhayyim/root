---
id: adr-2604271400-mcp-invoke-fee-and-erc8004-murakumo-bridge
title: "ADR: MCP invoke fee + ERC-8004 ↔ Murakumo operator bridge"
status: active
doc_type: adr
topic: mcp-invoke-fee-erc8004-murakumo-bridge
authoritative: true
last_verified: 2026-04-27
authoritative_for:
  - MCP `tools/call` 従量課金 (`mcp_invoke` action) と 10% public fund 再分配の継承
  - Murakumo operator (`MurakumoRegistry`) と ERC-8004 agent identity (`etzhayyimAgentRegistry`) の bridge
related:
  - adr-2604261000-mcp-registry-via-kysely-schema
  - adr-2604262100-erc725-erc8004-k8s-ipfs-agent-runtime
  - adr-2604262145-erc8004-protocol-root-atproto-profile
  - adr-0061-murakumo-platform-auth-unification
  - adr-0087-magatama-mcp-tool-facade
supersedes: []
superseded_by: []
---

# Context

現状 (2026-04-27) は次の 2 つの欠落で connect が切れている。

1. **MCP `tools/call` の従量課金が未設計**。credits ledger
   (`20-actors/credits/`) は `EarnCredits` / `SpendCredits` を持ち、
   `SpendCredits` 経路では消費額の 10% が `public-fund:*` に自動分配される
   (`20-actors/credits/CLAUDE.md` L9-14, L40, L135)。
   ただし Spend rate table に登録されている action は `Post` / `Reply` /
   `DM` のみで、MCP 経由 (`/mcp` Streamable HTTP, ADR-0087) や
   `mcp.etzhayyim.com/xrpc/com.etzhayyim.mcp.message` 経由の tool 呼び出しは
   metering されていない。host-sdk
   (`20-actors/magatama/sdk/magatama-host-sdk/src/mcp-server.ts`) の
   `tools/call` は `app.handleXRPC()` または BPMN dispatcher に
   delegate するだけで credits ledger を経由しない。

2. **ERC-8004 agent identity と Murakumo operator が分離している**。
   `etzhayyimAgentRegistry`
   (`0xcA3480edDAfa39c9377B83eEB18291286C8Cb865`, ADR-2604262100) は
   ERC-8004 形 agent registry で、ERC725 root DID hash → tokenId +
   agentURI (ipfs://) を持つ。一方 `MurakumoRegistry`
   (`0x4E3d742ece9483f97c3094b40c4b8C7901a6E3B6`) は inference operator
   stake (1000 GCC ≥) + endpoint + capabilities を `did:etzhayyim` hash
   keyed で持つ。両者を接続する on-chain 紐付けが無いため、
   ERC-8004 経由で agent discovery した caller は Murakumo node の
   stake / SLA reputation を verify できない。

ADR-2604261000 で MCP registry は L4 RisingWave SSoT 化された (Kysely
SELECT, 60s cache)。ADR-0087 で per-actor `/mcp` facade が確立された。
ADR-2604262100 で ERC-8004 agent registry contract が deploy された
(`openRegistration=false`, `nextTokenId=1`)。残るのは **fee plumbing**
と **registry bridge** の 2 点。

# Decision

## D1. `mcp_invoke` action を credits ledger に追加 (10% redistribution は既存ロジックで継承)

`20-actors/credits/CLAUDE.md` の Spend rate table に `MCP invoke` 行を
追加する。料金は (a) base call fee + (b) per-payload-byte fee の二項
モデルとし、計算は credits-mcp が行う。

| Action | Cost (credits) |
|---|---|
| MCP invoke (base) | ¥0.5 |
| MCP invoke (per 1KB request payload) | ¥0.1 |
| MCP invoke (per 1KB response payload) | ¥0.1 |

10% public fund 再分配は **既存の `SpendCredits` allocation 経路で
自動継承**。`mcp_invoke` action の追加で新しい分配ロジックは導入しない。
`SpendCredits` への入力は `{ user_id, action: "mcp_invoke", amount,
destination_id?, metadata: { tool_nsid, actor_did } }`。

## D2. host-sdk MCP dispatch に metering hook を追加

`20-actors/magatama/sdk/magatama-host-sdk/src/mcp-server.ts` の
`dispatchMcp()` に metering hook を 1 箇所だけ追加する。

```ts
// tools/call 直前 (BPMN router lookup 前):
//   const meter = ctx.meter;
//   const billable = meter ? await meter.checkSpendAllowed({
//     userId: ctx.callerUserId,
//     action: "mcp_invoke",
//     payloadBytes: bodyBytes.byteLength,
//   }) : null;
//   if (meter && !billable.allowed) return errorResp(id, INSUFFICIENT_CREDITS, billable.reason);
//
// tools/call 完了後 (delegate result 取得後):
//   if (meter) await meter.spendCredits({
//     userId: ctx.callerUserId,
//     action: "mcp_invoke",
//     toolNsid: name,
//     actorDid: ctx.actorDid,
//     reqBytes: bodyBytes.byteLength,
//     resBytes: result.body.byteLength,
//   });
```

`McpServerContext` に optional `meter: McpMeter` と `callerUserId: string`
を追加。`McpMeter` interface は `credits.etzhayyim.com` の `CheckSpendAllowed`
+ `SpendCredits` 2 mutation を抽象化した薄いラッパー。`meter` 未設定時
は metering を skip (既存 host-sdk consumer に対する後方互換)。

新しい error code を `INSUFFICIENT_CREDITS = -32010` として MCP
JSON-RPC layer に追加 (MCP spec の implementation-defined range)。

10% redistribution 自体は credits-mcp 側 `SpendCredits` で完結。
host-sdk は分配を意識しない。

## D3. `MurakumoAgentBridge` contract を新設

`50-infra/vultr/geth-private/contracts/src/MurakumoAgentBridge.sol` を
追加し、`MurakumoRegistry.operatorDid` (bytes32) と
`etzhayyimAgentRegistry` tokenId を双方向 mapping する。

```solidity
contract MurakumoAgentBridge {
    IMurakumoRegistry public immutable murakumo;
    IetzhayyimAgentRegistry public immutable agents;
    address public owner;

    mapping(bytes32 operatorDid => uint256 agentTokenId) public agentByOperator;
    mapping(uint256 agentTokenId => bytes32 operatorDid) public operatorByAgent;

    event Linked(bytes32 indexed operatorDid, uint256 indexed agentTokenId);
    event Unlinked(bytes32 indexed operatorDid, uint256 indexed agentTokenId);

    function link(bytes32 operatorDid, uint256 agentTokenId) external {
        // operator must be active in MurakumoRegistry (stake intact)
        // agentTokenId must be issued by etzhayyimAgentRegistry
        // caller must be MurakumoRegistry operator (payoutAddress) OR owner
        ...
    }
    function unlink(bytes32 operatorDid) external { ... }
    function resolveAgent(bytes32 operatorDid) external view returns (uint256, bytes memory agentURI);
    function resolveOperator(uint256 agentTokenId) external view returns (bytes32, address payoutAddress, uint256 stake);
}
```

deploy script `script/DeployMurakumoBridge.s.sol` を追加。GCC / EntryPoint
と同様に `forge script ... --broadcast` で `https://geth.etzhayyim.com` 経由で
deploy。`ADDRESSES.md` に行追加。off-chain caller (yoro UI / authz Worker
/ MCP discovery) は `MurakumoAgentBridge.resolveAgent(...)` 1 call で
ERC-8004 agentURI と Murakumo stake を同時に取得できる。

bridge 自体は state を持つだけで escrow / slash には触らない。
`MurakumoRegistry` の slash 経路で operator stake が 0 になった場合、
off-chain reader が `agentByOperator[did]` を引いた上で
`murakumo.operators(did).active` を確認するのが正攻法。

## D4. tier roll-out

| Tier | scope | trigger |
|---|---|---|
| **T0** (本 ADR) | credits rate table 追加、host-sdk hook 実装、bridge contract 設計 | accept |
| **T1** | host-sdk PR + credits-mcp deploy。pilot は lawfirm.etzhayyim.com (ADR-0087 既存 pilot)。`mcpRegistry: { meter: { ... } }` を opt-in | T0 merge |
| **T2** | bridge contract deploy + `MurakumoRegistry` operator 全件 (現 mac mini fleet 4 node) を bridge に link | T1 安定後 |
| **T3** | ERC-8004 agentURI に MCP endpoint + `mcp_invoke` rate を含める (agent.json に rate field 追加)。caller が discovery で fee を事前確認可能 | T2 完了後 |

# Consequences

**Positive**:

- MCP `tools/call` が credits ledger を経由するようになり、
  10% public fund redistribution が自動で適用される (既存 ledger 機構を
  そのまま継承、新規分配ロジックなし)。
- ERC-8004 経由の agent discovery に対し、Murakumo operator の stake と
  reputation を 1 contract call (`resolveAgent`) で照合できる。
- credits ledger の rate table が SSoT 化され、新規 action 追加が
  CLAUDE.md row 1 行で完結する。

**Negative / risks**:

- host-sdk `dispatchMcp` に新規 dependency が増える (credits-mcp Worker
  への HTTP / RPC)。dispatch path 上の追加 RTT。`meter` を optional に
  することで back-compat を確保するが、production rollout 時は
  credits-mcp 可用性が actor liveness に直結する。
- payload size based 課金は AT Repo / E2E ciphertext (signal:v1:) の
  byte 計上が plaintext と等価でない (ADR-2604261000)。当面は
  `bodyBytes.byteLength` (wire size) を採用、AT-decode 後の semantic
  size と齟齬がある場合は T3 で見直す。
- bridge link は operator 申請 + owner 承認の 2 段で運用 (Phase 2-A
  conservative pattern)。Phase 3 で multisig + open-link に開放する。

**Out of scope**:

- ETH gas fee の credits 換算 (Murakumo escrow GCC settlement は別系統)。
- A2A protocol fee, OAuth introspection fee, browser/automation tool fee
  (将来的に同じ `mcp_invoke` action 拡張で吸収可能)。
- 非同期 SSE stream の per-token 課金 (ADR-0087 で SSE は CF 30s 制約で
  out-of-scope)。

# Alternatives Considered

1. **Do not meter MCP**: 推論 (`SpendCredits action: "inference"`) のみ
   課金、tool 呼び出しは無料。却下 — public fund 再分配の網羅性が落ち、
   高頻度 tool spammer に対する rate-limit 経済 incentive が消える。
2. **MCP fee を inference fee に折り込む**: tool 呼び出しが LLM call を
   伴う場合のみ inference 経由で課金。却下 — pure tool (search /
   read / write) は LLM call を伴わないため網羅性に穴が空く。
3. **bridge contract 不要、registry SELECT で resolve**: off-chain で
   `MurakumoRegistry` + `etzhayyimAgentRegistry` 両方を読んで JOIN。却下 —
   ERC-8004 caller (外部 agent ecosystem) は on-chain 単一 view を期待
   する。bridge が無いと caller 側に etzhayyim 内部の registry topology
   knowledge を強制する。
4. **新規 ERC-8004 token を Murakumo operator 1:1 で再発行**:
   `etzhayyimAgentRegistry.openRegistration=true` にして operator が直接
   mint。却下 — root identity (ERC725) が agent token に対応しない
   operator (mac mini 等の物理 node) が混入し、ADR-2604262100 の
   identity hierarchy が壊れる。

# References

- `90-docs/adr/2604261000-mcp-registry-via-kysely-schema.md`
- `90-docs/adr/2604262100-erc725-erc8004-k8s-ipfs-agent-runtime.md`
- `90-docs/adr/2604262145-erc8004-protocol-root-atproto-profile.md`
- `90-docs/adr/0061-murakumo-platform-auth-unification.md`
- `90-docs/adr/0087-magatama-mcp-tool-facade.md`
- `20-actors/credits/CLAUDE.md`
- `20-actors/magatama/sdk/magatama-host-sdk/src/mcp-server.ts`
- `50-infra/vultr/geth-private/contracts/ADDRESSES.md`
- `50-infra/vultr/geth-private/contracts/src/MurakumoRegistry.sol`
- `50-infra/vultr/geth-private/contracts/src/etzhayyimAgentRegistry.sol`
