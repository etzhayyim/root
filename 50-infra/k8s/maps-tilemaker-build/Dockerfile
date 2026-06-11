# syntax=docker/dockerfile:1.6
#
# maps-tilemaker-build
# --------------------
# Builds OSM PBF → OpenMapTiles-schema PMTiles via tilemaker, then uploads the
# resulting .pmtiles blob + manifest.json to Cloudflare R2.
#
# Base image: systemed/tilemaker (upstream, statically-linked tilemaker v2.x)
# Upload:     rclone (R2 is S3-compatible; rclone has first-class S3 support
#             and handles multipart + resume for 100 GB+ planet outputs).
#
# Entry:      /usr/local/bin/run-tilemaker.sh
#
# Typical job (Japan extract):  CPU 8 / RAM 16 Gi / scratch 80 Gi / ~1 h
# Typical job (planet):         CPU 16 / RAM 96 Gi / scratch 300 Gi / ~12 h
#
FROM systemed/tilemaker:v2.4.0

# tilemaker base is Debian bookworm-slim; add rclone + curl + jq for upload + manifest.
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      jq \
      rclone \
      tini \
 && rm -rf /var/lib/apt/lists/*

# Vendored OpenMapTiles shortbread-compat config from upstream tilemaker resources.
# Source: https://github.com/systemed/tilemaker/tree/master/resources
# Pinned commit ref should match the tilemaker image tag above.
# If CONFIG_FETCH_AT_RUNTIME=1, run-tilemaker.sh will curl the latest config
# instead of using the vendored copies — useful for style iteration.
COPY openmaptiles.json /config/openmaptiles.json
COPY openmaptiles.lua  /config/openmaptiles.lua

COPY run-tilemaker.sh /usr/local/bin/run-tilemaker.sh
RUN chmod +x /usr/local/bin/run-tilemaker.sh

# Scratch is a Kubernetes emptyDir volume mounted at /scratch.
WORKDIR /scratch

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/run-tilemaker.sh"]
