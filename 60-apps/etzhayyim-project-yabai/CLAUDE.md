> **DEPRECATED**: Actor migrated to `20-actors/yabai/actor-manifest.jsonld` (T1 MCP-Compose). This project wasm/*/src/app.ts is retained as T3 fallback only.

# yabai.etzhayyim.com — Risk Intelligence Platform

AML/sanctions/anti-social forces risk scoring + IP access filtering。

## Architecture

| 項目 | 値 |
|---|---|
| **Runtime** | Single Worker (`y8b41k0x`) |
| **UI** | appview (Protocol Canvas card UI) |
| **Data** | SQL graph (yata Workers RPC) — `YabaiEntity`, `YabaiEvidence`, `YabaiRisk`, `YabaiAlert`, `YabaiEnforcement`, `YabaiAuditLog`, `YabaiEvolution*`, `WhoisRecord`, `DnsRecord`, `AsnInfo`, `GeoipEnrichment`, `CveEntry`, `MitreTechnique`, `ExploitObservation`, `TlsCertificate`, `TlsAnomaly`, `MalwareSample`, `IocIndicator`, `PhishingUrl`, `StixBundle`, `BgpEvent`, `AbuseReport`, `HostingProvider`, `IpHostingHistory`, `IpLocationHistory`, `EmailAddress`, `PhishingSite`, `IntelAccessLog`, `IntelSession`, `IntelDevice`, `CfHttpRequestLog`, `CfFirewallEvent`, `CfBotScore` |
| **W Protocol Event Stream** | WRecord kinds: `yabai.entity`, `yabai.evidence`, `yabai.risk`, `yabai.alert`, `yabai.enforcement`, `yabai.ip_risk`, `yabai.whois_record`, `yabai.dns_record`, `yabai.asn_info`, `yabai.geoip_enrichment`, `yabai.cve_entry`, `yabai.mitre_technique`, `yabai.exploit_observation`, `yabai.tls_certificate`, `yabai.tls_anomaly`, `yabai.malware_sample`, `yabai.ioc_indicator`, `yabai.phishing_url`, `yabai.stix_bundle`, `yabai.bgp_event`, `yabai.abuse_report`。Write: `WRecord(kind, payload)`、Read: `G("Label").Match(Eq{...}).Query()` |
| **W Protocol** | 4 channels: `yabai-feed`, `yabai-alerts`, `yabai-audit`, `yabai-evolution` + stream method `stream-alerts` |
| **WIT export** | `etzhayyim:yabai-risk/risk-assessment@1.0.0`, `network-intel@1.0.0`, `vuln-intel@1.0.0`, `threat-intel@1.0.0`, `exchange-intel@1.0.0`, `infra-intel@1.0.0`, `access-audit@1.0.0`, `cf-metrics-ingest@1.0.0` |
| **Agent tools** | `get-risk`, `evaluate-entity`, `explain-score`, `get-entity`, `analyze-entity`, `get-summary`, `list-entities`, `get-entity-graph`, `ingest-ip`, `get-ip-risk`, `report-rate-abuse`, `sync-waf-lists`, `ingest-whois`, `get-whois`, `ingest-dns`, `get-dns`, `ingest-asn`, `get-asn`, `ingest-geoip`, `get-geoip`, `detect-whois-anomalies`, `detect-dns-anomalies`, `ingest-cve`, `get-cve`, `search-cves`, `ingest-mitre-technique`, `get-mitre-technique`, `map-actor-techniques`, `record-exploit-observation`, `list-exploit-observations`, `ingest-tls-certificate`, `get-tls-certificate`, `record-tls-anomaly`, `ingest-malware-sample`, `get-malware-sample`, `ingest-ioc`, `search-iocs`, `ingest-phishing-url`, `list-phishing-urls`, `ingest-stix-bundle`, `get-stix-bundle`, `export-stix-bundle`, `record-bgp-event`, `list-bgp-events`, `submit-abuse-report`, `get-abuse-report`, `list-abuse-reports` |
| **Domain** | `yabai.etzhayyim.com` / `y8b41k0x.etzhayyim.com` |

## Reactive Runtime (Design D 準拠)

- **Input**: `subscribe-repos.handle-repo-commit` (`handleComAtprotoSyncSubscribeReposCommit`) で `com.etzhayyim.apps.yabai.*` + `com.etzhayyim.apps.ipaddress.*` commit を受けて即時処理
- **Follow-based input**: `kotodama.Follow("n7w1p4d0")` で ipaddress.etzhayyim.com を Follow → `ip_address`/`ip_analysis`/`geolocation`/`whois_snapshot` を自動受信
- **Processing**: yabai commit → reactive publish。ipaddress commit → auto IP ingest + risk evaluation
- **Output (stream)**: `serve.handle-stream("stream-alerts")` を subscriber role + trust level で配信
- **Output (social)**: `postRiskAnalysis()` でリスクスコアリング結果を entity の path-based DID (`ip:*`/`person:*`/`org:*`) に `AppBskyFeedPost` で投稿
- **Output (event cards)**: `wPublish(...)` で feed/alerts/audit channel に即時反映
- **方針**: batch polling ではなく event-driven (`handleComAtprotoSyncSubscribeReposCommit`) を主経路にする

## Risk Scoring

- **Entity evidence categories**: SanctionHit (×20), CriminalEvidence (×15), AntiSocialAssociation (×12), AMLPattern (×10), FraudSignal (×8), IntelExtraction (×3)
- **IP evidence categories**: KnownBotnet (×15), BruteForce (×12), TorExitNode (×10), RateAbuse (×8), GeoAnomaly (×5), VPNDatacenter (×3)
- **Recency decay**: ≤30d → 1.0, ≤1y → 0.9, ≤3y → 0.7, >3y → 0.5
- **Neighbor contagion**: 1-hop graph traversal, max 30 points
- **Alert thresholds**: Monitor ≥70, Challenge ≥85, Deny ≥95

## CRITICAL: IP Risk Scoring + CF WAF Integration

→ `etzhayyim dodaf tv1 query --id etzhayyim-project-yabai-ip-risk-scoring-+-cf-waf-integration` / MCP `etzhayyim.dodaf.tv1.query`

## Cyber Threat Intelligence (CTI) Layers

### Network Intel (WHOIS/DNS/ASN/GeoIP)

IP/Domain の帰属・インフラ文脈。スコアリング入力 + anomaly detection。

| Graph Node | 用途 | Key Fields |
|---|---|---|
| `WhoisRecord` | ドメイン/IP 登録者情報 | domain, ip, registrant_name/org/email, registrar, nameservers, created_at, expires_at, privacy_protected |
| `DnsRecord` | A/AAAA/MX/NS/TXT/CNAME + passive DNS | domain, type, value, ttl, first_seen, last_seen |
| `AsnInfo` | ASN 事業者・prefix 情報 | asn, name, country, rir, prefixes |
| `GeoipEnrichment` | IP → 地理/ISP/proxy 判定 | ip, country, city, isp, org, is_proxy, is_mobile, is_datacenter, lat/lng |

**Anomaly detection**: `detect-whois-anomalies` (短命ドメイン, privacy mask), `detect-dns-anomalies` (fast-flux, DGA)

### Vuln Intel (CVE/MITRE/Exploit)

攻撃手法・脆弱性の追跡。ThreatActor → Technique マッピング。

| Graph Node | 用途 | Key Fields |
|---|---|---|
| `CveEntry` | CVE 脆弱性 | cve_id, cvss_score, cvss_vector, cwe_id, affected_products, exploit_available, epss_score |
| `MitreTechnique` | MITRE ATT&CK 手法 | technique_id, name, tactic, platform, detection, data_sources |
| `ExploitObservation` | 野生での exploit 観測 | cve_id, source_ip, target_ip, payload_hash, observed_at, confidence |

**Cross-link**: ExploitObservation の source_ip は自動的に IP entity + evidence として ingest

### Threat Intel (TLS/Malware/IOC/Phishing)

| Graph Node | 用途 | Key Fields |
|---|---|---|
| `TlsCertificate` | TLS 証明書チェーン | sha256_fingerprint, issuer, subject, san, not_before/after, ct_log_timestamp |
| `TlsAnomaly` | TLS 異常 (self_signed/expired/san_mismatch/ct_missing/short_lived) | domain/ip, anomaly_type, ja3_hash, ja3s_hash |
| `MalwareSample` | マルウェア検体 | sha256, md5, family, yara_rules, vt_detection_rate, c2_domains, c2_ips |
| `IocIndicator` | 統一 IOC ストア (ip/domain/url/hash/email) | type, value, tlp, confidence, source, tags, first_seen, last_seen |
| `PhishingUrl` | フィッシング URL | url, brand_target, status, screenshot_cid, detection_method |

**Cross-link**: Malware C2 IPs → auto-ingest as KnownBotnet evidence。Phishing URL → auto-ingest as IOC。

### Exchange Intel (STIX/BGP/Abuse)

| Graph Node | 用途 | Key Fields |
|---|---|---|
| `StixBundle` | STIX 2.1 バンドル (ingest/export) | bundle_id, bundle_json, creator, tlp, share_targets |
| `BgpEvent` | BGP hijack/leak/origin change | prefix, event_type, asn_origin, asn_expected |
| `AbuseReport` | ISP abuse 報告追跡 | ip/domain, abuse_contact, report_template, evidence_ids, status |

### Infra Intel (Hosting/IP History/Email/Phishing Site)

IP/ドメインのホスティング帰属・地理的移動履歴・メール情報・フィッシングサイト深掘り。

| Graph Node | 用途 | Key Fields |
|---|---|---|
| `HostingProvider` | Hosting 会社 entity (DID 対応) | provider_id, name, asn, country, abuse_contact, ip_ranges, provider_type (cloud/vps/dedicated/bulletproof/residential), reputation_score |
| `IpHostingHistory` | IP → Hosting 変更履歴 (時系列) | ip, provider_id, asn, country, city, datacenter, observed_at, previous_provider_id, change_reason |
| `IpLocationHistory` | IP → 地理的位置変更履歴 (時系列) | ip, country, city, isp, org, latitude, longitude, is_proxy, is_datacenter, observed_at, previous_country, previous_city |
| `EmailAddress` | メールアドレス intelligence | email, domain, associated_ips, associated_actors, breach_count, reputation (clean/suspicious/malicious/unknown), source, tags |
| `PhishingSite` | フィッシングサイト (拡張版) | url, domain, ip, hosting_provider_id, brand_target, kit_hash, html_hash, status, ssl_issuer, registration_date, screenshot_cid, registrant_email, nameservers |

**Anomaly detection**: `detect-hosting-anomalies` (bulletproof hosting 検知, rapid hosting migration)
**Phishing correlation**: `correlate-phishing-kits` (同一 kit_hash/html_hash/registrant_email でサイト横断相関)

**Path-Based DIDs** (Hosting Providers + Risk Entities):
```
did:web:yabai.etzhayyim.com:hosting:cloudflare
did:web:yabai.etzhayyim.com:hosting:aws
did:web:yabai.etzhayyim.com:hosting:hetzner
did:web:yabai.etzhayyim.com:ip:192_168_1_1          # IPAddress risk profile
did:web:yabai.etzhayyim.com:person:john_doe          # Person risk profile
did:web:yabai.etzhayyim.com:org:acme_corp            # Organization risk profile
did:web:yabai.etzhayyim.com:entity:ent_abc123        # Generic entity risk profile
```

### Access Audit (Intel Access Log / Session / Device)

Intelligence データへのアクセス履歴・セッション・端末情報。threat graph と自動クロスリンク。

| Graph Node | 用途 | Key Fields |
|---|---|---|
| `IntelAccessLog` | Intel query/view/export 履歴 | log_id, accessor_id, accessor_type (user/agent/system/api_key), accessor_ip, action (query/view/export/download/search/bulk_query), resource_type, resource_id, query_text, result_count, session_id, device_fingerprint, user_agent, accessed_at |
| `IntelSession` | アクセスセッション (accessor × device × IP) | session_id, accessor_id, device_fingerprint, ip, user_agent, os, browser, browser_version, device_type (desktop/mobile/tablet/bot/unknown), screen_resolution, timezone, accept_language, webgl_renderer, canvas_hash |
| `IntelDevice` | 端末フィンガープリント | device_fingerprint, user_agent, os, browser, browser_version, device_type, screen_resolution, webgl_renderer, canvas_hash, last_seen_ip |

**Cross-links to threat graph**:
- `IntelAccessLog.accessor_ip` → `YabaiEntity (IPAddress)` / `IpHostingHistory` / `GeoipEnrichment`
- `IntelAccessLog.resource_id` → `YabaiEntity` / `ThreatActor` / `HostingProvider` / `EmailAddress` etc.
- `IntelSession.ip` → same IP graph
- `IntelDevice.device_fingerprint` → multi-session correlation

**Anomaly detection**: `detect-access-anomalies` (bulk query, export, multi-IP accessor = impossible travel)
**Correlation**: `correlate-ip-activity` (IP → all accessors/sessions/devices/resources/risk), `correlate-accessor-activity` (accessor → all IPs/sessions/devices/resources)

### Graph Relationships (CTI)

```
YabaiEntity -[:REGISTERED_BY]-> WhoisRecord
YabaiEntity -[:HOSTED_ON]-> AsnInfo
YabaiEntity -[:RESOLVES_TO]-> DnsRecord
YabaiEntity -[:HAS_CERT]-> TlsCertificate
YabaiEntity -[:USES_TECHNIQUE]-> MitreTechnique
CveEntry -[:EXPLOITED_BY]-> YabaiEntity
MalwareSample -[:CONTACTS_C2]-> YabaiEntity
PhishingUrl -[:IMPERSONATES]-> YabaiEntity
ExploitObservation -[:EXPLOITS]-> CveEntry
IpHostingHistory -[:HOSTED_BY]-> HostingProvider
IpLocationHistory -[:LOCATED_AT]-> GeoipEnrichment
EmailAddress -[:ASSOCIATED_IP]-> YabaiEntity
EmailAddress -[:USED_BY]-> ThreatActor (malak)
PhishingSite -[:HOSTED_BY]-> HostingProvider
PhishingSite -[:REGISTERED_WITH]-> EmailAddress
PhishingSite -[:USES_KIT]-> PhishingSite (kit_hash correlation)
IntelAccessLog -[:ACCESSED_FROM]-> YabaiEntity (IPAddress)
IntelAccessLog -[:ACCESSED_RESOURCE]-> YabaiEntity|ThreatActor|HostingProvider|EmailAddress
IntelAccessLog -[:IN_SESSION]-> IntelSession
IntelSession -[:USED_DEVICE]-> IntelDevice
IntelSession -[:FROM_IP]-> YabaiEntity (IPAddress)
```

## CRITICAL: CF Traffic Analysis — Logpush (全アクセス) + GraphQL (aggregate)

→ `etzhayyim dodaf tv1 query --id etzhayyim-project-yabai-cf-traffic-analysis-logpush-全アク�` / MCP `etzhayyim.dodaf.tv1.query`

## W Protocol Events

| Event | Channel | Card Type |
|---|---|---|
| `yabai.risk.scored` | `yabai-feed` | `risk-score` |
| `yabai.entity.ingested` | `yabai-feed` | `entity-ingest` |
| `yabai.alert.created` | `yabai-alerts` | `alert` |
| `yabai.removal.reviewed` | `yabai-audit` | `removal-review` |
| `yabai.evolution.started` | `yabai-evolution` | `evolution` |
| `yabai.exploit.observed` | `yabai-alerts` | `exploit-observation` |
| `yabai.phishing.detected` | `yabai-alerts` | `phishing-alert` |
| `yabai.bgp.hijack` | `yabai-alerts` | `bgp-hijack` |

## Key Files

| File | Purpose |
|---|---|
| `wasm/etzhayyim-wasm-yabai-y8b41k0x/src/app.ts` | Single-file business logic |
| `wasm/etzhayyim-wasm-yabai-y8b41k0x/kotodama.jsonld` | Runtime config, space, triggers |
| `wasm/etzhayyim-wasm-yabai-y8b41k0x/wit/world.wit` | WIT capability export |
| `wit/yabai-risk/package.wit` | Domain WIT interfaces (risk-assessment, network-intel, vuln-intel, threat-intel, exchange-intel) |
| `content/` | Entity/evidence/risk JSON-LD archive (461 entities) |

## Phishing Infrastructure Tracking (2026-04-19)

`tools/track-phishing-infra/` — local node scripts for enriching `com.etzhayyim.apps.yabai.entity WHERE entity_type='phishing_url'` with hosting/registrar/TLS intel and linking operators to GLEIF legal-entity DIDs. Not a CF Worker (active TLS probes need raw TCP, and `whois`/`dig` aren't available in Worker runtime).

| Script | Purpose |
|---|---|
| `track-phishing-infra.mjs` | Per-domain probe: DNS (dig) + WHOIS + Team Cymru ASN + crt.sh CT + HTTP HEAD + openssl s_client. INSERT into `vertex_yabai_infra_track`. `--no-active` for passive-only. |
| `expand-coverage.mjs` | Reverse-IP pivot (hackertarget) on known phishing IPs + crt.sh fuzzy keyword search → sibling domain discovery → `/tmp/yabai-coverage-candidates.tsv` for human review, then INSERT into `vertex_yabai_entity`. |
| `enrich-legal-entity.mjs` | GLEIF LEI fuzzy lookup for hosting/registrar operators → `vertex_legal_entity` + `edge_yabai_operated_by`. LEI-identified: Alibaba Cloud US LLC (9845000B4FL02B89BB41) / Hostinger UAB (254900RUFNPSZGPS5402) / GMO Internet (529900BFZEY3BESHBW90). LEI not filed: UCLOUD HK / CTG Server / Dynadot / NameSilo / Gname / Metaregistrar BV. |
| `abuse-drafts/generate-drafts.mjs` | Pull per-ASN + per-registrar domain lists from RW and emit `.eml` drafts for abuse@ submission. **Drafts only** — sending requires explicit override of `etzhayyim_agent` rule `メール=下書きonly`. |

Entity conventions:
- `entity_type='phishing_url'` — apex domain (value = domain)
- `entity_type='asn'` — AS{number} (value = LEI if linked, else descr)
- `entity_type='hosting_provider'` / `'registrar'` — operator (value = LEI if linked)
- `edge_yabai_operated_by` (src=asn/registrar yabai entity, dst=legal-entity vertex_id)
- ASN-level `PhishingInfrastructure` evidence rolls up per-URL evidence (severity 3-4, confidence 0.92-0.98)

Current coverage (as of 2026-04-19): 173 phishing domains tracked across 4 ASNs. 84% concentration on UCLOUD HK (AS135377, 73 domains) + CTG Server HK (AS152194, 51 domains). Primary campaigns: WhatsApp typosquats, LINE me-TLD typosquats, MasterCard/Apple/SMBC help-TLD nanoid campaigns.

Schema: `30-graph/graph-schema/migrations/20260419130000_vertex_yabai_infra_track.ts`.

## Shinka (joucho 情緒 cadence)

joucho 情緒 cadence heartbeat (`resolveHeartbeatCadence`)。mood-driven で投稿/engage/drill/validate を自律決定。follower KPI reward (wellness/dojo 上昇 → like/love)。
