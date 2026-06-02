/**
 * OpenRouter AI Image Generation Client
 * Uses Seedream 4.5 via OpenRouter
 */

const OPENROUTER_API_KEY = import.meta.env.VITE_OPENROUTER_API_KEY || '';
const OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions';

export interface ImageGenerationOptions {
	prompt: string;
	model?: string;
	aspectRatio?: string;
	imageSize?: string;
}

export interface ImageGenerationResponse {
	success: boolean;
	imageUrl?: string;
	error?: string;
}

type OpenRouterResponse = {
	choices?: Array<{
		message?: {
			images?: Array<{ image_url?: { url?: string } }>;
			content?: string;
		};
	}>;
};

/**
 * Generate image using OpenRouter AI.
 */
export async function generateImage(
	options: ImageGenerationOptions
): Promise<ImageGenerationResponse> {
	if (!OPENROUTER_API_KEY) {
		return {
			success: false,
			error: 'OPENROUTER_API_KEY is not set. Please set VITE_OPENROUTER_API_KEY environment variable.',
		};
	}

	const {
		prompt,
		model = 'bytedance-seed/seedream-4.5',
		aspectRatio = '16:9',
		imageSize = '1024x1024',
	} = options;

	try {
		console.log('[openrouter-image] Generating image with prompt:', prompt);
		console.log('[openrouter-image] Model:', model);

		const response = await fetch(OPENROUTER_API_URL, {
			method: 'POST',
			headers: {
				Authorization: `Bearer ${OPENROUTER_API_KEY}`,
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				model,
				messages: [
					{
						role: 'user',
						content: [
							{
								type: 'text',
								text: `${prompt}\n\nAspect ratio: ${aspectRatio}\nImage size: ${imageSize}`,
							},
						],
					},
				],
			}),
		});

		if (!response.ok) {
			const errorText = await response.text();
			return {
				success: false,
				error: `OpenRouter request failed: ${response.status} ${errorText}`,
			};
		}

		const payload = (await response.json()) as OpenRouterResponse;
		const imageUrl = payload.choices?.[0]?.message?.images?.[0]?.image_url?.url;
		if (!imageUrl) {
			return {
				success: false,
				error: payload.choices?.[0]?.message?.content || 'OpenRouter response did not include an image URL.',
			};
		}

		return {
			success: true,
			imageUrl,
		};
	} catch (error) {
		return {
			success: false,
			error: error instanceof Error ? error.message : 'Unknown OpenRouter error',
		};
	}
}
