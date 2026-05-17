# Stage 1: install cargo-chef
FROM rust:1-bookworm AS chef
RUN cargo install cargo-chef --locked
RUN apt-get update && apt-get install -y --no-install-recommends \
    libprotobuf-dev \
    protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /build

# Stage 2: generate dependency recipe (cached unless Cargo.toml/Cargo.lock change)
FROM chef AS planner
COPY Cargo.toml Cargo.toml
COPY Cargo.lock Cargo.lock
COPY src/ src/
RUN cargo chef prepare --recipe-path recipe.json

# Stage 3: compile dependencies only (cached as long as recipe.json is unchanged)
FROM chef AS cacher
COPY --from=planner /build/recipe.json recipe.json
RUN cargo chef cook --release --locked --recipe-path recipe.json

# Stage 4: compile tonbo itself (only src/ changes trigger this layer)
FROM chef AS builder
COPY Cargo.toml Cargo.toml
COPY Cargo.lock Cargo.lock
COPY src/ src/
COPY --from=cacher /build/target target
COPY --from=cacher /usr/local/cargo /usr/local/cargo
RUN cargo build --release --locked

# Stage 5: minimal runtime image
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates libssl3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/target/release/tonbo /usr/local/bin/tonbo

ENV RUST_LOG=tonbo=info
EXPOSE 8084 50050

ENTRYPOINT ["tonbo"]
