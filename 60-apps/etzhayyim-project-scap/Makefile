# SCAP Etzhayyim.AI Makefile
# Development and deployment automation

.PHONY: help dev build test deploy clean docker k8s

# Default target
help: ## Show this help message
	@echo "SCAP Etzhayyim.AI - Makefile Commands"
	@echo ""
	@echo "📋 Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

## Development Commands

dev: ## Start development server with file watching
	@echo "🚀 Starting development server..."
	pnpm dev

install: ## Install dependencies using pnpm
	@echo "📦 Installing dependencies..."
	pnpm install

build: ## Build Next.js application for production
	@echo "🔨 Building application..."
	pnpm build

lint: ## Run ESLint and fix auto-fixable issues
	@echo "🔍 Running linter..."
	pnpm lint

typecheck: ## Run TypeScript type checking
	@echo "📝 Running TypeScript checks..."
	pnpm tsc --noEmit

test: ## Run all tests
	@echo "🧪 Running tests..."
	pnpm test

clean: ## Clean build artifacts and node_modules
	@echo "🧹 Cleaning up..."
	rm -rf .next
	rm -rf node_modules
	rm -rf dist
	rm -rf logs

## Worker Commands

worker-integrated: ## Start integrated SCAP worker locally
	@echo "🔄 Starting integrated SCAP worker..."
	npx tsx workers/integrated-scap-worker.ts

worker-nvd: ## Start NVD worker locally
	@echo "🔍 Starting NVD worker..."
	npx tsx workers/data-sources/nvd-worker.ts

worker-oval: ## Start OVAL worker locally
	@echo "🛡️ Starting OVAL worker..."
	npx tsx workers/data-sources/mitre-oval-worker.ts

worker-openscap: ## Start OpenSCAP worker locally
	@echo "📋 Starting OpenSCAP worker..."
	npx tsx workers/data-sources/openscap-worker.ts

worker-stig: ## Start DISA STIG worker locally
	@echo "🏛️ Starting DISA STIG worker..."
	npx tsx workers/data-sources/disa-stig-worker.ts


BUILDKIT_BUILDER ?= etzhayyim-vke
BUILDKIT_PLATFORM ?= linux/amd64
BUILDKIT_CACHE_REF ?= ghcr.io/etzhayyim/build-cache:scap
BUILDX_REMOTE_BUILD = docker buildx build --builder $(BUILDKIT_BUILDER) --platform $(BUILDKIT_PLATFORM) --cache-from type=registry,ref=$(BUILDKIT_CACHE_REF) --cache-to type=registry,ref=$(BUILDKIT_CACHE_REF),mode=max --output=type=cacheonly

## Docker Commands

docker-build: ## Build all Docker images
	@echo "🐳 Building Docker images..."
	$(BUILDX_REMOTE_BUILD) -t scap-etzhayyim/web:latest -f Dockerfile.prod .
	$(BUILDX_REMOTE_BUILD) -t scap-etzhayyim/worker:latest -f Dockerfile.worker .

docker-dev: ## Start development environment with Docker Compose
	@echo "🐳 Starting Docker development environment..."
	docker-compose up -d

docker-prod: ## Start production environment with Docker Compose
	@echo "🐳 Starting Docker production environment..."
	docker-compose -f docker-compose.prod.yml up -d

docker-logs: ## Show Docker Compose logs
	@echo "📋 Showing Docker logs..."
	docker-compose -f docker-compose.prod.yml logs -f

docker-stop: ## Stop Docker Compose services
	@echo "🛑 Stopping Docker services..."
	docker-compose -f docker-compose.prod.yml down

docker-clean: ## Clean Docker images and containers
	@echo "🧹 Cleaning Docker artifacts..."
	docker-compose -f docker-compose.prod.yml down -v
	docker system prune -f

## Kubernetes Commands

k8s-namespace: ## Create Kubernetes namespace
	@echo "🎯 Creating Kubernetes namespace..."
	kubectl create namespace scap-etzhayyim --dry-run=client -o yaml | kubectl apply -f -

k8s-secrets: ## Apply Kubernetes secrets (requires manual editing)
	@echo "🔐 Applying Kubernetes secrets..."
	@echo "⚠️  Make sure to edit deploy/kubernetes/secrets.yaml with real values first!"
	kubectl apply -f deploy/kubernetes/secrets-template.yaml

k8s-deploy: ## Deploy to Kubernetes
	@echo "🚀 Deploying to Kubernetes..."
	kubectl apply -f deploy/kubernetes/scap-worker-deployment.yaml

k8s-status: ## Check Kubernetes deployment status
	@echo "📊 Checking Kubernetes status..."
	kubectl get all -n scap-etzhayyim
	kubectl get secrets -n scap-etzhayyim
	kubectl get configmaps -n scap-etzhayyim

k8s-logs: ## Show Kubernetes pod logs
	@echo "📋 Showing Kubernetes logs..."

k8s-delete: ## Delete Kubernetes deployment
	@echo "🗑️ Deleting Kubernetes deployment..."
	kubectl delete namespace scap-etzhayyim

## Environment Setup Commands

env-check: ## Check environment variables and dependencies
	@echo "🔍 Checking environment..."
	@echo "Node.js version: $$(node --version)"
	@echo "pnpm version: $$(pnpm --version)"
	@echo "Docker version: $$(docker --version)"
	@echo "kubectl version: $$(kubectl version --client --short 2>/dev/null || echo 'kubectl not found')"
	@echo ""
	@echo "Environment variables:"
	@echo "  DATABASE_URL: $${DATABASE_URL:-❌ Not set}"
	@echo "  SUPABASE_URL: $${SUPABASE_URL:-❌ Not set}"
	@echo "  SUPABASE_ANON_KEY: $${SUPABASE_ANON_KEY:-❌ Not set}"
	@echo "  SUPABASE_SERVICE_ROLE_KEY: $${SUPABASE_SERVICE_ROLE_KEY:-⚠️ Optional (server-side only)}"
	@echo "  NVD_API_KEY: $${NVD_API_KEY:-⚠️ Optional (public rate limits)}"

env-template: ## Create environment template file
	@echo "📝 Creating environment template..."
	@printf '%s\n' \
		'# Supabase Database Configuration' \
		'DATABASE_URL=postgresql://postgres:[password]@[host]:[port]/[database]' \
		'' \
		'# Supabase API Configuration' \
		'SUPABASE_URL=https://[project-id].supabase.co' \
		'SUPABASE_ANON_KEY=your-anon-key' \
		'SUPABASE_SERVICE_ROLE_KEY=your-service-role-key' \
		'' \
		'# NVD API Configuration (Optional - for higher rate limits)' \
		'NVD_API_KEY=your-nvd-api-key' \
		'' \
		'# Application Configuration' \
		'NODE_ENV=development' \
		'WORKER_STATUS_REFRESH_INTERVAL=30000' \
		'MOCK_MODE=false' \
		> .env.example
	@echo "✅ Created .env.example - copy to .env and edit with your values"

## License Compliance Commands

license-check: ## Check license compliance for all data sources
	@echo "📋 License Compliance Check:"
	@echo ""
	@echo "✅ Commercial Use Approved:"
	@echo "   - NIST NVD (Public Domain)"
	@echo "   - MITRE OVAL (Commercial Permitted)"
	@echo "   - OpenSCAP Security Guide (BSD-3-Clause)"
	@echo "   - DISA STIG (Public Domain)"
	@echo ""
	@echo "❌ Restricted for Commercial Use:"
	@echo "   - CIS Benchmarks (Requires SecureSuite membership)"
	@echo ""
	@echo "📝 Required Notices:"
	@echo "   - NVD: 'This product uses the NVD API but is not endorsed or certified by the NVD.'"
	@echo "   - OpenSCAP: BSD-3-Clause license and copyright notice required"
	@echo "   - DISA: Subject to U.S. Government Notice and Consent"

license-notices: ## Generate license notice file
	@echo "📄 Generating NOTICES.txt..."
	@printf '%s\n' \
		'SCAP Etzhayyim.AI - Third Party Notices' \
		'' \
		'This software includes content from the following sources:' \
		'' \
		'1. NIST National Vulnerability Database (NVD)' \
		'   License: Public Domain (17 U.S.C. § 105)' \
		'   Notice: This product uses the NVD API but is not endorsed or certified by the NVD.' \
		'' \
		'2. MITRE OVAL Definitions' \
		'   License: OVAL Terms of Use' \
		'   Copyright: MITRE Corporation' \
		'' \
		'3. OpenSCAP Security Guide' \
		'   License: BSD-3-Clause License' \
		'   Copyright: ComplianceAsCode/content contributors' \
		'' \
		'4. DISA Security Technical Implementation Guides (STIGs)' \
		'   License: Public Domain (17 U.S.C. § 105)' \
		'   Notice: Subject to U.S. Government Notice and Consent system usage terms' \
		'' \
		'For complete license terms, see the individual source repositories.' \
		> NOTICES.txt
	@echo "✅ Created NOTICES.txt"

## Monitoring Commands

health-check: ## Check application health
	@echo "🏥 Checking application health..."
	@curl -f http://localhost:3000/api/health || echo "❌ Health check failed"

metrics: ## Show worker metrics (if running)
	@echo "📊 Worker metrics:"
	@curl -s http://localhost:3000/api/scap/worker-status | jq '.' || echo "❌ Metrics unavailable"

## Release Commands

release-check: ## Pre-release checks
	@echo "🔍 Running pre-release checks..."
	$(MAKE) typecheck
	$(MAKE) lint
	$(MAKE) license-check
	$(MAKE) build
	@echo "✅ Pre-release checks passed"

release-docker: ## Build and tag Docker images for release
	@echo "🏷️ Building release Docker images..."
	$(BUILDX_REMOTE_BUILD) -t scap-etzhayyim/web:$$(date +%Y%m%d) -t scap-etzhayyim/web:latest -f Dockerfile.prod .
	$(BUILDX_REMOTE_BUILD) -t scap-etzhayyim/worker:$$(date +%Y%m%d) -t scap-etzhayyim/worker:latest -f Dockerfile.worker .
	@echo "✅ Release images built with tag: $$(date +%Y%m%d)"

## Security Commands

security-scan: ## Run security vulnerability scan
	@echo "🔒 Running security scan..."
	pnpm audit --audit-level moderate

security-update: ## Update dependencies for security
	@echo "🔄 Updating dependencies..."
	pnpm update

## Utility Commands

logs: ## Show application logs
	@echo "📋 Application logs:"
	@tail -f logs/*.log 2>/dev/null || echo "No log files found"

backup-config: ## Backup configuration files
	@echo "💾 Backing up configuration..."
	@mkdir -p backup
	@tar czf backup/config-$$(date +%Y%m%d-%H%M%S).tar.gz .env* deploy/ *.yml *.yaml

restore-config: ## List available configuration backups
	@echo "📁 Available configuration backups:"
	@ls -la backup/config-*.tar.gz 2>/dev/null || echo "No backups found"

## All-in-one Commands

setup: ## Complete setup for new environment
	@echo "🏗️ Setting up SCAP Etzhayyim.AI..."
	$(MAKE) install
	$(MAKE) env-template
	$(MAKE) license-notices
	@echo ""
	@echo "✅ Setup complete! Next steps:"
	@echo "1. Copy .env.example to .env and configure with your credentials"
	@echo "2. Run 'make env-check' to verify configuration"
	@echo "3. Run 'make dev' for development or 'make docker-prod' for production"

deploy-full: ## Full production deployment
	@echo "🚀 Full production deployment..."
	$(MAKE) release-check
	$(MAKE) docker-build
	$(MAKE) docker-prod
	@echo "✅ Production deployment complete!"

deploy-k8s: ## Full Kubernetes deployment
	@echo "⚡ Kubernetes deployment..."
	$(MAKE) release-check
	$(MAKE) docker-build
	$(MAKE) k8s-namespace
	@echo "⚠️  Please edit deploy/kubernetes/secrets.yaml with your credentials"
	@echo "⚠️  Then run: make k8s-secrets && make k8s-deploy"
