# Rare Earth Supply Chain Graph

- as of: `2026-04-13`
- data file: [rare-earth-supply-chain-2026-04-13.graph.json](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-resource-flow/data/rare-earth-supply-chain-2026-04-13.graph.json)
- shape: `vertices[]` + `edges[]`
- vertex identity: every vertex has a `did`
- dependency encoding: every vertex has `deps[]` and the graph also has explicit `policy/resource_flow/capital_flow/offtake` edges

## Coverage

- upstream extraction: China north (`Bayan Obo`), China south ionic clays, Myanmar ionic clays, US (`Mountain Pass`), Australia (`Mt Weld`)
- midstream separation/refining: `China Northern Rare Earth`, `China Rare Earth Group`, `Shenghe`, `Lynas Malaysia`, `MP Materials`, `Eneabba`, `Caremag`
- downstream magnets/demand: China magnet sector, EV, wind, defense, GM
- regulation and finance: China `State Council / MOFCOM / GAC`, US `White House / DoD / DOE / USGS`, Australia `DISR / EFA`, EU `Council / Commission / CRM Board`, Japan `METI / JOGMEC`

## Mermaid

```mermaid
flowchart LR
  SC[State Council] --> MOFCOM[MOFCOM]
  SC --> GAC[GAC]
  Bayan[Bayan Obo] --> CNR[China Northern Rare Earth]
  SouthClay[Southern China ionic clays] --> CREG[China Rare Earth Group]
  Myanmar[Myanmar ionic clays] --> CREG
  CNR --> ChinaMag[China magnet sector]
  CREG --> ChinaMag
  Shenghe[Shenghe] --> ChinaMag

  WH[White House] --> DoD[US DoD / OSC]
  WH --> DOE[DOE]
  MPMine[Mountain Pass] --> MP[MP Materials]
  DoD --> MP
  MP --> MPTX[MP Texas magnetics]
  MPTX --> GM[GM]
  MP --> Defense[Global defense OEM]

  MtWeld[Mt Weld] --> LynasMY[Lynas Malaysia]
  LynasMY --> EV[Global EV OEM]
  LynasMY --> Wind[Global wind OEM]

  DISR[Australia DISR] --> EFA[Export Finance Australia]
  EFA --> Iluka[Iluka]
  Iluka --> Eneabba[Eneabba refinery]

  EUCouncil[EU Council] --> EUComm[EU Commission]
  EUComm --> CRMBoard[EU CRM Board]

  METI[METI] --> JOGMEC[JOGMEC]
  JOGMEC --> Caremag[Caremag]
  Caremag --> Defense
  Caremag --> EV

  ChinaMag --> EV
  ChinaMag --> Wind
  ChinaMag --> Defense
```

## Notes

- `active` means operating or currently in force.
- `planned` means publicly backed but not yet fully online.
- `confidence=medium` means the dependency is real but the exact commercial counterparty path is not fully public.
