export type RouteConfig = Record<string, unknown>;

type ZodLike = Record<string, unknown> & ((...args: unknown[]) => ZodLike);

function makeZodLike(): ZodLike {
  const target = (() => proxy) as unknown as ZodLike;
  const proxy = new Proxy(target, {
    get: (_obj, key) => {
      if (key === "toJSON") return () => ({});
      if (key === Symbol.toPrimitive) return () => "[zod-shim]";
      return proxy;
    },
    apply: () => proxy,
  });
  return proxy;
}

const z = makeZodLike();

export function createRoute<T extends RouteConfig>(route: T): T {
  return route;
}

export class OpenAPIHono {
  #routes: RouteConfig[] = [];

  openapi(route: RouteConfig, _handler: unknown): void {
    this.#routes.push(route);
  }

  getOpenAPIDocument(init: Record<string, unknown>): Record<string, unknown> {
    return {
      ...init,
      paths: {},
      "x-generated-routes": this.#routes.length,
    };
  }
}

export { z };
