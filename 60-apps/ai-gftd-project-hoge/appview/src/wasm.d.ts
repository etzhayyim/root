/** Type declaration for Wrangler CompiledWasm module imports. */
declare module "*.wasm" {
  const module: WebAssembly.Module;
  export default module;
}
