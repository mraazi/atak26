// billplz-worker.js
// Cloudflare Worker — CORS proxy for Billplz API
//
// DEPLOY STEPS:
//   1. npm i -g wrangler
//   2. wrangler login
//   3. wrangler deploy billplz-worker.js --name billplz-proxy
//   4. wrangler secret put BILLPLZ_API_KEY
//      → enter your key: S-pSRtKJx9shBNtW8EnJPsUg
//   5. Copy the Worker URL shown after deploy
//      (e.g. https://billplz-proxy.yourname.workers.dev)
//   6. In ATAK app → Admin → CMS → ⚙ Tetapan → paste URL → Simpan

export default {
  async fetch(request, env) {
    const cors = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    // Preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: cors });
    }

    const url = new URL(request.url);
    const billplzBase = 'https://www.billplz.com/api/v3';
    const target = billplzBase + url.pathname + url.search;

    const apiKey = env.BILLPLZ_API_KEY || '';
    if (!apiKey) {
      return new Response(
        JSON.stringify({ error: 'BILLPLZ_API_KEY secret not configured' }),
        { status: 500, headers: { ...cors, 'Content-Type': 'application/json' } },
      );
    }

    const auth = 'Basic ' + btoa(apiKey + ':');

    let body = undefined;
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      body = await request.arrayBuffer();
    }

    const upstream = await fetch(target, {
      method: request.method,
      headers: {
        'Authorization': auth,
        'Content-Type': request.headers.get('Content-Type') || 'application/x-www-form-urlencoded',
      },
      body,
    });

    const text = await upstream.text();
    return new Response(text, {
      status: upstream.status,
      headers: { ...cors, 'Content-Type': 'application/json' },
    });
  },
};
