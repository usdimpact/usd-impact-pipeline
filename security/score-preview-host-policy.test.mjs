import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  SCORE_DIRECT_PREVIEW_HOST as PAGES_HOST,
  SCORE_DIRECT_WEBSITE_ORIGIN as PAGES_ISSUER,
  scoreDevBrokerPreviewEnabled as previewEnabled,
} from './score-preview-host-policy.mjs';
import {
  SCORE_DIRECT_PREVIEW_HOST as RPC_HOST,
  SCORE_DIRECT_WEBSITE_ORIGIN as RPC_ISSUER,
} from './score-preview-dev-rpc.mjs';

test('Pages preview imports cannot bring privileged Supabase RPC code into the bundle', () => {
  for (const path of ['../functions/_middleware.js', '../functions/score-redeem.js']) {
    const code = readFileSync(new URL(path, import.meta.url), 'utf8');
    assert.match(code, /score-preview-host-policy\.mjs/);
    assert.doesNotMatch(code, /score-preview-dev-rpc\.mjs/);
  }
  assert.equal(PAGES_HOST, RPC_HOST);
  assert.equal(PAGES_ISSUER, RPC_ISSUER);
  assert.equal(PAGES_ISSUER,'https://usd-impact-site-55p15tktn-usd-impact.vercel.app');
  assert.notEqual(PAGES_ISSUER,'https://usd-impact-site-git-feat-score-membership-han-fb189b-usd-impact.vercel.app');
});

test('credential-free Pages policy selects one exact isolated HTTPS Preview host', () => {
  const enabled = { SCORE_DEV_BROKER_ENABLED: 'true' };
  const request = (url) => new Request(url);
  assert.equal(previewEnabled(request('https://' + PAGES_HOST + '/en/'), enabled), true);
  for (const url of [
    'http://' + PAGES_HOST + '/en/',
    'https://other.usd-impact-pipeline.pages.dev/en/',
    'https://usd-impact-pipeline.pages.dev/en/',
    'https://score.usd-impact.com/en/',
    'https://' + PAGES_HOST + ':8443/en/',
  ]) {
    assert.equal(previewEnabled(request(url), enabled), false, url);
  }
  assert.equal(previewEnabled(request('https://' + PAGES_HOST + '/en/'), {}), false);
});

test('the complete Pages module graph stays credential-free (not only direct imports)', () => {
  // Allowlist every runtime module reachable from the two Cloudflare entrypoints.
  // A new import fails CI until its security boundary is explicitly reviewed.
  const root = fileURLToPath(new URL('../', import.meta.url));
  const approved = new Set([
    'functions/_middleware.js',
    'functions/score-redeem.js',
    'security/score-session-cookie.mjs',
    'security/score-backend-endpoints.mjs',
    'security/score-preview-host-policy.mjs',
    'security/score-preview-broker-client.mjs',
    'security/score-public-paths.mjs',
    'security/score-ticket-form.mjs',
  ]);
  const queue = ['functions/_middleware.js', 'functions/score-redeem.js'];
  const visited = new Set();
  while (queue.length > 0) {
    const file = queue.pop();
    assert.ok(approved.has(file), 'Unreviewed Pages module: ' + file);
    if (visited.has(file)) continue;
    visited.add(file);
    const source = readFileSync(resolve(root, file), 'utf8');
    assert.doesNotMatch(source, /\b(?:require|import)\s*\(/, 'No dynamic imports in ' + file);
    assert.doesNotMatch(source, /SUPABASE_(?:SECRET_KEYS|SERVICE_ROLE_KEY)|SCORE_PREVIEW_SUPABASE_SECRET_KEY|\/rest\/v1\/rpc\//,
      'No privileged database RPC or key in ' + file);
    // All current runtime relative imports use static import/export declarations.
    const direct = /(?:\b(?:import|export)\s+[\s\S]{0,200}?\s+from\s*|\bimport\s*)['"](\.{1,2}\/[^'"]+)['"]/g;
    for (const match of source.matchAll(direct)) {
      const child = relative(root, resolve(dirname(resolve(root, file)), match[1]))
        .split(sep).join('/');
      assert.ok(!child.startsWith('..'), 'Pages import escapes project: ' + match[1]);
      assert.ok(approved.has(child), 'Unreviewed Pages dependency: ' + file + ' => ' + child);
      queue.push(child);
    }
  }
  assert.deepEqual([...visited].sort(), [...approved].sort());
});
