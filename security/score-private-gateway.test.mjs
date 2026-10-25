import test from 'node:test';
import assert from 'node:assert/strict';
import { onRequest } from '../functions/_middleware.js';

const token = 'a'.repeat(43);
function ctx(path = '/en/', options = {}) {
  let calls = 0;
  return {
    request: new Request('https://usd-impact-pipeline.pages.dev' + path, {
      method: options.method || 'GET',
      headers: options.cookie ? { cookie: '__Host-score_session=' + options.cookie } : {},
    }),
    env: {
      SCORE_EDGE_GATE_ENABLED: options.enabled === false ? 'false' : 'true',
      SCORE_VALIDATION_BACKEND_URL: 'https://www.usd-impact.com/api/score-edge-validate',
      SCORE_EDGE_SHARED_SECRET: 'x'.repeat(48),
    },
    next: async () => { calls++; return new Response('premium content'); },
    get calls() { return calls; },
  };
}
test('feature disabled denies without invoking backend', async () => {
  const c = ctx('/en/', { enabled: false, cookie: token });
  assert.equal((await onRequest(c)).status, 403);
  assert.equal(c.calls, 0);
});
test('missing cookie denied', async () => {
  const c = ctx();
  assert.equal((await onRequest(c)).status, 403);
  assert.equal(c.calls, 0);
});
test('redemption POST is routed independently', async () => {
  const c = ctx('/score-redeem', { method: 'POST' });
  assert.equal((await onRequest(c)).status, 200);
  assert.equal(c.calls, 1);
});
test('invalid validation backend denies', async () => {
  const c = ctx('/en/', { cookie: token });
  c.env.SCORE_VALIDATION_BACKEND_URL = 'http://example.test/api/score-edge-validate';
  assert.equal((await onRequest(c)).status, 403);
});

test('verified backend permits premium content without caching', async (t) => {
  const c = ctx('/en/', { cookie: token });
  const originalFetch = globalThis.fetch;
  let requests = 0;
  t.after(() => { globalThis.fetch = originalFetch; });
  globalThis.fetch = async (url, options) => {
    requests++;
    assert.equal(url, 'https://www.usd-impact.com/api/score-edge-validate');
    assert.equal(options.method, 'POST');
    assert.equal(options.redirect, 'manual');
    assert.equal(options.headers['X-Score-Edge-Secret'], 'x'.repeat(48));
    assert.deepEqual(JSON.parse(options.body), { token });
    return Response.json({ allowed: true });
  };
  const response = await onRequest(c);
  assert.equal(response.status, 200);
  assert.equal(await response.text(), 'premium content');
  assert.equal(response.headers.get('Cache-Control'), 'private, no-store');
  assert.equal(response.headers.get('X-Robots-Tag'), 'noindex, nofollow');
  assert.equal(c.calls, 1);
  assert.equal(requests, 1);
});

test('backend membership denial blocks premium content', async (t) => {
  const c = ctx('/en/', { cookie: token });
  const originalFetch = globalThis.fetch;
  t.after(() => { globalThis.fetch = originalFetch; });
  globalThis.fetch = async () => Response.json({ allowed: false });
  const response = await onRequest(c);
  assert.equal(response.status, 403);
  assert.equal(c.calls, 0);
});


test('invalid or stale Preview validation hosts are blocked before forwarding the shared secret', async (t) => {
  const originalFetch = globalThis.fetch;
  t.after(() => { globalThis.fetch = originalFetch; });
  let calls = 0;
  globalThis.fetch = async () => { calls++; throw Error('must not fetch attacker endpoint'); };
  for (const url of [
    'https://evil.example.test/api/score-edge-validate',
    'https://usd-impact-site-8lvzao44t-usd-impact.vercel.app/api/score-edge-validate',
    'https://www.usd-impact.com/api/score-edge-validate?next=evil',
  ]) {
    const c = ctx('/en/', { cookie: token });
    c.env.SCORE_VALIDATION_BACKEND_URL = url;
    assert.equal((await onRequest(c)).status, 403);
    assert.equal(c.calls, 0);
  }
  assert.equal(calls, 0);
});


test('isolated Production-service Preview requires exact pinned Pages host', async () => {
  const exact = 'fix-score-membership-handoff-147.usd-impact-pipeline.pages.dev';
  let calls = 0;
  const make = (host) => ({
    request: new Request('https://' + host + '/en/'),
    env: {
      SCORE_PRODUCTION_SERVICE_PREVIEW_ENABLED: 'true',
      SCORE_PREVIEW_REDEMPTION_HOST: exact,
      SCORE_PRODUCTION_WORKER: {
        fetch: async (request) => {
          calls++;
          assert.equal(new URL(request.url).origin, 'https://score.usd-impact.com');
          return new Response('production-worker-preview');
        },
      },
    },
    next: async () => new Response('must not reach Pages asset'),
  });
  assert.equal((await onRequest(make('other.usd-impact-pipeline.pages.dev'))).status, 403);
  const response = await onRequest(make(exact));
  assert.equal(response.status, 200);
  assert.equal(await response.text(), 'production-worker-preview');
  assert.equal(calls, 1);
});

test('isolated Production-service Preview fails closed when service binding is absent', async () => {
  const exact = 'fix-score-membership-handoff-147.usd-impact-pipeline.pages.dev';
  const c = {
    request: new Request('https://' + exact + '/en/'),
    env: {
      SCORE_PRODUCTION_SERVICE_PREVIEW_ENABLED: 'true',
      SCORE_PREVIEW_REDEMPTION_HOST: exact,
    },
    next: async () => new Response('must not reach Pages asset'),
  };
  const response = await onRequest(c);
  assert.equal(response.status, 503);
  assert.equal(await response.text(), 'Score unavailable');
});
