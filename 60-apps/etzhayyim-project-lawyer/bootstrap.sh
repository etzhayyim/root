#!/usr/bin/env bash
# bootstrap.sh — lawyer.etzhayyim.com × etzhayyim × Kagoshima University case MVP
#
# 前提:
#   1. etzhayyim auth login (j.kawasaki) 済み  → `etzhayyim auth whoami` で did:etzhayyim:* 確認
#   2. Azure AD app に ChannelMessage.Read.All の admin consent 済み
#   3. mac Keychain に etzhayyim.m365 credentials 設定済み (root CLAUDE.md 参照)
#
# Phase 1 (did:etzhayyim bootstrap, 3 種) → Phase 3 (lawyer records, 3 種)
# Phase 4 (Teams sync) は sync_teams_channel.mjs を別途実行。
# Phase 5 (markdown) は kagoshima-univ.md を Phase 3 結果で手動更新。
#
# 実行順:
#   bash 60-apps/etzhayyim-project-lawyer/bootstrap.sh phase1  # mint 3 DIDs
#   bash 60-apps/etzhayyim-project-lawyer/bootstrap.sh phase3  # write 3 records
#
# 出力: ~/.local/etzhayyim/bootstrap/lawyer-$(date +%Y%m%d).json (DID + record URI の台帳)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="${HOME}/.local/etzhayyim/bootstrap"
OUT_FILE="${OUT_DIR}/lawyer-$(date +%Y%m%d).json"
mkdir -p "${OUT_DIR}"
touch "${OUT_FILE}"

# ── helpers ──────────────────────────────────────────────────────────────
die() { echo "error: $*" >&2; exit 1; }
require_etzhayyim() { command -v etzhayyim >/dev/null 2>&1 || die "etzhayyim CLI not found"; }
require_jq()   { command -v jq >/dev/null 2>&1 || die "jq not found (brew install jq)"; }
require_auth() {
  etzhayyim auth whoami >/dev/null 2>&1 || die "run 'etzhayyim auth login' first"
}
save_kv() {
  # $1 = key, $2 = value → merge into OUT_FILE
  local tmp
  tmp=$(mktemp)
  if [ -s "${OUT_FILE}" ]; then
    jq --arg k "$1" --arg v "$2" '. + {($k): $v}' "${OUT_FILE}" > "${tmp}"
  else
    jq -n --arg k "$1" --arg v "$2" '{($k): $v}' > "${tmp}"
  fi
  mv "${tmp}" "${OUT_FILE}"
}
load_kv() {
  jq -r --arg k "$1" '.[$k] // empty' "${OUT_FILE}" 2>/dev/null
}

# ── Phase 1: did:etzhayyim bootstrap ──────────────────────────────────────────
phase1() {
  require_etzhayyim; require_jq; require_auth
  echo "=== Phase 1: mint did:etzhayyim roots + k.bakshi child ==="

  # (1) etzhayyim Japan (client) root
  local etzhayyim_user="etzhayyim-${RANDOM}"
  local etzhayyim_pw
  etzhayyim_pw=$(openssl rand -hex 16)
  echo "→ createGuestAccount etzhayyim root (username=${etzhayyim_user})"
  local etzhayyim_resp
  etzhayyim_resp=$(etzhayyim xrpc com.etzhayyim.auth.createGuestAccount \
    -d "$(jq -n --arg u "${etzhayyim_user}" --arg p "${etzhayyim_pw}" '{username:$u,password:$p}')" \
    --json)
  local etzhayyim_did
  etzhayyim_did=$(echo "${etzhayyim_resp}" | jq -r .did)
  [ -n "${etzhayyim_did}" ] && [ "${etzhayyim_did}" != "null" ] || die "etzhayyim did mint failed: ${etzhayyim_resp}"
  save_kv "etzhayyim_did_etzhayyim" "${etzhayyim_did}"
  save_kv "etzhayyim_bootstrap_username" "${etzhayyim_user}"
  # password は 1Password / Keychain に転送、ここには残さない
  security add-generic-password -s "etzhayyim.lawyer.bootstrap" -a "${etzhayyim_user}" -w "${etzhayyim_pw}" -U 2>/dev/null || true
  echo "  ✓ ${etzhayyim_did}"

  # (2) lawyer.etzhayyim.com firm root
  local lawyer_user="etzhayyim-lawyer-${RANDOM}"
  local lawyer_pw
  lawyer_pw=$(openssl rand -hex 16)
  echo "→ createGuestAccount lawyer root (username=${lawyer_user})"
  local lawyer_resp
  lawyer_resp=$(etzhayyim xrpc com.etzhayyim.auth.createGuestAccount \
    -d "$(jq -n --arg u "${lawyer_user}" --arg p "${lawyer_pw}" '{username:$u,password:$p}')" \
    --json)
  local lawyer_did
  lawyer_did=$(echo "${lawyer_resp}" | jq -r .did)
  [ -n "${lawyer_did}" ] && [ "${lawyer_did}" != "null" ] || die "lawyer did mint failed: ${lawyer_resp}"
  save_kv "lawyer_did_etzhayyim" "${lawyer_did}"
  save_kv "lawyer_bootstrap_username" "${lawyer_user}"
  security add-generic-password -s "etzhayyim.lawyer.bootstrap" -a "${lawyer_user}" -w "${lawyer_pw}" -U 2>/dev/null || true
  echo "  ✓ ${lawyer_did}"

  # (3) k.bakshi child (pubkey) under lawyer root
  # NOTE: mintChildDid requires caller session to control parentDid — need to switch to lawyer session
  echo "→ switch session to lawyer root"
  local lawyer_refresh
  lawyer_refresh=$(echo "${lawyer_resp}" | jq -r .refreshJwt)
  [ -n "${lawyer_refresh}" ] && [ "${lawyer_refresh}" != "null" ] || die "lawyer refreshJwt missing"
  # etzhayyim CLI にはセッション切替 API がないため、直接 XRPC Bearer で呼ぶ
  local lawyer_access
  lawyer_access=$(echo "${lawyer_resp}" | jq -r .accessJwt)

  echo "→ mintChildDid k.bakshi under ${lawyer_did}"
  local bakshi_resp
  bakshi_resp=$(curl -sf -X POST "https://atproto.etzhayyim.com/xrpc/com.etzhayyim.auth.mintChildDid" \
    -H "Authorization: Bearer ${lawyer_access}" \
    -H "Content-Type: application/json" \
    -d "$(jq -n --arg parent "${lawyer_did}" '{parentDid:$parent,materialKind:"pubkey",material:{roleName:"CLO",holderDid:"did:web:etzhayyim.com:user:k.bakshi"},handle:"k.bakshi",performerType:"person"}')")
  local bakshi_did
  bakshi_did=$(echo "${bakshi_resp}" | jq -r .did)
  [ -n "${bakshi_did}" ] && [ "${bakshi_did}" != "null" ] || die "bakshi child mint failed: ${bakshi_resp}"
  save_kv "bakshi_did_etzhayyim" "${bakshi_did}"
  save_kv "lawyer_access_jwt" "${lawyer_access}"  # Phase 3 で使う (short-lived)
  echo "  ✓ ${bakshi_did}"

  echo
  echo "Phase 1 done. Results in ${OUT_FILE}:"
  jq . "${OUT_FILE}"
}

# ── Phase 3: lawfirm records on lawfirm Worker with lawyer firmDid ──────
phase3() {
  require_etzhayyim; require_jq; require_auth
  [ -s "${OUT_FILE}" ] || die "${OUT_FILE} empty — run phase1 first"

  local lawyer_did etzhayyim_did bakshi_did lawyer_access
  lawyer_did=$(load_kv lawyer_did_etzhayyim)
  etzhayyim_did=$(load_kv etzhayyim_did_etzhayyim)
  bakshi_did=$(load_kv bakshi_did_etzhayyim)
  lawyer_access=$(load_kv lawyer_access_jwt)
  [ -n "${lawyer_did}" ]   || die "lawyer_did_etzhayyim missing"
  [ -n "${etzhayyim_did}" ] || die "etzhayyim_did_etzhayyim missing"
  [ -n "${bakshi_did}" ]   || die "bakshi_did_etzhayyim missing"
  [ -n "${lawyer_access}" ] || die "lawyer_access_jwt missing (re-run phase1 or refresh)"

  echo "=== Phase 3: register lawfirmProfile + engagement + matter ==="

  # (1) lawfirmProfile for lawyer.etzhayyim.com
  echo "→ registerLawfirm (lawyer.etzhayyim.com)"
  local lf_resp
  lf_resp=$(curl -sf -X POST "https://lawfirm.etzhayyim.com/xrpc/com.etzhayyim.apps.lawfirm.registerLawfirm" \
    -H "Authorization: Bearer ${lawyer_access}" \
    -H "Content-Type: application/json" \
    -d "$(jq -n --arg did "${lawyer_did}" '{firmDid:$did,name:"etzhayyim Lawyer",displayName:"etzhayyim Lawyer",jurisdictions:["JPN"],barAssociation:"JFBA",websiteUrl:"https://lawyer.etzhayyim.com",contactEmail:"legal@etzhayyim.com"}')")
  local lf_uri
  lf_uri=$(echo "${lf_resp}" | jq -r .uri)
  save_kv "lawfirm_profile_uri" "${lf_uri}"
  echo "  ✓ ${lf_uri}"

  # (2) engagement: etzhayyim → lawyer
  echo "→ createEngagement (client=${etzhayyim_did}, firm=${lawyer_did})"
  local eng_resp
  eng_resp=$(curl -sf -X POST "https://lawfirm.etzhayyim.com/xrpc/com.etzhayyim.apps.lawfirm.createEngagement" \
    -H "Authorization: Bearer ${lawyer_access}" \
    -H "Content-Type: application/json" \
    -d "$(jq -n --arg firm "${lawyer_did}" --arg client "${etzhayyim_did}" '{firmDid:$firm,clientDid:$client,scope:"pre-litigation representation — Kagoshima University dispute",status:"active"}')")
  local eng_uri
  eng_uri=$(echo "${eng_resp}" | jq -r .uri)
  save_kv "engagement_uri" "${eng_uri}"
  echo "  ✓ ${eng_uri}"

  # (3) matter: Kagoshima University
  # openedAt は Teams channel の最古 message 日時を使用するのが望ましい。
  # 未 sync なら今日の日付で仮登録 → Phase 4 後に updateMatterStatus で調整。
  local opened_at
  opened_at=$(date -u +%Y-%m-%dT00:00:00Z)
  echo "→ createMatter (Kagoshima University)"
  local mat_resp
  mat_resp=$(curl -sf -X POST "https://lawfirm.etzhayyim.com/xrpc/com.etzhayyim.apps.lawfirm.createMatter" \
    -H "Authorization: Bearer ${lawyer_access}" \
    -H "Content-Type: application/json" \
    -d "$(jq -n \
      --arg firm "${lawyer_did}" \
      --arg client "${etzhayyim_did}" \
      --arg lead "${bakshi_did}" \
      --arg opened "${opened_at}" \
      '{firmDid:$firm,matterType:"litigation",clientDid:$client,leadBengoshiDid:$lead,openedAt:$opened,jurisdiction:"JPN",subjectMatter:"鹿児島大学との紛争 (pre-litigation)",feeStructure:"hourly",currency:"JPY",matterNumber:"KAGOSHIMA-2504"}')")
  local matter_did matter_rkey matter_uri
  matter_did=$(echo "${mat_resp}" | jq -r .matterDid)
  matter_rkey=$(echo "${mat_resp}" | jq -r .matterRkey)
  matter_uri=$(echo "${mat_resp}" | jq -r .uri)
  save_kv "kagoshima_matter_did" "${matter_did}"
  save_kv "kagoshima_matter_rkey" "${matter_rkey}"
  save_kv "kagoshima_matter_uri" "${matter_uri}"
  echo "  ✓ ${matter_uri}"

  echo
  echo "Phase 3 done. Ledger:"
  jq . "${OUT_FILE}"
  echo
  echo "Next: update 60-apps/etzhayyim-project-kaisya/cases/kagoshima-univ.md"
  echo "      front-matter placeholders ({h_lawyer}, {h_bakshi}, {h_etzhayyim}, matter_uri, engagement_uri)"
}

case "${1:-}" in
  phase1) phase1 ;;
  phase3) phase3 ;;
  *)
    cat <<USAGE
Usage: $0 <phase1|phase3>
  phase1  — mint 3 did:etzhayyim (etzhayyim root / lawyer root / k.bakshi pubkey child)
  phase3  — register lawfirmProfile + engagement + matter on lawfirm.etzhayyim.com Worker

Ledger output: ${OUT_FILE}
USAGE
    exit 2
    ;;
esac
