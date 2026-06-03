# ETZHAYYIM TIA Workspace Makefile
# Merkle DAG: workspace_makefile_v1

.PHONY: help schema graphql-schema types build test clean

help:
	@echo "Available targets:"
	@echo "  schema          - Generate GraphQL schema from Rust (SDL)"
	@echo "  graphql-schema  - Alias for schema"
	@echo "  types           - Generate TypeScript types from GraphQL schema"
	@echo "  build           - Build all projects"
	@echo "  test            - Run all tests"
	@echo "  clean           - Clean build artifacts"

schema graphql-schema:
	@echo "Generating GraphQL schema from Rust..."
	cd performers/services/graphql && cargo run --bin generate-schema
	@echo "✓ Schema generated at performers/ports/graphql/schema.graphql"

types:
	@echo "Generating TypeScript types from GraphQL schema..."
	@echo "Note: Run 'make schema' first to ensure schema.graphql exists"
	cd performers/actors/internetaccountowner && pnpm generate:types
	cd performers/actors/admin && pnpm generate:types
	cd performers/actors/seeker && pnpm generate:types

generate: schema types
	@echo "✓ Schema and types generated"

build:
	@echo "Building GraphQL service..."
	cd performers/services/graphql && cargo build --release
	@echo "Building TypeScript actors..."
	cd performers/actors/internetaccountowner && pnpm build
	cd performers/actors/admin && pnpm build
	cd performers/actors/seeker && pnpm build

test:
	@echo "Running Rust tests..."
	cd performers/services/graphql && cargo test
	@echo "Running TypeScript tests..."
	cd performers/actors/internetaccountowner && pnpm test
	cd performers/actors/admin && pnpm test
	cd performers/actors/seeker && pnpm test

clean:
	@echo "Cleaning Rust build artifacts..."
	cd performers/services/graphql && cargo clean
	@echo "Cleaning TypeScript build artifacts..."
	cd performers/actors/internetaccountowner && rm -rf .next dist
	cd performers/actors/admin && rm -rf .next dist
	cd performers/actors/seeker && rm -rf .next dist
