# etzhayyim Public Resources

Public JSON-LD entity resources for etzhayyim projects. Content under `content/` is stored as normalized JSON-LD entity files.

## Structure

```
content/
├── ti/                    # Threat Intelligence entities
│   ├── indicator/         # IoC indicators (domain, ip, url, hash)
│   ├── host/              # Host fingerprints
│   └── locale/            # Geolocation context
├── resource/              # Global resource entities
└── system/                # System model entities
```

## Schema Validation

SHACL shapes under `shacl/` define data quality gates for JSON-LD entities.

## License

Apache License 2.0 — see [LICENSE](LICENSE).
