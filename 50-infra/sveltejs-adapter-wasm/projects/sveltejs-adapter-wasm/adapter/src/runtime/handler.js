// @ts-ignore
import { Server } from '$server';
// @ts-ignore
import { manifest } from '$manifest';

const server = new Server(manifest);

/**
 * WASI HTTP Incoming Handler
 * @param {import('./types').IncomingRequest} request
 * @param {import('./types').ResponseOutparam} responseOut
 */
export async function handle(request, responseOut) {
    try {
        // Convert WASI request to SvelteKit Request
        // Note: In a real Javy environment, we need to map WASI types to standard Web Request
        const url = new URL(request.pathWithQuery() || '/', `http://${request.headers().get('host') || 'localhost'}`);
        
        const skRequest = new Request(url, {
            method: request.method(),
            headers: new Headers(request.headers())
        });

        const response = await server.respond(skRequest, {
            getClientAddress() {
                return skRequest.headers.get('x-forwarded-for') || '127.0.0.1';
            }
        });

        // Map SvelteKit Response back to WASI OutgoingResponse
        // This is a simplified version; real Javy might have specific APIs
        responseOut.set(response);
    } catch (e) {
        console.error(e);
    }
}
