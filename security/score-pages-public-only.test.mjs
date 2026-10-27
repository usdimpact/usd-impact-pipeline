import test from 'node:test';
import assert from 'node:assert/strict';
import { onRequest } from '../functions/_middleware.js';

function context(path, {
  method = 'GET',
  host = 'usd-impact-pipeline.pages.dev',
  headers = {},
  env = {},
} = {}) {
  let nextCalls = 0;
  return {
    request: new Request('https://' + host + path, { method, headers }),
    env,
    next: async () => {
      nextCalls += 1;
      return new Response('public asset', { status: 200 });
    },
    get nextCalls() { return nextCalls; },
  };
}

test('premium HTML is denied even with legacy cookies, secrets, and enable flags', async () => {
  const legacy = {
    SCORE_EDGE_GATE_ENABLED: 'true',
    SCORE_EDGE_REDEMPTION_ENABLED: 'true',
    SCORE_DEV_BROKER_ENABLED: 'true',
    SCORE_EDGE_SHARED_SECRET: 'x'.repeat(64),
  };
  for (const path of [
    '/', '/en/', '/es/', '/en/index.html', '/es/index.html',
    '/archive/en/', '/archive/es/',
    '/archive/2026-10-16/en.html', '/archive/2026-10-16/es.html',
    '/private.html', '/hidden',
  ]) {
    const ctx = context(path, {
      headers: { cookie: '__Host-score_session=' + 'a'.repeat(43) },
      env: legacy,
    });
    const response = await onRequest(ctx);
    assert.equal(response.status, 403, path);
    assert.equal(ctx.nextCalls, 0, path);
    assert.equal(response.headers.get('Set-Cookie'), null);
    assert.equal(response.headers.get('Cache-Control'), 'private, no-store');
    assert.match(await response.text(), /usd-impact\.com\/score\//);
  }
});

test('only explicit public methodology, research, and reproduction assets pass through', async () => {
  for (const path of [
    '/member-required.html',
    '/robots.txt',
    '/favicon.ico',
    '/data/score_v2_methodology.json',
    '/data/score_v2_methodology.schema.json',
    '/data/usd_impact_score_v2.csv',
    '/data/weekly_input_latest.json',
    '/data/research/score_v2_vintage_comparison_latest.html',
    '/data/research/independent_replication_protocol.json',
    '/archive/2026-10-16/weekly_input.json',
    '/archive/2026-10-16/score.json',
    '/archive/2026-10-16/repro_bundle.json',
  ]) {
    const ctx = context(path);
    const response = await onRequest(ctx);
    assert.equal(response.status, 200, path);
    assert.equal(ctx.nextCalls, 1, path);
  }
});

test('retired redemption endpoint is gone and never reaches an asset or backend', async () => {
  for (const method of ['GET', 'POST']) {
    const ctx = context('/score-redeem', {
      method,
      headers: method === 'POST'
        ? { 'content-type': 'application/x-www-form-urlencoded' }
        : {},
      env: {
        SCORE_EDGE_REDEMPTION_ENABLED: 'true',
        SCORE_EDGE_SHARED_SECRET: 'x'.repeat(64),
      },
    });
    const response = await onRequest(ctx);
    assert.equal(response.status, 410);
    assert.equal(ctx.nextCalls, 0);
    assert.equal(response.headers.get('Set-Cookie'), null);
  }
});

test('write methods cannot reach public assets', async () => {
  const ctx = context('/data/score_v2_methodology.json', { method: 'POST' });
  const response = await onRequest(ctx);
  assert.equal(response.status, 405);
  assert.equal(response.headers.get('Allow'), 'GET, HEAD');
  assert.equal(ctx.nextCalls, 0);
});

test('branded and preview Pages hosts use the same public-only policy', async () => {
  for (const host of [
    'score.usd-impact.com',
    'fix-score-membership-handoff-147.usd-impact-pipeline.pages.dev',
  ]) {
    const publicCtx = context('/data/score_v2_methodology.json', { host });
    assert.equal((await onRequest(publicCtx)).status, 200);
    assert.equal(publicCtx.nextCalls, 1);

    const premiumCtx = context('/en/', { host });
    assert.equal((await onRequest(premiumCtx)).status, 403);
    assert.equal(premiumCtx.nextCalls, 0);
  }
});

test('unrelated hosts cannot use the middleware as an open public proxy', async () => {
  const ctx = context('/data/score_v2_methodology.json', { host: 'attacker.example' });
  assert.equal((await onRequest(ctx)).status, 403);
  assert.equal(ctx.nextCalls, 0);
});
