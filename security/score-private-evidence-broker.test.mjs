import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

import {
  buildOidcPolicy,
  objectPathForWeek,
  parseBearerToken,
  sha256Hex,
  validateSyntheticBundleBytes,
  validateSyntheticWeek,
  WORKFLOW_REFS,
} from '../prototypes/score-private-evidence-broker/broker-core.mjs';
import {
  verifyGithubOidcJwt,
} from '../prototypes/score-private-evidence-broker/github-oidc.mjs';

const NOW = 1_800_000_000;
const KID = 'review-test-key';

function jsonB64(value) {
  return Buffer.from(JSON.stringify(value)).toString('base64url');
}

async function generateSigningKey() {
  const pair = await crypto.subtle.generateKey(
    {
      name: 'RSASSA-PKCS1-v1_5',
      modulusLength: 2048,
      publicExponent: new Uint8Array([1, 0, 1]),
      hash: 'SHA-256',
    },
    true,
    ['sign', 'verify'],
  );
  const jwk = await crypto.subtle.exportKey('jwk', pair.publicKey);
  return {
    privateKey: pair.privateKey,
    jwks: {
      keys: [{ ...jwk, kid: KID, alg: 'RS256', use: 'sig' }],
    },
  };
}

function validClaims(policy, overrides = {}) {
  return {
    iss: 'https://token.actions.githubusercontent.com',
    aud: policy.audience,
    sub: 'repo:usdimpact/usd-impact-pipeline:ref:refs/heads/main',
    repository: 'usdimpact/usd-impact-pipeline',
    repository_id: '1207104487',
    repository_owner: 'usdimpact',
    repository_owner_id: '275107298',
    ref: 'refs/heads/main',
    ref_type: 'branch',
    workflow_ref: policy.workflowRef,
    event_name: 'workflow_dispatch',
    runner_environment: 'github-hosted',
    sha: 'a'.repeat(40),
    run_id: '40600000000',
    run_number: '1',
    run_attempt: '1',
    jti: 'review-jti-1',
    iat: NOW,
    nbf: NOW - 1,
    exp: NOW + 300,
    ...overrides,
  };
}

async function signJwt(privateKey, claims, header = { alg: 'RS256', typ: 'JWT', kid: KID }) {
  const encodedHeader = jsonB64(header);
  const encodedClaims = jsonB64(claims);
  const signed = `${encodedHeader}.${encodedClaims}`;
  const signature = await crypto.subtle.sign(
    { name: 'RSASSA-PKCS1-v1_5' },
    privateKey,
    new TextEncoder().encode(signed),
  );
  return `${signed}.${Buffer.from(signature).toString('base64url')}`;
}

function syntheticBundle(week = '2099-01-02') {
  const components = {};
  for (const [index, name] of [
    'DXY', 'WTI', 'SPX', 'VIX', 'BTC', 'GOLD', 'UST_2Y', 'UST_10Y',
  ].entries()) {
    components[name] = {
      weekly_level: 1000 + index,
      z_clipped: 0,
      weight: name === 'DXY' || name === 'VIX' || name.startsWith('UST_') ? 0.125 : -0.125,
    };
  }
  return {
    synthetic_fixture_version: 'score-private-evidence-synthetic-v1',
    synthetic_rehearsal: true,
    do_not_publish: true,
    score_week: week,
    pipeline_git_sha: '0'.repeat(40),
    requirements_lock_sha256: '0'.repeat(64),
    components,
    calculation: { regime_bands: [] },
    published: { score: 0, regime: 'Neutral / transitional' },
  };
}

test('verifies a correctly signed write token with immutable repository claims', async () => {
  const policy = buildOidcPolicy('write');
  const { privateKey, jwks } = await generateSigningKey();
  const token = await signJwt(privateKey, validClaims(policy));
  const result = await verifyGithubOidcJwt(token, policy, { jwks, nowSeconds: NOW });

  assert.equal(result.identity.repositoryId, '1207104487');
  assert.equal(result.identity.workflowRef, WORKFLOW_REFS.write);
  assert.equal(result.identity.runId, '40600000000');
});

test('read and write identities cannot reuse the same OIDC token', async () => {
  const writePolicy = buildOidcPolicy('write');
  const readPolicy = buildOidcPolicy('read');
  const { privateKey, jwks } = await generateSigningKey();
  const token = await signJwt(privateKey, validClaims(writePolicy));

  await assert.rejects(
    verifyGithubOidcJwt(token, readPolicy, { jwks, nowSeconds: NOW }),
    /audience|workflow ref/i,
  );
});

test('rejects wrong immutable repository identity', async () => {
  const policy = buildOidcPolicy('write');
  const { privateKey, jwks } = await generateSigningKey();
  const token = await signJwt(
    privateKey,
    validClaims(policy, { repository_id: '999999' }),
  );

  await assert.rejects(
    verifyGithubOidcJwt(token, policy, { jwks, nowSeconds: NOW }),
    /repository ID/,
  );
});

test('rejects wrong workflow ref even with valid signature', async () => {
  const policy = buildOidcPolicy('write');
  const { privateKey, jwks } = await generateSigningKey();
  const token = await signJwt(
    privateKey,
    validClaims(policy, {
      workflow_ref: 'usdimpact/usd-impact-pipeline/.github/workflows/weekly.yml@refs/heads/main',
    }),
  );

  await assert.rejects(
    verifyGithubOidcJwt(token, policy, { jwks, nowSeconds: NOW }),
    /workflow ref/,
  );
});

test('rejects expired OIDC token', async () => {
  const policy = buildOidcPolicy('write');
  const { privateKey, jwks } = await generateSigningKey();
  const token = await signJwt(
    privateKey,
    validClaims(policy, { iat: NOW - 900, nbf: NOW - 900, exp: NOW - 500 }),
  );

  await assert.rejects(
    verifyGithubOidcJwt(token, policy, { jwks, nowSeconds: NOW }),
    /expired|too old/i,
  );
});

test('rejects tampered JWT payload even when claims look acceptable', async () => {
  const policy = buildOidcPolicy('write');
  const { privateKey, jwks } = await generateSigningKey();
  const token = await signJwt(privateKey, validClaims(policy));
  const [header, _claims, signature] = token.split('.');
  const tamperedClaims = jsonB64(validClaims(policy, { run_id: '99999999999' }));
  const tampered = `${header}.${tamperedClaims}.${signature}`;

  await assert.rejects(
    verifyGithubOidcJwt(tampered, policy, { jwks, nowSeconds: NOW }),
    /signature verification failed/,
  );
});

test('synthetic-only namespace rejects current production weeks', () => {
  assert.throws(() => validateSyntheticWeek('2026-10-30'), /synthetic calendar years/);
  assert.throws(() => validateSyntheticWeek('2099-01-03'), /Friday/);
  assert.equal(validateSyntheticWeek('2099-01-02'), '2099-01-02');
  assert.equal(
    objectPathForWeek('2099-01-02'),
    'rehearsal/score-v2/archive/2099-01-02/repro_bundle.json',
  );
});

test('synthetic fixture passes while provider/source markers fail closed', async () => {
  const payload = syntheticBundle();
  const bytes = new TextEncoder().encode(JSON.stringify(payload));
  const parsed = validateSyntheticBundleBytes(bytes, '2099-01-02');
  assert.equal(parsed.synthetic_rehearsal, true);

  const sha = await sha256Hex(bytes);
  assert.match(sha, /^[0-9a-f]{64}$/);

  const contaminated = syntheticBundle();
  contaminated.source_provenance = {
    DXY: { provider: 'Yahoo Finance', source_url: 'https://example.invalid' },
  };
  const contaminatedBytes = new TextEncoder().encode(JSON.stringify(contaminated));
  assert.throws(
    () => validateSyntheticBundleBytes(contaminatedBytes, '2099-01-02'),
    /provider marker|URL/,
  );
});

test('bearer parser accepts only one compact token', () => {
  assert.equal(parseBearerToken('Bearer abc.def.ghi'), 'abc.def.ghi');
  assert.throws(() => parseBearerToken('Basic abc'), /Bearer token/);
  assert.throws(() => parseBearerToken('Bearer abc def'), /Bearer token/);
});

test('workflow examples are manual, secretless and least-privilege only', async () => {
  const examples = [
    {
      file: '../prototypes/score-private-evidence-broker/write-rehearsal.workflow.example.yml',
      audience: 'urn:usd-impact:score-private-evidence:write:development',
    },
    {
      file: '../prototypes/score-private-evidence-broker/read-rehearsal.workflow.example.yml',
      audience: 'urn:usd-impact:score-private-evidence:read:development',
    },
  ];

  for (const example of examples) {
    const source = await readFile(new URL(example.file, import.meta.url), 'utf8');
    assert.match(source, /workflow_dispatch:/);
    assert.match(source, /contents:\s*read/);
    assert.match(source, /id-token:\s*write/);
    assert.match(source, /SYNTHETIC_WEEK:\s*'2099-01-02'/);
    assert.doesNotMatch(source, /inputs\.synthetic_week/);
    assert.match(source, /persist-credentials:\s*false/);
    assert.ok(source.includes(example.audience));
    assert.match(source, /xakayexlzyrazuunqlxe\.supabase\.co/);
    assert.doesNotMatch(source, /\bschedule:/);
    assert.doesNotMatch(source, /\bpull_request(?:_target)?:/);
    assert.doesNotMatch(source, /\bpush:/);
    assert.doesNotMatch(source, /secrets\./);
    assert.doesNotMatch(source, /SUPABASE_(?:SERVICE_ROLE|SECRET|ACCESS)_KEY/);
  }
});
test('edge wrapper has no list/delete/signed-url or legacy service-role escape hatch', async () => {
  const source = await readFile(
    new URL('../prototypes/score-private-evidence-broker/index.ts', import.meta.url),
    'utf8',
  );

  assert.match(source, /upsert:\s*false/);
  assert.match(source, /SCORE_BROKER_MODE/);
  assert.match(source, /synthetic_bundle_rejected/);
  assert.doesNotMatch(source, /\.remove\s*\(/);
  assert.doesNotMatch(source, /\.list\s*\(/);
  assert.doesNotMatch(source, /createSignedUrl/);
  assert.doesNotMatch(source, /SUPABASE_SERVICE_ROLE_KEY/);
  assert.doesNotMatch(source, /Access-Control-Allow-Origin/i);
});
