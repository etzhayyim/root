CREATE INDEX IF NOT EXISTS idx_vertex_spatial_label_latlng
      ON vertex_spatial (label, lat, lng);

CREATE INDEX IF NOT EXISTS idx_vertex_spatial_latlng
      ON vertex_spatial (lat, lng);
