import test from 'node:test';
import assert from 'node:assert/strict';
import { scoreAccessDecision, safeScoreReturnPath } from './score-access-policy.mjs';

const nowMs = Date.parse('2026-10-19T12:00:00Z');
const verifiedUser = { id: 'account-A', emailConfirmedAt: '2026-10-01T00:00:00Z' };
const profile = { accountId: 'account-A', status: 'active' };
const entitlement = { accountId: 'account-A', productId: 'research-membership',
  state: 'active', startsAt: '2026-10-01T00:00:00Z', endsAt: null };
const decision = (overrides = {}) => scoreAccessDecision({
  verifiedUser, profile, entitlement, nowMs, ...overrides,
});
test('active research member allowed', () => assert.equal(decision().allowed, true));
test('no verified user denied', () => assert.equal(decision({ verifiedUser: null }).allowed, false));
test('unconfirmed user denied', () => assert.equal(decision({ verifiedUser: { id: 'account-A' } }).allowed, false));
test('inactive profile denied', () => assert.equal(decision({ profile: { ...profile, status: 'deleted' } }).allowed, false));
test('different account denied', () => assert.equal(decision({ entitlement: { ...entitlement, accountId: 'account-B' } }).allowed, false));
test('library pass only denied', () => assert.equal(decision({ entitlement: { ...entitlement, productId: 'library-pass' } }).allowed, false));
for (const state of ['revoked', 'refunded', 'cancelled', 'disputed', 'charged_back', 'past_due']) {
  test(state + ' denied', () => assert.equal(decision({ entitlement: { ...entitlement, state } }).allowed, false));
}
test('future start denied', () => assert.equal(decision({ entitlement: { ...entitlement, startsAt: '2026-10-20T00:00:00Z' } }).allowed, false));
test('expired denied', () => assert.equal(decision({ entitlement: { ...entitlement, endsAt: '2026-10-19T11:59:59Z' } }).allowed, false));
test('invalid expiry denied', () => assert.equal(decision({ entitlement: { ...entitlement, endsAt: 'bad' } }).allowed, false));
test('allowed return paths', () => {
  for (const path of ['/en/', '/es/', '/archive/en/', '/archive/es/']) assert.equal(safeScoreReturnPath(path), path);
});
test('open redirects and arbitrary routes denied', () => {
  for (const path of ['https://evil.example', '//evil.example', '/admin/', '/en/../admin', '/en/?next=https://evil.example', null]) {
    assert.equal(safeScoreReturnPath(path), null);
  }
});
