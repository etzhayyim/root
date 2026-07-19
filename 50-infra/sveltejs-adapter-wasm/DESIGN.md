# sveltejs-adapter-wasm design

The adapter has one supported runtime boundary: Javy.

1. SvelteKit emits client, prerendered, and server artifacts.
2. The adapter bundles the server entry with esbuild.
3. Javy compiles the JavaScript bundle to a core WebAssembly module.
4. `wasm-tools component new` adapts it to a WASI 0.2 component.

Runtime selection remains explicit in the TypeScript API so unsupported values
fail type checking. Go and TinyGo orchestration were retired under the canonical
policy in `GO-DEPRECATION.edn`.
