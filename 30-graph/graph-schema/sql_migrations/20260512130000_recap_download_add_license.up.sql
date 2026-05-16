-- Add license column to vertex_recap_download.
-- yt-dlp returns license (e.g. "Creative Commons Attribution licence (reuse allowed)")
-- for YouTube videos with CC license set by the uploader.

ALTER TABLE vertex_recap_download
    ADD COLUMN IF NOT EXISTS license varchar;
