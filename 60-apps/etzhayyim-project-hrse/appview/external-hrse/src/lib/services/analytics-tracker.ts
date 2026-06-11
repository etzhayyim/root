// @etzhayyim/etzhayyim-hrse#AnalyticsTracker
// Comprehensive Analytics Tracker for Secure Links

export interface ClickEvent {
	element: string;
	x: number;
	y: number;
	timestamp: Date;
}

export interface MouseMovement {
	x: number;
	y: number;
	timestamp: Date;
}

export interface AnalyticsData {
	secureLinkId: string;
	email: string;
	pagePath: string;
	timeOnPage: number; // seconds
	scrollDepth: number; // percentage 0-100
	clicks: ClickEvent[];
	mouseMovements: MouseMovement[];
	focusTime: number; // seconds
	exitPoint?: string;
	sectionsViewed: string[];
}

type AccessLogPayload = {
	secureLinkId: string;
	email: string;
	pagePath: string;
	timeOnPage: number;
	scrollDepth: number;
	focusTime: number;
	exitPoint?: string;
	sectionsViewed?: string[];
	clicks?: ClickEvent[];
	mouseMovements?: MouseMovement[];
};

export class AnalyticsTracker {
	private secureLinkId: string;
	private email: string;
	private startTime: Date;
	private lastActivityTime: Date;
	private clicks: ClickEvent[] = [];
	private mouseMovements: MouseMovement[] = [];
	private sectionsViewed: Set<string> = new Set();
	private maxScrollDepth: number = 0;
	private focusStartTime: Date | null = null;
	private totalFocusTime: number = 0;
	private isTracking: boolean = false;
	private movementSampleRate: number = 10; // Sample every 10th movement
	private movementCounter: number = 0;

	constructor(secureLinkId: string, email: string) {
		this.secureLinkId = secureLinkId;
		this.email = email;
		this.startTime = new Date();
		this.lastActivityTime = new Date();
	}

	startTracking() {
		if (this.isTracking) return;
		this.isTracking = true;

		// Track page visibility
		document.addEventListener("visibilitychange", this.handleVisibilityChange);
		document.addEventListener("focus", this.handleFocus);
		document.addEventListener("blur", this.handleBlur);

		// Track clicks
		document.addEventListener("click", this.handleClick);

		// Track mouse movements (sampled)
		document.addEventListener("mousemove", this.handleMouseMove);

		// Track scroll
		window.addEventListener("scroll", this.handleScroll);

		// Track sections viewed
		this.trackSections();

		// Send heartbeat every 30 seconds
		this.heartbeatInterval = setInterval(() => {
			this.sendHeartbeat();
		}, 30000);

		// Send final data on page unload
		window.addEventListener("beforeunload", this.handleBeforeUnload);
	}

	stopTracking() {
		if (!this.isTracking) return;
		this.isTracking = false;

		document.removeEventListener("visibilitychange", this.handleVisibilityChange);
		document.removeEventListener("focus", this.handleFocus);
		document.removeEventListener("blur", this.handleBlur);
		document.removeEventListener("click", this.handleClick);
		document.removeEventListener("mousemove", this.handleMouseMove);
		window.removeEventListener("scroll", this.handleScroll);
		window.removeEventListener("beforeunload", this.handleBeforeUnload);

		if (this.heartbeatInterval) {
			clearInterval(this.heartbeatInterval);
		}
	}

	private handleVisibilityChange = () => {
		if (document.hidden) {
			this.handleBlur();
		} else {
			this.handleFocus();
		}
	};

	private handleFocus = () => {
		this.focusStartTime = new Date();
	};

	private handleBlur = () => {
		if (this.focusStartTime) {
			const focusDuration =
				(new Date().getTime() - this.focusStartTime.getTime()) / 1000;
			this.totalFocusTime += focusDuration;
			this.focusStartTime = null;
		}
	};

	private handleClick = (event: MouseEvent) => {
		const target = event.target as HTMLElement;
		const element = target.tagName + (target.id ? `#${target.id}` : "") + (target.className ? `.${target.className}` : "");

		this.clicks.push({
			element,
			x: event.clientX,
			y: event.clientY,
			timestamp: new Date(),
		});

		this.lastActivityTime = new Date();
	};

	private handleMouseMove = (event: MouseEvent) => {
		this.movementCounter++;
		if (this.movementCounter % this.movementSampleRate !== 0) {
			return;
		}

		this.mouseMovements.push({
			x: event.clientX,
			y: event.clientY,
			timestamp: new Date(),
		});

		// Limit stored movements to prevent memory issues
		if (this.mouseMovements.length > 1000) {
			this.mouseMovements = this.mouseMovements.slice(-500);
		}
	};

	private handleScroll = () => {
		const scrollHeight = document.documentElement.scrollHeight;
		const clientHeight = window.innerHeight;
		const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
		const scrollDepth = (scrollTop / (scrollHeight - clientHeight)) * 100;
		this.maxScrollDepth = Math.max(this.maxScrollDepth, scrollDepth);
		this.lastActivityTime = new Date();
	};

	private trackSections() {
		const sections = document.querySelectorAll("[data-section]");
		const observer = new IntersectionObserver(
			(entries) => {
				entries.forEach((entry) => {
					if (entry.isIntersecting) {
						const sectionId = entry.target.getAttribute("data-section");
						if (sectionId) {
							this.sectionsViewed.add(sectionId);
						}
					}
				});
			},
			{ threshold: 0.5 },
		);

		sections.forEach((section) => observer.observe(section));
	}

	private heartbeatInterval: NodeJS.Timeout | null = null;

	private sendHeartbeat = () => {
		const timeOnPage =
			(new Date().getTime() - this.startTime.getTime()) / 1000;
		const data: AccessLogPayload = {
			secureLinkId: this.secureLinkId,
			email: this.email,
			pagePath: window.location.pathname,
			timeOnPage: Math.floor(timeOnPage),
			scrollDepth: Math.round(this.maxScrollDepth),
			focusTime: Math.floor(this.totalFocusTime),
			sectionsViewed: Array.from(this.sectionsViewed),
		};

		// Send heartbeat (non-blocking) via Connect
		void this.sendAccessLog(data).catch((_err) => {
			// Ignore errors
		});
	};

	private handleBeforeUnload = () => {
		this.sendFinalData();
	};

	async sendFinalData() {
		const timeOnPage =
			(new Date().getTime() - this.startTime.getTime()) / 1000;

		// Calculate final focus time
		if (this.focusStartTime) {
			const focusDuration =
				(new Date().getTime() - this.focusStartTime.getTime()) / 1000;
			this.totalFocusTime += focusDuration;
		}

		const data: AnalyticsData = {
			secureLinkId: this.secureLinkId,
			email: this.email,
			pagePath: window.location.pathname,
			timeOnPage: Math.floor(timeOnPage),
			scrollDepth: Math.round(this.maxScrollDepth),
			clicks: this.clicks.slice(-100), // Limit to last 100 clicks
			mouseMovements: this.mouseMovements.slice(-500), // Limit to last 500 movements
			focusTime: Math.floor(this.totalFocusTime),
			exitPoint: document.activeElement?.tagName || undefined,
			sectionsViewed: Array.from(this.sectionsViewed),
		};

		// Save access log via Connect-Web
		await this.sendAccessLog(data);
	}

	private async sendAccessLog(data: AccessLogPayload): Promise<void> {
		try {
			const { create } = await import("@bufbuild/protobuf");
			const { createClient } = await import("@connectrpc/connect");
			const { createTransport } = await import("@/lib/connect/client");
			const emailAgentProto = await import("@/gen/proto/hrse/v1/emailAgentPb");
			const { EmailAgentService, SaveAccessLogRequestSchema } = emailAgentProto;

			if (!EmailAgentService || !SaveAccessLogRequestSchema) {
				throw new Error("Unsupported: hrse.v1.EmailAgentService/SaveAccessLog descriptor is unavailable");
			}

			// Convert clicks and mouse movements to protobuf format
			// Note: Timestamp is created manually from Date
			const dateToTimestamp = (date: Date) => {
				const seconds = Math.floor(date.getTime() / 1000);
				const nanos = (date.getTime() % 1000) * 1000000;
				return { seconds: BigInt(seconds), nanos };
			};

			const clicks = (data.clicks || []).map(click => ({
				element: click.element,
				x: click.x,
				y: click.y,
				timestamp: dateToTimestamp(click.timestamp),
			}));

			const mouseMovements = (data.mouseMovements || []).map(movement => ({
				x: movement.x,
				y: movement.y,
				timestamp: dateToTimestamp(movement.timestamp),
			}));

			const request = create(SaveAccessLogRequestSchema, {
				secureLinkId: data.secureLinkId,
				email: data.email,
				ipAddress: "", // Will be set by server
				userAgent: navigator.userAgent,
				pagePath: data.pagePath,
				timeOnPage: data.timeOnPage,
				scrollDepth: data.scrollDepth,
				clicks: clicks,
				mouseMovements: mouseMovements,
				focusTime: data.focusTime,
				exitPoint: data.exitPoint,
				sectionsViewed: data.sectionsViewed || [],
			});

			const transport = createTransport();
			const client = createClient(EmailAgentService, transport);
			if (typeof client.saveAccessLog !== "function") {
				throw new Error("Unsupported: hrse.v1.EmailAgentService/SaveAccessLog descriptor is unavailable");
			}
			await client.saveAccessLog(request);
		} catch (error) {
			if (
				error instanceof Error &&
				error.message.includes("emailAgentPb")
			) {
				throw new Error("Unsupported: hrse.v1.EmailAgentService/SaveAccessLog descriptor is unavailable");
			}

			if (
				error instanceof Error &&
				error.message.includes("Unsupported: hrse.v1.EmailAgentService/SaveAccessLog descriptor is unavailable")
			) {
				throw error;
			}

			console.error("Failed to save access log:", error);
		}
	}
}
