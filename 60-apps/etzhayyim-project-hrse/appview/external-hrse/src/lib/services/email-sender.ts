// @etzhayyim/etzhayyim-hrse#EmailSender
// Email Sending Service with Resend integration and secure link generation

import { randomBytes } from "crypto";

export interface SecureLinkConfig {
	entityType: "job" | "jobSeeker";
	entityId: string;
	allowedEmails: string[];
	expiresInDays?: number;
}

export interface SecureLink {
	id: string;
	token: string;
	url: string;
	expiresAt: Date;
}

export interface SendEmailOptions {
	to: string;
	subject: string;
	bodyHtml: string;
	bodyText: string;
	from?: string;
	secureLink?: SecureLink;
}

export class EmailSenderService {
	private defaultFrom: string;

	constructor() {
		const resendApiKey = process.env.RESEND_API_KEY || "";
		if (!resendApiKey) {
			throw new Error("RESEND_API_KEY environment variable not set");
		}

		this.defaultFrom =
			process.env.RESEND_FROM_EMAIL || "noreply@etzhayyim.com";
	}

	/**
	 * セキュアURLを生成
	 */
	async createSecureLink(
		config: SecureLinkConfig,
	): Promise<SecureLink> {
		// Generate a secure token: UUID v4 + additional entropy
		const uuid = this.generateUUID();
		const entropy = randomBytes(16).toString("hex");
		const token = `${uuid}-${entropy}`;

		const expiresInDays = config.expiresInDays || 30;
		const expiresAt = new Date();
		expiresAt.setDate(expiresAt.getDate() + expiresInDays);

		const baseUrl =
			process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";
		const url = `${baseUrl}/secure/${token}`;

		// Note: In production, this should save to database via API call
		// For now, we return the link structure
		return {
			id: uuid, // This should be the database ID
			token,
			url,
			expiresAt,
		};
	}

	/**
	 * マッチング通知メールを送信（セキュアURLを含む）
	 */
	async sendMatchingEmail(
		options: SendEmailOptions,
	): Promise<{ success: boolean; emailId?: string; error?: string }> {
		try {
			// Replace secure link placeholder if present
			let bodyHtml = options.bodyHtml;
			let bodyText = options.bodyText;

			if (options.secureLink) {
				const secureLinkHtml = `<a href="${options.secureLink.url}" style="display: inline-block; padding: 12px 24px; background-color: #0070f3; color: white; text-decoration: none; border-radius: 5px; margin: 16px 0;">詳細を確認する</a>`;
				const secureLinkText = `詳細を確認: ${options.secureLink.url}`;

				bodyHtml = bodyHtml.replace(
					/\[SECURE_LINK_PLACEHOLDER\]/g,
					secureLinkHtml,
				);
				bodyText = bodyText.replace(
					/\[SECURE_LINK_PLACEHOLDER\]/g,
					secureLinkText,
				);
			}

			return {
				success: false,
				error:
					"Unsupported: direct Resend API fetch is disabled. Use a descriptor-backed Connect email sending endpoint.",
			};
		} catch (error) {
			return {
				success: false,
				error:
					error instanceof Error ? error.message : "Unknown error",
			};
		}
	}

	/**
	 * セキュアURLを含むメールを送信
	 */
	async sendEmailWithSecureLink(
		options: SendEmailOptions,
		secureLinkConfig: SecureLinkConfig,
	): Promise<{ success: boolean; emailId?: string; secureLink?: SecureLink; error?: string }> {
		const secureLink = await this.createSecureLink(secureLinkConfig);

		const result = await this.sendMatchingEmail({
			...options,
			secureLink,
		});

		if (result.success) {
			return {
				success: true,
				emailId: result.emailId,
				secureLink,
			};
		}

		return {
			success: false,
			error: result.error,
		};
	}

	private generateUUID(): string {
		// Generate UUID v4
		return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(
			/[xy]/g,
			function (c) {
				const r = (Math.random() * 16) | 0;
				const v = c === "x" ? r : (r & 0x3) | 0x8;
				return v.toString(16);
			},
		);
	}
}
