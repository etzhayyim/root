-- kagami-bench ClickHouse init: load Parquet into MergeTree table.
CREATE DATABASE IF NOT EXISTS kagami;

CREATE TABLE IF NOT EXISTS kagami.p9v20 (
    record_type   String DEFAULT '',
    vertex_id     String DEFAULT '',
    edge_id       String DEFAULT '',
    label         String DEFAULT '',
    timestamp_ms  String DEFAULT '',
    rkey          String DEFAULT '',
    repo          String DEFAULT '',
    did           String DEFAULT '',
    collection    String DEFAULT '',
    status        String DEFAULT '',
    _alive        String DEFAULT '',
    _seq          String DEFAULT '',
    src_vid       String DEFAULT '',
    dst_vid       String DEFAULT '',
    src_label     String DEFAULT '',
    dst_label     String DEFAULT '',
    val           String DEFAULT '',
    weight        String DEFAULT '',
    embedding     String DEFAULT '',
    embedding_norm String DEFAULT '',
    embedding_q8  String DEFAULT '',
    quantization_scale String DEFAULT '',
    ivf_cluster_id String DEFAULT ''
) ENGINE = MergeTree()
ORDER BY (label, _seq)
SETTINGS index_granularity = 8192;

-- Load data from mounted Parquet (if exists)
INSERT INTO kagami.p9v20
SELECT * FROM file('p9v20.parquet', Parquet);
