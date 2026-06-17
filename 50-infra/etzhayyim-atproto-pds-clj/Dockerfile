# Independent etzhayyim atproto PDS — babashka runtime.
# No Node/Bun, no gftd code. Serves did:web:atproto.etzhayyim.com over the
# kotoba Datom-log store.
FROM babashka/babashka:1.12.196

WORKDIR /app
COPY bb.edn .
COPY src ./src
COPY did.json .

# Warm the classpath / fail fast on a compile error at build time.
RUN bb -e "(require 'etzhayyim.pds.server)" && echo "compile ok"

ENV PORT=8787 \
    PDS_HOST=atproto.etzhayyim.com \
    PDS_USER_DOMAINS=etzhayyim.com \
    APPVIEW_URL=https://bsky.etzhayyim.com \
    CHAT_URL=https://chat.etzhayyim.com

EXPOSE 8787
CMD ["bb", "serve"]
