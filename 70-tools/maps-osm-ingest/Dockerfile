# syntax=docker/dockerfile:1.6
FROM rust:1.88-slim AS build
WORKDIR /src
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      pkg-config libssl-dev ca-certificates build-essential cmake \
 && rm -rf /var/lib/apt/lists/*
COPY Cargo.toml ./
COPY src ./src
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=cache,target=/src/target \
    cargo build --release --bin maps-osm-ingest \
 && cp /src/target/release/maps-osm-ingest /usr/local/bin/maps-osm-ingest

FROM debian:bookworm-slim AS runtime
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*
COPY --from=build /usr/local/bin/maps-osm-ingest /usr/local/bin/maps-osm-ingest
ENV RUST_LOG=info
ENTRYPOINT ["/usr/local/bin/maps-osm-ingest"]
