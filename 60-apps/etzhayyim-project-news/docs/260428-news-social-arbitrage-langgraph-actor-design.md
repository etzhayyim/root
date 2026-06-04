# news.etzhayyim.com Social Arbitrage Intel Actor

Date: 2026-04-28

## Goal

Design a LangServer LangGraph actor that turns public information into
`news.etzhayyim.com` intel and social posts. The actor is not a generic news
summarizer. It searches for arbitrage where one public signal can reduce social
inequality, loneliness, or separation by connecting people to resources,
rights, communities, or underused capacity.

## Contract

- BPMN process: `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/news/socialArbitrageIntel.bpmn`
- LangServer worker: `50-infra/k8s/news-social-arbitrage-actor/worker.py`
- Discovery task: `news.socialArbitrage.discover`
- LangGraph task: `news.socialArbitrage.draft`
- RSS pipeline tasks: `news.rss.resolveSources`, `news.rss.ingestSource`
- Thin edge publish path: `com.etzhayyim.apps.news.analyzeIntel` then
  `com.etzhayyim.apps.news.publishIntel`
- Thin RSS write path: `com.etzhayyim.apps.news.commitArticle`
- Public actor: `did:web:news.etzhayyim.com`
- Writer DID: `did:web:news.etzhayyim.com:writer:social-arbitrage`

## Actor Shape

The worker has two explicit roles.

- `discover`: enumerate official/public source URLs and normalize each candidate
  into title, URL, source type, topic, and region.
- `draft`: run a LangGraph scoring graph that separates source-grounded facts
  from social-arbitrage interpretation, then produces a short social post draft.

The TypeScript/Cloudflare news worker is intentionally thin. It validates the
XRPC payload, writes `intel.report`, creates the writer-DID social post, and
returns the result. It does not own public-source fetch, extraction, scoring, or
drafting. Those pipeline responsibilities belong to the LangServer worker.

## Social Arbitrage Scoring

The actor computes a 0.0-1.0 `socialArbitrageScore` from four dimensions.

- `inequalityBridge`: improves access to money, care, mobility, education,
  legal remedies, public services, language, or assistive tools.
- `lonelinessBridge`: creates or strengthens low-friction community, mutual aid,
  mental health support, peer matching, or intergenerational contact.
- `separationBridge`: reduces geographic, linguistic, disability, bureaucratic,
  platform, or institutional separation.
- `actionability`: gives readers a concrete next action, deadline, eligibility
  clue, dataset, procurement opening, grant, open API, or contact surface.

Publish gate:

- `sourceCredibility >= 0.70`
- `socialArbitrageScore >= 0.58`
- at least one bridge dimension is `>= 0.60`
- draft contains source URL and no unsupported private claim

## LangGraph Nodes

```text
normalize_source
  -> extract_public_facts
  -> score_bridge_value
  -> identify_arbitrage
  -> draft_socialpost
  -> policy_gate
```

`extract_public_facts` may only use supplied public source text. `identify_arbitrage`
can infer implications, but every implication must point back to a fact or a
public source URL.

## Output Payload

```json
{
  "title": "Public signal title",
  "url": "https://example.gov/source",
  "sourceId": "social-arbitrage",
  "sourceType": "official",
  "topic": "social-arbitrage",
  "region": "global",
  "summary": "Source-grounded brief.",
  "facts": ["..."],
  "findings": ["..."],
  "socialPost": "1-2 sentence public post with source URL.",
  "socialArbitrageScore": 0.72,
  "bridgeScores": {
    "inequalityBridge": 0.7,
    "lonelinessBridge": 0.4,
    "separationBridge": 0.8,
    "actionability": 0.7
  },
  "credibility": 0.9,
  "priority": 0.67,
  "publish": true
}
```

## Source Policy

Preferred sources:

- government and regulator notices
- official statistics and open data portals
- public procurement, grants, and consultation calls
- public health, education, labor, housing, transport, and accessibility data
- standards bodies, NGOs with transparent methodology, and direct institutional
  announcements

Disallowed for automatic publication:

- private personal information
- unsupported claims about vulnerable groups
- outrage framing without a concrete bridge or action
- content whose only arbitrage is financial extraction from scarcity

## Social Post Format

The social post is a compact article lead, not clickbait.

```text
Public signal -> bridge -> action.

Source URL
```

Example:

```text
A city open-data release shows unused evening community-room capacity near high-loneliness districts. The arbitrage is to match verified local groups to idle rooms before new construction is funded.

https://example.gov/open-data
```

## Operations

The deployment is intentionally independent from the Cloudflare news app. LangServer
controls orchestration, the Python pod handles public-source fetch, extraction,
scoring, and socialpost drafting, and `news.etzhayyim.com` handles only edge
persistence/posting. This keeps public publishing behind the existing news
governance gates while moving the pipeline runtime out of the edge worker.
