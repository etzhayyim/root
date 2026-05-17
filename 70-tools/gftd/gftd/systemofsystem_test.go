package main

import (
	"testing"
)

func TestSoSBuildReport_RepoWideInventoryAndInterfaces(t *testing.T) {
	root := t.TempDir()

	writeTestFile(t, root+"/package.json", `{
  "name": "repo",
  "packageManager": "pnpm@10.18.2",
  "devDependencies": {
    "nx": "^21.0.0",
    "@playwright/test": "^1.58.2",
    "wrangler": "4.68.1"
  }
}`)
	writeTestFile(t, root+"/pnpm-workspace.yaml", "packages:\n  - packages/*\n")
	writeTestFile(t, root+"/pnpm-lock.yaml", "lockfileVersion: '9.0'\n")
	writeTestFile(t, root+"/go.mod", "module example.com/repo\n\ngo 1.23.0\n")
	writeTestFile(t, root+"/.github/workflows/ci.yml", "name: ci\n")
	writeTestFile(t, root+"/docs/_registry/docs.json", "{}\n")
	writeTestFile(t, root+"/reports/summary.md", "# summary\n")
	writeTestFile(t, root+"/infra/pulumi/index.ts", "export {};\n")
	writeTestFile(t, root+"/infra/cloudflare/workers/demo/package.json", `{"name":"worker-demo"}`)
	writeTestFile(t, root+"/infra/cloudflare/container/demo/Dockerfile", "FROM alpine:3.20\n")
	writeTestFile(t, root+"/20-actors/magatama/package.json", `{"name":"@gftd/magatama-host-sdk"}`)
	writeTestFile(t, root+"/40-engine/kami-engine/pkg/package.json", `{"name":"@gftd/kami-engine"}`)
	writeTestFile(t, root+"/40-engine/svelte/ui/package.json", `{"name":"@gftd/ui"}`)
	writeTestFile(t, root+"/70-tools/gftd/package.json", `{"name":"gftd"}`)

	writeTestFile(t, root+"/projects/ai-gftd-project-demo/wasm/demo-app/magatama.jsonld", `{
  "@id": "did:web:demo.etzhayyim.com",
  "name": "demo",
  "nanoid": "demo1234",
  "performerType": "service",
  "runtimeType": "worker",
  "uiType": "appview",
  "triggers": {
    "subscribeRepos": {
      "collections": ["ai.gftd.apps.demo.entry"]
    }
  }
}`)
	writeTestFile(t, root+"/projects/ai-gftd-project-demo/wasm/demo-app/package.json", `{"name":"demo-app"}`)

	writeTestFile(t, root+"/projects/ai-gftd-project-api/wasm/api-app/magatama.jsonld", `{
  "@id": "did:web:api.etzhayyim.com",
  "name": "api",
  "nanoid": "api56789",
  "performerType": "service",
  "runtimeType": "worker",
  "uiType": "yoro",
  "triggers": {
    "subscribeRepos": {
      "collections": ["ai.gftd.apps.api.entry"]
    }
  }
}`)
	writeTestFile(t, root+"/projects/ai-gftd-project-api/wasm/api-app/package.json", `{"name":"api-app"}`)
	writeTestFile(t, root+"/projects/ai-gftd-project-api/wasm/api-app/Dockerfile", "FROM node:22-alpine\n")

	writeTestFile(t, root+"/.deploy-state.json", `{
  "version": 1,
  "apps": {
    "demo1234": {
      "nanoid": "demo1234",
      "last_deployed_at": "2026-03-31T00:00:00Z"
    }
  }
}`)

	report := sosBuildReport(root)

	if report.Stats.TotalApps != 2 {
		t.Fatalf("total apps = %d, want 2", report.Stats.TotalApps)
	}
	if report.Inventory.PackageJSONCount < 8 {
		t.Fatalf("package json count = %d, want at least 8", report.Inventory.PackageJSONCount)
	}
	if report.Inventory.WorkflowCount != 1 {
		t.Fatalf("workflow count = %d, want 1", report.Inventory.WorkflowCount)
	}
	if report.Inventory.DockerfileCount < 2 {
		t.Fatalf("dockerfile count = %d, want at least 2", report.Inventory.DockerfileCount)
	}
	if report.Inventory.RuntimeVersions["packageManager"] != "pnpm@10.18.2" {
		t.Fatalf("package manager = %q", report.Inventory.RuntimeVersions["packageManager"])
	}

	assertHasSystem := func(id string) {
		t.Helper()
		for _, system := range report.Systems {
			if system.ID == id {
				return
			}
		}
		t.Fatalf("system %q not found", id)
	}
	assertHasSystem("workspace")
	assertHasSystem("pnpm")
	assertHasSystem("github_actions")
	assertHasSystem("magatama_runtime")
	assertHasSystem("deploy_state")
	assertHasSystem("cloudflare_workers")
	assertHasSystem("cloudflare_containers")
	assertHasSystem("demo")
	assertHasSystem("api")

	assertHasInterface := func(from, to, protocol string) {
		t.Helper()
		for _, iface := range report.Interfaces {
			if iface.From == from && iface.To == to && iface.Protocol == protocol {
				return
			}
		}
		t.Fatalf("interface %s -> %s (%s) not found", from, to, protocol)
	}
	assertHasInterface("workspace", "pnpm", "package_manager")
	assertHasInterface("demo", "magatama_runtime", "sdk")
	assertHasInterface("demo", "cloudflare_workers", "runtime")
	assertHasInterface("api", "cloudflare_workers", "runtime")
	assertHasInterface("deploy_state", "demo", "state")

	foundAppLayer := false
	for _, layer := range report.Layers {
		if layer.Name != "app" {
			continue
		}
		foundAppLayer = true
		if len(layer.Systems) == 0 {
			t.Fatal("app layer should not be empty")
		}
	}
	if !foundAppLayer {
		t.Fatal("app layer not found")
	}
}
