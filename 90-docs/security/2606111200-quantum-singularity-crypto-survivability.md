---
id: security-quantum-singularity-crypto-survivability
title: "暗号は無意味になるか — 量子計算機・シンギュラリティ下における etzhayyim 暗号基盤の生存性: 統計・数理分析"
status: active
doc_type: explanation
topic: post-quantum
authoritative: true
last_verified: 2026-06-11
authoritative_for:
  - quantum threat model and post-quantum migration rationale
related:
  - security-crypto-agility-policy
  - security-readme
supersedes: []
superseded_by: []
---

# 暗号は無意味になるか — 量子計算機・シンギュラリティ下における etzhayyim 暗号基盤の生存性: 統計・数理分析

**Will Cryptography Become Meaningless? A Statistical and Mathematical Survivability
Analysis of the etzhayyim Cryptographic Substrate under Quantum Computing and
a Technological Singularity**

Date: 2026-06-11 · Companion ADR: ADR-2606111300 (pqh-v1 hybrid layer)

## Abstract (EN)

We analyze the hypothesis that quantum computing and a technological singularity
will render cryptography meaningless, applied to the etzhayyim substrate
(XChaCha20-Poly1305, AES-256-GCM, Ed25519, secp256k1, P-256, X25519, SHA-256).
The hypothesis decomposes asymmetrically: (1) Shor's algorithm breaks all
elliptic-curve primitives in polynomial time once a cryptographically relevant
quantum computer (CRQC) exists — expert-survey aggregation places the median
arrival near 2040, with ~20–35% cumulative probability by 2035; (2) Grover's
algorithm is provably bounded at quadratic speedup (BBBV 1997), leaving 256-bit
symmetric primitives with 128-bit post-quantum security; (3) brute force beyond
that is excluded by thermodynamics (Landauer's principle), independent of
intelligence: enumerating 2^256 states costs ≥3.3×10^56 J, ~10^12 solar
lifetimes; (4) the one-time pad is unconditionally secure (Shannon 1949), so the
universal form of the hypothesis is mathematically false. The binding constraint
for etzhayyim is Mosca's inequality: ciphertext published permanently on public
substrates (MST/IPFS/L2) with multi-decade confidentiality requirements is
already exposed to harvest-now-decrypt-later. Remediation (suite pqh-v1:
X25519+ML-KEM-768 hybrid KEM, Ed25519+ML-DSA-65 dual signatures) is specified in
ADR-2606111300 and implemented in `@etzhayyim/sdk`.

## 要旨

「量子暗号(量子計算機)とシンギュラリティによって暗号は意味がなくなる」という
未来仮説を、etzhayyim 基盤の実際の暗号インベントリに対して統計・数理的に評価した。
結論: 仮説は**公開鍵暗号に限り条件付きで正しく**(CRQC 到来中央値 ~2040 年)、
**共通鍵暗号・情報理論的暗号については物理法則と証明済み定理により偽**である。
本稿の帰結として、脆弱成分のみをハイブリッド PQ 化する pqh-v1 スイートを導入した。

## 1. 脅威の分解 — 「暗号」は一枚岩ではない

評価対象のインベントリ(2026-06-11 時点、導入前):

| 用途 | プリミティブ | 量子攻撃 | 判定 |
|---|---|---|---|
| レコード暗号化 (`crypto.ts`, ADR-2605181100) | XChaCha20-Poly1305 (256bit) | Grover のみ | **実質安全** |
| Vault 保管 (`vault-crypto.ts`) | AES-256-GCM | Grover のみ | **実質安全** |
| ハッシュ/CID/anchor | SHA-256 / Keccak-256 / BLAKE2b | Grover/BHT | 余裕半減、十分 |
| DID 署名 (`did-signal.ts`) | Ed25519 | **Shor** | 破られる |
| ガバナンス署名 (`etzhayyim-authz`) | secp256k1 ECDSA | **Shor** | 破られる |
| Passkey (将来 R2) | P-256 ES256 | **Shor** | 破られる |
| セッション鍵交換 (`signal.ts` / libsignal) | X25519 | **Shor** | 破られる |
| KDF | PBKDF2-SHA256 (210k–310k iter) | Grover のみ | 暗号的には安全(人間由来エントロピーが弱点) |

脅威も三系統に分解する必要がある:

- **T1 量子計算機(アルゴリズム既知)** — Shor / Grover。数理的に確定済み、
  到来時期のみが確率変数。
- **T2 シンギュラリティ: 計算力爆発** — 物理限界で上界が引ける(§3)。
- **T3 シンギュラリティ: アルゴリズム的発見** — 新しい数学。確率を割り当て
  られないナイト的不確実性だが、構造的下界が存在する(§5)。

## 2. 数理分析 (T1): Shor と Grover の非対称性

**Shor.** 楕円曲線離散対数は量子多項式時間 O((log q)³)。256bit 曲線
(Ed25519 / secp256k1 / P-256)の代表的リソース見積もり:

- 論理量子ビット ≈ 2,330、Toffoli ≈ 1.26×10¹¹ (Roetteler–Naehrig–Svore–Lauter 2017)
- 表面符号誤り訂正込みの物理量子ビット: 10⁶ オーダー
  (Gidney–Ekerå 2019 の RSA-2048 = 2×10⁷ noisy qubits / 8h は、Gidney 2025 の
  改良で <10⁶ に低下。ECC-256 は RSA-2048 より**少ない**リソースで落ちる)

**Grover.** 鍵長 n の全探索は Θ(2^(n/2)) が**下界として証明済み**
(Bennett–Bernstein–Brassard–Vazirani 1997)。よって:

- XChaCha20 / AES-256: 実効 128bit。さらに Grover は逐次実行必須
  (並列化は √ 改善しか得られない)ため、実時間では 2^128 逐次量子ゲート
  ≈ 宇宙年齢を大きく超える。NIST PQC Category V のまま。
- SHA-256 衝突: Brassard–Høyer–Tapp 2^(n/3) ≈ 2^85、メモリコストで実用上無効。

**帰結**: 「量子で暗号が全滅する」は誤り。全滅するのは離散対数・素因数分解系
のみで、etzhayyim のレコード本体(対称層)は構造的に生き残る。

## 3. 物理的上界 (T2): 超知性も熱力学には従う

Landauer 限界: 1bit の不可逆状態遷移 ≥ kT ln2 ≈ 2.9×10⁻²¹ J (300K)。

- 2²⁵⁶ 鍵空間の単純列挙: E ≥ 2²⁵⁶ · kT ln2 ≈ **3.3×10⁵⁶ J**
  = 太陽の全生涯放出 (~1.2×10⁴⁴ J) の **~10¹² 倍**
- Grover 後の 2¹²⁸ でも: ≈ 9.8×10¹⁷ J(エネルギーは世界年間消費の ~0.2% で
  賄えるが、Margolus–Levitov 限界下の逐次量子演算時間が宇宙論的スケール)
- Bremermann 限界 (~1.36×10⁵⁰ bit/s/kg) を仮定した惑星質量コンピュータでも
  2²⁵⁶ 列挙は ~10⁶ 年オーダー

**帰結**: T2(計算力だけのシンギュラリティ)は 256bit 対称暗号を破れない。
これは知性の量に依存しない、保存則からの結論である。

## 4. 統計分析: CRQC 到来時期の分布

**専門家サーベイ** (Global Risk Institute "Quantum Threat Timeline"、毎年
40 名前後の量子情報研究者への構造化調査) の集約値 — RSA-2048 を 24h 以内に
破る CRQC の累積確率:

| 年 | P(CRQC ≤ t) |
|---|---|
| 2030 | ~5–10% |
| 2035 | ~20–35% |
| 2040 | ~50%(中央値シナリオ) |
| 2050 | ~80–90% |

**ハードウェアトレンドとの整合**: 物理量子ビットは ~2 年倍増
(2019 ~50 → 2025 ~10³)。誤り訂正は 2024 年 Google Willow で閾値以下動作を
初実証。必要量 (~10⁶ 物理 qubit) まで約 3 桁 → 倍増ペース維持で **~20 年
≈ 2045**、ロードマップ加速 (IBM 等) シナリオで 2035 前後。サーベイ分布と
独立推定が同じ 2035–2045 帯に収束する。

**注意**: ECC-256 は RSA-2048 より先に落ちる(§2)ため、上表は etzhayyim の
Ed25519/secp256k1 に対して**楽観側**のバウンドである。

## 5. シンギュラリティの形式的扱い (T3)

T3 を「超知性による未知の暗号解析的発見」と定義すると:

1. **普遍命題は偽**: ワンタイムパッドは Shannon (1949) により情報理論的に
   安全 — 「すべての暗号が無意味になる」未来は、いかなる知性の下でも
   数学的に存在しない。
2. **対称暗号の構造的根拠**: 一方向性関数が存在する限り(P≠NP より強いが
   広く信じられる仮定)、共通鍵暗号は健在。経験的にも AES への最良攻撃は
   25 年間で総当たり比 4 倍速 (Biclique, 2¹²⁶·¹) に留まり、攻撃進歩率は
   統計的に極めて緩慢。
3. **現実的な ASI 攻撃面は実装層**: 鍵管理、サイドチャネル、エンドポイント、
   そして人間由来パスワード(PBKDF2 の入力エントロピー)が、数理的暗号より
   先に落ちる。これは暗号アルゴリズム選択では救えず、no-server-key 原則
   (ADR-2605231525) と端末側鍵管理が対応する層である。

なお本稿は終末論ではなくリスク管理である(Charter §1.15 非終末論と整合)。
HNDL(§6)は「将来の審判」ではなく**現在進行形の収集**であり、対処は
現在時制の工学課題である。

## 6. etzhayyim 固有の拘束: Mosca 不等式と HNDL

Mosca の定理: 秘匿必要年数 x + 移行年数 y > CRQC 到来年数 z ならば今行動。

- **x**: 永久記憶 = Tier-0 priority(消去権なし)。暗号文は MST / IPFS /
  Base L2 上に**公開状態で永続化**される。x → 数十年〜無期限
- **y**: 50+ アクターへの協調展開 ≈ 3–5 年
- **z**: 中央値 ~15 年(§4)、悲観側 ~10 年

x + y ≫ z が成立し、さらに**収穫攻撃 (harvest now, decrypt later)** により
今日公開された X25519 ハンドシェイクは CRQC 到来日に遡って復号される。
ただしレコード本体は XChaCha20-Poly1305 であるため、HNDL の実効的な急所は
(a) 鍵交換・鍵ラップ経路、(b) 署名の事後偽造(DID 乗っ取り・ガバナンス偽造)
の 2 点に**限定**される。

## 7. 対策 (実装済み: suite pqh-v1, ADR-2606111300)

設計原則: **ハイブリッド AND 構成** — 攻撃者は古典成分と PQ 成分の**両方**を
破らなければならない(片方の未知の弱点に対する保険)。

| 層 | 旧 | pqh-v1 | 状態 |
|---|---|---|---|
| 鍵交換/鍵ラップ | X25519(または in-memory 乱数) | **X25519 + ML-KEM-768** (FIPS 203)、HKDF-SHA256 transcript-bound combiner | `sdk/src/pq.ts` + `signal.ts` 実装済み |
| DID↔Signal binding 署名 | Ed25519 単独 | **Ed25519 + ML-DSA-65** (FIPS 204) 二重署名、PQ 鍵既知時はダウングレード拒否 | `sdk/src/did-signal.ts` 実装済み |
| KEM 公開鍵の配布 | — | `SignalIdentityBody.pqX25519PublicKey / pqMlkemPublicKey`(binding 署名で保護) | 実装済み |
| 対称層 | XChaCha20-Poly1305 256bit | **変更なし**(§2/§3 により量子後も有効) | — |
| ハッシュ | SHA-256 系 | 変更なし | — |

**残余リスクと今後**(優先度順):

1. **secp256k1 ガバナンス署名** — ERC-4337 / Base L2 のチェーン側制約により
   単独では PQ 化不能。緩和: 鍵ローテーション短期化 + Council 多署名は
   「z 到来前に使い切る」運用。チェーン側 PQ 対応 (EIP 系) を追跡。
2. **PBKDF2 → Argon2id**(yoro/vault)— 量子非依存だが T3 実装層で最弱。
3. **libsignal 経路** — upstream PQXDH (X25519+Kyber) 追従。optional 依存の
   バージョン更新で取り込む。
4. **DID document への ML-DSA verification method 公開** — did:web の
   `verificationMethod` 拡張(one R-cycle 後に enforcement へ)。
5. ML-KEM-768/ML-DSA-65 は ~2030 年以降 ML-KEM-1024/ML-DSA-87 への
   引き上げを再評価(ASD ガイダンス)— crypto-agility-policy の
   suite-versioning に従い pqh-v2 として導入可能。

## 8. 結論

「量子+シンギュラリティで暗号は無意味になる」という仮説の真理値は:

- **公開鍵暗号(現行)**: 条件付きで真。P ≈ 50% / 2040、~85% / 2050。
  → pqh-v1 ハイブリッドで AND 構成に変換済み。
- **256bit 対称暗号**: 偽(Grover 下界 + Landauer 限界)。
- **情報理論的暗号 (OTP)**: 偽(Shannon 1949、知性非依存)。
- **実装・人間層**: 暗号以前に最弱。no-server-key + Argon2id + 端末鍵管理が対応層。

etzhayyim はレコード本体を対称暗号で保護する設計だったため、PQ 移行の急所は
鍵交換と署名の 2 点に収束し、本 wave で SDK seam の範囲は閉じた。

## References

- Shor, P. (1994). Algorithms for quantum computation: discrete logarithms and factoring.
- Bennett, Bernstein, Brassard, Vazirani (1997). Strengths and Weaknesses of Quantum Computing. (BBBV 下界)
- Shannon, C. (1949). Communication Theory of Secrecy Systems. (OTP 完全秘匿)
- Roetteler, Naehrig, Svore, Lauter (2017). Quantum resource estimates for computing elliptic curve discrete logarithms.
- Gidney, Ekerå (2019). How to factor 2048 bit RSA integers in 8 hours using 20 million noisy qubits. / Gidney (2025) update (<1M qubits).
- Landauer, R. (1961). Irreversibility and Heat Generation in the Computing Process.
- Mosca, M. (2015). Cybersecurity in an era with quantum computers: will we be ready?
- Global Risk Institute. Quantum Threat Timeline Report (annual expert survey).
- NIST FIPS 203 (ML-KEM), FIPS 204 (ML-DSA), 2024. / X-Wing hybrid KEM (Connolly et al. 2024).
- Bogdanov, Khovratovich, Rechberger (2011). Biclique Cryptanalysis of the Full AES.
- ADR-2605181100 (Tahoe-pattern AEAD), ADR-2605231525 (no-server-key), ADR-2606111300 (pqh-v1).
