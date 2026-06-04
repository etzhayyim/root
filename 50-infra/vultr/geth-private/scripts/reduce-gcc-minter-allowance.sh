#!/usr/bin/env bash
# Reduce GCC sealer minterAllowance to zero via Safe 2-of-3 (ADR-0074 Phase 3).
#
# The Gnosis Safe (0xc0C2…) is masterMinter. configureMinter(sealer, 0) zeros
# the minting power without removing isMinter, so block production continues
# and the allowance can be re-granted later via another Safe tx.
#
# Requires K1_PRIV + K2_PRIV (Safe owners, macOS Keychain etzhayyim.safe-owners)
# and SEALER_PRIV for gas (macOS Keychain etzhayyim.private-chain SEALER_PRIV).
#
# Usage:
#   bash 50-infra/vultr/geth-private/scripts/reduce-gcc-minter-allowance.sh
#
# Dry-run (no broadcast):
#   DRY_RUN=1 bash ... reduce-gcc-minter-allowance.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

SEALER=0xaFed0Cb7633EDBd26aA52658e71528309F562501
GCC=0x8e9A5162b2800E0D19acC1708A531A3954900E21
RPC=https://geth.etzhayyim.com

echo "==> Fetching keys from macOS Keychain..."
K1_PRIV=$(security find-generic-password -s "etzhayyim.safe-owners" -a "K1_PRIV" -w)
K2_PRIV=$(security find-generic-password -s "etzhayyim.safe-owners" -a "K2_PRIV" -w)
SEALER_PRIV=$(security find-generic-password -s "etzhayyim.private-chain" -a "SEALER_PRIV" -w)

echo "==> Current sealer minterAllowance:"
CURRENT=$(cast call "$GCC" 'minterAllowance(address)(uint256)' "$SEALER" --rpc-url "$RPC")
echo "    $CURRENT ($(echo "scale=2; $CURRENT / 10^18" | bc) GCC)"

if [ "${DRY_RUN:-0}" = "1" ]; then
  echo "==> DRY_RUN=1 — printing calldata only, no broadcast"
  cast calldata 'configureMinter(address,uint256)' "$SEALER" 0
  exit 0
fi

echo ""
echo "==> Submitting Safe tx: configureMinter(sealer, 0)"
echo "    Target: $GCC (GCCStablecoin)"
echo "    Caller: Safe 0xc0C20918372bf200faf3587eB0C6685a830daFc1"

CALLDATA=$(cast calldata 'configureMinter(address,uint256)' "$SEALER" 0)

cd "$SCRIPT_DIR/contracts"
MIGRATE_LIVE=true \
  K1_PRIV="$K1_PRIV" \
  K2_PRIV="$K2_PRIV" \
  SENDER_PRIV="$SEALER_PRIV" \
  TARGET="$GCC" \
  CALLDATA="$CALLDATA" \
  forge script script/ExecSafeCall.s.sol \
    --rpc-url "$RPC" --broadcast --legacy \
    -vvv

echo ""
echo "==> Verifying allowance after tx..."
NEW=$(cast call "$GCC" 'minterAllowance(address)(uint256)' "$SEALER" --rpc-url "$RPC")
echo "    minterAllowance: $NEW"
if [ "$NEW" = "0" ]; then
  echo "    ✓ Allowance zeroed successfully."
else
  echo "    ✗ Expected 0, got $NEW — check Safe tx above."
  exit 1
fi

echo ""
echo "==> Done. To re-grant allowance for a mint run:"
echo "    TARGET=$GCC CALLDATA=\$(cast calldata 'configureMinter(address,uint256)' $SEALER <AMOUNT_WEI>) \\"
echo "    ... forge script ExecSafeCall.s.sol ..."
