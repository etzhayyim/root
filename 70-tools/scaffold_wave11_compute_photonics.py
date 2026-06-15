#!/usr/bin/env python3
"""
Wave 11 Scaffolding — Compute & Photonics Frontier.

Generates L4 clean-room actors for the compute / memory / photonics stack that
the corpus was missing (root-actor coverage gap audit, 2026-06):

  - NVIDIA Cosmos compatibility  (World Foundation Models / Physical AI sim)
  - Memory design & manufacture  (DRAM, GDDR, HBM)
  - LPU                          (deterministic language-processing inference)
  - CPU                          (RISC-V core design) ............ [emphasis]
  - 光電融合 / silicon photonics + co-packaged optics ............ [emphasis]
  - Semiconductor fab + fab-automation robotics (design + implementation)

Self-contained: emits the SAME L4 surface the existing corpus uses
(schema.kotoba + src/main.py CRUD + openapi.json + manifest.json with the four
capability surfaces api/supplychain/socialpost/mcp + contract test), and the
same content-addressed CIDv1 program bundle as register_cleanroom_actors.py.

No proprietary code or credentials; resource shapes only (Charter
no-server-key, ADR-2605231525 / 2606036000). Idempotent.
"""

import os
import re
import json
import base64
import hashlib

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS_DIR)
ACTORS_DIR = os.path.join(ROOT, "20-actors")

DEFAULT_LIMIT = 20
MAX_LIMIT = 100

# ---------------------------------------------------------------------------
# Domain models — { handle: (id_prefix, category-blurb, {Entity: {field: type}}) }
# Field types: string | integer | float | boolean | datetime
# A field ending in "Id" is treated as a relation (drives ?expand=).
# Required = first 1-2 non-relational fields (matches deepen._required_fields).
# ---------------------------------------------------------------------------
COHORT = {
    "nvidia_cosmos": ("cosmos", "World Foundation Models / Physical AI simulation", {
        "WorldModel": {"name": "string", "modelType": "string", "parameters": "integer",
                       "checkpoint": "string", "license": "string"},
        "Tokenizer": {"name": "string", "kind": "string", "compressionRatio": "float",
                      "modality": "string"},
        "SimRun": {"worldModelId": "string", "prompt": "string", "frames": "integer",
                   "status": "string"},
        "Embodiment": {"name": "string", "dof": "integer", "robotType": "string", "urdf": "string"},
        "Prompt": {"text": "string", "modality": "string", "conditioning": "string"},
        "GuardrailCheck": {"simRunId": "string", "policy": "string", "verdict": "string",
                           "score": "float"},
    }),
    "hbm_memory": ("hbm", "HBM stack design / 3D TSV memory manufacture", {
        "MemoryStack": {"partNumber": "string", "generation": "string", "heightDie": "integer",
                        "capacityGb": "integer", "bandwidthGbps": "float"},
        "DramDie": {"stackId": "string", "processNode": "string", "capacityGb": "integer",
                    "knownGoodDie": "boolean"},
        "ThroughSiliconVia": {"stackId": "string", "count": "integer", "pitchUm": "float",
                              "aspectRatio": "float"},
        "MemoryChannel": {"stackId": "string", "width": "integer", "pseudoChannels": "integer",
                          "dataRateGbps": "float"},
        "RefreshPolicy": {"stackId": "string", "mode": "string", "intervalNs": "float",
                          "temperatureC": "float"},
        "TestBin": {"stackId": "string", "binCode": "string", "yield": "float", "status": "string"},
    }),
    "dram_design": ("dram", "DRAM cell / array design (DDR5 / LPDDR)", {
        "DramDevice": {"partNumber": "string", "generation": "string", "densityGb": "integer",
                       "dataRateMtps": "integer"},
        "CellArray": {"deviceId": "string", "rows": "integer", "columns": "integer",
                      "capacitorType": "string"},
        "Bank": {"deviceId": "string", "bankGroup": "integer", "index": "integer",
                 "pageSizeKb": "float"},
        "TimingProfile": {"deviceId": "string", "casLatency": "integer", "tRCD": "integer",
                          "tRP": "integer"},
        "SpeedBin": {"deviceId": "string", "grade": "string", "voltage": "float",
                     "dataRateMtps": "integer"},
        "JedecSpec": {"deviceId": "string", "standard": "string", "revision": "string",
                      "compliant": "boolean"},
    }),
    "gddr_memory": ("gddr", "GDDR6 / GDDR7 graphics memory design", {
        "GddrDevice": {"partNumber": "string", "generation": "string", "capacityGb": "integer",
                       "dataRateGbps": "float"},
        "MemoryChannel": {"deviceId": "string", "width": "integer", "prefetch": "integer",
                          "dataRateGbps": "float"},
        "SignalingMode": {"deviceId": "string", "scheme": "string", "levels": "integer",
                          "eyeHeightMv": "float"},
        "ThermalProfile": {"deviceId": "string", "tjMaxC": "float", "powerW": "float",
                           "throttle": "boolean"},
        "SpeedGrade": {"deviceId": "string", "grade": "string", "voltage": "float",
                       "dataRateGbps": "float"},
        "TestBin": {"deviceId": "string", "binCode": "string", "yield": "float", "status": "string"},
    }),
    "groq_lpu": ("lpu", "LPU deterministic language-processing inference", {
        "LpuChip": {"name": "string", "generation": "string", "sramMb": "integer", "tflops": "float"},
        "TensorStream": {"chipId": "string", "direction": "string", "widthBytes": "integer",
                         "throughputGbps": "float"},
        "ScheduleSlot": {"chipId": "string", "cycle": "integer", "instruction": "string",
                         "unit": "string"},
        "Model": {"name": "string", "parameters": "integer", "quantization": "string",
                  "tokensPerSec": "float"},
        "InterconnectLink": {"chipId": "string", "peerId": "string", "bandwidthGbps": "float",
                             "topology": "string"},
        "InferenceJob": {"modelId": "string", "chipId": "string", "batchSize": "integer",
                         "status": "string"},
    }),
    "riscv_cpu": ("cpu", "CPU core microarchitecture design (RISC-V ISA)", {
        "CpuCore": {"name": "string", "isa": "string", "microarch": "string",
                    "frequencyGhz": "float", "issueWidth": "integer"},
        "Pipeline": {"coreId": "string", "stages": "integer", "type": "string",
                     "branchPredictor": "string"},
        "RegisterFile": {"coreId": "string", "kind": "string", "count": "integer",
                         "widthBits": "integer"},
        "CacheLevel": {"coreId": "string", "level": "string", "sizeKb": "integer",
                       "associativity": "integer", "latencyCycles": "integer"},
        "IsaExtension": {"coreId": "string", "name": "string", "version": "string",
                         "ratified": "boolean"},
        "Microbench": {"coreId": "string", "name": "string", "ipc": "float", "scoreType": "string"},
    }),
    "silicon_photonics": ("siph", "Silicon photonics / 光電融合 photonic integrated circuit", {
        "PhotonicDie": {"name": "string", "platform": "string", "processNode": "string",
                        "areaMm2": "float"},
        "OpticalWaveguide": {"dieId": "string", "material": "string", "widthNm": "float",
                             "lossDbCm": "float"},
        "Modulator": {"dieId": "string", "type": "string", "bandwidthGhz": "float", "vpiV": "float"},
        "Photodetector": {"dieId": "string", "material": "string", "responsivityAW": "float",
                          "bandwidthGhz": "float"},
        "LaserSource": {"dieId": "string", "type": "string", "wavelengthNm": "float",
                        "powerMw": "float"},
        "WavelengthChannel": {"dieId": "string", "lambdaNm": "float", "spacingGhz": "float",
                              "dataRateGbps": "float"},
    }),
    "copackaged_optics": ("cpo", "Co-packaged optics / 光電融合 optical interconnect", {
        "OpticalEngine": {"name": "string", "generation": "string", "lanes": "integer",
                          "aggregateTbps": "float"},
        "ElectroOpticTile": {"engineId": "string", "tileType": "string", "channels": "integer",
                             "powerPjPerBit": "float"},
        "FiberLink": {"engineId": "string", "fiberType": "string", "reachM": "float",
                      "dataRateGbps": "float"},
        "SerdesLane": {"engineId": "string", "index": "integer", "modulation": "string",
                       "dataRateGbps": "float"},
        "OpticalSwitch": {"engineId": "string", "radix": "integer", "technology": "string",
                          "insertionLossDb": "float"},
        "LinkBudget": {"engineId": "string", "txPowerDbm": "float", "rxSensitivityDbm": "float",
                       "marginDb": "float"},
    }),
    "fab_lithography": ("fab", "Semiconductor fab / EUV lithography process", {
        "Wafer": {"lotId": "string", "diameterMm": "integer", "processNode": "string",
                  "status": "string"},
        "ProcessStep": {"waferId": "string", "name": "string", "tool": "string", "stepType": "string"},
        "Reticle": {"name": "string", "layer": "string", "euv": "boolean",
                    "numericalAperture": "float"},
        "ProcessRecipe": {"stepId": "string", "name": "string", "doseMjCm2": "float",
                          "focusNm": "float"},
        "DefectScan": {"waferId": "string", "defectCount": "integer", "defectDensity": "float",
                       "classification": "string"},
        "Yield": {"waferId": "string", "dieTotal": "integer", "dieGood": "integer",
                  "yieldPct": "float"},
    }),
    "semicon_robotics": ("sbot", "Fab-automation robotics — wafer handling design + implementation", {
        "WaferRobot": {"name": "string", "vendor": "string", "axes": "integer",
                       "payloadKg": "float", "cleanClass": "string"},
        "EfemModule": {"robotId": "string", "ports": "integer", "ffuFlowM3h": "float",
                       "status": "string"},
        "TransferJob": {"robotId": "string", "source": "string", "destination": "string",
                        "status": "string"},
        "LoadPort": {"moduleId": "string", "standard": "string", "slots": "integer",
                     "occupied": "boolean"},
        "MotionProgram": {"robotId": "string", "name": "string", "waypoints": "integer",
                          "cycleTimeS": "float"},
        "Interlock": {"robotId": "string", "kind": "string", "triggered": "boolean",
                      "severity": "string"},
    }),

    # ===== Wave 11b — adjacency fill (CPU + 光電融合 emphasis), 2026-06-14 =====
    "optical_compute": ("opc", "Photonic computing / optical matrix-multiply 光電融合", {
        "PhotonicProcessor": {"name": "string", "platform": "string", "topsPerWatt": "float",
                              "wavelengths": "integer"},
        "MziMesh": {"processorId": "string", "rows": "integer", "columns": "integer",
                    "phaseShifter": "string"},
        "OpticalCore": {"processorId": "string", "macsPerCycle": "integer", "precisionBits": "integer",
                        "clockGhz": "float"},
        "NonlinearUnit": {"coreId": "string", "activation": "string", "thresholdMw": "float"},
        "WdmBus": {"processorId": "string", "channels": "integer", "spacingGhz": "float",
                   "aggregateTbps": "float"},
        "ComputeTile": {"processorId": "string", "index": "integer", "utilization": "float",
                        "status": "string"},
    }),
    "photonic_switch": ("psw", "Optical circuit switch / 光電融合 routing fabric", {
        "SwitchFabric": {"name": "string", "radix": "integer", "technology": "string",
                         "switchingTimeNs": "float"},
        "OpticalPort": {"fabricId": "string", "index": "integer", "direction": "string",
                        "lambdaNm": "float"},
        "WaveguideCross": {"fabricId": "string", "row": "integer", "column": "integer",
                           "state": "string"},
        "MemsMirror": {"fabricId": "string", "tiltDeg": "float", "settleTimeMs": "float",
                       "status": "string"},
        "RoutePath": {"fabricId": "string", "ingressPort": "string", "egressPort": "string",
                      "hops": "integer"},
        "LossBudget": {"fabricId": "string", "insertionLossDb": "float", "crosstalkDb": "float",
                       "marginDb": "float"},
    }),
    "arm_cpu": ("acpu", "Arm CPU core microarchitecture design", {
        "ArmCore": {"name": "string", "isa": "string", "microarch": "string",
                    "frequencyGhz": "float", "issueWidth": "integer"},
        "Cluster": {"coreId": "string", "coreCount": "integer", "topology": "string",
                    "sharedCacheKb": "integer"},
        "NeonUnit": {"coreId": "string", "kind": "string", "widthBits": "integer", "lanes": "integer"},
        "CacheLevel": {"coreId": "string", "level": "string", "sizeKb": "integer",
                       "associativity": "integer", "latencyCycles": "integer"},
        "Interrupt": {"coreId": "string", "controller": "string", "vectors": "integer",
                      "priorityBits": "integer"},
        "PowerState": {"coreId": "string", "name": "string", "voltageV": "float", "powerMw": "float"},
    }),
    "x86_cpu": ("xcpu", "x86 CPU microarchitecture design", {
        "X86Core": {"name": "string", "isa": "string", "microarch": "string",
                    "frequencyGhz": "float", "issueWidth": "integer"},
        "ExecPort": {"coreId": "string", "index": "integer", "units": "string", "throughput": "integer"},
        "MicroOp": {"coreId": "string", "mnemonic": "string", "fusedDomain": "string", "latency": "integer"},
        "CacheLevel": {"coreId": "string", "level": "string", "sizeKb": "integer",
                       "associativity": "integer", "latencyCycles": "integer"},
        "TlbLevel": {"coreId": "string", "level": "string", "entries": "integer", "pageSizeKb": "integer"},
        "PowerState": {"coreId": "string", "name": "string", "voltageV": "float", "tdpW": "float"},
    }),
    "cxl_memory": ("cxl", "CXL memory pooling / expansion fabric", {
        "CxlDevice": {"name": "string", "cxlVersion": "string", "type": "string", "capacityGb": "integer"},
        "MemoryRegion": {"deviceId": "string", "sizeGb": "integer", "interleave": "string",
                         "volatile": "boolean"},
        "FlitChannel": {"deviceId": "string", "lanes": "integer", "flitMode": "string",
                        "dataRateGtps": "float"},
        "CoherenceDomain": {"deviceId": "string", "hostCount": "integer", "protocol": "string",
                            "biasMode": "string"},
        "QosClass": {"deviceId": "string", "name": "string", "bandwidthGbps": "float",
                     "latencyNs": "float"},
        "HotplugEvent": {"deviceId": "string", "kind": "string", "slot": "integer", "status": "string"},
    }),
    "ucie_chiplet": ("ucie", "UCIe chiplet die-to-die interconnect / advanced packaging", {
        "Chiplet": {"name": "string", "function": "string", "processNode": "string", "areaMm2": "float"},
        "UcieLink": {"chipletId": "string", "mode": "string", "lanes": "integer", "dataRateGtps": "float"},
        "BumpArray": {"chipletId": "string", "pitchUm": "float", "count": "integer", "bumpType": "string"},
        "Sideband": {"linkId": "string", "function": "string", "frequencyMhz": "float"},
        "ProtocolLayer": {"linkId": "string", "protocol": "string", "flitFormat": "string",
                          "retimer": "boolean"},
        "Package": {"name": "string", "substrate": "string", "chipletCount": "integer",
                    "interposer": "string"},
    }),
    "nvidia_isaac": ("isaac", "Robotics simulation / manipulation (Isaac-style) physical-AI", {
        "SimRobot": {"name": "string", "embodiment": "string", "dof": "integer", "urdf": "string"},
        "Skill": {"robotId": "string", "name": "string", "policyType": "string", "successRate": "float"},
        "SimScene": {"name": "string", "assets": "integer", "domainRandomized": "boolean",
                     "physicsDt": "float"},
        "Policy": {"skillId": "string", "algorithm": "string", "checkpoint": "string", "reward": "float"},
        "Sensor": {"robotId": "string", "modality": "string", "rateHz": "float", "resolution": "string"},
        "Trajectory": {"robotId": "string", "waypoints": "integer", "durationS": "float", "status": "string"},
    }),
    "cerebras_wafer": ("cs", "Wafer-scale AI accelerator design", {
        "WaferEngine": {"name": "string", "generation": "string", "coreCount": "integer",
                        "sramGb": "integer"},
        "ProcessingElement": {"engineId": "string", "dataflow": "string", "flops": "float",
                              "localSramKb": "integer"},
        "Fabric": {"engineId": "string", "topology": "string", "bisectionBwTbps": "float",
                   "latencyNs": "float"},
        "MemoryBank": {"engineId": "string", "sizeGb": "integer", "bandwidthTbps": "float",
                       "kind": "string"},
        "Kernel": {"engineId": "string", "name": "string", "tiles": "integer", "occupancy": "float"},
        "WaferJob": {"engineId": "string", "model": "string", "tokensPerSec": "float", "status": "string"},
    }),

    # ===== Wave 11c — accelerator + optics + interconnect fill (CPU/光電融合 emphasis), 2026-06-15 =====
    "gpu_accelerator": ("gpu", "GPU streaming-multiprocessor accelerator design", {
        "Gpu": {"name": "string", "architecture": "string", "smCount": "integer",
                "vramGb": "integer", "tflops": "float"},
        "StreamingMultiprocessor": {"gpuId": "string", "index": "integer", "cudaCores": "integer",
                                    "sharedMemKb": "integer"},
        "TensorCore": {"smId": "string", "generation": "string", "precision": "string", "tops": "float"},
        "MemoryHierarchy": {"gpuId": "string", "level": "string", "sizeMb": "float",
                            "bandwidthGbps": "float"},
        "Warp": {"smId": "string", "threads": "integer", "scheduler": "string", "occupancy": "float"},
        "KernelLaunch": {"gpuId": "string", "name": "string", "gridDim": "integer",
                         "blockDim": "integer", "status": "string"},
    }),
    "npu_accelerator": ("npu", "NPU / systolic AI accelerator design", {
        "Npu": {"name": "string", "vendor": "string", "topsInt8": "float", "sramMb": "integer"},
        "SystolicArray": {"npuId": "string", "rows": "integer", "columns": "integer", "dataType": "string"},
        "MacUnit": {"arrayId": "string", "precision": "string", "count": "integer"},
        "Sram": {"npuId": "string", "sizeMb": "float", "banks": "integer", "bandwidthGbps": "float"},
        "Dataflow": {"npuId": "string", "kind": "string", "reuse": "string"},
        "InferenceTask": {"npuId": "string", "model": "string", "batchSize": "integer", "status": "string"},
    }),
    "dpu_smartnic": ("dpu", "DPU / SmartNIC data-path accelerator design", {
        "Dpu": {"name": "string", "vendor": "string", "portsGbps": "integer", "cores": "integer"},
        "PacketPipeline": {"dpuId": "string", "stages": "integer", "throughputMpps": "float"},
        "RdmaEngine": {"dpuId": "string", "protocol": "string", "queues": "integer", "latencyUs": "float"},
        "ArmComplex": {"dpuId": "string", "cores": "integer", "frequencyGhz": "float", "isa": "string"},
        "FlowTable": {"dpuId": "string", "entries": "integer", "matchFields": "integer"},
        "Offload": {"dpuId": "string", "kind": "string", "status": "string"},
    }),
    "optical_transceiver": ("oxc", "Pluggable optical transceiver / 光電融合 module", {
        "Transceiver": {"partNumber": "string", "formFactor": "string", "dataRateGbps": "float",
                        "reachM": "float"},
        "OpticalLane": {"transceiverId": "string", "index": "integer", "lambdaNm": "float",
                        "modulation": "string"},
        "Dsp": {"transceiverId": "string", "vendor": "string", "fecType": "string", "powerW": "float"},
        "LaserDie": {"transceiverId": "string", "type": "string", "wavelengthNm": "float",
                     "powerMw": "float"},
        "Photodiode": {"transceiverId": "string", "material": "string", "responsivityAW": "float",
                       "bandwidthGhz": "float"},
        "DomTelemetry": {"transceiverId": "string", "txPowerDbm": "float", "rxPowerDbm": "float",
                         "tempC": "float"},
    }),
    "dwdm_system": ("dwd", "DWDM optical line system / 光電融合 transport", {
        "DwdmSystem": {"name": "string", "bandPlan": "string", "channels": "integer",
                       "capacityTbps": "float"},
        "OpticalChannel": {"systemId": "string", "lambdaNm": "float", "dataRateGbps": "float",
                           "status": "string"},
        "Amplifier": {"systemId": "string", "type": "string", "gainDb": "float", "noiseFigureDb": "float"},
        "Roadm": {"systemId": "string", "degree": "integer", "technology": "string",
                  "addDropPorts": "integer"},
        "Span": {"systemId": "string", "lengthKm": "float", "fiberType": "string", "lossDb": "float"},
        "SupervisoryChannel": {"systemId": "string", "lambdaNm": "float", "protocol": "string",
                               "status": "string"},
    }),
    "serdes_phy": ("ser", "High-speed SerDes PHY design", {
        "SerdesPhy": {"name": "string", "modulation": "string", "dataRateGbps": "float",
                      "process": "string"},
        "Lane": {"phyId": "string", "index": "integer", "direction": "string", "dataRateGbps": "float"},
        "Equalizer": {"phyId": "string", "type": "string", "taps": "integer", "gainDb": "float"},
        "Pll": {"phyId": "string", "refClockMhz": "float", "jitterPs": "float", "lockTimeUs": "float"},
        "EyeDiagram": {"laneId": "string", "eyeHeightMv": "float", "eyeWidthPs": "float", "ber": "float"},
        "BertRun": {"phyId": "string", "patternType": "string", "bitsTested": "integer",
                    "errors": "integer"},
    }),
    "lpddr_mobile": ("lpd", "LPDDR mobile / low-power DRAM design", {
        "LpddrDevice": {"partNumber": "string", "generation": "string", "densityGb": "integer",
                        "dataRateMtps": "integer"},
        "Channel": {"deviceId": "string", "width": "integer", "index": "integer", "dataRateMtps": "integer"},
        "PowerMode": {"deviceId": "string", "name": "string", "currentMa": "float", "voltageV": "float"},
        "TimingProfile": {"deviceId": "string", "casLatency": "integer", "tRCD": "integer", "tRP": "integer"},
        "SpeedBin": {"deviceId": "string", "grade": "string", "voltageV": "float", "dataRateMtps": "integer"},
        "JedecSpec": {"deviceId": "string", "standard": "string", "revision": "string", "compliant": "boolean"},
    }),
    "cobot_assembly": ("cob", "Collaborative assembly robotics (electronics/semiconductor)", {
        "Cobot": {"name": "string", "vendor": "string", "payloadKg": "float", "reachMm": "float",
                  "axes": "integer"},
        "Joint": {"cobotId": "string", "index": "integer", "type": "string", "rangeDeg": "float"},
        "EndEffector": {"cobotId": "string", "kind": "string", "gripForceN": "float", "status": "string"},
        "AssemblyTask": {"cobotId": "string", "name": "string", "cycleTimeS": "float", "status": "string"},
        "SafetyZone": {"cobotId": "string", "kind": "string", "radiusMm": "float", "speedLimitMmS": "float"},
        "ForceProfile": {"cobotId": "string", "axis": "string", "maxForceN": "float", "complianceNm": "float"},
    }),
}

SBOM_DEPS = ["kotoba", "kotodama-wasm", "datomic-client"]

# ---------------------------------------------------------------------------
# Helpers (mirror deepen_actors.py / register_cleanroom_actors.py exactly).
# ---------------------------------------------------------------------------


def _snake(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _pluralize(name):
    if name.endswith("y") and name[-2:-1] not in "aeiou":
        return name[:-1] + "ies"
    if name.endswith(("s", "x", "z", "ch", "sh")):
        return name + "es"
    return name + "s"


def _required_fields(fields):
    req = []
    for fname in fields:
        if fname.endswith("Id") or fname.endswith("Ref"):
            continue
        req.append(fname)
        if len(req) >= 2:
            break
    return req


def _refs(model, fields):
    """Map *Id fields to a sibling entity (drives ?expand=)."""
    out = {}
    for f in fields:
        if f.endswith("Id"):
            guess = f[:-2][0].upper() + f[:-2][1:]
            if guess in model:
                out[f] = guess
    return out


def _json_type(t):
    return {"string": "string", "integer": "integer", "float": "number",
            "boolean": "boolean", "datetime": "string"}.get(t, "string")


def _cast(t):
    return {"integer": "_as_int", "float": "_as_float", "boolean": "_as_bool"}.get(t)


def cid_v1_raw(data: bytes) -> str:
    digest = hashlib.sha256(data).digest()
    cid = bytes([0x01, 0x55, 0x12, 0x20]) + digest
    b32 = base64.b32encode(cid).decode("ascii").lower().rstrip("=")
    return "b" + b32


def program_bundle(adir: str, handle: str) -> bytes:
    parts = []
    for rel in (f"schema/{handle}.kotoba", "src/main.py", "deps.toml"):
        p = os.path.join(adir, rel)
        body = open(p, "rb").read() if os.path.exists(p) else b""
        parts.append(f"--- {rel} ({len(body)}) ---\n".encode("utf-8"))
        parts.append(body)
        parts.append(b"\n")
    return b"".join(parts)


# ---------------------------------------------------------------------------
# File generators.
# ---------------------------------------------------------------------------


def gen_schema(handle, blurb, model):
    out = [f"// {handle} clean-room schema -> Datomic EAVT mapping",
           f"// {blurb}.",
           "// Generated by 70-tools/scaffold_wave11_compute_photonics.py.",
           "",
           f"namespace {handle} {{", ""]
    for ent, fields in model.items():
        out.append(f"    entity {ent} {{")
        out.append("        id: string @unique")
        for f, t in fields.items():
            out.append(f"        {f}: {t}")
        out.append("        createdAt: datetime")
        out.append("        updatedAt: datetime")
        out.append("    }")
        out.append("")
    out.append("}")
    out.append("")
    out += ["    // Auto-injected Cognitive Schema",
            "    entity CognitiveRecord {",
            "        id: string @unique",
            "        originalPayload: string",
            "        aiStatus: string",
            "        aiInsights: json",
            "        computedAt: datetime",
            "    }", ""]
    return "\n".join(out)


def gen_main(handle, id_prefix, model):
    refs_all = {ent: _refs(model, fields) for ent, fields in model.items()}
    head = f'''"""
Py Kotodama WASM entrypoint for the {handle} clean-room actor (L4).

L4 production surface: CRUD + pagination + filtering + relationship
expansion + validation, over a Datomic-backed Kotoba schema.
Generated by 70-tools/scaffold_wave11_compute_photonics.py.
No proprietary code or credentials; resource shapes only.
"""
from kotodama import Runtime
from kotoba import load_schema
from datomic import DatomicClient
import uuid
import datetime

schema = load_schema("../schema/{handle}.kotoba")
db = DatomicClient.connect()
app = Runtime("{handle}-compat")

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def now():
    return datetime.datetime.utcnow().isoformat()


def new_id(prefix):
    return f"{{prefix}}_" + uuid.uuid4().hex[:16]


def _as_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _as_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _as_bool(v):
    return str(v).lower() in ("1", "true", "yes", "on") if v is not None else False


def _persist(entity, rec):
    """Transact a record into Datomic as namespaced EAVT facts."""
    facts = {{}}
    for k, v in rec.items():
        facts[f"{handle}.{{entity}}/{{k}}"] = v
    db.transact([facts])
    return rec


def _query(entity, eid=None):
    pattern = {{"entity": f"{handle}.{{entity}}"}}
    if eid is not None:
        pattern["id"] = eid
    return db.query(pattern)


def _require(data, fields):
    missing = [f for f in fields if not data.get(f)]
    if missing:
        return {{"error": {{"message": "Missing required fields: " + ", ".join(missing),
                          "type": "invalid_request_error"}}}}
    return None


def _reject_unknown(data, allowed):
    """Reject body fields not in the entity schema (strict validation)."""
    extra = [k for k in data if k not in allowed]
    if extra:
        return {{"error": {{"message": "Unknown fields: " + ", ".join(extra),
                          "type": "invalid_request_error"}}}}
    return None


def _apply_filters(rows, params, fields):
    """Filter rows by any schema field present in the query params."""
    out = rows
    for f in fields:
        if f in params and params[f] not in (None, ""):
            want = str(params[f])
            out = [r for r in out if str(r.get(f)) == want]
    return out


def _paginate(rows, params):
    """Cursor pagination: limit + starting_after (an id). Returns (page, has_more)."""
    limit = min(max(_as_int(params.get("limit")) or DEFAULT_LIMIT, 1), MAX_LIMIT)
    start = params.get("starting_after")
    if start is not None:
        ids = [r.get("id") for r in rows]
        if start in ids:
            rows = rows[ids.index(start) + 1:]
    page = rows[:limit]
    return page, len(rows) > limit


def _expand(rec, params, refs):
    """?expand=<field> inlines a referenced entity (rec[field+"_obj"])."""
    want = (params.get("expand") or "").split(",")
    for field, ent in refs.items():
        if field in want and rec.get(field):
            rows = _query(ent, rec[field])
            rec[field + "_obj"] = rows[0] if rows else None
    return rec
'''
    blocks = [head]
    for ent, fields in model.items():
        plural = _pluralize(ent).lower()
        allowed = list(fields.keys())
        required = _required_fields(fields)
        prefix = f"{id_prefix}_{ent[:3].lower()}"
        refs = refs_all[ent]

        # assignment lines for create
        asn = []
        for f, t in fields.items():
            c = _cast(t)
            if c:
                asn.append(f'    rec["{f}"] = {c}(data.get({f!r}))')
            else:
                asn.append(f'    rec["{f}"] = data.get({f!r})')
        asn_block = "\n".join(asn)

        get_expand = ""
        if refs:
            get_expand = f"\n    rec = _expand(rec, request.query or {{}}, {refs!r})"

        b = f'''
@app.route("/v1/{plural}", methods=["POST"])
def create_{_snake(ent)}(request):
    """Create a {ent}."""
    data = request.json or request.form or {{}}
    err = _reject_unknown(data, {allowed!r})
    if err:
        return err, 400
    err = _require(data, {required!r})
    if err:
        return err, 400
    rec = {{"id": new_id("{prefix}")}}
{asn_block}
    rec["createdAt"] = now()
    rec["updatedAt"] = rec["createdAt"]
    _persist("{ent}", rec)
    return rec, 201

@app.route("/v1/{plural}", methods=["GET"])
def list_{_snake(_pluralize(ent))}(request):
    """List {_pluralize(ent)} with filtering + cursor pagination."""
    params = request.query or {{}}
    rows = _query("{ent}")
    rows = _apply_filters(rows, params, {allowed!r})
    page, has_more = _paginate(rows, params)
    return {{"object": "list", "data": page, "has_more": has_more,
            "count": len(page), "total": len(rows)}}, 200

@app.route("/v1/{plural}/<eid>", methods=["GET"])
def get_{_snake(ent)}(request, eid):
    """Retrieve a {ent} by id (supports ?expand=)."""
    rows = _query("{ent}", eid)
    if not rows:
        return {{"error": {{"message": "Not found", "type": "not_found"}}}}, 404
    rec = rows[0]{get_expand}
    return rec, 200

@app.route("/v1/{plural}/<eid>", methods=["POST", "PATCH"])
def update_{_snake(ent)}(request, eid):
    """Update a {ent}."""
    rows = _query("{ent}", eid)
    if not rows:
        return {{"error": {{"message": "Not found", "type": "not_found"}}}}, 404
    data = request.json or request.form or {{}}
    err = _reject_unknown(data, {allowed!r})
    if err:
        return err, 400
    rec = rows[0]
    for k, v in data.items():
        if k not in ("id", "createdAt"):
            rec[k] = v
    rec["updatedAt"] = now()
    _persist("{ent}", rec)
    return rec, 200

@app.route("/v1/{plural}/<eid>", methods=["DELETE"])
def delete_{_snake(ent)}(request, eid):
    """Delete a {ent}."""
    rows = _query("{ent}", eid)
    if not rows:
        return {{"error": {{"message": "Not found", "type": "not_found"}}}}, 404
    db.retract({{"entity": f"{handle}.{ent}", "id": eid}})
    return {{"id": eid, "deleted": True}}, 200
'''
        blocks.append(b)

    entities = list(model.keys())
    tail = f'''
@app.route("/healthz", methods=["GET"])
def healthz(request):
    return {{"status": "ok", "actor": "{handle}-compat", "tier": "L4",
            "entities": {entities!r}}}, 200


if __name__ == "__main__":
    app.start()
'''
    blocks.append(tail)
    return "".join(blocks)


def gen_openapi(handle, blurb, cid, model):
    paths = {}
    list_params = [
        {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20, "maximum": 100}},
        {"name": "starting_after", "in": "query", "schema": {"type": "string"}},
        {"name": "expand", "in": "query", "schema": {"type": "string"}},
    ]
    components = {"schemas": {}}
    for ent, fields in model.items():
        plural = _pluralize(ent).lower()
        props = {"id": {"type": "string"}}
        for f, t in fields.items():
            props[f] = {"type": _json_type(t)}
        props["createdAt"] = {"type": "string"}
        props["updatedAt"] = {"type": "string"}
        components["schemas"][ent] = {"type": "object", "properties": props}
        ref = {"$ref": f"#/components/schemas/{ent}"}
        body = {"required": True, "content": {"application/json": {"schema": ref}}}
        paths[f"/v1/{plural}"] = {
            "get": {"summary": f"List {_pluralize(ent)}", "parameters": list_params,
                    "responses": {"200": {"description": "list",
                                          "content": {"application/json": {"schema": {"type": "object",
                                              "properties": {"object": {"type": "string"},
                                                             "data": {"type": "array", "items": ref},
                                                             "has_more": {"type": "boolean"}}}}}}}},
            "post": {"summary": f"Create {ent}", "requestBody": body,
                     "responses": {"201": {"description": "created",
                                           "content": {"application/json": {"schema": ref}}}}},
        }
        paths[f"/v1/{plural}/{{id}}"] = {
            "get": {"summary": f"Get {ent}",
                    "parameters": [{"name": "id", "in": "path", "required": True,
                                    "schema": {"type": "string"}},
                                   {"name": "expand", "in": "query", "schema": {"type": "string"}}],
                    "responses": {"200": {"description": "ok",
                                          "content": {"application/json": {"schema": ref}}},
                                  "404": {"description": "not found"}}},
            "patch": {"summary": f"Update {ent}",
                      "parameters": [{"name": "id", "in": "path", "required": True,
                                      "schema": {"type": "string"}}],
                      "requestBody": body,
                      "responses": {"200": {"description": "updated",
                                            "content": {"application/json": {"schema": ref}}}}},
            "delete": {"summary": f"Delete {ent}",
                       "parameters": [{"name": "id", "in": "path", "required": True,
                                       "schema": {"type": "string"}}],
                       "responses": {"200": {"description": "deleted"}}},
        }
    return {
        "openapi": "3.1.0",
        "info": {
            "title": f"{handle} clean-room API",
            "version": "1.0.0",
            "description": f"Clean-room, API-compatible {blurb} actor ({handle}); "
                           f"runs browser-local on IPFS + kotoba-WASM.",
            "x-etzhayyim-did": f"did:web:etzhayyim.com:actor:{handle}-compat",
            "x-wasm-cid": cid,
            "x-runtime": "kotoba-wasm",
            "x-exec": "browser-local|donated-mesh",
            "x-tier": "L4",
        },
        "servers": [{"url": f"ipfs://{cid}", "description": "browser-local kotoba-wasm component"}],
        "paths": paths,
        "components": components,
    }


def gen_mcp_tools(model):
    tools = []
    for ent, fields in model.items():
        props = {f: {"type": _json_type(t)} for f, t in fields.items()}
        required = _required_fields(fields)
        tools.append({"name": f"create_{_snake(ent)}", "description": f"Create a {ent}.",
                      "inputSchema": {"type": "object", "properties": props, "required": required}})
        tools.append({"name": f"list_{_snake(_pluralize(ent))}", "description": f"List {_pluralize(ent)}.",
                      "inputSchema": {"type": "object", "properties": {}}})
        tools.append({"name": f"get_{_snake(ent)}", "description": f"Get a {ent} by id.",
                      "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}},
                                      "required": ["id"]}})
        tools.append({"name": f"update_{_snake(ent)}", "description": f"Update a {ent}.",
                      "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}, **props},
                                      "required": ["id"]}})
        tools.append({"name": f"delete_{_snake(ent)}", "description": f"Delete a {ent}.",
                      "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}},
                                      "required": ["id"]}})
    return tools


def gen_rest_routes(model):
    routes = []
    for ent in model:
        plural = _pluralize(ent).lower()
        routes.append({"method": "POST", "path": f"/v1/{plural}", "op": f"create {ent}"})
        routes.append({"method": "GET", "path": f"/v1/{plural}", "op": f"list {ent}"})
        routes.append({"method": "GET", "path": f"/v1/{plural}/{{id}}", "op": f"get {ent}"})
        routes.append({"method": "PATCH", "path": f"/v1/{plural}/{{id}}", "op": f"update {ent}"})
        routes.append({"method": "DELETE", "path": f"/v1/{plural}/{{id}}", "op": f"delete {ent}"})
    return routes


def gen_manifest(handle, blurb, cid, model):
    entities = list(model.keys())
    routes = gen_rest_routes(model)
    sbom = {
        "bomFormat": "CycloneDX", "specVersion": "1.5",
        "metadata": {"component": {"type": "application", "name": f"{handle}-compat",
                                   "purl": f"pkg:etzhayyim/{handle}-compat"}},
        "components": [{"type": "library", "name": d, "scope": "required",
                        "purl": f"pkg:etzhayyim/{d}"} for d in SBOM_DEPS],
    }
    return {
        "schemaVersion": "1.0",
        "handle": f"{handle}-compat",
        "did": f"did:web:etzhayyim.com:actor:{handle}-compat",
        "kind": "compat",
        "title": f"{handle} clean-room actor",
        "description": f"Clean-room, API-compatible {blurb} actor ({handle}); "
                       f"runs browser-local on IPFS + kotoba-WASM.",
        "wasmCid": cid,
        "wasmProvenance": "program-source-cid",
        "runtime": "kotoba-wasm",
        "exec": "browser-local|donated-mesh",
        "ipfs": f"ipfs://{cid}",
        "schema": f"schema/{handle}.kotoba",
        "tier": "L4",
        "verified": None,
        "entities": entities,
        "adr": ["260607", "2606014500", "2606013800", "2606036000"],
        "capabilities": {
            "api": {"type": "rest", "runtime": "kotoba-wasm", "endpointCount": len(routes),
                    "routes": routes,
                    "features": {"pagination": True, "filtering": True, "relationExpansion": True,
                                 "strictValidation": True, "contractTest": True},
                    "health": "/healthz"},
            "supplychain": {"type": "cyclonedx-sbom", "runtime": "kotoba-wasm",
                            "sbom": "manifest:supplychain.sbom", "sbomData": sbom,
                            "adr": ["2606036000"]},
            "socialpost": {"type": "datom-event-feed", "runtime": "kotoba-wasm",
                           "lexicon": "app.bsky.feed.post", "source": f"{handle}.* Datom events",
                           "mode": "dry-run", "gate": "G8"},
            "mcp": {"type": "model-context-protocol", "runtime": "kotoba-wasm",
                    "transport": "ipfs+kotoba-wasm", "toolCount": len(model) * 5,
                    "tools": gen_mcp_tools(model)},
        },
    }


def gen_test(handle, model):
    entities = list(model.keys())
    plurals = {ent: _pluralize(ent).lower() for ent in model}
    cls = "".join(p.capitalize() for p in handle.split("_")) + "Contract"
    return f'''"""
Contract test for the {handle}-compat L4 actor.
Static API-contract verification (stdlib unittest; no WASM runtime).
Generated by 70-tools/scaffold_wave11_compute_photonics.py.
"""
import ast
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ACTOR = os.path.dirname(HERE)
MAIN = os.path.join(ACTOR, "src", "main.py")
SCHEMA = os.path.join(ACTOR, "schema", "{handle}.kotoba")
ENTITIES = {entities!r}
PLURALS = {plurals!r}


class {cls}(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(MAIN, encoding="utf-8") as f:
            cls.src = f.read()
        cls.tree = ast.parse(cls.src)
        with open(SCHEMA, encoding="utf-8") as f:
            cls.schema = f.read()

    def test_compiles(self):
        self.assertIsInstance(self.tree, ast.Module)

    def test_schema_has_all_entities(self):
        for ent in ENTITIES:
            self.assertRegex(self.schema, r"entity\\s+" + ent + r"\\s*\\{{",
                             f"schema missing entity {{ent}}")

    def test_full_crud_per_entity(self):
        for ent, plural in PLURALS.items():
            base = "/v1/" + plural
            for needle in (
                f'@app.route("{{base}}", methods=["POST"])',
                f'@app.route("{{base}}", methods=["GET"])',
                f'@app.route("{{base}}/<eid>", methods=["GET"])',
                f'@app.route("{{base}}/<eid>", methods=["DELETE"])',
            ):
                self.assertIn(needle, self.src, f"missing route: {{needle}}")

    def test_list_has_pagination(self):
        self.assertIn("_paginate(", self.src)
        self.assertIn("has_more", self.src)
        self.assertIn("starting_after", self.src)

    def test_list_has_filtering(self):
        self.assertIn("_apply_filters(", self.src)

    def test_validation_present(self):
        self.assertIn("_reject_unknown(", self.src)
        self.assertIn("_require(", self.src)

    def test_healthz(self):
        self.assertIn('"tier": "L4"', self.src)

    def test_no_proprietary_imports(self):
        for bad in ("requests", "openai", "stripe", "boto3"):
            self.assertNotIn("import " + bad, self.src)


if __name__ == "__main__":
    unittest.main()
'''


def scaffold(handle, id_prefix, blurb, model):
    adir = os.path.join(ACTORS_DIR, f"{handle}-compat")
    os.makedirs(os.path.join(adir, "src"), exist_ok=True)
    os.makedirs(os.path.join(adir, "schema"), exist_ok=True)
    os.makedirs(os.path.join(adir, "tests"), exist_ok=True)

    with open(os.path.join(adir, "README.md"), "w") as f:
        f.write(f"# {handle.replace('_', ' ').title()} Clean Room Actor\n\n"
                f"Clean-room API-compatible {blurb} actor, backed by Datomic and Py "
                f"Kotodama WASM. Runs browser-local on IPFS + kotoba-WASM (one Worker, "
                f"many WASM actors). No proprietary code or credentials.\n")

    with open(os.path.join(adir, "deps.edn"), "w") as f:
        f.write(f'{{:project {{:name "{handle}-compat" :version "0.1.0"}} '
                f':dependencies {{:kotoba "workspace" :kotodama-wasm "workspace" '
                f':datomic-client "workspace"}}}}\n')

    with open(os.path.join(adir, "deps.toml"), "w") as f:
        f.write(f'[project]\nname = "{handle}-compat"\nversion = "0.1.0"\n\n[dependencies]\n'
                'kotoba = "workspace"\nkotodama-wasm = "workspace"\ndatomic-client = "workspace"\n')

    with open(os.path.join(adir, "schema", f"{handle}.kotoba"), "w") as f:
        f.write(gen_schema(handle, blurb, model))

    with open(os.path.join(adir, "src", "main.py"), "w") as f:
        f.write(gen_main(handle, id_prefix, model))

    with open(os.path.join(adir, "tests", f"test_{handle}_contract.py"), "w") as f:
        f.write(gen_test(handle, model))

    # CID is derived from the deterministic program bundle (schema+main+deps).
    cid = cid_v1_raw(program_bundle(adir, handle))

    with open(os.path.join(adir, "openapi.json"), "w") as f:
        json.dump(gen_openapi(handle, blurb, cid, model), f, indent=2)

    with open(os.path.join(adir, "manifest.json"), "w") as f:
        json.dump(gen_manifest(handle, blurb, cid, model), f, indent=2)

    return cid, len(model)


def run():
    print(f"Wave 11 — Compute & Photonics Frontier: {len(COHORT)} actors")
    summary = []
    for idx, (handle, (id_prefix, blurb, model)) in enumerate(COHORT.items(), 1):
        cid, n = scaffold(handle, id_prefix, blurb, model)
        print(f"[{idx:2d}/{len(COHORT)}] {handle:<20} entities={n:<2} cid={cid}")
        summary.append({"handle": f"{handle}-compat", "entities": list(model.keys()),
                        "endpointCount": n * 5, "wasmCid": cid, "tier": "L4"})
    out = os.path.join(TOOLS_DIR, "wave11_compute_photonics.index.json")
    with open(out, "w") as f:
        json.dump({"wave": 11, "title": "Compute & Photonics Frontier",
                   "count": len(summary), "actors": summary}, f, indent=2)
    print(f"\nWave 11 complete. Index -> {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
    run()
