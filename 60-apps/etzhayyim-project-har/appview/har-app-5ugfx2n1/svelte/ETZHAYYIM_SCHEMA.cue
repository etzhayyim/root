package etzhayyim

#Project: {
	nanoid: string
	name:   string
	type:   "app" | "service" | "actor"
	app?: {
		domain:     string
		framework:  string
		output_dir: string
	}
	build: {
		steps: [...#BuildStep]
	}
	deploy: {
		type:      string
		namespace: string
	}
}

#BuildStep: {
	name: string
	cmd:  string
}
