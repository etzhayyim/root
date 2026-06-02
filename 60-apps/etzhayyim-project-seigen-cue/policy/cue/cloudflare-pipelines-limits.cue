package seigen

#CloudflarePipelinesPolicy: {
  metadata: {
    provider: "cloudflare"
    product:  "pipelines"
    version:  string
    sourceDate: =~"^\\d{4}-\\d{2}-\\d{2}$"
  }

  limits: {
    maxStreams:        <=20
    maxSinks:          <=20
    maxPipelines:      <=20
    maxPayloadBytes:   <=5_000_000
    maxIngestRateBps:  <=5_000_000
  }

  constraints: {
    pipelineSqlImmutable: true
    sinkImmutable:        true
    structuredSchemaImmutable: true
    r2DataCatalogCrossJurisdictionUnsupported: true
    schemaMismatchDropsStructuredEvents: true
    // Sink roll interval must be 10s (CF minimum for R2 Data Catalog).
    // Default 300s is prohibitively slow for read-your-write latency.
    sinkRollIntervalSeconds: 10
  }

  // Sink creation policy: all sinks must use roll-interval 10s.
  sinkDefaults: {
    rollIntervalSeconds: 10
    format: "parquet"
    compression: "zstd"
  }
}

#CloudflarePipelinesInput: {
  provider: "cloudflare"
  product:  "pipelines"

  usage: {
    streams:       int & >=0
    sinks:         int & >=0
    pipelines:     int & >=0
    payloadBytes:  int & >=0
    ingestRateBps: int & >=0
  }

  pipeline: {
    sqlMutable: bool
  }

  sinks: [...{
    name: string
    type: string
    mutable: bool
    crossJurisdictionWrite?: bool
    rollIntervalSeconds: 10  // enforced: must be 10s
  }]

  streams: [...{
    name: string
    mode: "structured" | "unstructured"
    schemaMutable?: bool
    expectNoDropOnSchemaMismatch?: bool
  }]
}
