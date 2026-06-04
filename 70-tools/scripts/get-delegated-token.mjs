/**
 * get-delegated-token.mjs
 * Keychainのrefresh_tokenを使ってaccess_tokenを自動取得。
 * refresh_tokenが無い場合のみデバイスコード認証を実行。
 * Usage: node get-delegated-token.mjs [scope]
 */
import { execSync } from 'child_process';

function kc(svc, acct) {
  return execSync(`security find-generic-password -s "${svc}" -a "${acct}" -w`, { encoding: 'utf8' }).trim();
}
function kcSave(svc, acct, val) {
  try { execSync(`security add-generic-password -s "${svc}" -a "${acct}" -w "${val}" -U`); }
  catch { execSync(`security add-generic-password -s "${svc}" -a "${acct}" -w "${val}"`); }
}

const TENANT    = kc('etzhayyim.m365', 'TENANT_ID');
const CLIENT_ID = kc('etzhayyim.m365', 'CLIENT_ID');
const SCOPE     = process.argv[2] || 'https://graph.microsoft.com/ChannelMessage.Send offline_access';

// 1. refresh_token があれば使う
let refreshToken = '';
try { refreshToken = kc('etzhayyim.m365', 'DELEGATED_REFRESH_TOKEN'); } catch {}

if (refreshToken) {
  const res = await fetch(`https://login.microsoftonline.com/${TENANT}/oauth2/v2.0/token`, {
    method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ client_id: CLIENT_ID, grant_type: 'refresh_token', refresh_token: refreshToken, scope: SCOPE })
  });
  const token = await res.json();
  if (token.access_token) {
    if (token.refresh_token) kcSave('etzhayyim.m365', 'DELEGATED_REFRESH_TOKEN', token.refresh_token);
    process.stdout.write(token.access_token);
    process.exit(0);
  }
  console.error('refresh failed:', token.error, '— falling back to device code');
}

// 2. デバイスコード (初回 or refresh 失敗時のみ)
const dcResp = await fetch(`https://login.microsoftonline.com/${TENANT}/oauth2/v2.0/devicecode`, {
  method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({ client_id: CLIENT_ID, scope: SCOPE })
});
const dc = await dcResp.json();
console.error(`\n=== デバイスコード認証 ===\nURL: https://login.microsoft.com/device\nCODE: ${dc.user_code}\n=========================\n`);

const start = Date.now();
while (Date.now() - start < 300000) {
  await new Promise(r => setTimeout(r, (dc.interval || 5) * 1000));
  const res = await fetch(`https://login.microsoftonline.com/${TENANT}/oauth2/v2.0/token`, {
    method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ client_id: CLIENT_ID, grant_type: 'urn:ietf:params:oauth:grant-type:device_code', device_code: dc.device_code })
  });
  const token = await res.json();
  if (token.access_token) {
    if (token.refresh_token) {
      kcSave('etzhayyim.m365', 'DELEGATED_REFRESH_TOKEN', token.refresh_token);
      console.error('✅ refresh_token saved to Keychain');
    }
    process.stdout.write(token.access_token);
    process.exit(0);
  }
  if (token.error !== 'authorization_pending') { console.error('Error:', token.error); process.exit(1); }
  process.stderr.write('.');
}
console.error('\nTimeout');
process.exit(1);
