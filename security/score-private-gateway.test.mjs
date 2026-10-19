import test from 'node:test';
import assert from 'node:assert/strict';
import { onRequest } from '../functions/_middleware.js';

const token = 'a'.repeat(43);
function ctx(path = '/en/', options = {}) {
  let calls = 0;
  return {
    request: new Request('https://score.usd-impact.com' + path, {
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
