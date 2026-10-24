import test from 'node:test';
import assert from 'node:assert/strict';
import { authorizeScoreEdgeRequest } from './score-edge-authorization.mjs';
import { scoreSessionCookie } from './score-session-cookie.mjs';

const nowMs = 1800000000000;
const token = 'a'.repeat(43);
const accountId = '00000000-0000-4000-8000-000000000001';
function request(cookie = '') {
  return new Request('https://score.usd-impact.com/en/', { headers: { cookie } });
}
function deps(active = true) {
  return {
    nowMs,
    sessions: { lookup: async () => ({ accountId, expiresAtMs: nowMs + 60000 }) },
    membership: { isActive: async () => active },
  };
}
test('verified session and current active membership grant access', async () => {
  const result = await authorizeScoreEdgeRequest(request(scoreSessionCookie(token, nowMs + 60000, nowMs)), deps());
  assert.deepEqual(result, { allowed: true, accountId });
});
test('missing or duplicate cookie denied', async () => {
  assert.equal((await authorizeScoreEdgeRequest(request(), deps())).allowed, false);
  const duplicate = '__Host-score_session=' + token + '; __Host-score_session=' + token;
  assert.equal((await authorizeScoreEdgeRequest(request(duplicate), deps())).allowed, false);
});
test('revoked membership denied even with valid session', async () => {
  const result = await authorizeScoreEdgeRequest(request('__Host-score_session=' + token), deps(false));
  assert.equal(result.code, 'RESEARCH_MEMBERSHIP_REQUIRED');
});
test('expired session denied', async () => {
  const d = deps();
  d.sessions.lookup = async () => ({ accountId, expiresAtMs: nowMs });
  assert.equal((await authorizeScoreEdgeRequest(request('__Host-score_session=' + token), d)).allowed, false);
});
test('missing backend dependencies denied', async () => {
  assert.equal((await authorizeScoreEdgeRequest(request('__Host-score_session=' + token))).allowed, false);
});
test('backend outage fails closed', async () => {
  const d = deps();
  d.membership.isActive = async () => { throw new Error('outage'); };
  const result = await authorizeScoreEdgeRequest(request('__Host-score_session=' + token), d);
  assert.equal(result.code, 'AUTHORIZATION_UNAVAILABLE');
});
