import test from 'node:test';
import assert from 'node:assert/strict';
import { scoreBackendEndpoint } from './score-backend-endpoints.mjs';

const preview = 'https://usd-impact-site-qjfsh5lm7-usd-impact.vercel.app';
const production = 'https://www.usd-impact.com';
const redeem = '/api/score-edge-redeem';
const validate = '/api/score-edge-validate';

test('only exact known Preview and first-party production hosts can receive private requests', () => {
  for (const origin of [preview, production]) {
    for (const path of [redeem, validate]) {
      assert.equal(scoreBackendEndpoint(origin + path, path), origin + path);
      assert.equal(scoreBackendEndpoint(origin + path, path === redeem ? validate : redeem), null);
    }
  }
});
test('unapproved https hosts and lookalikes cannot receive the encrypted shared secret', () => {
  for (const input of [
    'https://evil.example.test' + redeem,
    'https://attacker.vercel.app' + redeem,
    'https://www.usd-impact.com.attacker.test' + redeem,
    'https://usd-impact-site-qjfsh5lm7-usd-impact.vercel.app.attacker.test' + redeem,
    'https://usd-impact-site-8lvzao44t-usd-impact.vercel.app' + redeem,
    'https://score.usd-impact.com' + redeem,
    'https://localhost' + redeem,
    'https://127.0.0.1' + redeem,
    'http://www.usd-impact.com' + redeem,
    'https://username:password@www.usd-impact.com' + redeem,
    preview + redeem + '?token=secret',
    preview + redeem + '#private',
    preview + '/api/score-edge-redeem/extra',
    preview + '/api/score-edge-redeem/..',
    preview + '/api/score-edge-redeem%2f..',
    preview + '/api/score-edge-redeem%2Fvalidate',
    '',
    null, undefined, false,
  ]) {
    assert.equal(scoreBackendEndpoint(input, redeem), null, String(input));
  }
  assert.equal(scoreBackendEndpoint(preview + redeem, '/arbitrary-path'), null);
});
test('validation target must not accept a redemption endpoint', () => {
  assert.equal(scoreBackendEndpoint(preview + redeem, validate), null);
  assert.equal(scoreBackendEndpoint(production + validate, redeem), null);
});
