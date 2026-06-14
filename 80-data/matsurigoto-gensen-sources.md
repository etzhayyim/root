# 80-data/matsurigoto-gensen-sources — catalog (tracked pointer)

matsurigoto `tax-collect` (源泉所得税・復興特別所得税の納付処理, ADR-2606141200) が
`:authoritative` 値の根拠とする **国税庁・財務省の一次資料 PDF**。

ADR-2605241500 (Dataset CID substrate) に従い、**bytes は DataLad/git-annex の nested dataset**
`80-data/matsurigoto-gensen-sources/` に保存 (annex→IPFS)。monorepo git にはこの catalog のみ
track する (dataset 本体は `.gitignore` 済 — embedded-repo 回避)。

## 収録 PDF (git-annex MD5E backend)

| ファイル | 発行 | 一次URL | annex key | bytes |
|---|---|---|---|---|
| nta-denshi-keisan-tokurei-r3-r7.pdf | 国税庁 | https://www.nta.go.jp/publication/pamph/gensen/zeigakuhyo2022/data/denshi_10.pdf | `MD5E-s115788--04bf2152f40e69b818a43d04f669dcf8.pdf` | 115788 |
| nta-bureaus-offices-list-2024.pdf | 国税庁 | https://www.nta.go.jp/taxes/sake/shiori-gaikyo/shiori/2024/pdf/0030-1.pdf | `MD5E-s388904--834d891635d062a9f9c2bdcae94a621d.pdf` | 388904 |
| mof-entaizei-kasanzei-rates.pdf | 財務省 | https://www.mof.go.jp/tax_policy/summary/tins/n04_5.pdf | `MD5E-s194797--baa19f57bd3301b3f1b2655f8f2a3a56.pdf` | 194797 |

ライセンス: 政府標準利用規約(2.0) — 出典明示で複製可 (≒ CC BY 4.0)。

## 再取得 / 検証

```bash
# nested dataset として download-url で再取得済。bytes 復元 + 検証:
git -C 80-data/matsurigoto-gensen-sources annex get .
git -C 80-data/matsurigoto-gensen-sources annex whereis   # 一次URLが登録済
git -C 80-data/matsurigoto-gensen-sources annex fsck       # MD5整合
```

IPFS 公開 (各 annex object → CID, manifest.edn の `:cid` に追記) は Council+operator step。
