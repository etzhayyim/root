import { writable, get } from 'svelte/store';

export type SimulationPhase = 'init' | 'design' | 'procure' | 'manufacture_test' | 'operate';

export interface EngineDesign {
    model_name: string;
    thrust_kn: number;
    weight_kg: number;
    bypass_ratio: number;
    core_materials: string[];
    rtl_validation_passed: boolean;
}

export interface EngineTestMetrics {
    max_temp_celsius: number;
    vibration_hz: number;
    fuel_flow_kg_s: number;
    emission_nox_ppm: number;
    passed_certification: boolean;
}

export interface SimulationState {
    phase: SimulationPhase;
    project_id?: string;
    aircraft_model: string;

    engine_design?: EngineDesign;

    unspsc_bom?: string[];
    isic_suppliers?: {name: string, isic: string}[];

    engine_test_metrics?: EngineTestMetrics;
    assembly_robot_ids?: string[];

    icao24_address?: string;
    flight_state?: string;
    telemetry?: {alt: number, spd: number, thrust: string}[];

    log: string[];
    isProcessing: boolean;
}

const initialState: SimulationState = {
    phase: 'init',
    aircraft_model: 'etzhayyim-Aero-777',
    log: ['[SYSTEM] System Ready. Awaiting initialization.'],
    isProcessing: false
};

function createSimulationStore() {
    const { subscribe, set, update } = writable<SimulationState>(initialState);

    const log = (msg: string) => update(s => ({ ...s, log: [...s.log, msg] }));

    const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

    return {
        subscribe,
        reset: () => set(initialState),
        start: async () => {
            update(s => ({ ...s, isProcessing: true }));
            log('[???] Initializing new aircraft project for model: etzhayyim-Aero-777');
            await delay(800);

            update(s => ({
                ...s,
                project_id: 'd3cc6ba6',
                phase: 'design',
                isProcessing: false
            }));
        },
        runDesign: async () => {
            update(s => ({ ...s, isProcessing: true }));
            const pid = get({subscribe}).project_id;
            log(`[${pid}] PHASE 1: ENGINE DESIGN (Kami CAD/CAE)`);
            await delay(1000);
            log(`[${pid}]  -> Designed Engine: etzhayyim-NextGen-TF9000`);

            const design: EngineDesign = {
                model_name: "etzhayyim-NextGen-TF9000",
                thrust_kn: 343.3,
                weight_kg: 4218.5,
                bypass_ratio: 11.5,
                core_materials: ["UNSPSC 11171901 (TA6V Titanium)", "UNSPSC 11151514 (Aramid fibers)"],
                rtl_validation_passed: true
            };

            update(s => ({ ...s, engine_design: design }));

            await delay(1000);
            log(`[${pid}] PHASE 2: ENGINE EVALUATION (Kami RTL Simulation)`);
            log(`[${pid}]  -> Running RTL physical simulation for FADEC...`);
            await delay(1000);
            log(`[${pid}]  -> RTL Verification PASSED.`);

            update(s => ({ ...s, phase: 'procure', isProcessing: false }));
        },
        runProcure: async () => {
            update(s => ({ ...s, isProcessing: true }));
            const pid = get({subscribe}).project_id;
            log(`[${pid}] PHASE 3: PROCUREMENT (UNSPSC & ISIC)`);
            await delay(1000);

            const bom = [
                'UNSPSC 11171901 (TA6V Titanium)',
                'UNSPSC 11151514 (Aramid fibers)',
                'UNSPSC 25131506 (Commercial passenger jet aircraft)',
                'UNSPSC 23152203 (Engine test stands)'
            ];
            log(`[${pid}]  -> Generating BOM...`);

            update(s => ({
                ...s,
                unspsc_bom: bom,
                isic_suppliers: [
                    {name: "AeroTitanium Inc.", isic: "3030 (Manufacture of air and spacecraft)"},
                    {name: "Global Test Systems", isic: "2651 (Manufacture of measuring instruments)"}
                ]
            }));

            await delay(1000);
            log(`[${pid}]  -> Component Procurement Approved via CAB-Review.`);

            update(s => ({ ...s, phase: 'manufacture_test', isProcessing: false }));
        },
        runTest: async () => {
            update(s => ({ ...s, isProcessing: true }));
            const pid = get({subscribe}).project_id;
            log(`[${pid}] PHASE 4: PHYSICAL TESTING (UNSPSC 23152203 Test Stands)`);
            await delay(500);
            log(`[${pid}]  -> Executing 150-hour continuous endurance test...`);

            const totalSteps = 40;
            const stepDelay = 100; // 4 seconds total

            // Initial metrics
            let currentMetrics: EngineTestMetrics = {
                max_temp_celsius: 20.0,
                vibration_hz: 0.0,
                fuel_flow_kg_s: 0.0,
                emission_nox_ppm: 0.0,
                passed_certification: false
            };

            update(s => ({ ...s, engine_test_metrics: {...currentMetrics} }));

            // Streaming physics data
            for (let i = 1; i <= totalSteps; i++) {
                await delay(stepDelay);
                const progress = i / totalSteps;
                // Add some noise to make it look real
                const noise = () => (Math.random() - 0.5) * 2;

                currentMetrics = {
                    max_temp_celsius: 20 + (1540 - 20) * progress + (progress > 0.1 ? noise() * 15 : 0),
                    vibration_hz: (12.31 * progress) + (progress > 0.2 ? noise() * 2 : 0),
                    fuel_flow_kg_s: (1.364 * progress) + (progress > 0.1 ? noise() * 0.1 : 0),
                    emission_nox_ppm: (48.8 * progress) + (progress > 0.5 ? noise() * 3 : 0),
                    passed_certification: i === totalSteps
                };

                // Snap to final values on last step
                if (i === totalSteps) {
                    currentMetrics.max_temp_celsius = 1540.0;
                    currentMetrics.vibration_hz = 12.31;
                    currentMetrics.fuel_flow_kg_s = 1.364;
                    currentMetrics.emission_nox_ppm = 48.8;
                }

                update(s => ({ ...s, engine_test_metrics: {...currentMetrics} }));
            }

            log(`[${pid}]  -> Engine physical test PASSED. Certified for flight.`);

            await delay(800);
            log(`[${pid}]  -> Integrating engine to wing pylon via Robotics (UNSPSC 23153200).`);
            update(s => ({ ...s, assembly_robot_ids: ["RoboArm-Welding-01", "PickPlace-03"] }));

            await delay(800);
            update(s => ({ ...s, phase: 'operate', isProcessing: false }));
        },
        runOperate: async () => {
            update(s => ({ ...s, isProcessing: true }));
            const pid = get({subscribe}).project_id;
            log(`[${pid}] PHASE 5: ASSEMBLY & DIGITAL TWIN OPERATION`);
            await delay(1000);

            const icao24 = "A3414D";
            log(`[${pid}]  -> Aircraft commissioned. ICAO24 Address: ${icao24}`);
            update(s => ({ ...s, icao24_address: icao24 }));

            await delay(1000);
            log(`[${pid}]  -> Digital Twin Simulation (maps_twin_sensor_sim): Simulating maiden flight...`);

            const telemetry = [
                {alt: 0, spd: 0, thrust: 'IDLE'},
                {alt: 10000, spd: 400, thrust: 'MCT (Max Continuous)'},
                {alt: 35000, spd: 850, thrust: 'CRUISE'}
            ];

            update(s => ({ ...s, telemetry: [] }));

            for (const t of telemetry) {
                await delay(1000);
                log(`[${pid}]     - Flight Stream: ${JSON.stringify(t)}`);
                update(s => ({ ...s, flight_state: t.thrust, telemetry: [...(s.telemetry || []), t] }));
            }

            log(`[${pid}] SUCCESS: Aircraft (ICAO24: ${icao24}) is in CRUISE.`);
            update(s => ({ ...s, isProcessing: false }));
        }
    };
}

export const simulation = createSimulationStore();
