/**
 * capability-probe.ts — Detect browser GPU/memory/battery/network capabilities.
 * Used by BrowserInferenceAgent to register with murakumo gateway.
 */

import type { BrowserCapability } from './browser-gateway-client.js';

export interface GPUInfo {
	available: boolean;
	adapter: string;
	features: string[];
	'maxStorageBufferBindingSize': number;
	'maxComputeWorkgroupStorageSize': number;
}

export async function probeCapabilities(): Promise<BrowserCapability> {
	const gpu = await probeGPU();
	const memClass = classifyMemory();
	const netClass = classifyNetwork();
	const powerClass = await classifyPower();
	const gpuTier = classifyGPUTier(gpu, powerClass);

	return {
		'wasmSimd': typeof WebAssembly !== 'undefined',
		'wasmThreads': typeof SharedArrayBuffer !== 'undefined',
		gpu,
		'memClass': memClass,
		'netClass': netClass,
		'powerClass': powerClass,
		'gpuTier': gpuTier,
		cores: typeof navigator !== 'undefined' ? navigator.hardwareConcurrency ?? 1 : 1,
		'userAgent': typeof navigator !== 'undefined' ? navigator.userAgent : '',
	};
}

async function probeGPU(): Promise<GPUInfo> {
	const info: GPUInfo = {
		available: false,
		adapter: 'unknown',
		features: [],
		'maxStorageBufferBindingSize': 0,
		'maxComputeWorkgroupStorageSize': 0,
	};

	if (typeof navigator === 'undefined' || !('gpu' in navigator)) return info;

	try {
		const adapter = await (navigator as any).gpu.requestAdapter();
		if (!adapter) return info;

		info.available = true;

		const adapterInfo = adapter.info ?? (adapter as any).requestAdapterInfo?.();
		if (adapterInfo) {
			const vendor = (adapterInfo.vendor ?? '').toLowerCase();
			if (vendor.includes('apple')) info.adapter = 'apple';
			else if (vendor.includes('intel')) info.adapter = 'intel';
			else if (vendor.includes('nvidia')) info.adapter = 'nvidia';
			else if (vendor.includes('amd') || vendor.includes('ati')) info.adapter = 'amd';
			else if (vendor.includes('qualcomm')) info.adapter = 'qualcomm';
		}

		info.features = Array.from(adapter.features as Set<string>);
		info.maxStorageBufferBindingSize = adapter.limits.maxStorageBufferBindingSize ?? 0;
		info.maxComputeWorkgroupStorageSize = adapter.limits.maxComputeWorkgroupStorageSize ?? 0;
	} catch {
		// WebGPU not available
	}

	return info;
}

function classifyMemory(): string {
	if (typeof navigator === 'undefined') return 'mid';
	const mem = (navigator as any).deviceMemory;
	if (typeof mem !== 'number') return 'mid';
	if (mem >= 8) return 'high';
	if (mem >= 4) return 'mid';
	return 'low';
}

function classifyNetwork(): string {
	if (typeof navigator === 'undefined') return 'ok';
	const conn = (navigator as any).connection;
	if (!conn) return 'ok';
	const type = conn.effectiveType;
	if (type === '4g') return 'good';
	if (type === '3g') return 'ok';
	return 'poor';
}

async function classifyPower(): Promise<string> {
	if (typeof navigator === 'undefined' || !('getBattery' in navigator)) return 'desktop';
	try {
		const battery = await (navigator as any).getBattery();
		if (!battery) return 'desktop';
		if (battery.charging) return 'charging';
		return 'battery';
	} catch {
		return 'desktop';
	}
}

export function classifyGPUTier(gpu: GPUInfo, powerClass: string): string {
	if (!gpu.available) return 'g0';
	const hasF16 = gpu.features.includes('shader-f16');
	const bigBuf = gpu.maxStorageBufferBindingSize >= 256 * 1024 * 1024;
	const veryBigBuf = gpu.maxStorageBufferBindingSize >= 1024 * 1024 * 1024;

	if (hasF16 && veryBigBuf && powerClass === 'desktop') return 'g4';
	if (hasF16 && bigBuf) return 'g3';
	if (hasF16) return 'g2';
	return 'g1';
}
