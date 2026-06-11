# murakumo-kubelet build + push targets.
# Apache 2.0.

IMAGE ?= ghcr.io/etzhayyim/murakumo-kubelet
TAG   ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo dev)

.PHONY: tidy build image push lint test help

help:
	@echo "tidy   — go mod tidy"
	@echo "build  — local linux/amd64 binary"
	@echo "image  — docker build $(IMAGE):$(TAG)"
	@echo "push   — docker push $(IMAGE):$(TAG)"
	@echo "lint   — go vet"
	@echo "test   — go test ./..."

tidy:
	go mod tidy

build:
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -trimpath -ldflags='-s -w' \
		-o bin/murakumo-kubelet ./cmd/murakumo-kubelet

image:
	docker buildx build --builder etzhayyim-vke --platform linux/amd64 \
		-t $(IMAGE):$(TAG) -t $(IMAGE):latest \
		--push .

push: image  # alias

lint:
	go vet ./...

test:
	go test ./...
