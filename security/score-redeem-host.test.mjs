import test from 'node:test';
import assert from 'node:assert/strict';
import { onRequestPost } from '../functions/score-redeem.js';

const ticket = 'a'.repeat(43);
const preview = 'fix-score-membership-handoff-147.usd-impact-pipeline.pages.dev';
const backend = 'https://preview.example.test/api/score-edge-redeem';
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
