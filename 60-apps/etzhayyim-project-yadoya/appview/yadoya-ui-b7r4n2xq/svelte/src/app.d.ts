/// <reference types="@sveltejs/adapter-cloudflare" />

interface SecretsStoreSecret {
	get(): Promise<string>;
}

declare global {
	namespace App {
		interface Platform {
			env: {
				KOTODAMA: DurableObjectNamespace;
				ASSETS: Fetcher;
				YATA_R2: R2Bucket;
				CDN_R2: R2Bucket;
				SS_YATA_S3_KEY_ID: SecretsStoreSecret;
				SS_YATA_S3_SECRET_KEY: SecretsStoreSecret;
				SS_OPENROUTER_API_KEY: SecretsStoreSecret;
				SS_AT_BOT_SECRET: SecretsStoreSecret;
				SS_YATA_D1_API_TOKEN: SecretsStoreSecret;
			};
			context: ExecutionContext;
		}
	}
}

export {};
