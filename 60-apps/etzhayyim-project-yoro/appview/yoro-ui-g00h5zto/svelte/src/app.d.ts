interface SecretsStoreSecret {
	get(): Promise<string>;
}

interface FetchBinding {
	fetch(request: Request): Promise<Response>;
}

interface R2ObjectBody {
	json(): Promise<any>;
	customMetadata?: Record<string, string>;
}

interface R2BucketLike {
	get(key: string): Promise<R2ObjectBody | null>;
	put(
		key: string,
		value: string | ArrayBuffer | ArrayBufferView | ReadableStream,
		options?: {
			httpMetadata?: { contentType?: string };
			customMetadata?: Record<string, string>;
		}
	): Promise<void>;
}

declare global {
	interface Navigator {
		gpu?: unknown;
	}

	namespace App {
		interface Platform {
			env: {
				SS_PUBLIC_CLERK_PUBLISHABLE_KEY?: SecretsStoreSecret;
				SS_CLERK_SECRET_KEY?: SecretsStoreSecret;
				PDS_SERVICE?: FetchBinding;
				YATA_R2?: R2BucketLike;
			};
		}
	}
}

export {};
