import http from 'node:http';
import { handlePaymentIntent, handleCapture, handleRefund } from './stripe-compat/handler.js';
import { handleIso8583Auth } from './iso8583/handler.js';
import { handleNfcTap } from './nfc/handler.js';
import { MemorySubstrate } from './common/memory-substrate.js';
import { InMemoryIdempotencyStore } from './common/idempotency.js';

function readJsonBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => { body += chunk.toString(); });
    req.on('end', () => {
      if (!body) return resolve({});
      try {
        resolve(JSON.parse(body));
      } catch (e) {
        reject(new Error('Malformed JSON'));
      }
    });
    req.on('error', reject);
  });
}

function sendJson(res, statusCode, body) {
  res.writeHead(statusCode, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(body));
}

export function createServer(deps) {
  return http.createServer(async (req, res) => {
    if (req.method !== 'POST') {
      return sendJson(res, 404, { error: 'Not Found' });
    }

    try {
      const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
      const path = url.pathname;

      let body = {};
      try {
        body = await readJsonBody(req);
      } catch (e) {
        return sendJson(res, 400, { error: 'Malformed JSON' });
      }

      const idempotencyKey = req.headers['idempotency-key'] || body.idempotencyKey;

      if (path === '/v1/payment_intents') {
        const result = await handlePaymentIntent(body, idempotencyKey, deps);
        return sendJson(res, result.httpStatus, result.body);
      }

      const captureMatch = path.match(/^\/v1\/payment_intents\/([^/]+)\/capture$/);
      if (captureMatch) {
        const id = captureMatch[1];
        const result = await handleCapture(id, idempotencyKey, deps);
        return sendJson(res, result.httpStatus, result.body);
      }

      if (path === '/v1/refunds') {
        const result = await handleRefund(body, idempotencyKey, deps);
        return sendJson(res, result.httpStatus, result.body);
      }

      if (path === '/iso8583/auth') {
        const result = await handleIso8583Auth(body, deps, () => body.merchant_did);
        return sendJson(res, 200, result);
      }

      if (path === '/nfc/tap') {
        const result = await handleNfcTap(body, deps);
        return sendJson(res, 200, result);
      }

      return sendJson(res, 404, { error: 'Not Found' });
    } catch (e) {
      return sendJson(res, 500, { error: e.message || 'Internal Server Error' });
    }
  });
}

// PRODUCTION injects an @etzhayyim/sdk-backed substrate (ADR-2605231525: gateway holds NO private key).
export function devServer() {
  const substrate = new MemorySubstrate();
  const idemStore = new InMemoryIdempotencyStore();
  return createServer({ substrate, idemStore });
}
