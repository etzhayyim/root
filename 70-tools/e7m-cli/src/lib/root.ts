import fs from 'fs/promises';
import path from 'path';

const ANCHORS = ['deps.toml', 'CHARTER-RIDER.md', 'LICENSE'];

async function exists(p: string): Promise<boolean> {
  try { await fs.access(p); return true; } catch { return false; }
}

export async function findRepoRoot(start: string = process.cwd()): Promise<string> {
  let dir = path.resolve(start);
  while (true) {
    for (const anchor of ANCHORS) {
      if (await exists(path.join(dir, anchor))) {
        if (await exists(path.join(dir, '.git'))) return dir;
      }
    }
    const parent = path.dirname(dir);
    if (parent === dir) {
      throw new Error(
        'Could not locate etzhayyim monorepo root (no deps.toml + .git found ascending from ' +
        start + ')'
      );
    }
    dir = parent;
  }
}

export async function resolveApp(name: string): Promise<string> {
  const root = await findRepoRoot();
  const candidates = [
    path.join(root, '60-apps', name),
    path.join(root, '60-apps', `etzhayyim-project-${name}`),
  ];
  for (const c of candidates) {
    if (await exists(c)) return c;
  }
  throw new Error(`App not found in 60-apps/: tried ${candidates.join(', ')}`);
}

export async function resolveLayer(layer: '00-contracts' | '10-protocol' | '20-actors' | '30-graph' | '50-infra' | '60-apps' | '70-tools' | '90-docs'): Promise<string> {
  const root = await findRepoRoot();
  return path.join(root, layer);
}
