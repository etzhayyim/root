# sveltejs-adapter-wasm

SvelteKit adapter for WebAssembly (WASI 0.2) targeting wasmCloud through the
Javy JavaScript runtime.

The adapter bundles the SvelteKit server with esbuild, compiles it with Javy,
and wraps the core module as a WASI 0.2 component. Go and TinyGo runtimes are
not supported; see the canonical repository policy in `GO-DEPRECATION.edn`.

## Usage

```javascript
import adapter from '@etzhayyim/sveltejs-adapter-wasm';

export default {
  kit: {
    adapter: adapter({ runtime: 'javy', out: 'build' })
  }
};
```

## Requirements

- Javy
- wasm-tools
- pnpm 10+
- wasmCloud 1.4+

`demos/demo-javy` is the executable example. `demos/demo-ssg` uses the same
Javy component boundary with SvelteKit prerendering enabled by the app.
