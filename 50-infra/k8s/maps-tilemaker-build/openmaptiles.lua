-- Placeholder OpenMapTiles / shortbread Lua processor.
--
-- Build step either:
--   (a) replaces this file with a pinned copy from
--       https://github.com/systemed/tilemaker/blob/master/resources/process-openmaptiles.lua
--   (b) sets CONFIG_FETCH_AT_RUNTIME=1 so run-tilemaker.sh curls the upstream
--       master version before invoking tilemaker.
--
-- Do NOT hand-roll OMT schema here — use the authoritative upstream. This stub
-- exists only so the Docker layer has a file at /config/openmaptiles.lua even
-- before the fetch step runs (Dockerfile COPY is mandatory).

function node_function() end
function way_function() end
function relation_function() end
function relation_scan_function() end
