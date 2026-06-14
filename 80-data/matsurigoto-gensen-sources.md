# 80-data/matsurigoto-gensen-sources — catalog (tracked pointer)

matsurigoto `tax-collect` (源泉所得税・復興特別所得税の納付処理, ADR-2606141200) が
`:authoritative` 値の根拠とする **国税庁・財務省の一次資料 PDF**。

ADR-2605241500 (Dataset CID substrate) に従い、**bytes は DataLad/git-annex の nested dataset**
`80-data/matsurigoto-gensen-sources/` に保存 (annex→IPFS)。monorepo git にはこの catalog のみ
track する (dataset 本体は `.gitignore` 済 — embedded-repo 回避)。

## 収録 PDF (git-annex MD5E backend)

| ファイル | 発行 | 一次URL | IPFS CIDv1 | bytes |
|---|---|---|---|---|
| nta-denshi-keisan-tokurei-r3-r7.pdf | 国税庁 | https://www.nta.go.jp/publication/pamph/gensen/zeigakuhyo2022/data/denshi_10.pdf | `bafkreihadpbxrcs3ctacbut3a3nefgmilnm3o4yyplx7oior5wopuekaqi` | 115788 |
| nta-bureaus-offices-list-2024.pdf | 国税庁 | https://www.nta.go.jp/taxes/sake/shiori-gaikyo/shiori/2024/pdf/0030-1.pdf | `bafybeift7lxblt55dqgzfg7clcqshknfrihmqe2iych4ymljhctdlwigsu` | 388904 |
| mof-entaizei-kasanzei-rates.pdf | 財務省 | https://www.mof.go.jp/tax_policy/summary/tins/n04_5.pdf | `bafkreifa4dloqmf5nwoztqhkdkiowm55pbljefdavlow632mwunx7q7zva` | 194797 |

ライセンス: 政府標準利用規約(2.0) — 出典明示で複製可 (≒ CC BY 4.0)。

## IPFS 公開 (G7 = PR review で許可済, ADR-2606091500)

3点とも `ipfs add --cid-version=1` で content-addressed → ローカル pin + **公開DHTへ provide 済**
(任意のゲートウェイから取得可)。例: `https://ipfs.io/ipfs/<CID>` / `ipfs cat <CID>`。
annex の MD5E キー (各PDFの md5/サイズ) は `manifest.edn` 参照。

```bash
ipfs cat bafkreihadpbxrcs3ctacbut3a3nefgmilnm3o4yyplx7oior5wopuekaqi | head -c 4   # %PDF
```

**残: 永続 remote pin** — kotobase.net への pin (ADR-2606091500) は auth token を要する operator step。
現状は提供ノードが稼働中のみ取得可。durable 化は kotobase もしくは他 pinning service へ token 設定後 `ipfs pin remote add`。

## 再取得 / 検証

```bash
# nested dataset として download-url で再取得済。bytes 復元 + 検証:
git -C 80-data/matsurigoto-gensen-sources annex get .
git -C 80-data/matsurigoto-gensen-sources annex whereis   # 一次URLが登録済
git -C 80-data/matsurigoto-gensen-sources annex fsck       # MD5整合
```

IPFS 公開 (各 annex object → CID, manifest.edn の `:cid` に追記) は Council+operator step。
