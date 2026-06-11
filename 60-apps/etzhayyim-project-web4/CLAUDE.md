# etzhayyim-project-web4 (GCC Token & Minter)

## Deployed Contracts (Ethereum Mainnet)

| Contract | Address | Notes |
|---|---|---|
| GCC Token | `0x799d24a6FFBb758C6E2Ed8f981822A17Eaa5F30B` | FiatTokenV2_2 compatible, 6 decimals |
| GCCMinter | `0xAf80b152eD85067F8386416767b9658E86C253d9` | Accepts ETH/USDC/USDT, mints GCC |
| Safe (owner) | `0xA00366234D29d4F882088048c0B2fa0dB7302D4E` | 2/3 multisig, owns both contracts |
| Deployer EOA | `0xe255D68563C974ac061484cEce4E57de02a4E0Da` | No privileges post-transfer |
| Chainlink ETH/USD | `0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419` | 8 decimals |

## Foundry (Solidity)

- Path: `export PATH="$HOME/.foundry/bin:$PATH"` (not in PATH by default)
- Install deps: `forge install foundry-rs/forge-std --no-git` (`--no-commit` is invalid)
- RPC: `https://ethereum-rpc.publicnode.com` (CloudFlare/llamarpc unreliable)
- Verify selectors: `cast sig "functionName(uint256)"` — never guess selectors
- Staleness check: use `updatedAt + 1 hours > block.timestamp` (not `block.timestamp - 1 hours` which underflows)
- Tests: always `vm.warp(1700000000)` in setUp to avoid underflow with realistic timestamps
- USDT: non-standard ERC-20 (no return value on transfer), requires `_safeTransferFrom` pattern
- Deploy workflow: `forge script ... (dry-run)` → `forge script ... --broadcast --verify --slow`
- Contracts dir: `60-apps/etzhayyim-project-web4/contracts/usdc-test-t0k3n8x/`
- `.env` in contracts dir has DEPLOYER_PRIVATE_KEY, ETHERSCAN_API_KEY, SAFE_ADDRESS, TOKEN_ADDRESS

## CDN Deploy (S3)

- `aws` CLI v2 has bugs with `--endpoint-url` for Linode Object Storage; use `boto3` Python instead
- Create S3 keys via Linode API: `POST /v4/object-storage/keys` (secrets redacted after creation)
- Linode token in macOS Keychain: `security find-generic-password -s "etzhayyim.ai/pulumi" -a "LINODE_TOKEN" -w`
- Safe multisig (2/3 threshold): can't execute from CLI with single key, use Safe UI for admin ops

### Distributed MoE/TI2V S3 Layout

- Bucket: `etzhayyim-static-sites` (cluster: `jp-osa-1`)
- Qwen model id: `etzhayyim/etzhayyim-distributed-moe-260222`
  - experts: `models/qwen3-30b-a3b/experts/set-000.bin` ... `set-031.bin`
  - manifest: `models/qwen3-30b-a3b/manifests/latest.json`
- Wan model id: `etzhayyim/etzhayyim-distributed-ti2v-moe-260222`
  - experts: `models/wan2.2-ti2v-5b/experts/set-000.bin` ... `set-031.bin`
  - manifest: `models/wan2.2-ti2v-5b/manifests/latest.json`

### Recurrence Prevention (S3 publish)

- Always use **3-digit set names**: `set-000.bin` ... `set-031.bin` (not 2-digit).
- After upload, apply ACL for every object:
  - `aws s3api put-object-acl --acl public-read ...`
- Verify external reachability with `curl -I` for all 64 set objects + 2 manifests.
  - Release is blocked if any status is not `200`.
- Use temporary Object Storage key for upload and **delete key immediately** after publish.
- Regenerate embedded manifests before control-plane build:
  - `tools/qwen3_build_manifest.py`
  - `tools/wan22_build_manifest.py`
- After control-plane deploy, verify:
  - `/api/manifests`
  - `/api/manifest?model_id=etzhayyim/etzhayyim-distributed-moe-260222`
  - `/api/manifest?model_id=etzhayyim/etzhayyim-distributed-ti2v-moe-260222`

## blobstore-s3 Example

`60-apps/etzhayyim-project-web4/wasm/control-plane-25primzm/`:
```yaml
- name: blobstore-s3
  type: capability
  properties:
    image: ghcr.io/etzhayyimcojp/blobstore-s3:0.10.0
  traits:
    - type: link
      properties:
        target: <component>
        namespace: wasi
        package: blobstore
        interfaces: [blobstore]
        target_config:
          - name: s3-config
            properties:
              endpoint: "https://jp-osa-1.linodeobjects.com"
              region: "jp-osa-1"
              bucket: "etzhayyim-static-sites"
```

## Ads Playbook (as of 2026-02-22)

### Target Priority

- Primary acquisition GEO: India
- China strategy: avoid mainland-direct crypto acquisition; prioritize Chinese-speaking audiences outside mainland China (HK/SG/TW + diaspora communities)

### Recommended Channel Stack

- CoinGecko Ads: high-intent crypto audience (self-serve + managed)
- CoinMarketCap Ads: broad crypto reach + geo targeting
- Telegram Ads: community growth (public channels; message CTA points to `t.me` / `@` destinations)
- TrafficStars: performance testing channel (Pop/Push/Native mix), useful for fast creative/angle iteration

### Channel Constraints (Important)

- CoinGecko / CoinMarketCap / Telegram: treat as non-adult channels
- TrafficStars: adult inventory exists but must comply with platform legal/compliance rules
- Crypto/financial claims: avoid guaranteed-profit wording in all creatives/LPs

### API Availability (Public)

- CoinGecko: market data API exists; no public ad campaign management API documented
- CoinMarketCap: market data API exists; no public ad campaign management API documented
- Telegram Ads: advertiser dashboard flow; no public advertiser campaign API documented
- TrafficStars: advertiser API is available for campaign automation (after account setup)

### TrafficStars Execution Plan (India, 30 days)

1. Day 0-1 (tracking first):
   - Add click ID passthrough to LP URL:
     - Example: `...?ts_clickid={click_id}&utm_source=trafficstars&utm_campaign=<name>`
   - Configure S2S postback/conversion mapping with `click_id`
   - Define conversion events:
     - Primary: `buy_success`
     - Secondary: `wallet_connected`, `buy_started`, `provider_joined`
2. Day 1-7 (broad exploration):
   - Split campaigns by device (mobile/desktop)
   - Run separate campaign per format: Popunder, Push/In-Page Push, Native
   - Start on RON traffic, small budgets, aggressive exclusion of non-performing spots
3. Day 8-14 (selection):
   - Promote winners to whitelist + Prime inventory
   - Use optimizer/auto-rules for bid and blacklist tuning
4. Day 15-30 (scale):
   - Scale only campaigns below target CPA (stepwise budget increases)
   - Localize creatives: English + Hindi variants

### TrafficStars Practical Minima

- Minimum deposit: typically USD 100 (wire usually higher)
- Typical minimum campaign budget:
  - USD 10/day (general)
  - USD 25/day (In-Page Push guidance)
