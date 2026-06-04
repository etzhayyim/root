---
id: adr-2604252100-robotics-product-manufacturing-package
title: "ADR: Robotics control adapters and manufacturing package definition for physical products"
status: proposed
doc_type: adr
topic: robotics-manufacturing-package
authoritative: true
last_verified: 2026-04-25
authoritative_for:
  - robotics-real-machine-control-boundary
  - robot-arm-drone-autonomous-vehicle-manufacturing-package
  - tsukuru-kami-robotics-product-definition-files
related:
  - adr-2604241500-cad-bim-per-game-wasm-topology
  - adr-0056-bpmn-as-actor
  - adr-0087-magatama-mcp-tool-facade
  - adr-2604250836-langgraph-as-zeebe-servicetask
  - robotics-manufacture-vehicle-product-package
supersedes: []
superseded_by: []
---

# Context

Tsukuru / KAMI / Magatama の robotics surface は、robot arm、drone、
AGV / AMR、自動運転車両の mission planning、dry-run simulation、
approval、telemetry、audit を BPMN / MCP / PyZeebe / KAMI Engine SDK
で統合し始めている。

次の未決事項は二つある。

1. AI agent が実機を操作する場合の安全な境界
2. robot arm、drone、自動運転車両そのものを製造するための設計図、
   部品表、3D print、CNC、PCB、組立、検査、出荷の定義ファイル

物理製品では「この 1 ファイルを渡せば必ず作れる」という単一標準は
存在しない。一般には CAD / ECAD / CAM / additive manufacturing /
BOM / routing / inspection / firmware / calibration を束ねた
manufacturing package が必要になる。特に robot arm と drone は
機械、電気、制御 software、安全規格、校正、現場 commissioning が
分離できない。

# Decision

etzhayyim robotics は、実機制御と製品製造を以下の二層で扱う。

## 1. 実機制御 adapter boundary

AI agent は actuator に直接 command を送ってはならない。AI agent は
mission plan、replan、approval request、simulation request までを作る。
実機送信は safety gateway が validation した後、asset-specific adapter
へ渡す。

標準 adapter は以下を default とする。

| Asset | Control standard / SDK | etzhayyim adapter |
|---|---|---|
| robot arm / cobot | ROS 2, ros2_control, MoveIt 2, vendor driver | `robotics.adapter.ros2_control` / `robotics.adapter.robot_arm` |
| drone | MAVLink, PX4 / ArduPilot, MAVSDK | `robotics.adapter.mavlink` |
| AGV / AMR | VDA 5050 | `robotics.adapter.vda5050` |
| autonomous vehicle / ROS robot | ROS 2 action / lifecycle / topic | `robotics.adapter.ros2_action` |

Common safety tools:

- `robotics.command.dispatch`
- `robotics.asset.pause`
- `robotics.asset.estop`
- `robotics.geofence.enforce`
- `robotics.safety.interlock.check`
- `robotics.telemetry.ingest`
- `robotics.mission.status`

Safety gateway MUST check:

- schema validity
- asset identity and operator permission
- approval record
- simulation / dry-run result
- safety envelope / geofence
- speed / acceleration / payload limit
- E-stop availability
- audit event sink availability

## 2. Manufacturing package for physical products

Robot arm、drone、自動運転車両を製造する入力は、単一の `*.robot` file
ではなく、以下の package manifest を SSoT とする。

```
robotics-product-package/
  product.manufacturing.json
  mechanical/
    assembly.step
    printable-parts.3mf
    printable-parts.stl
    drawings.pdf
    tolerances.json
  cam/
    cnc-operations.json
    mill-program.nc
    lathe-program.nc
    printer-profile.3mf
  electronics/
    pcb.ipc2581.xml
    gerber/
    bom.csv
    pick-place.csv
    test-points.csv
  control/
    ros2/
      urdf/
      srdf/
      ros2_control.yaml
      moveit_config/
    firmware/
    parameters.yaml
    calibration.json
  process/
    build.bpmn
    assembly-work-instructions.md
    inspection-plan.json
    end-of-line-test.json
    commissioning-checklist.json
  compliance/
    risk-assessment.md
    safety-requirements.json
    declarations/
```

`product.manufacturing.json` is the package index. It MUST reference all
files by content hash, role, version, author, target process, and required
machine capability.

For Alibaba / EMS RFQ use, the canonical practical ZIP profile is:

```
Project_XYZ/
  CAD/
    assembly.step
    drawings.pdf
    machining.dxf
    material-surface-treatment.pdf
  PCB/
    gerber-rs274x/
    drill-excellon/
    pick-place.csv
    schematic.pdf
  BOM/
    bom.csv
    bom.xlsx
  Assembly/
    assembly-drawing.pdf
    work-instructions.pdf
    torque-esd-notes.pdf
  QA/
    inspection-criteria.pdf
    measurement-method.pdf
    sample-photos/
  RFQ.pdf
```

This ZIP is the de-facto manufacturing package for supplier quotation.
Minimum quote inputs are STEP or dimensioned drawings, BOM when electronics
exist, quantity, and product image/reference. Production release requires
Gerber, drill, BOM, pick/place, assembly instructions, and inspection
criteria.

Minimum manifest fields:

```json
{
  "schema": "com.etzhayyim.robotics.product.manufacturing.v1",
  "productId": "robotics-product",
  "revision": "A",
  "assetKind": "robot-arm",
  "files": [
    {
      "path": "mechanical/assembly.step",
      "role": "mechanical-cad",
      "format": "STEP",
      "sha256": "..."
    }
  ],
  "manufacturingProcesses": [
    "mechanical-machining",
    "additive-manufacturing",
    "pcb-fabrication",
    "assembly",
    "firmware-flash",
    "calibration",
    "inspection"
  ],
  "requiredMachines": [
    "3d-printer",
    "cnc-mill",
    "soldering-or-pcba-line",
    "robot-calibration-rig"
  ],
  "qualityGates": [
    "incoming-material",
    "dimensional-inspection",
    "electrical-test",
    "firmware-test",
    "safety-interlock-test",
    "end-of-line-test"
  ]
}
```

## Standard file choices

| Domain | Preferred exchange files | Purpose |
|---|---|---|
| Mechanical CAD | STEP / ISO 10303, native CAD optional | assemblies, solids, product structure |
| Mesh preview / print fallback | STL | simple geometry exchange where metadata loss is acceptable |
| 3D printing | 3MF, AMF | additive manufacturing model, units, materials, build items |
| CNC machining | G-code / RS274-NGC dialect, setup sheet | machine path execution |
| PCB fabrication | Gerber X2/X3, IPC-2581, NC drill | board fabrication and assembly transfer |
| BOM | CSV / JSON / PLM export, IPC material declarations where required | procurement and traceability |
| Assembly process | BPMN, work instructions, torque table, fixture setup | repeatable build flow |
| Industrial integration | OPC UA information model, AutomationML / CAEX where needed | plant engineering and machine interoperability |
| Robot control | URDF, SRDF, ros2_control YAML, MoveIt config | kinematics, planning, hardware interface |
| Drone control | PX4 / ArduPilot parameters, MAVLink mission, geofence | autopilot configuration and mission execution |
| Inspection | QIF / JSON inspection plan, measurement CSV, end-of-line test record | quality evidence |

Common authoring / operating systems:

| System | Role |
|---|---|
| Autodesk Fusion 360 | CAD / CAM / additive / drawing export |
| KiCad / Altium Designer | ECAD, Gerber, drill, pick/place, schematic export |
| Arena PLM | BOM, engineering change, quality, supplier package control |
| Odoo MRP | manufacturing order, routing, inventory, purchasing, shop-floor execution |

## Product-type profiles

### Robot arm package

Required:

- STEP assembly for links, joints, actuator mounts, end effector, fixtures
- URDF / SRDF and ros2_control config
- MoveIt 2 config for planning groups and collision objects
- actuator, encoder, gearbox, brake, and limit switch BOM
- wiring harness and controller PCB package
- joint calibration and home-offset records
- E-stop, guard, safety-rated monitored stop, and interlock test records

### Drone package

Required:

- STEP / 3MF airframe and payload mount
- motor, ESC, propeller, battery, flight-controller BOM
- PCB package for carrier board or power distribution board
- PX4 / ArduPilot parameters
- MAVLink mission / geofence / failsafe profile
- thrust, payload, battery, vibration, GPS, and radio-link test records
- regulatory operation checklist for the deployment jurisdiction

### Autonomous vehicle package

Required:

- chassis / sensor mount / payload CAD
- drive-by-wire or motor-controller interface definition
- ROS 2 launch, lifecycle, action, and topic contract
- localization / perception sensor calibration
- route / operational design domain definition
- safety case, fallback maneuver, manual takeover, and E-stop validation

### Automotive manufacturing package

Vehicle programs use the same manufacturing package envelope, but the profile is
expanded beyond the robotics minimum because automotive production must bind
design, plant routing, supplier evidence, software release, regulatory evidence,
and service/repair data.

Required file groups:

| Domain | Preferred exchange files | Purpose |
|---|---|---|
| CAD / PLM | STEP AP242, JT, native CAD optional, PLM export JSON/CSV | body, chassis, closures, interior, battery, harness, and product structure |
| Drawings / GD&T | PDF, DXF/DWG, QIF, STEP PMI | drawings, tolerances, inspection features, supplier release |
| EBOM / MBOM / routing | CSV, JSON, PLM/MES export, B2MML where available | material views, plant-specific build sequence, station routing |
| Tooling / fixtures | STEP/JT, fixture setup sheet, robot program archive, torque table | dies, molds, weld fixtures, gauges, end effectors, torque tools |
| PCB / harness | IPC-2581, Gerber X2/X3, ODB++, IPC-D-356, harness XML/KBL | ECU boards, sensors, power distribution, wire harness transfer |
| Software / calibration | AUTOSAR ARXML, A2L, DBC, ODX, CDD, SREC/HEX, CycloneDX/SPDX | ECU integration, diagnostics, flashing, calibration, software supply chain |
| Process / quality | BPMN, APQP, PPAP, DFMEA, PFMEA, control plan, MSA, SPC, 8D | launch readiness, process risk, quality controls, corrective action |
| EOL / compliance | measurement CSV, QIF, EOL JSON, homologation PDF, DPP JSON-LD | VIN bind, EOL test, traceability, regulatory release, service evidence |

Required worker task types:

| Task type | Responsibility |
|---|---|
| `automotive.package.profile` | normalize vehicle program, plant, line, vehicle kind, and required evidence |
| `automotive.file.catalog` | classify CAD/PLM/CAM/PCB/software/QA/compliance/service files |
| `automotive.ebom.mbom.align` | compare EBOM, MBOM, routing, supplier, and plant-specific material views |
| `automotive.supply.process.link` | connect material requirements, suppliers, intermediate parts, people, responsible roles, and patent evidence |
| `automotive.material.procurement.plan` | plan steel, aluminum, resin, battery materials, semiconductors, harness, tires, glass, and logistics procurement |
| `automotive.intermediate.process.plan` | plan stamping, casting, machining, molding, welding, coating, cell/module/pack, ECU, harness, seat, and subassembly flows |
| `automotive.routing.plan` | build process routing for body, paint, powertrain, final assembly, EOL, and rework |
| `automotive.tooling.plan` | register die, mold, fixture, jig, gauge, robot program, and calibration needs |
| `automotive.line.balance` | check takt time, station work content, buffers, and bottleneck risk |
| `automotive.quality.gate` | evaluate APQP, PPAP, FMEA, control plan, MSA/SPC, EOL, and homologation evidence |
| `automotive.eol.plan` | plan VIN bind, ECU flashing, ADAS calibration, battery test, leak/NVH, dyno, and audit trail |
| `automotive.software.release` | bind firmware, ECU config, SBOM, calibration, cybersecurity, OTA, and rollback evidence |
| `automotive.dpp.export` | export battery passport, digital product passport, repairability, recycling, and service data |
| `automotive.rfq.export` | build RFQ packages for tier suppliers, EMS, tooling suppliers, logistics, and validation labs |

The vehicle-specific BPMN SSoT is
`etzhayyim-root/00-contracts/bpmn/com/etzhayyim/robotics/manufactureVehicleProductPackage.bpmn`.
The worker contract is mirrored in
`60-apps/etzhayyim-project-vehicle/WORKERS.md`.

The graph extension links vehicle packages to material procurement,
intermediate manufacturing outputs, legal entities / LEI records,
craftspersons or responsible persons, and patent evidence through
`30-graph/graph-schema/migrations/20260426123000_automotive_manufacturing_supply_process_edges.ts`.

# Consequences

## Positive

- Tsukuru can receive a product package and decide which parts are printable,
  machinable, purchasable, assembled, calibrated, inspected, or blocked.
- KAMI Engine SDK can preview the package as a 3D manufacturing cell and
  generate review scenes for robot arm / drone / transport / safety zones.
- MCP tools can expose package validation, process planning, and machine
  dispatch without letting AI agents bypass safety validation.
- BPMN remains the SSoT for manufacturing and commissioning processes.

## Negative / Trade-off

- A physical product still requires supplier capability, machine-specific
  post-processing, jigs, calibration, and safety review. The package is a
  manufacturability contract, not a guarantee that any factory can build it.
- STEP / 3MF / Gerber / G-code are exchange formats, not full product truth
  by themselves. Native CAD / PLM data may still be needed for editable source.
- Vendor robot arm and autopilot SDKs have hardware-specific constraints that
  must remain in adapter plugins.

## Implementation follow-up

- Add `robotics.product.package.validate` MCP tool.
- Add `robotics.command.dispatch`, `robotics.asset.pause`,
  `robotics.asset.estop`, and adapter dry-run tools.
- Add lexicons for `productManufacturingPackage`, `robotArmPackage`,
  `dronePackage`, and `autonomousVehiclePackage`.
- Add BPMN `manufactureRoboticsProduct.bpmn`:
  package validate -> process plan -> 3D print/CNC/PCB dispatch -> assembly
  -> calibration -> inspection -> commissioning -> audit.
- Add KAMI SDK package viewer helpers for STEP/3MF manifest references and
  safety-envelope review.

# Alternatives Considered

## A. Treat STEP or 3MF as the single source of truth

Rejected. STEP is strong for CAD exchange, and 3MF is strong for additive
manufacturing, but neither contains all electronics, firmware, calibration,
inspection, compliance, and shop-floor process requirements.

## B. Let AI generate direct robot / drone actuator commands

Rejected. This bypasses the safety gateway and makes audit, approval,
geofence, E-stop, and operator responsibility ambiguous.

## C. Adopt manufacturing package manifest + adapter boundary

Adopted. It matches how physical products are actually manufactured and keeps
AI planning separate from safety-checked execution.

# References

- ROS 2 documentation: https://docs.ros.org/
- ros2_control documentation: https://control.ros.org/
- MoveIt 2 documentation: https://moveit.picknik.ai/
- MAVLink developer guide: https://mavlink.io/
- MAVSDK documentation: https://mavsdk.mavlink.io/
- VDA 5050: https://www.vda.de/vda/en/topics/automotive-industry/vda-5050
- ISO 10303 / STEP overview (NIST): https://www.nist.gov/publications/introduction-iso-10303-step-standard-product-data-exchange-0
- 3MF specification: https://3mf.io/spec/
- ISO/ASTM 52915 AMF: https://www.iso.org/standard/74640.html
- LinuxCNC G-code / RS274-NGC overview: https://linuxcnc.org/docs/html/gcode/overview.html
- Gerber format: https://www.ucamco.com/en/file-formats
- IPC-2581 consortium: https://www.ipc2581.com/
- OPC UA: https://opcfoundation.org/about/opc-technologies/opc-ua/
- AutomationML: https://www.automationml.org/
