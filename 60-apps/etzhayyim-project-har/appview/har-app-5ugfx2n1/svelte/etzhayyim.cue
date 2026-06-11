package etzhayyim

project: #Project & {
	nanoid: "har-001"
	name:   "etzhayyim-har-\(nanoid)"
	type:   "app"
	app: {
		domain:     "har.etzhayyim.com"
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
		namespace: "etzhayyim-har-prod"
	}
}
