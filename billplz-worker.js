/**
 * Cloudflare Worker — Billplz API Proxy
 *
 * Proxies requests from the browser to Billplz API, adding:
 *   - Basic Auth using BILLPLZ_API_KEY secret (never exposed to browser)
 *   - CORS headers so GitHub Pages can call this Worker
 *
 * Supported routes:
 *   POST   /bills                    → create a bill
 *   GET    /bills/:id                → get bill status
 *   GET    /collections/:id          → validate collection ID (test connection)
 *
 * Environment variables (set as Worker Secrets in Cloudflare dashboard):
 *   BILLPLZ_API_KEY   — your Billplz API key (e.g. S-pSRtKJx9shBNtW8EnJPsUg)
 *
 * Deployment:
 *   1. Go to https://dash.cloudflare.com → Workers & Pages → Create Worker
 *   2. Paste this file content → Deploy
 *   3. Go to Worker Settings → Variables → Add Secret: BILLPLZ_API_KEY
 *   4. Copy your Worker URL (e.g. https://billplz-proxy.yourname.workers.dev)
 *   5. Paste the Worker URL into the LMS Billplz Settings modal
 */

const BILLPLZ_BASE = 'https://www.billplz.com/api/v3';
const ALLOWED_ORIGIN = 'https://mraazi.github.io';

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': ALLOWED_ORIGIN,
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

export default {
  async fetch(request, env) {
    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    // Only allow GET and POST
    if (!['GET', 'POST'].includes(request.method)) {
      return json({ error: 'Method not allowed' }, 405);
    }

    // Validate API key is configured
    if (!env.BILLPLZ_API_KEY) {
      return json({ error: 'BILLPLZ_API_KEY secret not set in Worker environment' }, 500);
    }

    const url = new URL(request.url);
    const path = url.pathname; // e.g. /bills, /bills/abc123, /collections/abc123

    // Only allow safe Billplz endpoints
    const allowed = /^\/(bills(\/[^\/]+)?|collections\/[^\/]+)$/;
    if (!allowed.test(path)) {
      return json({ error: 'Endpoint not allowed' }, 403);
    }

    const billplzUrl = BILLPLZ_BASE + path;
    const authHeader = 'Basic ' + btoa(env.BILLPLZ_API_KEY + ':');

    let billplzResp;
    try {
      billplzResp = await fetch(billplzUrl, {
        method: request.method,
        headers: {
          'Authorization': authHeader,
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: request.method === 'POST' ? await request.text() : undefined,
      });
    } catch (e) {
      return json({ error: 'Failed to reach Billplz: ' + e.message }, 502);
    }

    const responseText = await billplzResp.text();

    return new Response(responseText, {
      status: billplzResp.status,
      headers: {
        ...CORS_HEADERS,
        'Content-Type': 'application/json',
      },
    });
  },
};

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
  });
}
