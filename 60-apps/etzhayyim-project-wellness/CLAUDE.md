# etzhayyim-project-wellness

Wellness competency platform — 122-bit evaluation across 8 dimensions.

## Architecture

- **URL**: `https://wellness.etzhayyim.com`
- **Nanoid**: `w3lln3sx`
- **Port**: 21080
- **KV Bucket**: `wellness-content-store`
- **API**: `https://{nanoid}.etzhayyim.com/xrpc`
- **Frontend**: `wellness.etzhayyim.com` served from the parent App fileserver (`svelte/build/`)

## 8 Dimensions of Wellness (Syracuse University)

| Dimension | Bits | Range | Description |
|-----------|------|-------|-------------|
| Physical | 16 | 0–15 | Move, Nourish, Rest |
| Emotional | 15 | 16–30 | Feel, Understand, Cope |
| Spiritual | 14 | 31–44 | Reflect and Align |
| Intellectual | 15 | 45–59 | Stimulate and Grow |
| Environmental | 15 | 60–74 | Refresh Your Space |
| Financial | 14 | 75–88 | Plan and Empower |
| Occupational | 16 | 89–104 | Align and Purpose |
| Social | 17 | 105–121 | Connect and Belong |

## Specialization Domains (横断的専門分野)

5 specializations cross-cut the 8 dimensions:

| Specialization | Dimensions | Description |
|---|---|---|
| 身体知性 (Somatic Intelligence) | Physical, Emotional | Proprioception, interoception, body schema |
| フェルデンクライス (Feldenkrais) | Physical, Spiritual | ATM, Functional Integration |
| アレクサンダーテクニーク (Alexander Technique) | Physical, Spiritual | Inhibition, direction, primary control |
| 作業療法 (Occupational Therapy) | Occupational, Environmental | ADL, IADL, sensory integration |
| 公衆衛生 (Public Health) | Environmental, Social, Intellectual | Epidemiology, health promotion |

## 122-Bit Competency Model

Each bit is assessed on two axes:
- **理解度 (Understanding)**: 0=unaware, 1=aware, 2=familiar, 3=competent, 4=proficient, 5=expert
- **実践度 (Practice)**: 0=none, 1=observer, 2=beginner, 3=regular, 4=advanced, 5=master
- **Score** = understanding × practice (0–25 per bit)
- **Max total** = 122 × 25 = 3050

## Component

| Path | Description |
|------|-------------|
| `wasm/etzhayyim-wasm-wellness-w3lln3sx/` | App with API + static fileserver ownership |
| `wasm/etzhayyim-wasm-wellness-w3lln3sx/<repo-deploy-config>` | App manifest |

## MCP Tools (11)

| Tool | Description |
|------|-------------|
| `wellness.list_bits` | List 122 competency bits with dimension/specialization filters |
| `wellness.get_bit` | Get specific bit by index |
| `wellness.get_dimension_bits` | Get all bits for a dimension |
| `wellness.assess_bit` | Assess a bit (set understanding + practice) |
| `wellness.get_assessment` | Get assessment for a bit |
| `wellness.get_profile` | Get full 122-bit wellness profile |
| `wellness.get_dimension_summary` | Get dimension-level summary |
| `wellness.record_session` | Record a practice session |
| `wellness.list_sessions` | List practice sessions |
| `wellness.get_learning_path` | Get dimension learning path |
| `wellness.get_next_steps` | Get personalized next bits to learn |

## Build & Deploy

```bash
cd 60-apps/etzhayyim-project-wellness/wasm/etzhayyim-wasm-wellness-w3lln3sx
etzhayyim build
etzhayyim deploy --smoke-url https://w3lln3sx.etzhayyim.com/health
```
