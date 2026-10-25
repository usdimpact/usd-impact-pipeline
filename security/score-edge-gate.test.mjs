import test from 'node:test';
import assert from 'node:assert/strict';
import { onRequest } from '../functions/_middleware.js';

function context(path, method = 'GET') {
  let nextCalls = 0;
  return {
    request: new Request('https://score.usd-impact.com' + path, { method }),
    env: {},
    next: async () => { nextCalls++; return new Response('public'); },
    get nextCalls() { return nextCalls; },
  };
}
test('premium language routes denied without verified session', async () => {
  for (const path of ['/', '/en/', '/es/', '/en/index.html', '/es/index.html']) {
    const ctx = context(path);
    const response = await onRequest(ctx);
    assert.equal(response.status, 403, path);
    assert.equal(ctx.nextCalls, 0);
    assert.equal(response.headers.get('Cache-Control'), 'private, no-store');
  }
});
test('archive and direct HTML bypass attempts denied', async () => {
  for (const path of ['/archive/en/', '/archive/es/2026/index.html', '/private.html',
    '/report.json', '/script.js', '/hidden', '/en/%2e%2e/secret']) {
    const ctx = context(path);
    assert.equal((await onRequest(ctx)).status, 403, path);
    assert.equal(ctx.nextCalls, 0);
  }
});
test('only explicit public paths pass through', async () => {
  for (const path of ['/member-required.html', '/robots.txt', '/favicon.ico']) {
    const ctx = context(path);
    assert.equal((await onRequest(ctx)).status, 200);
    assert.equal(ctx.nextCalls, 1);
  }
});
test('published methodology and research data remain readable without membership', async () => {
  for (const path of [
    '/data/score_v2_methodology.json',
    '/data/score_v2_methodology.schema.json',
    '/data/usd_impact_score_v2.csv',
    '/data/weekly_input_latest.json',
    '/data/research/score_v2_vintage_comparison_latest.html',
    '/data/research/score_v2_vintage_comparison_latest',
    '/data/research/independent_replication_protocol.json',
    '/archive/2026-10-16/weekly_input.json',
    '/archive/2026-10-16/score.json',
    '/archive/2026-10-16/repro_bundle.json',
    '/member-required',
  ]) {
    const ctx = context(path);
    assert.equal((await onRequest(ctx)).status, 200, path);
    assert.equal(ctx.nextCalls, 1, path);
  }
});
test('an unpublished file or member archive cannot bypass the gate', async () => {
  for (const path of [
    '/data/secret.json',
    '/data/research/not-reviewed.html',
    '/data/research/score_v2_vintage_comparison_latest.html/extra',
    '/archive/en/',
    '/archive/2026-10-16/en.html',
    '/archive/2026-10-16/es.html',
    '/archive/2026-10-16/private.json',
    '/archive/2026-10-16/weekly_input.json/extra',
  ]) {
    const ctx = context(path);
    assert.equal((await onRequest(ctx)).status, 403, path);
    assert.equal(ctx.nextCalls, 0, path);
  }
});
test('POST requests cannot pass to assets', async () => {
  const ctx = context('/en/', 'POST');
  assert.equal((await onRequest(ctx)).status, 405);
  assert.equal(ctx.nextCalls, 0);
});
test('feature flag alone never grants access', async () => {
  const ctx = context('/en/');
  ctx.env.SCORE_HANDOFF_ISSUANCE_ENABLED = 'true';
  assert.equal((await onRequest(ctx)).status, 403);
});

test('denied premium requests provide safe recovery without granting access', async () => {
  for (const path of ['/en/', '/archive/en/', '/hidden.html']) {
    const ctx = context(path);
    const response = await onRequest(ctx);
    assert.equal(response.status, 403);
    assert.equal(ctx.nextCalls, 0);
    assert.equal(response.headers.get('Content-Type'), 'text/html; charset=utf-8');
    assert.equal(response.headers.get('Cache-Control'), 'private, no-store');
    assert.equal(response.headers.get('Referrer-Policy'), 'no-referrer');
    assert.equal(response.headers.get('Set-Cookie'), null);
    assert.match(response.headers.get('Content-Security-Policy'), /default-src 'none'/);
    const html = await response.text();
    assert.match(html, /href="https:\/\/www\.usd-impact\.com\/score\/"/);
    assert.match(html, /Research Membership required/);
    assert.doesNotMatch(html, /<script|javascript:|(?:ticket|access_token|refresh_token)=/i);
  }
});


test('Production hostname requires private Worker service binding and fails closed when missing', async () => {
  const ctx = context('/data/score_v2_methodology.json');
  const response = await onRequest(ctx);
  assert.equal(response.status, 503);
  assert.equal(ctx.nextCalls, 0);
  assert.equal(await response.text(), 'Score unavailable');
});

test('Production hostname delegates every request to private Worker service binding', async () => {
  let calls = 0;
  const ctx = context('/data/score_v2_methodology.json');
  ctx.env.SCORE_PRODUCTION_WORKER = {
    fetch: async (request) => {
      calls++;
      assert.equal(new URL(request.url).origin, 'https://score.usd-impact.com');
      return new Response('delegated', { status: 207 });
    },
  };
  const response = await onRequest(ctx);
  assert.equal(response.status, 207);
  assert.equal(await response.text(), 'delegated');
  assert.equal(calls, 1);
  assert.equal(ctx.nextCalls, 0);
});
