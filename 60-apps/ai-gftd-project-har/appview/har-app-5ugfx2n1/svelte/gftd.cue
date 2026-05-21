package gftd

project: #Project & {
	nanoid: "har-001"
	name:   "ai-gftd-har-\(nanoid)"
	type:   "app"
	app: {
		domain:     "har.gftd.ai"
		framework:  "svelte"
		output_dir: "build"
	}
	build: {
		steps: [
			{ name: "Install", cmd: "pnpm install" },
			{ name: "Generate Proto", cmd: "buf generate" },
			{ name: "Build", cmd: "pnpm run build" }
		]
	}
	deploy: {
		type:      "static"
		namespace: "ai-gftd-har-prod"
	}
}
