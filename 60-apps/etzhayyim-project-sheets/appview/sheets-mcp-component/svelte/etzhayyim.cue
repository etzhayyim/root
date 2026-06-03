package etzhayyim

project: #Project & {
	nanoid: "7ratoixl"
	name:   "sheets-app-\(nanoid)"
	type:   "app"
	app: {
		domain:     "sheets.apps.etzhayyim.com"
		framework:  "svelte"
		output_dir: "build"
	}
	build: {
		steps: [
			{ name: "Install", cmd: "pnpm install" },
			{ name: "Build", cmd: "pnpm run build" }
		]
	}
	deploy: {
		type:      "static"
		namespace: "default"
	}
}
