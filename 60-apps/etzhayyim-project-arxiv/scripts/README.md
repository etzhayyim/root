# arXiv Submission Scripts

## Prerequisites

- `pdflatex` (TeX Live)
  - macOS: `brew install --cask mactex`
  - Ubuntu: `sudo apt-get install texlive-full`

## Usage

### 1. Validate LaTeX compilation

```bash
cd 60-apps/etzhayyim-project-arxiv
bash 70-tools/70-tools/70-tools/scripts/validate-tex.sh papers/moex-distributed-webgpu
```

Runs pdflatex 2-pass, reports warnings/errors, checks PDF size against arXiv 10MB limit.

### 2. Generate arXiv submission tarball

```bash
bash 70-tools/70-tools/70-tools/scripts/submit-arxiv.sh papers/moex-distributed-webgpu
```

Compiles, packages required files into `dist/<paper>-arxiv-<date>.tar.gz`, and prints upload instructions.

### 3. Submit to arXiv

1. Go to https://arxiv.org/submit
2. Upload the generated `.tar.gz`
3. Select category (e.g. `cs.DC`, `cs.LG`)
4. Fill in metadata
5. Submit

## Paper directory structure

```
papers/<paper-name>/
├── main.tex          # Primary TeX file (arXiv convention)
├── *.bib             # Bibliography (optional, inline also OK)
├── *.sty / *.cls     # Custom styles (optional)
└── figures/          # Image files (optional)
```

## Current papers

| Paper | Directory | arXiv Category |
|---|---|---|
| MoEx: Distributed MoE via WebGPU | `papers/moex-distributed-webgpu/` | cs.DC / cs.LG |
