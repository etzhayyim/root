# open-denki XRPC Adapter

CF Worker exposes 12 rw-free smart-grid commands.

## Endpoints

- Topology: `defineGenerationNode`, `defineSubstation`, `defineFeeder`, `registerSmartMeter`, `getNode`
- Events: `recordMeterReading`, `reportFault`, `recordDemandResponse`, `recordRenewableOutput`
- Queries: `listFeeders`, `listFaults`, `listReadings`

Routes: open-denki.etzhayyim.com/xrpc/ai.gftd.apps.openDenki.*

IEC 61968/61970 CIM aligned. Integer units (kW, kV, MVA, meters). See ADR-2605210000.
