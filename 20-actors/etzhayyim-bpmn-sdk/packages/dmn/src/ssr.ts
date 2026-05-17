export function assertClient(): void {
  if (typeof window === "undefined" || typeof document === "undefined") {
    throw new Error("@gftd/bpmn-sdk/dmn requires a browser (client) environment");
  }
}

