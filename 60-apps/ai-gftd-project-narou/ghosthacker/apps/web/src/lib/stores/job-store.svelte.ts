/**
 * Reactive store for image generation job state.
 * Tracks active jobs and their progress, updated via StreamUpdates.
 */

export interface JobState {
	jobId: string;
	episodeId: string;
	pageNumber: number;
	panel: number;
	status: string; // "queued" | "running" | "completed" | "failed" | "cancelled"
	currentStep: number;
	totalSteps: number;
	etaMs: number;
	error: string;
	imageUrl: string;
}

// Module-level reactive state
let jobs = $state(new Map<string, JobState>());

export function getActiveJobs(): Map<string, JobState> {
	return jobs;
}

export function updateJob(jobId: string, update: Partial<JobState>) {
	const existing = jobs.get(jobId);
	if (existing) {
		const updated = { ...existing, ...update };
		jobs.set(jobId, updated);
		// Trigger reactivity by replacing the map
		jobs = new Map(jobs);
	} else if (update.status) {
		jobs.set(jobId, {
			jobId,
			episodeId: '',
			pageNumber: 0,
			panel: 0,
			status: 'queued',
			currentStep: 0,
			totalSteps: 28,
			etaMs: 0,
			error: '',
			imageUrl: '',
			...update,
		} as JobState);
		jobs = new Map(jobs);
	}
}

export function removeJob(jobId: string) {
	jobs.delete(jobId);
	jobs = new Map(jobs);
}

/** Find the active job for a specific panel. */
export function getJobForPanel(episodeId: string, pageNumber: number, panel: number): JobState | undefined {
	for (const job of jobs.values()) {
		if (
			job.episodeId === episodeId &&
			job.pageNumber === pageNumber &&
			job.panel === panel &&
			(job.status === 'queued' || job.status === 'running')
		) {
			return job;
		}
	}
	return undefined;
}

/** Count of currently active (queued + running) jobs. */
export function getActiveJobCount(): number {
	let count = 0;
	for (const job of jobs.values()) {
		if (job.status === 'queued' || job.status === 'running') {
			count++;
		}
	}
	return count;
}
