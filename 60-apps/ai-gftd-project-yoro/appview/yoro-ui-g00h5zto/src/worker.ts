interface Env {
  ASSETS: Fetcher;
  APP_DEPLOY_AT?: string;
  APP_DEPLOY_SHA?: string;
}

const DID_DOCUMENT = {
  "@context": [
    "https://www.w3.org/ns/did/v1",
    "https://w3id.org/security/suites/jws-2020/v1"
  ],
  id: "did:web:yoro.etzhayyim.com",
  alsoKnownAs: ["at://yoro.etzhayyim.com"],
  service: [
    {
      id: "#atproto_pds",
      type: "AtprotoPersonalDataServer",
      serviceEndpoint: "https://atproto.etzhayyim.com"
    },
    {
      id: "#appview",
      type: "YoroAppView",
      serviceEndpoint: "https://yoro.etzhayyim.com"
    }
  ]
};

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/.well-known/did.json") {
      return json(DID_DOCUMENT, {
        "Cache-Control": "public, max-age=300"
      });
    }

    if (url.pathname === "/_app/version.json") {
      return json({
        app: "yoro",
        did: "did:web:yoro.etzhayyim.com",
        deployAt: env.APP_DEPLOY_AT ?? null,
        deploySha: env.APP_DEPLOY_SHA ?? null
      }, {
        "Cache-Control": "no-store"
      });
    }

    return env.ASSETS.fetch(request);
  }
};

function json(body: unknown, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      ...headers
    }
  });
}
