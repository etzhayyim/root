# 暗号解析に効く「構造・発見」サーベイ（元記事の外）

> 文脈: 本ディレクトリの PoC — **ECDSA nonce/HNP 格子攻撃（実装可能）** と
> **Semaev index-calculus（素体で壁）** — を踏まえ、2019〜2026 の「新しい数学的構造の発見」
> と「AI/ML の応用」のうち、secp256k1/ECDLP 解析に *実際に* 参考になるものを調査・評価した。
> 5 本の並行リサーチ（SIKE / nonce-HNP / 格子簡約 / index-calculus / AI・構造）を統合。

## TL;DR

1. **新構造が実暗号を破った最大の事例 = SIKE/SIDH 破壊（2022）**。25 年眠っていた Kani の定理
   ＋高次元アーベル多様体で、10 年安全とされた問題がラップトップ数分〜1 時間で陥落。
   **だが ECDLP/secp256k1 には波及しない**（SIDH が *公開していた補助トーション点* を食う攻撃で、
   ECDSA は同種の補助データを公開しない）。← 記事の精神そのもの＋その限界。
2. **実際に Bitcoin 鍵が盗まれる唯一の経路は nonce**。我々の H5 と一致。さらに上があり、
   **1 bit 未満の偏りでも Bleichenbacher FFT で破れる（LadderLeak）**。
3. **格子簡約は進化（BKZ2.0→G6K→flatter）**。だが ECDLP は格子問題ではなく、**2024 の Chen
   量子 LWE 論文は撤回**。256-bit ECDLP への古典/格子の脅威は無い。
4. **素体 secp256k1 が安全な理由は実測どおり**: Weil descent に必要な部分体が無く、factor base が
   作れない。我々の H2 実測（O(p^1.5) ≫ √p）は文献と完全整合。
5. **AI/ML は標準公開鍵（RSA/ECDLP）を一切破っていない**。効くのは「縮約ラウンド対称暗号・
   サイドチャネル・疎な秘密の LWE・探索ヒューリスティック」だけ。我々の C 実測（素体に構造なし）と一致。

---

## 1. 新構造が難問を破った典型 — SIKE/SIDH（記事の精神の実例）

- **破壊の3論文**: Castryck–Decru *An efficient key recovery attack on SIDH*（[ePrint 2022/975](https://eprint.iacr.org/2022/975), EUROCRYPT 2023）→ Maino–Martindale（[2022/1026](https://eprint.iacr.org/2022/1026), 任意の開始曲線）→ Damien Robert *Breaking SIDH in polynomial time*（[2022/1038](https://inria.hal.science/hal-03943959/), 全ケース多項式時間）。
- **速度**: $50,000 の IKEp217 を **1 コア5分未満**、SIKEp434（NIST L1）を**1時間未満**（[Quanta](https://www.quantamagazine.org/post-quantum-cryptography-scheme-is-cracked-on-a-laptop-20220824/)）。
- **機構**: **Kani の定理（1997）**＝「glue-and-split」。1 次元の同種写像問題を **2 次元アーベル多様体（種数2 Jacobian）** に埋め込み、(2,2)-isogeny で正しい中間曲線を判定して秘密ウォークを復元。Robert は次元 4・8 に上げて多項式時間化（Zarhin の4平方トリック）。
- **何を食ったか**: SIDH が**公開する補助トーション点の像 P,Q（秘密同種写像による）と既知の写像次数**。
- **なぜ ECDLP に波及しないか（決定的）**: 攻撃は「(1) 秘密同種写像の次数既知 (2) 補助点が与えられる」に依存（[ellipticnews](https://ellipticnews.wordpress.com/2022/07/31/breaking-supersingular-isogeny-diffie-hellman-sidh/)）。**ECDSA/secp256k1 は秘密写像の次数も補助トーション像も公開しない** → Kani の定理が噛む構造が存在しない。CSIDH/SQISign も無事。
- **教訓**: 暗号リスクは *スキームが公開せざるを得ない補助データ* に集中する。隣接する地味な数学（量子でも総当たりでもない）が「10 年安全」を「1 時間で陥落」に変える。

## 2. ECDSA nonce / HNP の実世界攻撃（我々の H5 の地続き・上位）

- **理論**: nonce が偏る/一部既知 → **Hidden Number Problem（Boneh–Venkatesan, CRYPTO1996）**→ CVP を LLL+Babai で解く。
- **閾値の目安**:
  - **nonce 再利用**: 2署名で純代数復元（我々の攻撃A）。実害: PS3定数nonce、**Android SecureRandom 2013（~55.82 BTC 盗難, [bitcoin.org alert](https://bitcoin.org/en/alert/2013-08-11-android)）**。
  - **格子**: Howgrave-Graham–Smart で **160-bit DSA を 8 既知bit×~30署名**で復元。実務則 **~2–4 bit × 数百署名**。**1 bit はピュア格子では困難**。
  - **Bleichenbacher FFT**: **1 bit 未満の偏り**でも破れるが**数百万署名**（範囲縮約）。De Mulder et al.（CHES2013）は **5-bit leak × ~4,000 署名**で 384-bit ECDSA を復元。
- **実装攻撃の最新**:
  - **LadderLeak**（Aranha+, CCS2020, [2020/615](https://eprint.iacr.org/2020/615)）: Montgomery ladder の側路で **1 bit 未満**の nonce MSB を漏らし P-192/sect163r1 を破る（Bleichenbacher-FFT）。
  - **Minerva**（TCHES2020, [2020/728](https://eprint.iacr.org/2020/728.pdf)）: nonce の**ビット長**がタイミングで漏れ、**~500–2,100 署名**で 256-bit 鍵復元。
  - **TPM-Fail**（USENIX2020, [tpm.fail](https://tpm.fail/)）: Intel fTPM を **~1,300 観測・2分未満**、VPN を **~45,000 ハンドシェイク**で。
  - **Biased Nonce Sense**（Breitner–Heninger, FC2019, [2019/023](https://eprint.iacr.org/2019/023)）: Bitcoin/Ethereum/Ripple/HTTPS/SSH を走査し **Bitcoin で数百鍵**復元（残高は僅少）。偏り＝再利用・下位128bit共有・上下bit差。
- **防御**: **RFC 6979**（決定的 nonce, HMAC-DRBG）。我々の結論と同一。

## 3. 格子簡約の進展と「Chen 2024 撤回」

- **系譜**: BKZ 2.0（Chen–Nguyen, ASIACRYPT2011, simulator付）→ **G6K**（篩, EUROCRYPT2019, [2019/089](https://eprint.iacr.org/2019/089)）→ **flatter**（Ryan–Heninger, CRYPTO2023, [2023/237](https://eprint.iacr.org/2023/237)）= 反復圧縮で次元>1000・数百万bit係数の LLL を桁違い高速化（**Coppersmith 系/巨大 HNP に効く**）。
- **Chen 2024 量子LWE**: [ePrint 2024/555](https://eprint.iacr.org/2024/555) で多項式時間量子 LWE を主張→ **Step 9 のバグを Hongxun Wu と Thomas Vidick が独立に発見（2024-04-18）**、修正できず **LWE主張は撤回**（[Aaronson blog](https://scottaaronson.blog/?p=7946)）。**格子 PQC は破られていない**。
- **ECDLP への含意**: 格子は **nonce 漏洩経由でしか** ECDSA を攻撃しない。完全乱数 nonce なら無効。**ECDLP は格子問題ではない**。実務的含意 = もし我々が HNP をブロックチェーン規模に拡張するなら **flatter / G6K** が道具になる（攻撃の数学は不変、規模が伸びる）。

## 4. EC index-calculus / Semaev — なぜ素体が安全か（我々の H2 を文献が裏書き）

- **Semaev 総和多項式**（[2004/031](https://eprint.iacr.org/2004/031)）= 点分解を代数化（我々が S_3/S_4 で実装したもの）。
- **Gaudry/Diem**: index-calculus は **拡大体 F_{q^n} の Weil 制限**で factor base を作れる時のみ効く。Diem（Compositio 2011）は **n が増大/合成**のとき subexponential を証明、ただし定数が **2^{O(n^2)}（over-exponential）**。
- **first-fall-degree 仮説**（Petit–Quisquater, ASIACRYPT2012）で二進体 subexponential を期待 → **後続（Kosters–Yeo 等）で likely false**＝Gröbner 次数が爆発（我々が m=2/m=3 で見た探索コスト爆発と同型）。
- **決定的**: **素体 F_p には部分体が無い → Weil descent 不可 → 自然な factor base 無し → subexponential index-calculus 無し**。最良は generic Pollard rho **≈2^128**（[Galbraith–Gaudry survey 2015/1022](https://eprint.iacr.org/2015/1022.pdf)）。**secp256k1 が素体であること自体が安全の根拠** — 我々の実測（|FB|~√p、分解~O(p)、合計 O(p^1.5)≫√p）と完全一致。

## 5. AI/ML 暗号解析 — 何ができて何ができないか

- **Gohr**（CRYPTO2019, [2019/037](https://eprint.iacr.org/2019/037)）: NN 識別器が **縮約ラウンド Speck32/64**（対称暗号）を改善。差分以外の構造を抽出するが**フル暗号も公開鍵も非対象**。
- **DeepMind**: **FunSearch**（Nature2023, cap set/bin-packing）、**AlphaEvolve**（2025, 4×4 複素行列積を 48 乗算 = Strassen 以来56年ぶり更新）、**AlphaProof/AlphaGeometry**（2024, IMO 銀）。**いずれも暗号/ECDLP に未着手**。
- **SALSA 系**（Wenger–Charton–Lauter）: transformer で **疎・小さい秘密の LWE**（n≤512, 疎性≤0.12）を攻撃。**本番 dense LWE は未破壊**で、重い仕事は**古典 BKZ 前処理**がやっている（ML はラッパ）。
- **正直な総括**: **ML/AI は標準公開鍵（RSA/ECDLP/secp256k1）を一つも破っていない**。効くのは縮約対称暗号・サイドチャネル・疎LWE・探索ヒューリスティック。**我々の C 実測（素体 Semaev 分解に bandit 加速なし=構造なし）と整合**。

## 6. secp256k1 固有の構造 — GLV と SafeCurves

- **GLV 自己準同型**: j=0、CM by √−3。ψ(x,y)=(βx, y)=λ·P（[GLV, CRYPTO2001](https://link.springer.com/chapter/10.1007/3-540-44647-8_11)）。Bitcoin は k≡k₁+k₂λ 分解で**スカラー倍を高速化**（libsecp256k1）。
- **攻撃には使えない**: 位数 d の自己同型は rho を **√d 倍**しか速くしない。λ(√3)＋negation(√2) で secp256k1 は generic 256-bit より**数 bit 弱いだけ**（≈2^127）。**構造は速度用、破壊用ではない**。
- **SafeCurves**（Bernstein–Lange）: secp256k1 は **ECDLP 硬度（rho/transfer/MOV/大素数位数）は合格**。落ちるのは **実装安全性**（ladder 無し・加法非完備・twist 安全性弱）— これは*実装*の話で ECDLP 破壊可能性ではない。Curve25519 はこれらも通すよう後発設計。

---

## 7. 我々の PoC への含意と「次に試す価値のある3方向」

調査の結論は、**(a) 素体 ECDLP の数学正面は古典・格子・AI・量子前のどれでも動かない**（H2 の壁は本物）、
**(b) 実害も実装可能な攻撃も nonce/運用に集中**（H5 が正しい）、
**(c) リスクは "公開される補助データ" に宿る**（SIKE の教訓）。これを踏まえ:

### 方向① — Bleichenbacher FFT nonce 攻撃（H5 の上位互換, 実装可能・防御的）
現 PoC の格子/HNP は「≥2–4 bit × 少数署名」。**Bleichenbacher の FFT 法**を足すと
**1 bit 未満の偏り × 大量署名**（LadderLeak/Minerva クラス）に届く。
→ ブロックチェーン規模の **nonce 偏り監査**（脆弱 RNG 系統の検出→所有者警告）に直結。defensive。

### 方向② — 「構造がある曲線」との対照実験（H2 の決定打）
拡大体 E(F_{q^n}）（n 合成）や二進体で **index-calculus/Semaev が rho を実際に超える**様子を実装し、
**素体 secp256k1 と並べて**「構造の有無で攻撃が効く/効かない」を一画面で実測。
SIKE の教訓（構造＝攻撃の入口）を、自前の数字で示す。我々の C（bandit）も構造側で大加速するはず。

### 方向③ — 「補助データ」レンズの監査ツール（SIKE 教訓の Bitcoin 版, 防御）
SIKE が示した「公開補助データにリスクが宿る」を Bitcoin に当てる: nonce 統計指紋・アドレス再利用・
署名メタデータから **実装系統を ML で同定**し、**at-risk ウォレットを事前警告**。
方向①の FFT 検出器と合流させると、攻撃ではなく**公開台帳の健全性モニタ**になる。

> いずれも「自分が鍵を持つテスト/合成データ・公開台帳の健全性監査」に限定し、
> 他者資金の窃取設計は作らない、という本 PoC の境界を維持する。

---

## 出典（主要）

- SIKE 破壊: [Castryck–Decru 2022/975](https://eprint.iacr.org/2022/975) · [Maino–Martindale 2022/1026](https://eprint.iacr.org/2022/1026) · [Robert HAL](https://inria.hal.science/hal-03943959/) · [Quanta](https://www.quantamagazine.org/post-quantum-cryptography-scheme-is-cracked-on-a-laptop-20220824/) · [ellipticnews](https://ellipticnews.wordpress.com/2022/08/12/attacks-on-sidh-sike/)
- nonce/HNP: [LadderLeak 2020/615](https://eprint.iacr.org/2020/615) · [Minerva 2020/728](https://eprint.iacr.org/2020/728.pdf) · [TPM-Fail](https://tpm.fail/) · [Biased Nonce Sense 2019/023](https://eprint.iacr.org/2019/023) · [RFC 6979](https://www.rfc-editor.org/rfc/rfc6979)
- 格子: [G6K 2019/089](https://eprint.iacr.org/2019/089) · [flatter 2023/237](https://eprint.iacr.org/2023/237) · [Chen 2024/555](https://eprint.iacr.org/2024/555) · [Aaronson on retraction](https://scottaaronson.blog/?p=7946)
- index-calculus: [Semaev 2004/031](https://eprint.iacr.org/2004/031) · [Diem, Compositio 2011](https://www.cambridge.org/core/journals/compositio-mathematica/article/on-the-discrete-logarithm-problem-in-elliptic-curves/59B877810708C90F6287972486A5BF0C) · [Galbraith–Gaudry 2015/1022](https://eprint.iacr.org/2015/1022.pdf)
- AI/ML: [Gohr 2019/037](https://eprint.iacr.org/2019/037) · [FunSearch, Nature 2023](https://www.nature.com/articles/s41586-023-06924-6) · [AlphaEvolve](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/) · [SALSA arXiv:2207.04785](https://arxiv.org/abs/2207.04785) · [PICANTE arXiv:2303.04178](https://arxiv.org/abs/2303.04178)
- secp256k1 構造: [GLV CRYPTO2001](https://link.springer.com/chapter/10.1007/3-540-44647-8_11) · [SafeCurves](https://safecurves.cr.yp.to/)

*（注: LadderLeak の曲線別署名本数の厳密値、SafeCurves の一部頁は取得時にブロック/403。各主張は別の一次/権威ソースで裏取り済み。）*
