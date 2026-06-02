import { AtpBaseClient } from '@atproto/api';
import type {
	GetEpisodesResponse,
	GetEpisodePanelsResponse,
	StreamUpdatesResponse,
	GetArcsResponse,
	GetArcPanelsResponse,
	ExportPdfResponse,
	ListProjectsResponse,
	SubmitGenerationJobResponse,
	CancelGenerationJobResponse,
	ListGenerationJobsResponse
} from '$lib/gen/proto/storyboard_pb';

// Determine API base URL
const getApiBaseUrl = (): string => {
	if (typeof window === 'undefined') {
		return 'http://localhost:8081';
	}
	// In development, frontend runs on 1421, backend on 8081
	if (window.location.port === '1421' || window.location.hostname === 'localhost') {
		return 'http://localhost:8081';
	}
	// In production, use same origin
	return window.location.origin;
};

const transport = new AtpBaseClient({
	service: getApiBaseUrl,
});

async function callProcedure<T>(
	nsid: string,
	body: Record<string, unknown> = {},
	signal?: AbortSignal
): Promise<T> {
	const response = await transport.call(nsid, undefined, body, {
		headers: { 'content-type': 'application/json' },
		signal
	});
	return response.data as T;
}

export const storyboardClient = transport;

/**
 * Type-safe wrapper for getEpisodes with runtime validation
 */
export async function getEpisodes(filePath: string = ''): Promise<GetEpisodesResponse['episodes']> {
	console.log('[storyboard-client] getEpisodes: calling API', { filePath, baseUrl: getApiBaseUrl() });

	try {
		const response = await callProcedure<GetEpisodesResponse>('ai.gftd.narou.getEpisodes', { filePath });
		console.log('[storyboard-client] getEpisodes: raw response', response);

		// Runtime validation
		if (!response || typeof response !== 'object') {
			throw new Error(`Invalid response: response is not an object, got ${typeof response}`);
		}

		if (!('episodes' in response)) {
			console.error('[storyboard-client] getEpisodes: response keys', Object.keys(response));
			throw new Error('Invalid response: missing episodes field');
		}

		if (!Array.isArray(response.episodes)) {
			throw new Error(`Invalid response: episodes is not an array, got ${typeof response.episodes}, value: ${JSON.stringify(response.episodes)}`);
		}

		console.log('[storyboard-client] getEpisodes: validation passed', { count: response.episodes.length });
		return response.episodes;
	} catch (err) {
		console.error('[storyboard-client] getEpisodes: error', err);
		throw err;
	}
}

/**
 * Type-safe wrapper for getArcs with runtime validation
 */
export async function getArcs(filePath: string = ''): Promise<GetArcsResponse['arcs']> {
	console.log('[storyboard-client] getArcs: calling API', { filePath, baseUrl: getApiBaseUrl() });

	try {
		const response = await callProcedure<GetArcsResponse>('ai.gftd.narou.getArcs', { filePath });
		console.log('[storyboard-client] getArcs: raw response', response);

		if (!response || typeof response !== 'object') {
			throw new Error('Invalid response: response is not an object');
		}

		if (!('arcs' in response)) {
			throw new Error('Invalid response: missing arcs field');
		}

		if (!Array.isArray(response.arcs)) {
			throw new Error(`Invalid response: arcs is not an array, got ${typeof response.arcs}`);
		}

		return response.arcs;
	} catch (err) {
		console.error('[storyboard-client] getArcs: error', err);
		throw err;
	}
}

/**
 * Type-safe wrapper for getEpisodePanels with runtime validation
 */
export async function getEpisodePanels(
	filePath: string,
	episodeId: string,
	pageNumber: number
): Promise<GetEpisodePanelsResponse['panels']> {
	const response = await callProcedure<GetEpisodePanelsResponse>('ai.gftd.narou.getEpisodePanels', {
		filePath,
		episodeId,
		pageNumber
	});

	// Runtime validation
	if (!response || typeof response !== 'object') {
		throw new Error('Invalid response: response is not an object');
	}

	if (!('panels' in response)) {
		throw new Error('Invalid response: missing panels field');
	}

	if (!Array.isArray(response.panels)) {
		throw new Error(`Invalid response: panels is not an array, got ${typeof response.panels}`);
	}

	return response.panels;
}

/**
 * Type-safe wrapper for getArcPanels with runtime validation
 */
export async function getArcPanels(
	filePath: string,
	arcId: string
): Promise<GetArcPanelsResponse['panels']> {
	const response = await callProcedure<GetArcPanelsResponse>('ai.gftd.narou.getArcPanels', {
		filePath,
		arcId
	});

	if (!response || typeof response !== 'object') {
		throw new Error('Invalid response: response is not an object');
	}

	if (!('panels' in response)) {
		throw new Error('Invalid response: missing panels field');
	}

	if (!Array.isArray(response.panels)) {
		throw new Error(`Invalid response: panels is not an array, got ${typeof response.panels}`);
	}

	return response.panels;
}

/**
 * Generate image for a panel using backend API
 */
export async function generatePanelImage(
	filePath: string,
	episodeId: string,
	pageNumber: number,
	panel: number,
	panelData: any,
	model: string = ''
) {
	const response = await callProcedure<any>('ai.gftd.narou.generatePanelImage', {
		filePath,
		episodeId,
		pageNumber,
		panel,
		panelData,
		model,
	});

	if (!response || typeof response !== 'object') {
		throw new Error('Invalid response: response is not an object');
	}

	if (!response.success) {
		throw new Error(response.message || 'Failed to generate image');
	}

	return response;
}

/**
 * Generate dialogue for a panel using backend (OpenRouter text)
 */
export async function generatePanelDialogue(
	filePath: string,
	episodeId: string,
	pageNumber: number,
	panel: number,
	panelData: any,
	options?: {
		maxLines?: number;
		style?: string;
		strictKnownFacts?: boolean;
	}
) {
	const response = await callProcedure<any>('ai.gftd.narou.generateDialogue', {
		filePath,
		episodeId,
		pageNumber,
		panel,
		panelData,
		maxLines: options?.maxLines ?? 0,
		style: options?.style ?? '',
		strictKnownFacts: options?.strictKnownFacts ?? true,
	});

	if (!response || typeof response !== 'object') {
		throw new Error('Invalid response: response is not an object');
	}

	if (!response.success) {
		throw new Error(response.message || 'Failed to generate dialogue');
	}

	return response;
}

/**
 * Export storyboard to PDF using backend API
 */
export async function exportPdf(
	filePath: string,
	episodeId: string,
	arcId: string,
	mode: string
): Promise<ExportPdfResponse> {
	const response = await callProcedure<ExportPdfResponse>('ai.gftd.narou.exportPdf', {
		filePath,
		episodeId,
		arcId,
		mode
	});

	if (!response || typeof response !== 'object') {
		throw new Error('Invalid response: response is not an object');
	}

	if (!(response as any).success) {
		throw new Error((response as any).message || 'Failed to export PDF');
	}

	return response;
}

/**
 * Subscribe to real-time updates from the server
 */
export function streamUpdates(
	filePath: string,
	sessionId: string,
	onUpdate: (update: StreamUpdatesResponse) => void,
	onError: (err: any) => void
) {
	const abortController = new AbortController();

	(async () => {
		try {
			const update = await callProcedure<StreamUpdatesResponse>(
				'ai.gftd.narou.streamUpdates',
				{ filePath, sessionId },
				abortController.signal
			);
			onUpdate(update);
		} catch (err: any) {
			const isCanceled =
				err?.name === 'AbortError' ||
				(err instanceof Error && (
					err.message.includes('aborted') ||
					err.message.includes('canceled') ||
					err.message.includes('signal is aborted')
				));

			if (isCanceled) {
				console.log('[storyboard-client] streamUpdates: connection closed (canceled)');
				return;
			}
			console.error('[storyboard-client] streamUpdates: error', err);
			onError(err);
		}
	})();

	return () => abortController.abort();
}

/**
 * List available projects in the workspace
 */
export async function listProjects(): Promise<ListProjectsResponse> {
	console.log('[storyboard-client] listProjects: calling API');
	const response = await callProcedure<ListProjectsResponse>('ai.gftd.narou.listProjects');
	console.log('[storyboard-client] listProjects: response', response, 'projects:', response.projects?.length);
	return response;
}

/**
 * Switch the active project
 */
export async function switchProject(projectId: string) {
	const response = await callProcedure<any>('ai.gftd.narou.switchProject', { projectId });
	if (!response.success) {
		throw new Error(response.message || 'Failed to switch project');
	}
	return response;
}

// --- Image Generation Job Queue ---

/**
 * Submit an image generation job to the queue
 */
export async function submitGenerationJob(
	filePath: string,
	episodeId: string,
	pageNumber: number,
	panel: number,
	panelData: any,
	model: string = ''
): Promise<SubmitGenerationJobResponse> {
	const response = await callProcedure<SubmitGenerationJobResponse>('ai.gftd.narou.submitGenerationJob', {
		filePath,
		episodeId,
		pageNumber,
		panel,
		panelData,
		model,
	});
	if (!(response as any).success) {
		throw new Error((response as any).message || 'Failed to submit generation job');
	}
	return response;
}

/**
 * Cancel a generation job
 */
export async function cancelGenerationJob(jobId: string): Promise<CancelGenerationJobResponse> {
	return callProcedure<CancelGenerationJobResponse>('ai.gftd.narou.cancelGenerationJob', { jobId });
}

/**
 * List all generation jobs
 */
export async function listGenerationJobs(): Promise<ListGenerationJobsResponse> {
	return callProcedure<ListGenerationJobsResponse>('ai.gftd.narou.listGenerationJobs');
}
