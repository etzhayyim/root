# 260409 KAMI Engineering SDK Design

Date: 2026-04-09

## Goal

KAMI Engine に **EDA / CAD / CAM / RTL / CAE** の 5 ドメインを統合した Engineering SDK を追加する。全ドメインが KAMI Engine の wgpu 統一レンダラ + hecs ECS + kami-input (stylus/tablet) + scene graph を共有し、ブラウザ内で動作する。

## Design Principles

1. **wgpu 統一レンダラ** — Threlte/three.js 不使用。全描画は kami-render wgpu PBR pipeline + 2D overlay (kami-ui-gpu)
2. **Rust WASM** — 全計算カーネルは Rust → wasm-pack → ブラウザ。JS 再実装禁止
3. **既存 crate 再利用** — kami-sdf (CSG), kami-scad (parametric), kami-mesher (mesh), kami-graph (PCB layout), kami-scene-graph (hierarchy), kami-input (stylus), kami-physics-2d (constraint solver seed)
4. **WIT contract** — 各ドメインに WIT interface 定義。`etzhayyim:kami-eng-*@1.0.0`
5. **Nintendo UI/UX** — クリーム背景 `#f0ead6`, Nunito, spring physics, kami-ui-sdk overlay
6. **AT Protocol faithful** — 設計データは W Protocol Event Stream。Design E 3-Tier Write

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    KAMI Engineering Workbench                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │  EDA    │ │  CAD    │ │  CAM    │ │  RTL    │ │  CAE    │  │
│  │Schematic│ │  BREP   │ │Toolpath │ │  HDL    │ │  FEA    │  │
│  │PCB Lay. │ │Assembly │ │ G-code  │ │Simulate │ │ Solver  │  │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘  │
│       └──────┬─────┴──────┬────┴──────┬────┴──────┬────┘       │
│              ▼            ▼           ▼           ▼            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              kami-eng-core (共通基盤)                       │ │
│  │  Constraint Solver │ Parameter Engine │ History/Undo       │ │
│  │  Selection System  │ Snap/Grid       │ Measurement        │ │
│  │  Layer Manager     │ Symbol Library  │ DRC/ERC Engine      │ │
│  └────────────────────────────────────────────────────────────┘ │
│              ▼            ▼           ▼           ▼            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              KAMI Engine (既存)                             │ │
│  │  kami-render (wgpu) │ kami-scene-graph │ kami-input        │ │
│  │  kami-sdf/kami-scad │ kami-mesher      │ kami-ui-gpu       │ │
│  │  kami-graph (PCB)   │ kami-core (hecs) │ kami-text         │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## New Crate Map (11 crates)

### Shared Foundation (2 crates)

| Crate | 役割 | 依存 |
|---|---|---|
| **kami-eng-core** | 共通基盤: constraint solver, parametric engine, undo/redo (command pattern), snap/grid, measurement, selection system, layer manager, DRC/ERC base, symbol/library management, file format registry | kami-core, kami-scene-graph, kami-input, glam, hecs |
| **kami-eng-render** | Engineering 2D/3D rendering: schematic line, pad/pin, dimension annotation, hatching, center-line, cross-section view, grid overlay, ruler, cursor crosshair, zoom-to-fit | kami-render, kami-ui-gpu, kami-text, kami-postfx |

### Domain Crates (5 crates)

| Crate | 役割 | 依存 |
|---|---|---|
| **kami-eda** | EDA: schematic editor (symbol, wire, bus, net, hierarchy), PCB layout (footprint, trace, via, pour, DRC), netlist (SPICE, Verilog gate-level), BOM generation, Gerber/ODB++ export | kami-eng-core, kami-eng-render, kami-graph |
| **kami-cad** | CAD: BREP kernel (face, edge, vertex, shell, solid), parametric feature tree (extrude, revolve, fillet, chamfer, boolean, sweep, loft), assembly (mate, constraint), STEP/IGES import/export, drawing/annotation | kami-eng-core, kami-eng-render, kami-sdf, kami-scad, kami-mesher, kami-gltf |
| **kami-cam** | CAM: toolpath generation (2.5D/3D), G-code/M-code output, tool library, stock definition, roughing/finishing strategy, collision detection, material removal simulation, CNC post-processor | kami-eng-core, kami-eng-render, kami-cad, kami-voxel |
| **kami-rtl** | RTL: HDL editor (Verilog/VHDL/SystemVerilog syntax), digital logic schematic, simulation engine (event-driven), waveform viewer, synthesis (logic optimization, technology mapping), timing analysis (STA), FPGA bitstream target | kami-eng-core, kami-eng-render, kami-eda |
| **kami-cae** | CAE: FEA mesh generation (tet/hex), boundary condition, material library, linear/nonlinear solver (CG/GMRES), thermal/structural/modal analysis, post-processing (stress/strain/displacement color map, deformation animation) | kami-eng-core, kami-eng-render, kami-cad, kami-mesher, kami-voxel |

### Integration Crates (2 crates)

| Crate | 役割 | 依存 |
|---|---|---|
| **kami-eng-io** | File I/O: STEP AP203/AP214, IGES, STL, OBJ, glTF/GLB, Gerber RS-274X, ODB++, Excellon drill, G-code, Verilog, VHDL, SPICE netlist, EDIF, LEF/DEF, Liberty (.lib), SDF, VCD waveform, BSDL, JED/SVF | kami-eng-core |
| **kami-eng-web** | WASM entry point: wasm-bindgen exports for all engineering functions, JS interop, Svelte SDK bridge | kami-eda, kami-cad, kami-cam, kami-rtl, kami-cae, kami-web |

### Updated kami-engine Cargo.toml (workspace members 追加)

```toml
# Engineering SDK crates
"kami-eng-core",
"kami-eng-render",
"kami-eda",
"kami-cad",
"kami-cam",
"kami-rtl",
"kami-cae",
"kami-eng-io",
"kami-eng-web",
```

## Domain Deep Dive

### 1. EDA (Electronic Design Automation)

#### 1.1 Schematic Editor

```
SchematicSheet
├── Symbol instances (component placements)
│   ├── Pin[] (electrical connection points)
│   └── Graphics[] (lines, arcs, text — decorative)
├── Wire[] (electrical connections between pins)
├── Bus[] (grouped signal bundle)
├── NetLabel[] (named net references)
├── PowerPort[] (VCC, GND, etc.)
├── Junction[] (wire intersection markers)
└── HierarchicalSheet[] (sub-sheet references)
```

**Data Model (hecs components):**

```rust
// kami-eda/src/schematic.rs

/// Schematic sheet entity
pub struct SchematicSheet {
    pub name: String,
    pub size: SheetSize,        // A4, A3, A2, A1, A0, custom
    pub grid_spacing: f32,      // default 2.54mm (100mil)
}

/// Component symbol instance
pub struct SymbolInstance {
    pub library_ref: String,    // e.g. "Resistor_SMD:R_0402_1005Metric"
    pub designator: String,     // e.g. "R1", "U3", "C15"
    pub value: String,          // e.g. "10kΩ", "STM32F407VGT6"
    pub position: Vec2,
    pub rotation: f32,          // 0, 90, 180, 270
    pub mirror: bool,
}

/// Electrical pin on a symbol
pub struct Pin {
    pub name: String,           // e.g. "VDD", "PA0", "GND"
    pub number: String,         // physical pin number
    pub electrical_type: PinType, // Input, Output, Bidirectional, Passive, Power, OpenCollector, etc.
    pub position: Vec2,         // relative to symbol origin
    pub orientation: PinOrientation,
}

pub enum PinType {
    Input, Output, Bidirectional, TriState, Passive,
    Power, OpenCollector, OpenEmitter, NotConnected, Unspecified,
}

/// Wire segment
pub struct Wire {
    pub start: Vec2,
    pub end: Vec2,
    pub net_id: Option<NetId>,  // assigned during netlist generation
}

/// Net (auto-generated from wire connectivity)
pub struct Net {
    pub name: String,           // auto or user-assigned
    pub pins: Vec<(Entity, usize)>, // (symbol_entity, pin_index)
}
```

**ERC (Electrical Rules Check):**

| Rule | Severity | Description |
|---|---|---|
| Unconnected pin | Error | Input/Output pin with no wire |
| Output-to-output | Error | Two output pins on same net |
| Power pin undriven | Error | Power pin with no power source |
| Input floating | Warning | Input pin connected only to passive |
| Net with single pin | Warning | Net has only one connection |
| Duplicate designator | Error | Same designator on multiple symbols |
| Missing value | Warning | Symbol without value assignment |

#### 1.2 PCB Layout

```
PcbBoard
├── BoardOutline (closed polyline, milling boundary)
├── Layer Stack
│   ├── F.Cu (front copper)
│   ├── In1.Cu ... InN.Cu (inner copper)
│   ├── B.Cu (back copper)
│   ├── F.SilkS / B.SilkS (silkscreen)
│   ├── F.Mask / B.Mask (solder mask)
│   ├── F.Paste / B.Paste (solder paste)
│   ├── Edge.Cuts (board outline)
│   └── User layers (mechanical, assembly, fab notes)
├── Footprint[] (component land patterns)
│   ├── Pad[] (SMD, TH, NPTH)
│   └── Courtyard / Fab layer graphics
├── Trace[] (copper routing segments)
├── Via[] (layer transitions)
├── Zone[] (copper pour / ground plane)
├── DimensionAnnotation[]
└── DrillTable
```

**Auto-Router Strategy:**

```rust
pub enum RoutingStrategy {
    /// Interactive: user-guided with DRC snap
    Interactive,
    /// Push-and-shove: move existing traces to accommodate new route
    PushAndShove,
    /// Grid-based A* (Lee algorithm variant) for simple boards
    GridRouter {
        grid_size: f32,
        via_cost: f32,
        layer_change_cost: f32,
    },
    /// Topological router for differential pairs and length matching
    Topological {
        max_detour_ratio: f32,
    },
}
```

**DRC (Design Rules Check):**

| Rule | Parameter | Default |
|---|---|---|
| Minimum trace width | `min_trace_width_mm` | 0.15 |
| Minimum clearance | `min_clearance_mm` | 0.15 |
| Minimum via drill | `min_via_drill_mm` | 0.3 |
| Minimum via annular ring | `min_annular_ring_mm` | 0.13 |
| Minimum hole-to-hole | `min_hole_clearance_mm` | 0.25 |
| Copper-to-edge clearance | `min_edge_clearance_mm` | 0.3 |
| Silk over pad | `silk_pad_clearance_mm` | 0.1 |
| Courtyard overlap | `courtyard_check` | true |
| Unrouted nets | `check_unrouted` | true |
| Differential pair skew | `max_dp_skew_mm` | 0.1 |

**Gerber Export Pipeline:**

```
PCB data → Layer separation → Aperture definition (D-codes)
  → RS-274X Gerber per layer → Excellon drill file → Pick-and-place CSV
  → BOM CSV → Assembly drawing PDF → Fabrication notes
```

#### 1.3 kami-graph Integration (PCB Layout Rendering)

既存 `kami-graph` の `PcbLayout` アルゴリズムを EDA PCB レンダリングに活用:

- Layer 0 (component side) / Layer 1 (solder side) の 2-layer basic view
- Bus lines → signal bus rendering
- Force-directed → auto-placement initial seed
- wgpu instanced rendering for thousands of pads/vias

### 2. CAD (Computer-Aided Design)

#### 2.1 BREP Kernel

```
Topology Hierarchy:
  Solid
  ├── Shell (closed boundary)
  │   ├── Face (bounded surface region)
  │   │   ├── Wire (closed loop of edges on face)
  │   │   │   └── Edge (bounded curve)
  │   │   │       ├── Vertex (start)
  │   │   │       └── Vertex (end)
  │   │   └── Surface (underlying geometric surface)
  │   └── ...
  └── ...
```

**Core Types:**

```rust
// kami-cad/src/brep.rs

pub type TopoId = u64; // stable topology identifier

/// Boundary Representation solid
pub struct BrepSolid {
    pub id: TopoId,
    pub shells: Vec<BrepShell>,
}

pub struct BrepShell {
    pub id: TopoId,
    pub faces: Vec<BrepFace>,
    pub orientation: Orientation, // Forward, Reversed
}

pub struct BrepFace {
    pub id: TopoId,
    pub surface: Surface,
    pub wires: Vec<BrepWire>,    // outer + inner (holes)
    pub orientation: Orientation,
}

pub struct BrepEdge {
    pub id: TopoId,
    pub curve: Curve,
    pub start: TopoId,          // vertex id
    pub end: TopoId,            // vertex id
    pub t_range: (f64, f64),    // parameter range on curve
}

pub struct BrepVertex {
    pub id: TopoId,
    pub point: DVec3,           // f64 precision for CAD
}

/// Geometric surfaces
pub enum Surface {
    Plane { origin: DVec3, normal: DVec3 },
    Cylinder { origin: DVec3, axis: DVec3, radius: f64 },
    Cone { origin: DVec3, axis: DVec3, half_angle: f64 },
    Sphere { center: DVec3, radius: f64 },
    Torus { center: DVec3, axis: DVec3, major_r: f64, minor_r: f64 },
    BSpline { control_points: Vec<Vec<DVec3>>, knots_u: Vec<f64>, knots_v: Vec<f64>, degree_u: u32, degree_v: u32 },
    Revolution { profile: Box<Curve>, axis: DVec3, origin: DVec3 },
    Extrusion { profile: Box<Curve>, direction: DVec3 },
}

/// Geometric curves
pub enum Curve {
    Line { origin: DVec3, direction: DVec3 },
    Circle { center: DVec3, normal: DVec3, radius: f64 },
    Ellipse { center: DVec3, major_axis: DVec3, minor_axis: DVec3 },
    BSpline { control_points: Vec<DVec3>, knots: Vec<f64>, degree: u32 },
}
```

#### 2.2 Parametric Feature Tree

```rust
// kami-cad/src/feature.rs

pub enum Feature {
    /// Base sketch on a plane
    Sketch {
        plane: SketchPlane,
        entities: Vec<SketchEntity>, // line, arc, circle, spline, dimension, constraint
    },
    /// Linear extrusion from sketch profile
    Extrude {
        sketch_ref: FeatureId,
        direction: ExtrudeDirection, // Blind(f64), ThroughAll, ToFace(TopoId), Symmetric(f64)
        operation: BooleanOp,        // New, Add, Cut, Intersect
    },
    /// Rotational sweep from sketch profile
    Revolve {
        sketch_ref: FeatureId,
        axis: SketchAxisRef,
        angle: f64,                  // radians, 2π for full revolution
        operation: BooleanOp,
    },
    /// Edge rounding
    Fillet {
        edges: Vec<TopoId>,
        radius: f64,
        variable: Option<Vec<(f64, f64)>>, // (t, radius) for variable fillet
    },
    /// Edge beveling
    Chamfer {
        edges: Vec<TopoId>,
        distance: f64,
        angle: Option<f64>,          // None = symmetric
    },
    /// Sweep along path
    Sweep {
        profile_ref: FeatureId,
        path_ref: FeatureId,
        twist_angle: f64,
    },
    /// Loft between profiles
    Loft {
        profile_refs: Vec<FeatureId>,
        guide_curves: Vec<FeatureId>,
    },
    /// Shell (hollow out solid)
    Shell {
        faces_to_remove: Vec<TopoId>,
        thickness: f64,
    },
    /// Linear/circular pattern
    Pattern {
        feature_refs: Vec<FeatureId>,
        pattern_type: PatternType,
    },
    /// Boolean operation with another body
    Boolean {
        tool_body: FeatureId,
        operation: BooleanOp,
    },
}

pub enum BooleanOp { New, Add, Cut, Intersect }

pub enum SketchEntity {
    Line { start: DVec2, end: DVec2 },
    Arc { center: DVec2, start: DVec2, end: DVec2, clockwise: bool },
    Circle { center: DVec2, radius: f64 },
    Spline { control_points: Vec<DVec2>, degree: u32 },
    Dimension { entity_refs: Vec<usize>, value: f64, kind: DimensionKind },
    Constraint { kind: ConstraintKind, entity_refs: Vec<usize> },
}

pub enum ConstraintKind {
    Coincident, Parallel, Perpendicular, Tangent, Equal,
    Horizontal, Vertical, Fixed, Symmetric, Concentric,
    Midpoint, Collinear,
}
```

#### 2.3 Assembly System

```rust
// kami-cad/src/assembly.rs

pub struct Assembly {
    pub id: TopoId,
    pub instances: Vec<PartInstance>,
    pub constraints: Vec<AssemblyConstraint>,
}

pub struct PartInstance {
    pub id: TopoId,
    pub part_ref: PartRef,       // reference to part definition
    pub transform: DAffine3,     // placement in assembly space
    pub name: String,
    pub suppressed: bool,
}

pub enum AssemblyConstraint {
    Mate { face_a: (TopoId, TopoId), face_b: (TopoId, TopoId), offset: f64 },
    Align { axis_a: (TopoId, TopoId), axis_b: (TopoId, TopoId) },
    Insert { cyl_a: (TopoId, TopoId), cyl_b: (TopoId, TopoId) },
    Angle { face_a: (TopoId, TopoId), face_b: (TopoId, TopoId), angle: f64 },
    Distance { entity_a: (TopoId, TopoId), entity_b: (TopoId, TopoId), distance: f64 },
    Gear { axis_a: (TopoId, TopoId), axis_b: (TopoId, TopoId), ratio: f64 },
}
```

#### 2.4 Integration with Existing Crates

| Existing Crate | CAD Usage |
|---|---|
| kami-sdf | Quick preview of features (CSG preview before BREP rebuild) |
| kami-scad | OpenSCAD parametric models → BREP import path |
| kami-mesher | Tessellation of BREP faces for wgpu rendering |
| kami-gltf | glTF/GLB export of tessellated CAD models |
| kami-scene-graph | Assembly hierarchy (parent-child transform) |

### 3. CAM (Computer-Aided Manufacturing)

#### 3.1 Toolpath Generation

```rust
// kami-cam/src/toolpath.rs

pub struct CamJob {
    pub stock: Stock,
    pub operations: Vec<CamOperation>,
    pub tool_library: ToolLibrary,
    pub machine: MachineConfig,
}

pub struct Stock {
    pub shape: StockShape,       // Block, Cylinder, FromModel
    pub material: CamMaterial,
    pub dimensions: DVec3,       // bounding dimensions
}

pub enum CamOperation {
    /// 2.5D face milling (flat surface)
    FaceMill {
        tool_ref: ToolId,
        depth: f64,
        stepover: f64,            // % of tool diameter
        strategy: FaceStrategy,   // Zigzag, Spiral, OneWay
        feed_rate: f64,           // mm/min
        spindle_rpm: f64,
    },
    /// 2.5D pocket (enclosed region removal)
    Pocket {
        tool_ref: ToolId,
        region: PocketRegion,     // from CAD face selection
        depth: f64,
        step_down: f64,           // depth per pass
        stepover: f64,
        strategy: PocketStrategy, // Zigzag, Spiral, Trochoidal
        corner_mode: CornerMode,  // Sharp, Round, Loop
    },
    /// 2.5D contour (profile following)
    Contour {
        tool_ref: ToolId,
        profile: ContourProfile,
        depth: f64,
        step_down: f64,
        side: ContourSide,        // Inside, Outside, On
        lead_in: LeadType,        // Line, Arc, Tangent
    },
    /// 3D surface finishing
    Surface3D {
        tool_ref: ToolId,
        surface_refs: Vec<TopoId>,
        strategy: Surface3DStrategy, // Parallel, Scallop, Pencil, Flowline
        stepover: f64,
        tolerance: f64,            // surface deviation tolerance
    },
    /// Drilling
    Drill {
        tool_ref: ToolId,
        holes: Vec<DrillHole>,
        cycle: DrillCycle,         // Standard, Peck, ChipBreak, Tapping, Boring
        depth: f64,
        peck_depth: Option<f64>,
    },
    /// Turning (lathe)
    Turn {
        tool_ref: ToolId,
        profile: TurnProfile,
        operation: TurnOp,         // Roughing, Finishing, Grooving, Threading, Parting
        feed_per_rev: f64,
        spindle_rpm: f64,
    },
}

pub struct Tool {
    pub id: ToolId,
    pub name: String,
    pub tool_type: ToolType,      // EndMill, BallNose, BullNose, Drill, Tap, FaceMill, Lathe
    pub diameter: f64,
    pub flute_length: f64,
    pub overall_length: f64,
    pub flute_count: u32,
    pub corner_radius: Option<f64>,
    pub material: ToolMaterial,   // HSS, Carbide, Ceramic, CBN, PCD
    pub coating: Option<String>,  // TiN, TiAlN, AlTiN, DLC, etc.
}
```

#### 3.2 G-code Generation

```rust
// kami-cam/src/gcode.rs

pub struct GcodeConfig {
    pub machine: MachineType,     // Mill3Axis, Mill4Axis, Mill5Axis, Lathe, LaserCutter, Printer3D
    pub post_processor: PostProcessor, // Fanuc, Siemens, Haas, Heidenhain, LinuxCNC, Marlin, Grbl
    pub coordinate_system: CoordSystem, // G54-G59
    pub safe_height: f64,
    pub retract_height: f64,
    pub units: GcodeUnits,        // Metric (G21), Imperial (G20)
    pub coolant: CoolantMode,     // Off, Flood (M8), Mist (M7), Through
}

/// Generate G-code from toolpath
pub fn generate_gcode(job: &CamJob, config: &GcodeConfig) -> String {
    // Header: program number, units, coordinate system
    // Tool changes: T## M06
    // Per-operation: G00 rapid → G01/G02/G03 cutting moves
    // Canned cycles: G73 peck, G76 bore, G84 tap
    // Footer: M30 program end
    todo!()
}
```

#### 3.3 Material Removal Simulation

```rust
// kami-cam/src/simulation.rs — voxel-based stock removal visualization

pub struct CamSimulation {
    pub stock_voxels: kami_voxel::VoxelVolume,  // reuse existing kami-voxel
    pub tool_swept_volume: kami_sdf::SdfNode,   // tool shape as SDF
    pub current_step: usize,
    pub collision_detected: bool,
}

impl CamSimulation {
    /// Step simulation forward: subtract tool swept volume from stock
    pub fn step(&mut self, tool_position: DVec3, tool_orientation: DQuat) {
        // Transform tool SDF to current position
        // Boolean subtract from stock voxels
        // Check collision with fixture/clamp geometry
    }
}
```

### 4. RTL (Register Transfer Level)

#### 4.1 HDL Editor

```rust
// kami-rtl/src/hdl.rs

/// Parsed HDL module representation
pub struct RtlModule {
    pub name: String,
    pub ports: Vec<RtlPort>,
    pub parameters: Vec<RtlParameter>,
    pub internals: Vec<RtlSignal>,
    pub instances: Vec<RtlInstance>,
    pub always_blocks: Vec<AlwaysBlock>,
    pub assigns: Vec<ContinuousAssign>,
}

pub struct RtlPort {
    pub name: String,
    pub direction: PortDirection,  // Input, Output, Inout
    pub width: BitRange,           // [7:0], [31:0], scalar
    pub port_type: SignalType,     // Wire, Reg, Logic
}

pub enum AlwaysBlock {
    /// Combinational logic: always @(*) or always_comb
    Combinational {
        statements: Vec<RtlStatement>,
    },
    /// Sequential logic: always @(posedge clk) or always_ff
    Sequential {
        clock: ClockEdge,
        reset: Option<ResetSpec>,
        statements: Vec<RtlStatement>,
    },
}

pub enum RtlStatement {
    Assign { target: String, expr: RtlExpr },
    If { cond: RtlExpr, then_block: Vec<RtlStatement>, else_block: Vec<RtlStatement> },
    Case { selector: RtlExpr, items: Vec<(RtlExpr, Vec<RtlStatement>)>, default: Vec<RtlStatement> },
    ForLoop { var: String, range: (i64, i64), body: Vec<RtlStatement> },
}

pub enum RtlExpr {
    Literal(u64, u32),            // value, bit_width
    Signal(String),
    BinaryOp(Box<RtlExpr>, BinOp, Box<RtlExpr>),
    UnaryOp(UnOp, Box<RtlExpr>),
    Concat(Vec<RtlExpr>),
    Repeat(u32, Box<RtlExpr>),
    Select(Box<RtlExpr>, BitRange),
    Ternary(Box<RtlExpr>, Box<RtlExpr>, Box<RtlExpr>),
    FunctionCall(String, Vec<RtlExpr>),
}
```

#### 4.2 Event-Driven Simulation

```rust
// kami-rtl/src/simulator.rs

pub struct RtlSimulator {
    pub time: u64,                 // simulation time (in time units)
    pub event_queue: BinaryHeap<SimEvent>,
    pub signals: HashMap<String, SignalState>,
    pub modules: Vec<SimModule>,
    pub vcd_writer: Option<VcdWriter>, // Value Change Dump
}

pub struct SimEvent {
    pub time: u64,
    pub signal: String,
    pub value: LogicValue,
    pub delay_type: DelayType,     // Transport, Inertial
}

/// 4-value logic (IEEE 1364)
pub enum LogicValue {
    Zero,
    One,
    X,          // Unknown
    Z,          // High-impedance
}

/// Multi-bit signal value
pub struct SignalState {
    pub width: u32,
    pub values: Vec<LogicValue>,   // LSB first
    pub strength: DriveStrength,
}

impl RtlSimulator {
    /// Run simulation for specified duration
    pub fn run(&mut self, duration: u64) {
        let end_time = self.time + duration;
        while let Some(event) = self.event_queue.peek() {
            if event.time > end_time { break; }
            let event = self.event_queue.pop().unwrap();
            self.time = event.time;
            self.apply_event(&event);
            self.evaluate_sensitive_blocks(&event.signal);
        }
        self.time = end_time;
    }
}
```

#### 4.3 Waveform Viewer

```rust
// kami-rtl/src/waveform.rs — rendered via kami-eng-render (wgpu)

pub struct WaveformView {
    pub signals: Vec<WaveformSignal>,
    pub time_range: (u64, u64),
    pub cursor_time: u64,
    pub markers: Vec<WaveformMarker>,
    pub zoom_level: f64,
    pub scroll_offset: f64,
}

pub struct WaveformSignal {
    pub name: String,
    pub width: u32,
    pub transitions: Vec<(u64, LogicValue)>, // (time, new_value)
    pub display_format: DisplayFormat,        // Binary, Hex, Decimal, Analog
    pub color: [f32; 4],
    pub height: f32,
    pub group: Option<String>,
}
```

#### 4.4 Logic Synthesis (Basic)

```rust
// kami-rtl/src/synthesis.rs

/// Technology-independent optimization
pub enum OptimizationPass {
    ConstantFolding,
    DeadCodeElimination,
    CommonSubexpressionElimination,
    BooleanOptimization,        // Quine-McCluskey / Espresso
    StateMachineOptimization,
    RegisterRetiming,
}

/// Technology mapping target
pub enum TechnologyTarget {
    /// Generic gate library (for learning/visualization)
    GenericGates,
    /// FPGA LUT-based mapping
    FpgaLut {
        lut_size: u32,           // 4-LUT, 6-LUT
        family: FpgaFamily,      // Xilinx7, UltraScale, IntelCyclone, IntelStratix, Lattice
    },
    /// Standard cell (ASIC)
    StdCell {
        liberty_file: String,    // .lib timing library
    },
}
```

### 5. CAE (Computer-Aided Engineering)

#### 5.1 FEA Mesh Generation

```rust
// kami-cae/src/mesh.rs

pub struct FeaMesh {
    pub nodes: Vec<FeaNode>,
    pub elements: Vec<FeaElement>,
    pub node_sets: HashMap<String, Vec<NodeId>>,
    pub element_sets: HashMap<String, Vec<ElementId>>,
}

pub struct FeaNode {
    pub id: NodeId,
    pub position: DVec3,
    pub dof: DegreeOfFreedom,     // translational + rotational
}

pub enum FeaElement {
    /// 1D beam element
    Beam2 { nodes: [NodeId; 2], section: BeamSection },
    /// 2D triangle (linear)
    Tri3 { nodes: [NodeId; 3], thickness: f64 },
    /// 2D triangle (quadratic)
    Tri6 { nodes: [NodeId; 6], thickness: f64 },
    /// 2D quad (linear)
    Quad4 { nodes: [NodeId; 4], thickness: f64 },
    /// 3D tetrahedron (linear)
    Tet4 { nodes: [NodeId; 4] },
    /// 3D tetrahedron (quadratic, 10-node)
    Tet10 { nodes: [NodeId; 10] },
    /// 3D hexahedron (linear)
    Hex8 { nodes: [NodeId; 8] },
    /// 3D hexahedron (quadratic, 20-node)
    Hex20 { nodes: [NodeId; 20] },
}

/// Generate tetrahedral mesh from BREP solid (Delaunay)
pub fn mesh_brep_solid(solid: &BrepSolid, config: &MeshConfig) -> FeaMesh {
    // 1. Discretize BREP faces into surface triangulation
    // 2. Boundary-conforming Delaunay tetrahedralization
    // 3. Quality improvement (Laplacian smoothing, edge flips)
    // 4. Assign node/element IDs
    todo!()
}

pub struct MeshConfig {
    pub element_size: f64,         // target element size
    pub min_size: f64,             // minimum element size (for curvature refinement)
    pub max_size: f64,
    pub curvature_refinement: bool,
    pub feature_angle: f64,        // degrees — edges sharper than this get refinement
    pub quality_threshold: f64,    // minimum element aspect ratio
    pub element_order: ElementOrder, // Linear, Quadratic
}
```

#### 5.2 Solver

```rust
// kami-cae/src/solver.rs

pub enum AnalysisType {
    /// Linear static: Ku = F
    LinearStatic,
    /// Nonlinear static (Newton-Raphson iteration)
    NonlinearStatic {
        max_iterations: u32,
        convergence_tolerance: f64,
        load_steps: u32,
    },
    /// Modal analysis: eigenvalue problem Kφ = ω²Mφ
    Modal {
        num_modes: u32,
        frequency_range: Option<(f64, f64)>,
    },
    /// Steady-state thermal: KT = Q
    ThermalSteady,
    /// Transient thermal: CṪ + KT = Q
    ThermalTransient {
        time_step: f64,
        total_time: f64,
    },
    /// Linear buckling: (K + λKg)φ = 0
    Buckling { num_modes: u32 },
    /// Frequency response
    FrequencyResponse {
        freq_range: (f64, f64),
        freq_steps: u32,
        damping_ratio: f64,
    },
}

/// Material properties
pub struct FeMaterial {
    pub name: String,
    pub model: MaterialModel,
}

pub enum MaterialModel {
    LinearElastic {
        youngs_modulus: f64,      // Pa
        poissons_ratio: f64,
        density: f64,             // kg/m³
        thermal_expansion: f64,   // 1/K
        thermal_conductivity: f64, // W/(m·K)
        specific_heat: f64,       // J/(kg·K)
    },
    Hyperelastic {
        model: HyperelasticModel, // MooneyRivlin, NeoHookean, Ogden
        coefficients: Vec<f64>,
    },
    ElastoPlastic {
        yield_stress: f64,
        hardening: HardeningModel, // Isotropic, Kinematic, Combined
        stress_strain_curve: Vec<(f64, f64)>,
    },
}

/// Boundary conditions
pub enum BoundaryCondition {
    /// Fixed displacement (Dirichlet)
    Displacement {
        node_set: String,
        dof: DofMask,             // which DOFs are fixed
        value: DVec3,             // prescribed displacement
    },
    /// Applied force (Neumann)
    Force {
        node_set: String,
        value: DVec3,             // force vector
    },
    /// Pressure on face
    Pressure {
        face_set: String,
        value: f64,               // Pa
    },
    /// Temperature (for thermal)
    Temperature {
        node_set: String,
        value: f64,               // K
    },
    /// Convection
    Convection {
        face_set: String,
        coefficient: f64,         // W/(m²·K)
        ambient_temp: f64,        // K
    },
}

/// Sparse matrix solver
pub enum SolverMethod {
    /// Direct solver (LU/Cholesky) — exact, good for small/medium
    DirectCholesky,
    /// Conjugate Gradient — symmetric positive definite
    ConjugateGradient {
        max_iter: u32,
        tolerance: f64,
        preconditioner: Preconditioner, // None, Jacobi, IncompleteCholesky, AMG
    },
    /// GMRES — general (nonsymmetric)
    Gmres {
        max_iter: u32,
        tolerance: f64,
        restart: u32,
        preconditioner: Preconditioner,
    },
}
```

#### 5.3 Post-Processing

```rust
// kami-cae/src/postprocess.rs — visualized via kami-eng-render (wgpu)

pub enum ResultField {
    Displacement,                  // vector field
    VonMisesStress,               // scalar field
    PrincipalStress(u8),          // 1st, 2nd, 3rd principal
    Strain,                        // tensor field
    Temperature,                   // scalar field
    HeatFlux,                      // vector field
    ModeShape(u32),               // eigenvector for mode N
    SafetyFactor,                  // scalar (yield/applied)
    ReactionForce,                 // vector at constrained nodes
}

pub struct PostProcessView {
    pub result_field: ResultField,
    pub display_mode: DisplayMode,
    pub color_map: ColorMap,       // Rainbow, Jet, Viridis, Coolwarm, Grayscale
    pub deformation_scale: f64,    // amplify displacement for visualization
    pub contour_levels: u32,       // number of color bands
    pub min_value: Option<f64>,    // clamp range
    pub max_value: Option<f64>,
    pub show_mesh: bool,
    pub show_undeformed: bool,     // ghost overlay of original shape
    pub animate: bool,             // animate mode shapes / transient results
}
```

## WIT Interface Design

### Package: `etzhayyim:kami-eng-core@1.0.0`

```wit
package etzhayyim:kami-eng-core@1.0.0;

interface constraint-solver {
    record constraint {
        id: u64,
        kind: constraint-kind,
        entity-refs: list<u64>,
        value: option<f64>,
        status: constraint-status,
    }

    enum constraint-kind {
        coincident, parallel, perpendicular, tangent, equal,
        horizontal, vertical, fixed, symmetric, concentric,
        distance, angle, radius, diameter,
    }

    enum constraint-status { satisfied, under-constrained, over-constrained, conflicting }

    solve: func(constraints: list<constraint>) -> result<list<constraint>, string>;
}

interface parameter-engine {
    record parameter {
        name: string,
        value: f64,
        expression: option<string>,
        min-value: option<f64>,
        max-value: option<f64>,
    }

    evaluate: func(params: list<parameter>) -> result<list<parameter>, string>;
    update: func(name: string, value: f64) -> result<list<parameter>, string>;
}

interface history {
    record history-entry {
        id: u64,
        action: string,
        timestamp: u64,
        data: list<u8>,
    }

    undo: func() -> result<history-entry, string>;
    redo: func() -> result<history-entry, string>;
    push: func(action: string, data: list<u8>) -> u64;
    get-stack: func() -> list<history-entry>;
}

interface measurement {
    record measure-result {
        kind: string,
        value: f64,
        unit: string,
        points: list<tuple<f64, f64, f64>>,
    }

    distance-point-point: func(a: tuple<f64, f64, f64>, b: tuple<f64, f64, f64>) -> measure-result;
    angle-three-points: func(a: tuple<f64, f64, f64>, b: tuple<f64, f64, f64>, c: tuple<f64, f64, f64>) -> measure-result;
    area-face: func(face-id: u64) -> measure-result;
    volume-solid: func(solid-id: u64) -> measure-result;
}

interface layer-manager {
    record layer {
        id: u32,
        name: string,
        visible: bool,
        locked: bool,
        color: tuple<f32, f32, f32, f32>,
        line-width: f32,
    }

    create-layer: func(name: string) -> layer;
    set-active: func(id: u32) -> result<_, string>;
    set-visibility: func(id: u32, visible: bool) -> result<_, string>;
    list-layers: func() -> list<layer>;
}
```

### Package: `etzhayyim:kami-eda@1.0.0`

```wit
package etzhayyim:kami-eda@1.0.0;

interface schematic {
    use etzhayyim:kami-eng-core/layer-manager.{layer};

    record symbol-instance {
        id: u64,
        library-ref: string,
        designator: string,
        value: string,
        x: f32,
        y: f32,
        rotation: f32,
        mirror: bool,
    }

    record wire-segment { id: u64, x1: f32, y1: f32, x2: f32, y2: f32, net-id: option<u64> }
    record net { id: u64, name: string, pin-count: u32 }

    place-symbol: func(library-ref: string, x: f32, y: f32) -> symbol-instance;
    route-wire: func(x1: f32, y1: f32, x2: f32, y2: f32) -> wire-segment;
    generate-netlist: func() -> list<net>;
    run-erc: func() -> list<string>;
    export-spice: func() -> string;
}

interface pcb-layout {
    record footprint { id: u64, library-ref: string, designator: string, x: f32, y: f32, rotation: f32, layer: string }
    record trace { id: u64, net-id: u64, points: list<tuple<f32, f32>>, width: f32, layer: string }
    record via { id: u64, x: f32, y: f32, drill: f32, outer-diameter: f32 }

    place-footprint: func(library-ref: string, x: f32, y: f32) -> footprint;
    route-trace: func(net-id: u64, points: list<tuple<f32, f32>>, width: f32, layer: string) -> trace;
    add-via: func(x: f32, y: f32) -> via;
    pour-zone: func(net-id: u64, boundary: list<tuple<f32, f32>>, layer: string) -> u64;
    run-drc: func() -> list<string>;
    export-gerber: func() -> list<tuple<string, list<u8>>>;
}
```

### Package: `etzhayyim:kami-cad@1.0.0`

```wit
package etzhayyim:kami-cad@1.0.0;

interface modeling {
    record solid-id { value: u64 }
    record feature-id { value: u64 }

    create-sketch: func(plane: string) -> feature-id;
    extrude: func(sketch: feature-id, distance: f64, operation: string) -> solid-id;
    revolve: func(sketch: feature-id, axis: string, angle: f64) -> solid-id;
    fillet: func(solid: solid-id, edges: list<u64>, radius: f64) -> solid-id;
    chamfer: func(solid: solid-id, edges: list<u64>, distance: f64) -> solid-id;
    boolean-op: func(a: solid-id, b: solid-id, operation: string) -> solid-id;
    shell: func(solid: solid-id, faces: list<u64>, thickness: f64) -> solid-id;
    get-feature-tree: func() -> list<tuple<u64, string, string>>;
    tessellate: func(solid: solid-id, tolerance: f64) -> list<u8>;
}

interface assembly {
    record instance-id { value: u64 }

    add-instance: func(part-ref: string, name: string) -> instance-id;
    add-mate: func(face-a: u64, face-b: u64, offset: f64) -> u64;
    solve-assembly: func() -> result<_, string>;
    get-bom: func() -> list<tuple<string, string, u32>>;
    export-step: func() -> list<u8>;
}
```

### Package: `etzhayyim:kami-cam@1.0.0`

```wit
package etzhayyim:kami-cam@1.0.0;

interface toolpath {
    record tool { id: u64, name: string, diameter: f64, flute-length: f64, tool-type: string }
    record operation-id { value: u64 }

    define-stock: func(width: f64, height: f64, depth: f64, material: string) -> u64;
    add-tool: func(name: string, diameter: f64, tool-type: string) -> tool;
    create-pocket: func(tool-id: u64, region-faces: list<u64>, depth: f64, stepover: f64) -> operation-id;
    create-contour: func(tool-id: u64, profile-edges: list<u64>, depth: f64, side: string) -> operation-id;
    create-drill: func(tool-id: u64, holes: list<tuple<f64, f64>>, depth: f64) -> operation-id;
    create-surface-3d: func(tool-id: u64, surface-faces: list<u64>, stepover: f64) -> operation-id;
    generate-gcode: func(operations: list<operation-id>, post-processor: string) -> string;
    simulate-removal: func(operations: list<operation-id>) -> list<u8>;
}
```

### Package: `etzhayyim:kami-rtl@1.0.0`

```wit
package etzhayyim:kami-rtl@1.0.0;

interface hdl {
    record module-info { name: string, port-count: u32, instance-count: u32 }
    record port-info { name: string, direction: string, width: u32 }

    parse-verilog: func(source: string) -> result<module-info, string>;
    parse-vhdl: func(source: string) -> result<module-info, string>;
    get-ports: func(module-name: string) -> list<port-info>;
    get-hierarchy: func() -> list<tuple<string, list<string>>>;
    elaborate: func(top-module: string) -> result<_, string>;
}

interface simulator {
    record signal-value { name: string, width: u32, value: string, time: u64 }

    load-design: func(top-module: string) -> result<_, string>;
    set-input: func(signal: string, value: string) -> result<_, string>;
    run: func(duration: u64) -> list<signal-value>;
    get-signal: func(name: string) -> list<tuple<u64, string>>;
    export-vcd: func() -> string;
}

interface synthesis {
    record gate-stats { gate-count: u32, lut-count: u32, ff-count: u32, max-freq-mhz: f64 }

    synthesize: func(top-module: string, target: string) -> result<gate-stats, string>;
    optimize: func(passes: list<string>) -> result<gate-stats, string>;
    report-timing: func() -> string;
    report-utilization: func() -> string;
}
```

### Package: `etzhayyim:kami-cae@1.0.0`

```wit
package etzhayyim:kami-cae@1.0.0;

interface meshing {
    record mesh-stats { node-count: u32, element-count: u32, min-quality: f64, avg-quality: f64 }

    generate-mesh: func(solid-id: u64, element-size: f64, order: string) -> result<mesh-stats, string>;
    refine-region: func(node-set: string, target-size: f64) -> result<mesh-stats, string>;
    check-quality: func() -> mesh-stats;
    export-mesh: func(format: string) -> list<u8>;
}

interface analysis {
    record analysis-id { value: u64 }

    assign-material: func(element-set: string, material-name: string) -> result<_, string>;
    apply-displacement-bc: func(node-set: string, dof: string, value: f64) -> u64;
    apply-force: func(node-set: string, fx: f64, fy: f64, fz: f64) -> u64;
    apply-pressure: func(face-set: string, value: f64) -> u64;
    run-linear-static: func() -> result<analysis-id, string>;
    run-modal: func(num-modes: u32) -> result<analysis-id, string>;
    run-thermal-steady: func() -> result<analysis-id, string>;
}

interface postprocess {
    record field-range { min-value: f64, max-value: f64, avg-value: f64 }

    get-displacement: func(analysis-id: u64) -> field-range;
    get-von-mises-stress: func(analysis-id: u64) -> field-range;
    get-temperature: func(analysis-id: u64) -> field-range;
    get-mode-frequency: func(analysis-id: u64, mode: u32) -> f64;
    export-color-map: func(analysis-id: u64, field: string, color-map: string) -> list<u8>;
    probe-point: func(analysis-id: u64, field: string, x: f64, y: f64, z: f64) -> f64;
}
```

## UI/UX Design

### Unified Workbench Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  🔧 KAMI Engineering Workbench                    ▸ EDA ▸ CAD ▸ … │
├────────┬────────────────────────────────────────────┬──────────────┤
│        │                                            │              │
│  Tool  │              Main Viewport                 │  Properties  │
│ Palette│         (wgpu canvas, full bleed)          │   Panel      │
│        │                                            │              │
│ ┌────┐ │   ┌──────────────────────────────────┐    │ ▼ Selection  │
│ │ ✏️ │ │   │                                  │    │   Type: Face │
│ │ 📐 │ │   │    3D / 2D viewport               │    │   Area: 12.4│
│ │ 📏 │ │   │    (orbit, pan, zoom)             │    │   Normal: …  │
│ │ ✂️ │ │   │                                  │    │              │
│ │ 🔲 │ │   │    Grid + Axis + Cursor           │    │ ▼ Parameters │
│ │ 🔵 │ │   │                                  │    │   depth: 10  │
│ │ 📎 │ │   │    ← stylus pressure/tilt →       │    │   radius: 2  │
│ └────┘ │   │                                  │    │              │
│        │   └──────────────────────────────────┘    │ ▼ Material   │
│ ▼ Lib  │                                            │   Steel 1020 │
│  R_0402│   ┌──────────────────────────────────┐    │              │
│  C_0603│   │ Timeline / Waveform / Feature Tree│    │ ▼ Constraints│
│  U_QFP │   │ (context-dependent bottom panel)  │    │   3 solved   │
│  …     │   └──────────────────────────────────┘    │   1 warning  │
├────────┴────────────────────────────────────────────┴──────────────┤
│  Status: ✓ DRC Pass │ 127 nets │ Grid: 0.1mm │ Layer: F.Cu │ mm  │
└─────────────────────────────────────────────────────────────────────┘
```

### Domain-Specific Viewport Modes

| Domain | Viewport | Bottom Panel | Tool Palette |
|---|---|---|---|
| **EDA Schematic** | 2D orthographic, grid snap, wire routing cursor | Netlist / ERC results | Symbol, Wire, Bus, Label, Power, Junction |
| **EDA PCB** | 2D/3D toggle, layer visibility, ratsnest overlay | DRC results / Layer stack | Footprint, Trace, Via, Zone, Dimension |
| **CAD** | 3D perspective/ortho, orbit, section plane | Feature tree (drag reorder) | Sketch, Extrude, Revolve, Fillet, Boolean, Assembly |
| **CAM** | 3D with toolpath overlay, simulation playback | G-code preview / Operation list | Stock, Tool, Pocket, Contour, Drill, Surface |
| **RTL** | Split: code editor + schematic + waveform | Waveform viewer (zoomable timeline) | Module, Port, Wire, Instance, Testbench |
| **CAE** | 3D with color map overlay, deformation | Analysis setup / Results table | Mesh, Material, BC, Load, Solve, Probe |

### Interaction Design

#### Stylus Support (via kami-input)

| Gesture | EDA | CAD | CAM | RTL | CAE |
|---|---|---|---|---|---|
| Tap | Select component | Select face/edge | Select operation | Select signal | Select node |
| Drag | Move component / Route wire | Sketch draw / Orbit | — | — | — |
| Pressure | Line width (sketch) | Freeform curve weight | — | — | — |
| Tilt | — | Sculpt direction | — | — | — |
| Two-finger | Pan + Zoom | Pan + Zoom | Pan + Zoom | Pan + Zoom | Pan + Zoom |

#### Keyboard Shortcuts (cross-domain)

| Key | Action |
|---|---|
| `Space` | Pan mode (hold) |
| `Z` | Zoom-to-fit |
| `G` | Toggle grid |
| `L` | Toggle layer panel |
| `M` | Measure tool |
| `Ctrl+Z` | Undo |
| `Ctrl+Shift+Z` | Redo |
| `Delete` | Delete selected |
| `Escape` | Cancel current operation |
| `Tab` | Cycle viewport mode (2D↔3D) |
| `1-9` | Quick layer select |

### Color Palette (Nintendo-derived Engineering)

```
Background:     #f0ead6  (Nintendo cream)
Grid:           #e0d9c4  (subtle grid lines)
Grid Major:     #c8c0a8  (major grid lines)
Cursor:         #ff6b6b  (warm red crosshair)
Selection:      #4ecdc4  (teal highlight)
Hover:          #ffe66d  (warm yellow)

--- EDA Colors ---
Wire:           #2d3436  (dark gray)
Bus:            #0984e3  (blue)
Power Net:      #d63031  (red)
GND Net:        #00b894  (green)
Copper F.Cu:    #e74c3c  (red copper)
Copper B.Cu:    #3498db  (blue copper)
Silkscreen:     #f5f5dc  (cream white)
Courtyard:      #a29bfe  (lavender)

--- CAD Colors ---
Solid Face:     #b8c5d6  (steel blue)
Edge:           #2d3436  (dark)
Sketch Active:  #00b894  (green)
Sketch Locked:  #636e72  (gray)
Dimension:      #e17055  (coral)

--- CAE Colors ---
Stress Low:     #0984e3  (blue)
Stress Mid:     #fdcb6e  (yellow)
Stress High:    #e74c3c  (red)
Displacement:   #6c5ce7  (purple gradient)
```

### Mobile / Tablet Adaptation

| Screen | Layout |
|---|---|
| Desktop (>1024px) | 3-column: Tool + Viewport + Properties |
| Tablet (768-1024px) | 2-column: Viewport + slide-over panels |
| Mobile (<768px) | Full viewport + bottom sheet panels |

全 panel は AppShell v2 の drawer/bottom-sheet pattern に従う。viewport は常に最大化。

### Cross-Domain Workflow

```
CAD (Part Design)
  → CAE (Structural Analysis) — validate design loads
  → CAM (Manufacturing) — generate machining toolpaths
  → EDA (PCB for embedded electronics) — design control board
  → RTL (FPGA logic) — custom digital controller

Integration points:
  CAD ←→ CAE:  BREP solid → FEA mesh → results overlay on CAD model
  CAD ←→ CAM:  BREP solid → toolpath on CAD faces → G-code
  EDA ←→ RTL:  Netlist → RTL module ports → synthesis → gate-level back to EDA
  CAD ←→ EDA:  3D enclosure + PCB board outline alignment
```

## W Protocol Data Model

### AT Record Kinds (Design E 3-Tier Write)

| Kind | AT Collection NSID | Domain | Tier |
|---|---|---|---|
| `kami.eng.project` | `com.etzhayyim.apps.kami.eng.project` | Shared | T2 Domain |
| `kami.eng.revision` | `com.etzhayyim.apps.kami.eng.revision` | Shared | T2 Domain |
| `kami.eda.schematic` | `com.etzhayyim.apps.kami.eda.schematic` | EDA | T2 Domain |
| `kami.eda.pcbLayout` | `com.etzhayyim.apps.kami.eda.pcbLayout` | EDA | T2 Domain |
| `kami.eda.netlist` | `com.etzhayyim.apps.kami.eda.netlist` | EDA | T2 Domain |
| `kami.eda.symbolLibrary` | `com.etzhayyim.apps.kami.eda.symbolLibrary` | EDA | T2 Domain |
| `kami.cad.model` | `com.etzhayyim.apps.kami.cad.model` | CAD | T2 Domain |
| `kami.cad.featureTree` | `com.etzhayyim.apps.kami.cad.featureTree` | CAD | T2 Domain |
| `kami.cad.assembly` | `com.etzhayyim.apps.kami.cad.assembly` | CAD | T2 Domain |
| `kami.cam.job` | `com.etzhayyim.apps.kami.cam.job` | CAM | T2 Domain |
| `kami.cam.toolLibrary` | `com.etzhayyim.apps.kami.cam.toolLibrary` | CAM | T2 Domain |
| `kami.rtl.module` | `com.etzhayyim.apps.kami.rtl.module` | RTL | T2 Domain |
| `kami.rtl.simulation` | `com.etzhayyim.apps.kami.rtl.simulation` | RTL | T2 Domain |
| `kami.cae.analysis` | `com.etzhayyim.apps.kami.cae.analysis` | CAE | T2 Domain |
| `kami.cae.meshConfig` | `com.etzhayyim.apps.kami.cae.meshConfig` | CAE | T2 Domain |
| `kami.cae.materialLib` | `com.etzhayyim.apps.kami.cae.materialLib` | CAE | T2 Domain |

### Cypher Graph Labels

| Label | Properties | Domain |
|---|---|---|
| `:EngProject` | `projectId`, `name`, `domain`, `createdAt`, `org_id`, `user_id`, `actor_id` | Shared |
| `:EngRevision` | `revisionId`, `projectId`, `parentId`, `message`, `hash`, `createdAt` | Shared |
| `:EdaSymbol` | `symbolId`, `libraryRef`, `designator`, `value`, `x`, `y`, `sheetId` | EDA |
| `:EdaNet` | `netId`, `name`, `pinCount`, `sheetId` | EDA |
| `:EdaFootprint` | `footprintId`, `designator`, `x`, `y`, `layer`, `boardId` | EDA |
| `:EdaTrace` | `traceId`, `netId`, `width`, `layer`, `boardId` | EDA |
| `:CadSolid` | `solidId`, `name`, `volume`, `surfaceArea`, `materialId` | CAD |
| `:CadFeature` | `featureId`, `solidId`, `type`, `order`, `suppressed` | CAD |
| `:CamOperation` | `operationId`, `jobId`, `toolId`, `type`, `strategy` | CAM |
| `:RtlModule` | `moduleId`, `name`, `portCount`, `instanceCount` | RTL |
| `:CaeAnalysis` | `analysisId`, `type`, `status`, `maxStress`, `maxDisplacement` | CAE |

### Graph Edges

| Edge | From → To | Meaning |
|---|---|---|
| `:HAS_REVISION` | `:EngProject` → `:EngRevision` | revision lineage |
| `:CONNECTS` | `:EdaSymbol` → `:EdaNet` | pin-net connectivity |
| `:MAPS_TO` | `:EdaSymbol` → `:EdaFootprint` | schematic-PCB mapping |
| `:ROUTES` | `:EdaTrace` → `:EdaNet` | trace-net assignment |
| `:HAS_FEATURE` | `:CadSolid` → `:CadFeature` | feature tree |
| `:MATES_WITH` | `:CadSolid` → `:CadSolid` | assembly constraint |
| `:MACHINES` | `:CamOperation` → `:CadSolid` | CAM target |
| `:ANALYZES` | `:CaeAnalysis` → `:CadSolid` | FEA target |
| `:SYNTHESIZES_TO` | `:RtlModule` → `:EdaSymbol` | FPGA → PCB |

## Agent Tools (MCP)

| Tool | Domain | Description |
|---|---|---|
| `kami.eng.createProject` | Shared | Create engineering project |
| `kami.eda.placeComponent` | EDA | Place symbol on schematic |
| `kami.eda.autoRoute` | EDA | Auto-route PCB traces |
| `kami.eda.runDrc` | EDA | Run design rules check |
| `kami.eda.exportGerber` | EDA | Export Gerber fabrication files |
| `kami.cad.createSketch` | CAD | Create parametric sketch |
| `kami.cad.extrudeFeature` | CAD | Add extrude feature |
| `kami.cad.exportStep` | CAD | Export STEP file |
| `kami.cam.generateToolpath` | CAM | Generate machining toolpath |
| `kami.cam.exportGcode` | CAM | Export G-code |
| `kami.rtl.parseHdl` | RTL | Parse Verilog/VHDL source |
| `kami.rtl.simulate` | RTL | Run HDL simulation |
| `kami.rtl.synthesize` | RTL | Synthesize to gate-level |
| `kami.cae.generateMesh` | CAE | Generate FEA mesh |
| `kami.cae.runAnalysis` | CAE | Run structural/thermal analysis |
| `kami.cae.getResults` | CAE | Get analysis results |

## Cross-Project Dependencies

| Project | Integration | Purpose |
|---|---|---|
| `etzhayyim-project-cad` | Merge into kami-cad | Existing CAD viewer → enhanced with BREP kernel |
| `etzhayyim-project-handotai` | Invoke `kami.eda.*` | Semiconductor article → related EDA designs |
| `etzhayyim-project-tsukuru` | Invoke `kami.cam.*` | Manufacturing order → G-code generation |
| `etzhayyim-project-sense` | Invoke `kami.cae.*` | 3D scan → structural analysis |
| `etzhayyim-project-maps` | Invoke `kami.cad.*` | Spatial intelligence → building 3D model |
| `etzhayyim-project-sbom` | Invoke `kami.eda.*` | Component BOM → SBOM tracking |
| `etzhayyim-project-supply-chain` | Invoke `kami.eda.*` | Component sourcing risk |
| `etzhayyim-project-pptx` | Invoke `kami.cad.*` | 3D model → presentation slide rendering |
| `etzhayyim-project-okaimono` | Invoke `kami.cam.*` | D2C product → manufacturing spec |

## Build & Deploy

```bash
# Build engineering crates
cd 40-engine/kami-engine
cargo build -p kami-eng-core
cargo build -p kami-eda
cargo build -p kami-cad
cargo build -p kami-cam
cargo build -p kami-rtl
cargo build -p kami-cae
cargo test --workspace

# WASM build (includes engineering SDK)
wasm-pack build --target web kami-eng-web

# Deploy engineering workbench app
cd 60-apps/etzhayyim-project-kami/appview/kami-eng-workbench
etzhayyim deploy --smoke-url https://eng.kami.etzhayyim.com/health
```

## Phase Plan

### Phase 1: Foundation + EDA Schematic + CAD Viewer (Existing Merge)

- kami-eng-core (constraint, parameter, history, measurement, layer, grid)
- kami-eng-render (2D line, dimension annotation, grid overlay, cursor)
- kami-eda schematic (symbol, wire, net, ERC)
- kami-cad viewer (merge existing cad project, BREP tessellation viewer)
- kami-eng-io (STEP import, Gerber export, SPICE netlist)
- kami-eng-web (WASM entry)

### Phase 2: EDA PCB + CAD Modeling + RTL

- kami-eda PCB layout (footprint, trace, via, zone, DRC, auto-router)
- kami-cad parametric (sketch, extrude, revolve, fillet, boolean)
- kami-rtl HDL editor + simulation + waveform
- kami-eng-io (Verilog, VHDL, VCD, ODB++)

### Phase 3: CAM + CAE + Synthesis

- kami-cam (toolpath, G-code, simulation)
- kami-cae (mesh, solver, post-process)
- kami-rtl synthesis + timing
- kami-eng-io (G-code post-processors, LEF/DEF, Liberty)

### Phase 4: Cross-Domain Integration + AI

- CAD↔CAE loop (design → analyze → optimize)
- EDA↔RTL loop (schematic → synthesis → back-annotate)
- CAD↔CAM loop (model → toolpath → verify)
- Murakumo LLM assisted: auto-routing hints, DFM analysis, design review
- Multi-user collaboration (presence, cursor, review)
