import { Hono } from 'hono';

type Env = {
  // Bindings will go here
};

const app = new Hono<{ Bindings: Env }>();

// Health check
app.get('/health', (c) => {
  return c.json({ status: 'ok', service: 'agentgateway' });
});

// MCP router entrypoint
app.post('/xrpc/com.etzhayyim.mcp.message', async (c) => {
  try {
    const body = await c.req.json();

    // Basic validation for JSON-RPC 2.0
    if (body.jsonrpc !== '2.0' || !body.method) {
      return c.json({
        jsonrpc: '2.0',
        id: body.id || null,
        error: {
          code: -32600,
          message: 'Invalid Request',
        }
      }, 400);
    }

    const { method, params, id } = body;

    // TODO: Implement actual routing and discovery logic
    // Currently this is a stub for the new agentgateway
    if (method === 'tools/list') {
      return c.json({
        jsonrpc: '2.0',
        id,
        result: {
          tools: [
            {
              name: 'agentgateway.ping',
              description: 'Ping the new agentgateway',
              inputSchema: {
                type: 'object',
                properties: {}
              }
            }
          ]
        }
      });
    }

    if (method === 'tools/call') {
      const toolName = params?.name;
      if (toolName === 'agentgateway.ping') {
        return c.json({
          jsonrpc: '2.0',
          id,
          result: {
            content: [{ type: 'text', text: 'pong from new agentgateway' }]
          }
        });
      }

      return c.json({
        jsonrpc: '2.0',
        id,
        error: {
          code: -32601,
          message: `Method or Tool not found: ${toolName}`,
        }
      }, 404);
    }

    // Default error for unhandled methods
    return c.json({
      jsonrpc: '2.0',
      id,
      error: {
        code: -32601,
        message: `Method not found: ${method}`,
      }
    }, 404);

  } catch (err: any) {
    return c.json({
      jsonrpc: '2.0',
      id: null,
      error: {
        code: -32700,
        message: 'Parse error',
        data: err.message
      }
    }, 500);
  }
});

export default app;
