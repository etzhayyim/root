# Safe Multisig による TestUSDC デプロイ手順

## 前提条件

- Sepolia ETH を持つ EOA (ガス代支払い用)
- Safe multisig が Sepolia に作成済み (https://app.safe.global)
- Foundry インストール済み (`foundryup`)

## 方法 A: EOA デプロイ → Safe へ権限移譲 (推奨)

最もシンプルな方法。EOA でデプロイしてから全ロールを Safe に移す。

### Step 1: デプロイ

```bash
cd 60-apps/etzhayyim-project-web4/contracts/usdc-test-t0k3n8x

# .env を設定
cp .env.example .env
# SEPOLIA_RPC_URL, DEPLOYER_PRIVATE_KEY, ETHERSCAN_API_KEY を記入

source .env

# Sepolia にデプロイ + Etherscan verify
forge script script/Deploy.s.sol:Deploy \
    --rpc-url $SEPOLIA_RPC_URL \
    --private-key $DEPLOYER_PRIVATE_KEY \
    --broadcast --verify

# 出力から Token address を控える
# TestUSDC deployed at: 0x...
```

### Step 2: 動作確認

```bash
# balanceOf 確認
cast call $TOKEN_ADDRESS "balanceOf(address)(uint256)" $DEPLOYER_ADDRESS \
    --rpc-url $SEPOLIA_RPC_URL

# transfer テスト
cast send $TOKEN_ADDRESS "transfer(address,uint256)(bool)" \
    $RECIPIENT 1000000 \
    --rpc-url $SEPOLIA_RPC_URL \
    --private-key $DEPLOYER_PRIVATE_KEY
```

### Step 3: Safe へ全ロール移譲

```bash
export TOKEN_ADDRESS=0x...  # Step 1 で控えたアドレス
export SAFE_ADDRESS=0x...   # Safe のアドレス

forge script script/TransferToSafe.s.sol:TransferToSafe \
    --rpc-url $SEPOLIA_RPC_URL \
    --private-key $DEPLOYER_PRIVATE_KEY \
    --broadcast
```

移譲されるロール:
- `owner` → Safe
- `masterMinter` → Safe
- `pauser` → Safe
- `blacklister` → Safe
- `rescuer` → Safe

### Step 4: Safe から minter 設定

Safe UI → Apps → Transaction Builder:

1. **Enter Address**: `$TOKEN_ADDRESS`
2. **Select method**: `configureMinter(address,uint256)`
3. **Parameters**:
   - `minter`: minter に指定する EOA アドレス
   - `minterAllowedAmount`: `100000000000000000` (100B × 10^6)
4. **Create Batch** → 署名を集めて Execute

## 方法 B: Safe から直接デプロイ (Transaction Builder)

### Step 1: bytecode 取得

```bash
forge script script/Deploy.s.sol:Deploy --rpc-url $SEPOLIA_RPC_URL

# broadcast/Deploy.s.sol/11155111/dry-run/run-latest.json から
# transaction.data (creation bytecode) をコピー
```

### Step 2: Safe Transaction Builder

1. https://app.safe.global でログイン
2. **Apps** → **Transaction Builder**
3. **New Transaction**:
   - **To Address**: `0x0000000000000000000000000000000000000000`
   - **Value**: `0`
   - **Data**: Step 1 の bytecode を貼り付け
   - **Operation**: `0` (Call) — Safe は CREATE2 ではなく内部で deploy
4. **Add Transaction** → **Create Batch**
5. 必要な署名数を集めて **Execute**

> 注意: Safe から直接 CREATE する場合、`msg.sender` は Safe アドレスになる。
> そのため constructor の全ロール (owner, masterMinter, pauser, blacklister) が
> 最初から Safe に設定され、Step 3 の移譲が不要になる。

### Step 3: 初期 minter 設定

同じ Transaction Builder で:

1. **Enter Address**: デプロイされた token アドレス
2. ABI が自動読み込みされない場合は手動で入力
3. `configureMinter(minter, minterAllowedAmount)` を呼ぶ
4. 必要に応じて `mint(to, amount)` も batch に追加

## 方法 C: Safe SDK (プログラマティック)

```typescript
import Safe from '@safe-global/protocol-kit'
import SafeApiKit from '@safe-global/api-kit'

// 1. Safe SDK 初期化
const protocolKit = await Safe.init({
  provider: SEPOLIA_RPC_URL,
  signer: SIGNER_PRIVATE_KEY,
  safeAddress: SAFE_ADDRESS,
})

const apiKit = new SafeApiKit({ chainId: 11155111n })

// 2. デプロイ tx 作成
const deployTx = await protocolKit.createTransaction({
  transactions: [{
    to: '0x0000000000000000000000000000000000000000',
    value: '0',
    data: CREATION_BYTECODE,
    operation: 0, // Call
  }]
})

// 3. 署名 & 提案
const safeTxHash = await protocolKit.getTransactionHash(deployTx)
const signature = await protocolKit.signHash(safeTxHash)
await apiKit.proposeTransaction({
  safeAddress: SAFE_ADDRESS,
  safeTransactionData: deployTx.data,
  safeTxHash,
  senderAddress: SIGNER_ADDRESS,
  senderSignature: signature.data,
})

// 4. 他の signer が Safe UI で承認 → Execute
```

## デプロイ後チェックリスト

- [ ] `decimals()` → `6`
- [ ] `name()` → `"USD Coin"`
- [ ] `symbol()` → `"USDC"`
- [ ] `version()` → `"2"`
- [ ] `owner()` → Safe address
- [ ] `masterMinter()` → Safe address
- [ ] `pauser()` → Safe address
- [ ] `blacklister()` → Safe address
- [ ] `totalSupply()` → 初期 mint 額
- [ ] Etherscan で verified
- [ ] EIP-2612 permit が機能する
- [ ] EIP-3009 transferWithAuthorization が機能する
- [ ] `web3_payments.ts` の Sepolia USDC アドレスを更新

## web3-ui への統合

`wasm/web4-mcp-component` 側の決済トークン設定を更新:

```typescript
// Sepolia TestUSDC
const SEPOLIA_USDC = '0x<deployed-address>';
```

## ネットワーク情報

| 項目 | 値 |
|---|---|
| Network | Sepolia Testnet |
| Chain ID | 11155111 |
| RPC | https://rpc.sepolia.org |
| Explorer | https://sepolia.etherscan.io |
| Faucet | https://sepoliafaucet.com |
