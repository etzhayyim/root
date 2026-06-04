<script lang="ts">
	import {
		buildEmergencyKitText,
		downloadEmergencyKit,
		enrollKeyBundle,
		fetchAndUnlockKeyBundle,
		generateSecretKey,
	} from './key-bundle-flows.js';
	import type { KeyBundleClientConfig } from './types.js';

	interface Props {
		orgId: string;
		userId: string;
		deviceId: string;
		clientConfig?: KeyBundleClientConfig;
		defaultEnvelopeJson?: string;
	}

	const {
		orgId,
		userId,
		deviceId,
		clientConfig,
		defaultEnvelopeJson = `{
  "version": "zk-v1",
  "owner": {
    "clerkUserId": "${userId}",
    "clerkOrgId": "${orgId}"
  },
  "deviceId": "${deviceId}",
  "alg": {
    "kdf": "pbkdf2-sha256",
    "aead": "xchacha20poly1305",
    "wrap": "x25519-hkdf"
  },
  "wrappedKeys": {
    "akByMk": "b64url:replace-with-ciphertext",
    "dkByAk": "b64url:replace-with-ciphertext",
    "dekByAk": "b64url:replace-with-ciphertext"
  },
  "aad": {
    "objectId": "obj_...",
    "createdAt": "${new Date().toISOString()}"
  }
}`,
	}: Props = $props();

	let accountPassword = $state('');
	let secretKey = $state(generateSecretKey());
	let envelopeJson = $state('');
	let unlockPassword = $state('');
	let unlockSecretKey = $state('');
	let status = $state('ready');
	let lastSalt = $state('');
	let lastIterations = $state(0);

	$effect(() => {
		if (!envelopeJson) envelopeJson = defaultEnvelopeJson;
	});

	async function onEnroll() {
		status = 'enrolling...';
		try {
			const result = await enrollKeyBundle({
				orgId,
				userId,
				deviceId,
				accountPassword,
				secretKey,
				envelopeJson,
				clientConfig,
			});
			lastSalt = result.kdf.saltBase64Url;
			lastIterations = result.kdf.iterations;
			status = `enrolled: ${result.bundle.version} (${result.bundle.updatedAt})`;
		} catch (error) {
			status = `enroll failed: ${String(error)}`;
		}
	}

	async function onUnlock() {
		status = 'unlocking...';
		try {
			const result = await fetchAndUnlockKeyBundle({
				orgId,
				userId,
				deviceId,
				accountPassword: unlockPassword,
				secretKey: unlockSecretKey,
				clientConfig,
			});
			lastSalt = result.kdf.saltBase64Url;
			lastIterations = result.kdf.iterations;
			status = `unlock ok: wrapped key bytes=${result.wrappingKey.length} updated=${result.bundle.updatedAt}`;
		} catch (error) {
			status = `unlock failed: ${String(error)}`;
		}
	}

	function onGenerateSecret() {
		secretKey = generateSecretKey();
	}

	function onDownloadEmergencyKit() {
		if (!lastSalt || lastIterations <= 0) {
			status = 'emergency kit unavailable: enroll or unlock first';
			return;
		}
		const content = buildEmergencyKitText({
			userId,
			orgId,
			deviceId,
			secretKey,
			saltBase64Url: lastSalt,
			iterations: lastIterations,
		});
		downloadEmergencyKit(`etzhayyim-emergency-kit-${userId}-${deviceId}.txt`, content);
		status = 'emergency kit downloaded';
	}
</script>

<section class="grid gap-3 px-3 pb-[calc(18px+env(safe-area-inset-bottom))] pt-[calc(12px+env(safe-area-inset-top))] xl:mx-auto xl:max-w-[1280px]">
	<header class="rounded-xl border border-[color-mix(in_srgb,#70d6ff_26%,#1f2937_74%)] bg-[linear-gradient(140deg,rgba(9,16,28,0.92),rgba(20,31,51,0.82)),radial-gradient(circle_at_0%_0%,rgba(117,167,255,0.2),transparent_48%)] p-3.5 backdrop-blur-[30px]">
		<p class="m-0 text-[13px] uppercase tracking-[0.08em]">Identity & Key Vault</p>
		<h1 class="my-2 text-[34px] leading-[1.06]">IAM Security Center</h1>
		<p class="text-[17px] leading-[1.5]">Bind encrypted key bundles to Clerk identity and device context.</p>
	</header>

	<div class="grid gap-3 lg:grid-cols-2">
		<section class="rounded-xl border border-[color-mix(in_srgb,#70d6ff_26%,#1f2937_74%)] bg-[linear-gradient(140deg,rgba(9,16,28,0.92),rgba(20,31,51,0.82)),radial-gradient(circle_at_0%_0%,rgba(117,167,255,0.2),transparent_48%)] p-3.5 backdrop-blur-[20px]">
			<h2 class="mb-2 text-[28px]">Enrollment</h2>
			<label class="mt-2.5 grid gap-2 text-[17px]">Account Password <input class="min-h-11 rounded-xl border border-[#375376] bg-[#0b1220] px-3 py-2.5 text-inherit text-[#e8f2ff] [touch-action:manipulation]" type="password" bind:value={accountPassword} /></label>
			<label class="mt-2.5 grid gap-2 text-[17px]">Secret Key
				<div class="flex gap-2">
					<input class="min-h-11 flex-1 rounded-xl border border-[#375376] bg-[#0b1220] px-3 py-2.5 text-inherit text-[#e8f2ff] [touch-action:manipulation]" bind:value={secretKey} />
					<button class="min-h-11 rounded-xl border border-[#375376] bg-[#121d30] px-3 py-2.5 font-bold text-[#d7e6ff] [touch-action:manipulation]" onclick={onGenerateSecret}>Generate</button>
				</div>
			</label>
			<label class="mt-2.5 grid gap-2 text-[17px]">Envelope JSON <textarea class="min-h-[170px] resize-y rounded-xl border border-[#375376] bg-[#0b1220] px-3 py-2.5 text-inherit text-[#e8f2ff] [touch-action:manipulation]" bind:value={envelopeJson}></textarea></label>
			<button class="mt-2 min-h-11 rounded-xl bg-[linear-gradient(90deg,#70d6ff,#8ec5ff)] px-3 py-2.5 font-bold text-[#04111d] [touch-action:manipulation]" onclick={onEnroll}>Save Key Bundle</button>
		</section>

		<section class="rounded-xl border border-[color-mix(in_srgb,#70d6ff_26%,#1f2937_74%)] bg-[linear-gradient(140deg,rgba(9,16,28,0.92),rgba(20,31,51,0.82)),radial-gradient(circle_at_0%_0%,rgba(117,167,255,0.2),transparent_48%)] p-3.5 backdrop-blur-[20px]">
			<h2 class="mb-2 text-[28px]">Unlock</h2>
			<label class="mt-2.5 grid gap-2 text-[17px]">Account Password <input class="min-h-11 rounded-xl border border-[#375376] bg-[#0b1220] px-3 py-2.5 text-inherit text-[#e8f2ff] [touch-action:manipulation]" type="password" bind:value={unlockPassword} /></label>
			<label class="mt-2.5 grid gap-2 text-[17px]">Secret Key <input class="min-h-11 rounded-xl border border-[#375376] bg-[#0b1220] px-3 py-2.5 text-inherit text-[#e8f2ff] [touch-action:manipulation]" bind:value={unlockSecretKey} /></label>
			<button class="mt-2 min-h-11 rounded-xl bg-[linear-gradient(90deg,#70d6ff,#8ec5ff)] px-3 py-2.5 font-bold text-[#04111d] [touch-action:manipulation]" onclick={onUnlock}>Fetch + Unlock</button>
			<button class="mt-2 min-h-11 rounded-xl border border-[#375376] bg-[#121d30] px-3 py-2.5 font-bold text-[#d7e6ff] [touch-action:manipulation]" onclick={onDownloadEmergencyKit}>Download Emergency Kit</button>
			<p class="mt-2 text-[13px] opacity-85">salt: {lastSalt || '-'}</p>
			<p class="mt-2 text-[13px] opacity-85">iterations: {lastIterations || '-'}</p>
		</section>
	</div>

	<section class="rounded-xl border border-[color-mix(in_srgb,#70d6ff_26%,#1f2937_74%)] bg-[linear-gradient(140deg,rgba(9,16,28,0.92),rgba(20,31,51,0.82)),radial-gradient(circle_at_0%_0%,rgba(117,167,255,0.2),transparent_48%)] p-3.5 backdrop-blur-[20px]">
		<h2 class="mb-2 text-[28px]">Status</h2>
		<pre class="m-0 whitespace-pre-wrap text-[13px]">{status}</pre>
	</section>
</section>
