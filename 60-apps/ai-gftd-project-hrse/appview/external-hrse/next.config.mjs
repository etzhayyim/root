/** @type {import('next').NextConfig} */

// ビルド時に必要な環境変数をチェック（Docker ビルド時はスキップ）
const skipEnvCheck = process.env.SKIP_ENV_CHECK === 'true';
const requiredEnvVars = [
	"NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY",
];

if (!skipEnvCheck) {
	const missingEnvVars = requiredEnvVars.filter(
		(name) => !process.env[name] || process.env[name]?.trim() === "",
	);

	if (missingEnvVars.length > 0 && process.env.NODE_ENV !== "development") {
		console.error("\n❌ Build failed: Missing required environment variables:");
		missingEnvVars.forEach((name) => {
			console.error(`   - ${name}`);
		});
		console.error(
			"\n💡 Please set the required environment variables before building.",
		);
		console.error(
			"   For Vercel: Use 'vercel env add <VAR_NAME> production'",
		);
		console.error(
			"   For local: Create .env.local file with required variables",
		);
		process.exit(1);
	}
}

const nextConfig = {
	// Docker ビルド時は TypeScript エラーを無視
	typescript: {
		ignoreBuildErrors: skipEnvCheck,
	},
	// Docker ビルド時は ESLint エラーを無視
	eslint: {
		ignoreDuringBuilds: skipEnvCheck,
	},
	// Docker環境でのHMRを有効化
	webpack: (config, { dev, isServer }) => {
		if (dev && !isServer) {
			// クライアントサイドのHMR設定
			config.watchOptions = {
				poll: 1000, // 1秒ごとにポーリング
				aggregateTimeout: 300, // 変更を集約するタイムアウト
				ignored: ["**/node_modules", "**/.git", "**/.next"],
			};
		}
		return config;
	},
};

export default nextConfig;
