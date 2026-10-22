// Full Cloudflare middleware + Pages Function Preview flow using an in-memory
// mock of the existing Development Supabase RPCs. NO live user or DB changes.
import test from 'node:test';
import assert from 'node:assert/strict';
import { onRequest } from '../functions/_middleware.js';
import { onRequestPost } from '../functions/score-redeem.js';
import {
  SCORE_DIRECT_PREVIEW_HOST, SCORE_DIRECT_WEBSITE_ORIGIN,
} from './score-preview-dev-rpc.mjs';

const ticket = 'T'.repeat(43);
const devAccount = '11111111-1111-4111-8111-111111111111';
const developmentKey = 'sb_secret_' + 'M'.repeat(32);
const premiumHtml = 'ONLY_RESEARCH_MEMBERS_MAY_READ';
const expectedRpcPrefix = 'https://ycstrcvshdluovtuasjc.supabase.co/rest/v1/rpc/';

function fixture() {
  let ticketPending = true;
  let activeMembership = true;
  let sessionDigest = null;
  let premiumReads = 0;
  const rpcCalls = [];
  const env = {
    SCORE_DIRECT_DEV_BACKEND_ENABLED: 'true',
    SCORE_PREVIEW_SUPABASE_SECRET_KEY: developmentKey,
    SCORE_EDGE_GATE_ENABLED: 'true',
    SCORE_EDGE_REDEMPTION_ENABLED: 'true',
    SCORE_PREVIEW_REDEMPTION_HOST: SCORE_DIRECT_PREVIEW_HOST,
    // An unrelated, inaccessible Vercel backend must not be called.
    SCORE_BACKEND_URL: 'https://not-an-allowed-vercel-host.test/api/score-edge-redeem',
    SCORE_VALIDATION_BACKEND_URL: 'https://not-an-allowed-vercel-host.test/api/score-edge-validate',
    SCORE_EDGE_SHARED_SECRET: 'x'.repeat(48),
  };
  async function mockedFetch(url, options) {
    rpcCalls.push(url);
    assert.ok(url.startsWith(expectedRpcPrefix), 'Never call Vercel or arbitrary external URLs');
    assert.equal(options.headers.apikey, developmentKey);
    assert.equal(options.headers.Authorization, undefined);
    assert.equal(options.redirect, 'error');
    const kind = url.slice(expectedRpcPrefix.length);
    const input = JSON.parse(options.body);
    if (kind === 'score_ticket_consume_atomic') {
      if (!ticketPending) return Response.json(null);
      ticketPending = false;
      return Response.json({
        digest: input.p_digest, account_id: devAccount,
        audience: 'score.usd-impact.com', path: '/en/',
        expires_at: new Date(Date.now() + 40_000).toISOString(),
      });
    }
    if (kind === 'score_membership_active') return Response.json(activeMembership);
    if (kind === 'score_session_create') {
      if (!activeMembership) return Response.json(false);
      sessionDigest = input.p_digest;
      return Response.json(true);
    }
    if (kind === 'score_session_lookup') {
      return Response.json(activeMembership && input.p_digest === sessionDigest ?
        { account_id: devAccount, expires_at: new Date(Date.now() + 11 * 60_000).toISOString() } : null);
    }
    throw Error('Unexpected RPC name');
  }
  async function request(path, options = {}) {
    const method = options.method || 'GET';
    const headers = {};
    if (options.cookie) headers.cookie = options.cookie;
    if (method === 'POST') {
      headers['Content-Type'] = 'application/x-www-form-urlencoded';
      if (options.origin !== undefined) headers.Origin = options.origin;
    }
    const req = new Request('https://' + (options.host || SCORE_DIRECT_PREVIEW_HOST) + path, {
      method, headers, ...(method === 'POST' ? {
        body: new URLSearchParams({ ticket: options.ticket ?? ticket }),
      } : {}),
    });
    const chosenEnv = { ...env, ...options.override };
    return onRequest({
      request: req,
      env: chosenEnv,
      next() {
        if (path === '/score-redeem') return onRequestPost({ request: req, env: chosenEnv });
        if (path === '/data/score_v2_methodology.json') {
          return new Response('PUBLIC_METHOD', { status: 200 });
        }
        premiumReads++;
        return new Response(premiumHtml, { status: 200 });
      },
    });
  }
  return {
    mockedFetch, request, rpcCalls,
    get premiumReads() { return premiumReads; },
    revoke() { activeMembership = false; },
  };
}

test('direct Preview flow: one-use POST, secure cookie, every-request membership checks, revocation', async (t) => {
  const f=fixture();
  const originalFetch=globalThis.fetch;
  globalThis.fetch=f.mockedFetch;
  t.after(()=>{ globalThis.fetch=originalFetch; });
  const denied=await f.request('/en/');
  assert.equal(denied.status,403);
  assert.equal(f.premiumReads,0);
  const approved=await f.request('/data/score_v2_methodology.json');
  assert.equal(approved.status,200);
  assert.equal(await approved.text(),'PUBLIC_METHOD');

  const redeemed=await f.request('/score-redeem',{
    method:'POST',origin:SCORE_DIRECT_WEBSITE_ORIGIN,
  });
  assert.equal(redeemed.status,303);
  assert.equal(redeemed.headers.get('Location'),'/en/');
  assert.equal(redeemed.headers.get('Cache-Control'),'no-store');
  const setCookie=redeemed.headers.get('Set-Cookie');
  assert.match(setCookie,/^__Host-score_session=[A-Za-z0-9_-]{43};/);
  for(const required of ['Secure','HttpOnly','SameSite=Lax','Path=/']) {
    assert.ok(setCookie.includes(required));
  }
  assert.ok(!setCookie.includes(ticket));
  const cookie=setCookie.split(';')[0];
  assert.ok(f.rpcCalls.length===3);
  const content=await f.request('/en/',{cookie});
  assert.equal(content.status,200);
  assert.equal(await content.text(),premiumHtml);
  assert.equal(content.headers.get('Cache-Control'),'private, no-store');
  assert.equal(f.premiumReads,1);
  assert.equal((await f.request('/archive/en/',{cookie})).status,200);
  assert.equal(f.premiumReads,2);

  const replay=await f.request('/score-redeem',{method:'POST',origin:SCORE_DIRECT_WEBSITE_ORIGIN});
  assert.equal(replay.status,403);
  assert.equal(replay.headers.get('Set-Cookie'),null);
  f.revoke();
  const revoked=await f.request('/en/',{cookie});
  assert.equal(revoked.status,403);
  assert.doesNotMatch(await revoked.text(),/ONLY_RESEARCH_MEMBERS_MAY_READ/);
  assert.equal(f.premiumReads,2);
});

test('ticket injection, invalid preview host, production and disabled flags fail closed',async(t)=>{
  const f=fixture();
  const oldFetch=globalThis.fetch;
  globalThis.fetch=f.mockedFetch;
  t.after(()=>{globalThis.fetch=oldFetch;});
  const rejectOrigin=await f.request('/score-redeem',{
    method:'POST',origin:'https://evil.test',
  });
  assert.equal(rejectOrigin.status,403);
  assert.equal((await f.request('/score-redeem',{method:'POST'})).status,403,'no Origin is not allowed');
  assert.equal(f.rpcCalls.length,0);
  assert.equal((await f.request('/score-redeem',{
    method:'POST',origin:SCORE_DIRECT_WEBSITE_ORIGIN,
    host:'score.usd-impact.com',
  })).status,403,'production domain cannot use Development backend');
  assert.equal((await f.request('/score-redeem',{
    method:'POST',origin:SCORE_DIRECT_WEBSITE_ORIGIN,
    host:'other.usd-impact-pipeline.pages.dev',
  })).status,403,'unlisted Pages hosts are denied');
  assert.equal((await f.request('/score-redeem',{
    method:'POST',origin:SCORE_DIRECT_WEBSITE_ORIGIN,
    override:{SCORE_EDGE_REDEMPTION_ENABLED:'false'},
  })).status,503);
  assert.equal((await f.request('/en/',{
    cookie:'__Host-score_session='+'S'.repeat(43),
    override:{SCORE_EDGE_GATE_ENABLED:'false'},
  })).status,403);
  assert.equal(f.premiumReads,0);
  assert.equal(f.rpcCalls.length,0);
});

test('missing Development secret or RPC outage never grants a Preview session',async(t)=>{
  const f=fixture();
  const oldFetch=globalThis.fetch;
  globalThis.fetch=f.mockedFetch;
  t.after(()=>{globalThis.fetch=oldFetch;});
  const badKey=await f.request('/score-redeem',{
    method:'POST',origin:SCORE_DIRECT_WEBSITE_ORIGIN,
    override:{SCORE_PREVIEW_SUPABASE_SECRET_KEY:'sk_live_bad'},
  });
  assert.equal(badKey.status,503);
  assert.equal(badKey.headers.get('Set-Cookie'),null);
  assert.equal(f.rpcCalls.length,0);
  globalThis.fetch=async()=>{throw Error('network unreachable')};
  const outage=await f.request('/score-redeem',{
    method:'POST',origin:SCORE_DIRECT_WEBSITE_ORIGIN,
  });
  assert.equal(outage.status,503);
  assert.equal(outage.headers.get('Set-Cookie'),null);
  assert.equal((await f.request('/en/',{cookie:'__Host-score_session='+'S'.repeat(43)})).status,403);
  assert.equal(f.premiumReads,0);
});
