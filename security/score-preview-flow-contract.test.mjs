// In-memory, credential-free contract integration for the isolated Score Preview.
// Tests real Cloudflare middleware + redemption route with a deterministic private
// backend stub. This is NOT live authenticated Preview browser acceptance.
import test from 'node:test';
import assert from 'node:assert/strict';
import { onRequest } from '../functions/_middleware.js';
import { onRequestPost } from '../functions/score-redeem.js';

const HOST = 'fix-score-membership-handoff.usd-impact-pipeline.pages.dev';
const BACKEND = 'https://preview.example.test';
const TICKET = 'T'.repeat(43);
const SESSION = 'S'.repeat(43);
const SECRET = 'x'.repeat(48);
const PREMIUM = 'PRIVATE_SCORE_BYTES_TEST_FIXTURE';

function makeFixture() {
  let membershipActive = true;
  let ticketUnused = true;
  let backendUp = true;
  let backendCalls = 0;
  let premiumReads = 0;
  const env = {
    SCORE_EDGE_GATE_ENABLED: 'true',
    SCORE_EDGE_REDEMPTION_ENABLED: 'true',
    SCORE_PREVIEW_REDEMPTION_HOST: HOST,
    SCORE_BACKEND_URL: BACKEND + '/api/score-edge-redeem',
    SCORE_VALIDATION_BACKEND_URL: BACKEND + '/api/score-edge-validate',
    SCORE_EDGE_SHARED_SECRET: SECRET,
  };

  async function backendFetch(url, options) {
    backendCalls++;
    if (!backendUp) throw new Error('Preview backend unavailable');
    assert.equal(options.method, 'POST');
    assert.equal(options.redirect, 'manual');
    assert.equal(options.headers['X-Score-Edge-Secret'], SECRET);
    assert.equal(options.headers['Content-Type'], 'application/json');
    if (url === BACKEND + '/api/score-edge-redeem') {
      const { ticket } = JSON.parse(options.body);
      if (ticket !== TICKET || !ticketUnused || !membershipActive) {
        return Response.json({ allowed: false }, { status: 403 });
      }
      ticketUnused = false;
      return Response.json({
        allowed: true, token: SESSION, path: '/en/',
        expiresAtMs: Date.now() + 10 * 60_000,
      });
    }
    if (url === BACKEND + '/api/score-edge-validate') {
      const { token } = JSON.parse(options.body);
      return Response.json({ allowed: membershipActive && token === SESSION }, {
        status: membershipActive && token === SESSION ? 200 : 403,
      });
    }
    throw new Error('Unexpected cross-service endpoint');
  }

  async function request(path, { method = 'GET', cookie = '', ticket = TICKET,
    host = HOST, alternateEnv = {} } = {}) {
    const headers = {};
    if (cookie) headers.cookie = cookie;
    if (method === 'POST') headers['Content-Type'] = 'application/x-www-form-urlencoded';
    const req = new Request('https://' + host + path, {
      method, headers,
      ...(method === 'POST' ? { body: new URLSearchParams({ ticket }) } : {}),
    });
    const activeEnv = { ...env, ...alternateEnv };
    return onRequest({
      request: req, env: activeEnv,
      next: async () => {
        if (path === '/score-redeem') {
          return onRequestPost({ request: req, env: activeEnv });
        }
        premiumReads++;
        return new Response(PREMIUM, { status: 200 });
      },
    });
  }
  return {
    request, backendFetch, get premiumReads() { return premiumReads; },
    get backendCalls() { return backendCalls; },
    revoke() { membershipActive = false; },
    backendDown() { backendUp = false; },
  };
}

test('anonymous Preview is denied before serving premium bytes, public methodology remains public', async () => {
  const f = makeFixture();
  for (const path of ['/en/', '/archive/en/', '/en/index.html', '/secret.js']) {
    const r = await f.request(path);
    assert.equal(r.status, 403);
    assert.equal((await r.text()).includes(PREMIUM), false);
    assert.equal(r.headers.get('Cache-Control'), 'private, no-store');
  }
  assert.equal(f.premiumReads, 0);
  assert.equal(f.backendCalls, 0);
  const approved = await f.request('/data/score_v2_methodology.json');
  assert.equal(approved.status, 200);
  assert.equal(f.premiumReads, 1, 'public approved methodology follows the public static path');
});

test('single-use POST redemption issues a secure short-lived cookie; next request revalidates membership', async (t) => {
  const f = makeFixture();
  const oldFetch = globalThis.fetch;
  globalThis.fetch = f.backendFetch;
  t.after(() => { globalThis.fetch = oldFetch; });

  const response = await f.request('/score-redeem', { method: 'POST' });
  assert.equal(response.status, 303);
  assert.equal(response.headers.get('Location'), '/en/');
  assert.equal(response.headers.get('Cache-Control'), 'no-store');
  assert.equal(response.headers.get('Referrer-Policy'), 'no-referrer');
  const setCookie = response.headers.get('Set-Cookie');
  assert.match(setCookie, /^__Host-score_session=/);
  for (const attr of ['Secure', 'HttpOnly', 'SameSite=Lax', 'Path=/']) {
    assert.ok(setCookie.includes(attr), attr);
  }
  assert.equal(response.headers.get('Location').includes(TICKET), false);
  assert.equal(setCookie.includes(TICKET), false, 'handoff ticket must not become the session cookie');
  const cookie = setCookie.split(';')[0];

  const premium = await f.request('/en/', { cookie });
  assert.equal(premium.status, 200);
  assert.equal(await premium.text(), PREMIUM);
  assert.equal(premium.headers.get('Cache-Control'), 'private, no-store');
  assert.equal(premium.headers.get('X-Robots-Tag'), 'noindex, nofollow');
  assert.equal(f.premiumReads, 1);

  const replay = await f.request('/score-redeem', { method: 'POST' });
  assert.equal(replay.status, 403);
  assert.equal(replay.headers.get('Set-Cookie'), null);
  assert.equal(replay.headers.get('Location'), null);
  assert.equal(f.premiumReads, 1);

  f.revoke();
  const revoked = await f.request('/en/', { cookie });
  assert.equal(revoked.status, 403);
  assert.equal((await revoked.text()).includes(PREMIUM), false);
  assert.equal(f.premiumReads, 1);
});

test('missing flags, unknown preview host, invalid tickets and private backend outage fail closed', async (t) => {
  const f = makeFixture();
  const originalFetch = globalThis.fetch;
  globalThis.fetch = f.backendFetch;
  t.after(() => { globalThis.fetch = originalFetch; });

  const disabled = await f.request('/en/', {
    cookie: '__Host-score_session=' + SESSION, alternateEnv: { SCORE_EDGE_GATE_ENABLED: 'false' },
  });
  assert.equal(disabled.status, 403);
  assert.equal((await disabled.text()).includes(PREMIUM), false);

  const noPreviewPin = await f.request('/score-redeem', {
    method: 'POST', alternateEnv: { SCORE_PREVIEW_REDEMPTION_HOST: '' },
  });
  assert.equal(noPreviewPin.status, 403);
  const wrongHost = await f.request('/score-redeem', {
    method: 'POST', host: 'unapproved.usd-impact-pipeline.pages.dev',
  });
  assert.equal(wrongHost.status, 403);

  const badTicket = await f.request('/score-redeem', { method: 'POST', ticket: 'invalid' });
  assert.equal(badTicket.status, 400);
  assert.equal(badTicket.headers.get('Set-Cookie'), null);

  f.backendDown();
  const redeemOutage = await f.request('/score-redeem', { method: 'POST' });
  assert.equal(redeemOutage.status, 503);
  assert.equal(redeemOutage.headers.get('Set-Cookie'), null);
  const validationOutage = await f.request('/en/', { cookie: '__Host-score_session=' + SESSION });
  assert.equal(validationOutage.status, 403);
  assert.equal(f.premiumReads, 0);
});
