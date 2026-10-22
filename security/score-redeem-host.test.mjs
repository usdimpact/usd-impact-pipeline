import test from 'node:test';
import assert from 'node:assert/strict';
import { onRequestPost } from '../functions/score-redeem.js';

const ticket = 'a'.repeat(43);
const preview = 'fix-score-membership-handoff-147.usd-impact-pipeline.pages.dev';
const backend = 'https://usd-impact-site-qjfsh5lm7-usd-impact.vercel.app/api/score-edge-redeem';
function context(hostname, configuredHost) {
  return {
    request: new Request('https://' + hostname + '/score-redeem', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ ticket }),
    }),
    env: {
      SCORE_EDGE_REDEMPTION_ENABLED: 'true',
      SCORE_BACKEND_URL: backend,
      SCORE_EDGE_SHARED_SECRET: 'x'.repeat(48),
      ...(configuredHost ? { SCORE_PREVIEW_REDEMPTION_HOST: configuredHost } : {}),
    },
  };
}
test('unconfigured Preview redemption fails closed', async () => {
  assert.equal((await onRequestPost(context(preview))).status, 403);
});
test('arbitrary and parent Pages hosts are denied', async () => {
  for (const host of ['other.usd-impact-pipeline.pages.dev', 'usd-impact-pipeline.pages.dev', 'evil.example.test']) {
    assert.equal((await onRequestPost(context(host, preview))).status, 403);
  }
});
test('Preview setting cannot authorize a non-Pages host', async () => {
  assert.equal((await onRequestPost(context('evil.example.test', 'evil.example.test'))).status, 403);
});
test('exact pinned Preview host can reach private backend', async (t) => {
  const originalFetch = globalThis.fetch;
  t.after(() => { globalThis.fetch = originalFetch; });
  let calls = 0;
  globalThis.fetch = async (url, options) => {
    calls++;
    assert.equal(url, backend);
    assert.equal(options.redirect, 'manual');
    assert.deepEqual(JSON.parse(options.body), { ticket });
    return Response.json({ allowed: false }, { status: 403 });
  };
  assert.equal((await onRequestPost(context(preview, preview))).status, 403);
  assert.equal(calls, 1);
});
test('Production hostname remains accepted independently of Preview setting', async (t) => {
  const originalFetch = globalThis.fetch;
  t.after(() => { globalThis.fetch = originalFetch; });
  let calls = 0;
  globalThis.fetch = async () => { calls++; return Response.json({ allowed: false }, { status: 403 }); };
  assert.equal((await onRequestPost(context('score.usd-impact.com'))).status, 403);
  assert.equal(calls, 1);
});


test('a changed Preview backend host cannot receive the private edge secret', async (t) => {
  const originalFetch = globalThis.fetch;
  t.after(() => { globalThis.fetch = originalFetch; });
  let requests = 0;
  globalThis.fetch = async () => { requests++; throw Error('backend must not be contacted'); };
  for (const host of [
    'https://attacker.example.test/api/score-edge-redeem',
    'https://usd-impact-site-8lvzao44t-usd-impact.vercel.app/api/score-edge-redeem',
    'https://usd-impact-site-qjfsh5lm7-usd-impact.vercel.app/api/score-edge-redeem?redirect=1',
  ]) {
    const ctx = context(preview, preview);
    ctx.env.SCORE_BACKEND_URL = host;
    const resp = await onRequestPost(ctx);
    assert.equal(resp.status, 503);
    assert.equal(resp.headers.get('Set-Cookie'), null);
  }
  assert.equal(requests, 0);
});


function bodyContext(body, { mediaType = 'application/x-www-form-urlencoded', length = null, stream = false } = {}) {
  const ctx = context(preview, preview);
  const headers = { 'Content-Type': mediaType };
  if (length !== null) headers['Content-Length'] = String(length);
  const options = { method: 'POST', headers };
  if (stream) {
    const data = new TextEncoder().encode(body);
    options.body = new ReadableStream({
      start(controller) {
        controller.enqueue(data.slice(0, 12));
        controller.enqueue(data.slice(12));
        controller.close();
      },
    });
    options.duplex = 'half';
  } else {
    options.body = body;
  }
  ctx.request = new Request('https://' + preview + '/score-redeem', options);
  return ctx;
}

test('untrusted streamed POST bodies are byte-bounded and ambiguous tickets are rejected', async (t) => {
  const originalFetch = globalThis.fetch;
  t.after(() => { globalThis.fetch = originalFetch; });
  let calls = 0;
  globalThis.fetch = async () => { calls++; throw Error('Invalid form must never reach backend'); };

  for (const ctx of [
    bodyContext('ticket=' + ticket + '&ticket=' + ticket),
    bodyContext('ticket=' + ticket + '&account_id=other'),
    bodyContext('ticket=' + ticket, { mediaType: 'application/x-www-form-urlencoded-evil' }),
    bodyContext('ticket=' + ticket, { length: 99999 }),
    bodyContext('ticket=' + ticket, { length: 'not-a-length' }),
    bodyContext('ticket=' + ticket + '&padding=' + 'x'.repeat(3000), { stream: true }),
  ]) {
    const response = await onRequestPost(ctx);
    assert.equal(response.status, 400);
    assert.equal(response.headers.get('Set-Cookie'), null);
  }
  assert.equal(calls, 0);
});

test('one valid streamed form ticket remains accepted and forwarded without alteration', async (t) => {
  const originalFetch = globalThis.fetch;
  t.after(() => { globalThis.fetch = originalFetch; });
  let calls = 0;
  globalThis.fetch = async (url, options) => {
    calls++;
    assert.equal(url, backend);
    assert.deepEqual(JSON.parse(options.body), { ticket });
    return Response.json({ allowed: false }, { status: 403 });
  };
  const ctx = bodyContext('ticket=' + ticket, {
    mediaType: 'application/x-www-form-urlencoded; charset=UTF-8', stream: true,
  });
  assert.equal((await onRequestPost(ctx)).status, 403);
  assert.equal(calls, 1);
});
