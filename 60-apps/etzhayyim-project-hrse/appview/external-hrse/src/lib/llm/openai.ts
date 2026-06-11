// @etzhayyim/cyber-freelance#LLMService
// OpenAI API統合

import OpenAI from "openai";

export type EntityType = "JobSeeker" | "Job" | "Agency" | "Unknown";

export interface ExtractedEntity {
	'entityType': EntityType;
	confidence: number;
	'extractedData': Record<string, unknown>;
}

export interface EmailContent {
	from: string;
	to: string;
	subject: string;
	html: string | null;
	text: string | null;
	date: string | null;
}

export class LLMService {
	private client: OpenAI;

	constructor() {
		// OpenRouter APIキーを優先的に使用、なければOpenAI APIキーを使用
		const apiKey = process.env.OPENROUTER_API_KEY_251025 || process.env.OPENAI_API_KEY;
		if (!apiKey) {
			throw new Error("OPENROUTER_API_KEY_251025 or OPENAI_API_KEY environment variable not set");
		}

		// OpenRouterを使用する場合
		const baseURL = process.env.OPENROUTER_API_KEY_251025
			? "https://openrouter.ai/api/v1"
			: undefined;

		this.client = new OpenAI({
			apiKey,
			baseURL,
			defaultHeaders: process.env.OPENROUTER_API_KEY_251025
				? {
					"HTTP-Referer": process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",
					"X-Title": "AI etzhayyim HRSE",
				}
				: undefined,
		});
	}

	async analyzeEmail(email: EmailContent): Promise<ExtractedEntity> {
		const textContent = email.html
			? this.extractTextFromHtml(email.html) || email.text || ""
			: email.text || "";

		const prompt = this.buildAnalysisPrompt(email.subject, textContent);

		const response = await this.client.chat.completions.create({
			model: "gpt-4o",
			messages: [
				{
					role: "system",
					content:
						"You are an expert at extracting structured information from emails. Analyze the email content and determine if it contains information about a JobSeeker (person looking for work), a Job (job posting), or an Agency (recruitment agency). Extract all relevant structured data and return it as JSON.",
				},
				{
					role: "user",
					content: prompt,
				},
			],
			temperature: 0.3,
			'responseFormat': { type: "jsonObject" },
		});

		const content = response.choices[0]?.message?.content;
		if (!content) {
			throw new Error("No content in OpenAI response");
		}

		const parsed = JSON.parse(content) as {
			entityType: string;
			confidence: number;
			extractedData: Record<string, unknown>;
		};

		const entityType = this.normalizeEntityType(parsed.entityType);
		const confidence = Math.max(0, Math.min(1, parsed.confidence));

		return {
			'entityType': entityType,
			confidence,
			'extractedData': parsed.extractedData,
		};
	}

	async analyzeEmailWithRetry(
		email: EmailContent,
		maxRetries: number = 3,
	): Promise<ExtractedEntity> {
		let lastError: Error | null = null;

		for (let attempt = 0; attempt < maxRetries; attempt++) {
			try {
				return await this.analyzeEmail(email);
			} catch (error) {
				lastError = error instanceof Error ? error : new Error(String(error));
				if (attempt < maxRetries - 1) {
					const delay = Math.pow(2, attempt) * 1000; // Exponential backoff
					await new Promise((resolve) => setTimeout(resolve, delay));
				}
			}
		}

		throw lastError || new Error("Failed to analyze email after retries");
	}

	private normalizeEntityType(type: string): EntityType {
		const normalized = type.trim();
		if (normalized === "JobSeeker") return "JobSeeker";
		if (normalized === "Job") return "Job";
		if (normalized === "Agency") return "Agency";
		return "Unknown";
	}

	private buildAnalysisPrompt(subject: string, body: string): string {
		return `Analyze the following email and extract structured information.

Email Subject: ${subject}
Email Body: ${body}

Please determine the entity type (JobSeeker, Job, or Agency) and extract all relevant information as structured JSON.

Return a JSON object with the following structure:
{
  "entityType": "JobSeeker" | "Job" | "Agency" | "Unknown",
  "confidence": <number between 0 and 1>,
  "extractedData": {
    // Entity-specific fields based on the type
  }
}

For JobSeeker, extract: name, email, employmentType, nationality, workPermit, availability (from, workdaysPerWeek, remotePreference), desiredSalary (min, max), certifications, specializations, languages, and SES-specific fields (totalYearsOfExperience, commercialFlow, skillSheetUrl).

For Job, extract: title, description, location, salary (min, max), remoteAllowed, startDate, endDate, jobType, requirements (specializations, certifications, languages), postedBy, company, and SES-specific fields (commercialFlow, requirementRank).

For Agency, extract: name, email, phone, address, licenseNumber, and SES-specific fields (agencyType, partnershipRank).`;
	}

	private extractTextFromHtml(html: string): string | null {
		// Simple HTML text extraction (can be enhanced with a proper HTML parser)
		const text = html
			.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, "")
			.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, "")
			.replace(/<[^>]+>/g, " ")
			.replace(/\s+/g, " ")
			.trim();
		return text || null;
	}
}

