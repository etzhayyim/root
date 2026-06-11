declare module '*.svelte' {
  const component: unknown;
  export default component;
}

declare module 'svelte' {
  export function mount(component: unknown, options: { target: Element }): unknown;
}
