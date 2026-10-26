import test from 'node:test';
import assert from 'node:assert/strict';
import {
  SCORE_PRODUCTION_BRIDGE_ORIGIN,
  SCORE_PRODUCTION_BRIDGE_URL,
  redeemScoreEdgeTicket,
  scoreEdgeSessionAllowed,
} from './score-production-bridge-client.mjs';

const secret = 's'.repeat(64);
const ticket = 't'.repeat(43);
const token = 'k'.repeat(43);
const env = {
  SCORE_EDGE_BRIDGE_ORIGIN: SCORE_PRODUCTION_BRIDGE_ORIGIN,
  SCORE_EDGE_SHARED_SECRET: secret,
};

function jsonResponse(status, payload, headers = {}) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'Content-Type': 'application/json', ...headers },
  });
}

test('redeem calls only the exact first-party Production bridge', async () => {
  let seen;
  const expiresAt = new Date(Date.now() + 60_000).toISOString();
  const out = await redeemScoreEdgeTicket(ticket, env, async (url, options) => {
    seen = { url, options };
    return jsonResponse(200, { allowed: true, token, path: '/en/', expiresAt });
  });
  assert.equal(seen.url, SCORE_PRODUCTION_BRIDGE_URL);
  assert.equal(seen.options.method, 'POST');
  assert.equal(seen.options.redirect, 'error');
  assert.equal(seen.options.headers['X-Score-Edge-Secret'], secret);
  assert.equal(seen.options.headers.Authorization, undefined);
  assert.equal(seen.options.headers['x-vercel-protection-bypass'], undefined);
  assert.deepEqual(JSON.parse(seen.options.body), { action: 'redeem', ticket });
  assert.equal(out.token, token);
  assert.equal(out.path, '/en/');
});

test('validate uses the same bridge and never sends Supabase credentials', async () => {
  let seen;
  const allowed = await scoreEdgeSessionAllowed(token, env, async (url, options) => {
    seen = { url, options };
    return jsonResponse(200, { allowed: true });
  });
  assert.equal(allowed, true);
  assert.equal(seen.url, SCORE_PRODUCTION_BRIDGE_URL);
  assert.deepEqual(JSON.parse(seen.options.body), { action: 'validate', token });
  assert.equal('apikey' in seen.options.headers, false);
  assert.equal('Authorization' in seen.options.headers, false);
});


test('Stage E QA bridge override is opt-in and limited to usd-impact-site Vercel deployment origins', async () => {
  let seen;
  const qaEnv = {
    ...env,
    SCORE_PRODUCTION_QA_BRIDGE_ENABLED: 'true',
    SCORE_PRODUCTION_QA_BRIDGE_ORIGIN: 'https://usd-impact-site-q1t5jg69r-usd-impact.vercel.app',
    SCORE_PRODUCTION_QA_VERCEL_BYPASS_SECRET: 'v'.repeat(32),
  };
  const allowed = await scoreEdgeSessionAllowed(token, qaEnv, async (url, options) => {
    seen = { url, options };
    return jsonResponse(200, { allowed: true });
  });
  assert.equal(allowed, true);
  assert.equal(
    seen.url,
    'https://usd-impact-site-q1t5jg69r-usd-impact.vercel.app/api/account?action=score-edge',
  );
  assert.equal(
    seen.options.headers['x-vercel-protection-bypass'],
    qaEnv.SCORE_PRODUCTION_QA_VERCEL_BYPASS_SECRET,
  );
  assert.equal(
    seen.options.headers['X-Score-Edge-Secret'],
    qaEnv.SCORE_PRODUCTION_QA_VERCEL_BYPASS_SECRET,
  );

  let calls = 0;
  const probe = async () => { calls++; return jsonResponse(200, { allowed: true }); };
  await assert.rejects(
    scoreEdgeSessionAllowed(token, {
      ...qaEnv,
      SCORE_PRODUCTION_QA_BRIDGE_ORIGIN: 'https://attacker.vercel.app',
    }, probe),
    /unavailable/,
  );
  await assert.rejects(
    scoreEdgeSessionAllowed(token, {
      ...qaEnv,
      SCORE_PRODUCTION_QA_VERCEL_BYPASS_SECRET: 'short',
    }, probe),
    /unavailable/,
  );
  assert.equal(calls, 0);
});

test('403 is a generic deny for redeem and validate', async () => {
  const deny = async () => jsonResponse(403, { allowed: false });
  assert.equal(await redeemScoreEdgeTicket(ticket, env, deny), null);
  assert.equal(await scoreEdgeSessionAllowed(token, env, deny), false);
});

test('wrong bridge origin or malformed secret fails before fetch', async () => {
  let calls = 0;
  const probe = async () => { calls++; return jsonResponse(200, { allowed: true }); };
  await assert.rejects(
    scoreEdgeSessionAllowed(token, { ...env, SCORE_EDGE_BRIDGE_ORIGIN: 'https://attacker.test' }, probe),
    /unavailable/,
  );
  await assert.rejects(
    scoreEdgeSessionAllowed(token, { ...env, SCORE_EDGE_SHARED_SECRET: 'short' }, probe),
    /unavailable/,
  );
  assert.equal(calls, 0);
});

test('redeem response is strictly bounded to valid token, path and short expiry', async () => {
  const future = new Date(Date.now() + 60_000).toISOString();
  const wrongPath = async () => jsonResponse(200, { allowed: true, token, path: '//attacker.test', expiresAt: future });
  assert.equal(await redeemScoreEdgeTicket(ticket, env, wrongPath), null);

  const longExpiry = async () => jsonResponse(200, {
    allowed: true, token, path: '/en/', expiresAt: new Date(Date.now() + 16 * 60_000).toISOString(),
  });
  assert.equal(await redeemScoreEdgeTicket(ticket, env, longExpiry), null);
});

test('oversized upstream response fails closed', async () => {
  const fetchImpl = async () => new Response('x'.repeat(3000), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
  await assert.rejects(redeemScoreEdgeTicket(ticket, env, fetchImpl), /unavailable/);
});
