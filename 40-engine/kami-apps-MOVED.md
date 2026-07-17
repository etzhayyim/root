# kami-apps は独立リポジトリに移設されました

`40-engine/kami-apps/` は独立リポ **`github.com/etzhayyim/kami-apps`**
（west path `orgs/etzhayyim/kami-apps`）に移設されました（2026-07-16、ADR-2607171000
engine split-now leaf）。

kami-engine product apps（bim/cad/live/maps3d/animeka-timeline）の self-contained
Cargo workspace。全 crate は `etzhayyim/kami-engine` を git rev で依存（path 依存でない）
ため移設は clean、monorepo 側の消費者ゼロ。
