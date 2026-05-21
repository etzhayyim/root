// integrations.ts — public /integrations page.
//
// Each section is a 1-line copy-paste for a specific AI/dev tool.
// Picked the highest-conversion surfaces: Cursor (MCP), Continue.dev,
// LangChain (Python), OpenAI tool calling, Postman, raw curl,
// openapi-typescript.

export function integrationsResponse(): Response {
  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Integrations — Yatabase</title>
<meta name="description" content="Plug Yatabase into Cursor, Continue.dev, LangChain, OpenAI tool-calling, Postman, or any tool that speaks OpenAPI 3.1 or MCP." />
<style>
  body{margin:0;font:15px/1.6 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#0f172a;background:#fafafa}
  header,main,footer{max-width:980px;margin:0 auto;padding:0 24px}
  header{padding:28px 24px 12px;display:flex;align-items:center;justify-content:space-between}
  .logo{font-weight:700;font-size:20px;color:inherit;text-decoration:none}
  .logo span{color:#0ea5e9}
  nav a{color:#334155;text-decoration:none;margin-left:18px;font-size:14px}
  nav a:hover{color:#0ea5e9}
  main{padding:8px 0}
  h1{font-size:32px;letter-spacing:-.02em;margin:8px 0 4px}
  p.lede{font-size:17px;color:#475569;max-width:680px;margin:0 0 24px}
  .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:18px;margin:24px 0}
  .card{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:22px;box-shadow:0 1px 2px rgba(0,0,0,.04)}
  .card h2{margin:0 0 6px;font-size:18px}
  .card .who{font-size:12px;color:#64748b;margin:0 0 12px}
  .card pre{background:#0f172a;color:#e2e8f0;padding:14px 16px;border-radius:8px;font:12px/1.5 ui-monospace,SF Mono,Menlo,Consolas,monospace;overflow-x:auto;margin:8px 0}
  .card pre .c{color:#94a3b8}
  .card pre .k{color:#7dd3fc}
  .card pre .s{color:#fcd34d}
  .card p{margin:8px 0;font-size:13px;color:#475569}
  .card a{color:#0ea5e9;text-decoration:none}
  .pill{display:inline-block;font-size:10px;padding:2px 6px;border-radius:8px;background:#dbeafe;color:#1e40af;font-weight:600;text-transform:uppercase;letter-spacing:.05em}
  footer{padding:36px 0 56px;color:#64748b;font-size:12px}
  footer a{color:#0ea5e9}
</style>
</head>
<body>

<header>
  <a class="logo" href="/">y<span>at</span>abase</a>
  <nav>
    <a href="/docs">Docs</a>
    <a href="/openapi.json">OpenAPI</a>
    <a href="/team">Team</a>
    <a href="/status">Status</a>
  </nav>
</header>

<main style="padding:24px">

<h1>Integrations</h1>
<p class="lede">
  Yatabase is built for AI-native stacks. Every surface speaks OpenAPI 3.1
  (<a href="/openapi.json">/openapi.json</a>), MCP JSON-RPC 2.0
  (<a href="/.well-known/mcp.json">/.well-known/mcp.json</a>), or AT Protocol XRPC. Drop it in.
</p>

<div class="grid">

<article class="card">
  <h2>Cursor (MCP) <span class="pill">recommended</span></h2>
  <p class="who">Best for: developers who want yatabase as a tool inside their IDE chat.</p>
  <p>Add to <code>~/.cursor/mcp.json</code>:</p>
  <pre>{
  "<span class="k">mcpServers</span>": {
    "<span class="k">yatabase</span>": {
      "<span class="k">url</span>": <span class="s">"https://yatabase.gftd.ai/mcp"</span>,
      "<span class="k">headers</span>": {
        "<span class="k">Authorization</span>": <span class="s">"Bearer sk_live_yata_…"</span>
      }
    }
  }
}</pre>
  <p>Restart Cursor. The 8 yata.* tools (cypher, sparql, storage list/read/write, mcp call) appear in Composer.</p>
</article>

<article class="card">
  <h2>Continue.dev</h2>
  <p class="who">Same as Cursor — vendor-neutral MCP client.</p>
  <pre>{
  "<span class="k">tools</span>": [{
    "<span class="k">type</span>": <span class="s">"mcp"</span>,
    "<span class="k">url</span>": <span class="s">"https://yatabase.gftd.ai/mcp"</span>,
    "<span class="k">headers</span>": {"<span class="k">Authorization</span>":<span class="s">"Bearer sk_live_yata_…"</span>}
  }]
}</pre>
</article>

<article class="card">
  <h2>Claude Desktop / Anthropic MCP clients</h2>
  <p class="who">Add to <code>~/Library/Application Support/Claude/claude_desktop_config.json</code> (macOS):</p>
  <pre>{
  "<span class="k">mcpServers</span>": {
    "<span class="k">yatabase</span>": {
      "<span class="k">command</span>": <span class="s">"npx"</span>,
      "<span class="k">args</span>": [<span class="s">"-y"</span>, <span class="s">"mcp-remote"</span>, <span class="s">"https://yatabase.gftd.ai/mcp"</span>,
               <span class="s">"--header"</span>, <span class="s">"Authorization:Bearer sk_live_yata_…"</span>]
    }
  }
}</pre>
</article>

<article class="card">
  <h2>LangChain (Python)</h2>
  <p class="who">Best for: backend agents written in Python.</p>
  <pre><span class="c"># pip install langchain-mcp-adapters</span>
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
  <span class="s">"yatabase"</span>: {
    <span class="s">"transport"</span>: <span class="s">"streamable_http"</span>,
    <span class="s">"url"</span>: <span class="s">"https://yatabase.gftd.ai/mcp"</span>,
    <span class="s">"headers"</span>: {<span class="s">"Authorization"</span>: <span class="s">"Bearer sk_live_yata_…"</span>},
  }
})
tools = await client.get_tools()
<span class="c"># Pass \`tools\` to any LangChain agent (create_react_agent, etc.)</span></pre>
</article>

<article class="card">
  <h2>OpenAI tool calling</h2>
  <p class="who">For raw OpenAI Chat Completions / Responses API. Use the OpenAPI spec to autogenerate function schemas.</p>
  <pre><span class="c"># pip install openapi-pydantic</span>
import requests, json
spec = requests.get(<span class="s">"https://yatabase.gftd.ai/openapi.json"</span>).json()
<span class="c"># Convert each operation in spec['paths'] to an OpenAI</span>
<span class="c"># function spec via your favorite openapi→tool converter,</span>
<span class="c"># or use the MCP path above (simpler).</span></pre>
</article>

<article class="card">
  <h2>TypeScript client (typed)</h2>
  <p class="who">Generate a fully-typed fetch client from the OpenAPI spec.</p>
  <pre>npx openapi-typescript <span class="s">https://yatabase.gftd.ai/openapi.json</span> -o yatabase.d.ts

<span class="c">// then in code:</span>
import createClient from <span class="s">"openapi-fetch"</span>;
import type { paths } from <span class="s">"./yatabase"</span>;

const yata = createClient<paths>({
  <span class="k">baseUrl</span>: <span class="s">"https://yatabase.gftd.ai"</span>,
  <span class="k">headers</span>: { <span class="k">Authorization</span>: <span class="s">\`Bearer \${process.env.YATA_KEY}\`</span> },
});
const { data } = await yata.POST(<span class="s">"/cypher"</span>, {
  <span class="k">body</span>: { <span class="k">query</span>: <span class="s">"MATCH (n:Demo) RETURN n"</span> }
});</pre>
</article>

<article class="card">
  <h2>Postman</h2>
  <p class="who">Import the OpenAPI spec — Postman generates a collection automatically.</p>
  <pre>File → Import → Link → <span class="s">https://yatabase.gftd.ai/openapi.json</span></pre>
  <p>Or via CLI: <code>postman api create --workspace=&lt;ws&gt; --schema=https://yatabase.gftd.ai/openapi.json</code>.</p>
</article>

<article class="card">
  <h2>Python client</h2>
  <pre>pip install openapi-python-client
openapi-python-client generate \\
  --url <span class="s">https://yatabase.gftd.ai/openapi.json</span></pre>
  <p>Output: an installable package with typed dataclasses for every request / response in the spec.</p>
</article>

<article class="card">
  <h2>S3-compatible tooling (boto3 / aws-cli / rclone)</h2>
  <p class="who">Use the <code>awsAccessKeyId</code>+secret returned by <code>POST /auth/v1/signup</code>.</p>
  <pre>aws configure set endpoint_url <span class="s">https://yatabase.gftd.ai/s3</span>
aws s3 cp localfile.txt s3://my-bucket/file.txt
rclone copy localfile.txt yatabase:my-bucket/</pre>
</article>

<article class="card">
  <h2>Neo4j drivers (read-only Cypher subset)</h2>
  <p class="who">Use <code>POST /cypher</code> directly — Neo4j HTTP API shape.</p>
  <pre>curl -X POST <span class="s">https://yatabase.gftd.ai/cypher</span> \\
  -H <span class="s">"Authorization: Bearer sk_live_yata_…"</span> \\
  -d '{"<span class="k">query</span>":"MATCH (n) RETURN n LIMIT 10"}'</pre>
  <p>Bolt protocol (<code>:7687</code>) is on the roadmap (P11). Until then, the HTTP path is fully supported.</p>
</article>

<article class="card">
  <h2>AT Protocol / Bluesky</h2>
  <p class="who">Yatabase auth resolves AT Protocol session JWTs as well as <code>sk_live_yata_*</code>.</p>
  <pre><span class="c"># Sign in at atproto.gftd.ai, get a session JWT,</span>
<span class="c"># then use the same Bearer header on yatabase.gftd.ai.</span>
curl -H <span class="s">"Authorization: Bearer &lt;at-jwt&gt;"</span> \\
  <span class="s">https://yatabase.gftd.ai/api/plan</span></pre>
</article>

<article class="card">
  <h2>raw curl</h2>
  <p class="who">For shell scripts, CI, or just getting things done.</p>
  <pre><span class="c"># 1. Mint a key (anonymous)</span>
KEY=$(curl -sS -X POST <span class="s">https://yatabase.gftd.ai/auth/v1/signup</span> \\
       | jq -r .apiKey)

<span class="c"># 2. First Cypher query</span>
curl -X POST <span class="s">https://yatabase.gftd.ai/cypher</span> \\
  -H <span class="s">"Authorization: Bearer $KEY"</span> \\
  -d '{"<span class="k">query</span>":"CREATE (n:Hello) RETURN n"}'</pre>
</article>

</div>

<p style="margin-top:32px;color:#475569;font-size:14px">
  Don't see your tool? File an issue at <a href="https://github.com/gftdcojp">github.com/gftdcojp</a> or email
  <a href="mailto:support@gftd.ai">support@gftd.ai</a>. The OpenAPI spec at
  <a href="/openapi.json">/openapi.json</a> covers every endpoint and is the canonical source for codegen.
</p>

</main>

<footer>
  <p>© 2026 etz hayim · <a href="/">yatabase.gftd.ai</a> · <a href="/docs">/docs</a> · <a href="/status">/status</a> · <a href="/.well-known/agent.json">/.well-known/agent.json</a></p>
</footer>

</body></html>`;

  return new Response(html, {
    status: 200,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "x-yatabase-surface": "integrations",
      "cache-control": "public, max-age=300, s-maxage=600",
    },
  });
}
