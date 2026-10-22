import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
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
