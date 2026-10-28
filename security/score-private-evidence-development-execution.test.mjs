import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

import {
  WORKFLOW_REFS,
} from '../prototypes/score-private-evidence-broker/broker-core.mjs';

const repoRoot = new URL('../', import.meta.url);

async function text(path) {
  return readFile(new URL(path, repoRoot), 'utf8');
}

test('deployable broker package remains byte-identical to accepted prototype', async () => {
  const pairs = [
    [
      'prototypes/score-private-evidence-broker/broker-core.mjs',
      'provisioning/score-private-evidence-development/function/broker-core.mjs',
    ],
    [
      'prototypes/score-private-evidence-broker/github-oidc.mjs',
      'provisioning/score-private-evidence-development/function/github-oidc.mjs',
    ],
    [
      'prototypes/score-private-evidence-broker/index.ts',
      'provisioning/score-private-evidence-development/function/index.ts',
    ],
  ];

  for (const [prototypePath, deployPath] of pairs) {
    assert.equal(
      await text(deployPath),
      await text(prototypePath),
      `${deployPath} differs from accepted prototype`,
    );
  }
});

test('Development bucket SQL is private, JSON-only, 1 MiB and create-only', async () => {
  const sql = await text(
    'provisioning/score-private-evidence-development/create_bucket.sql',
  );

  assert.match(sql, /insert into storage\.buckets/i);
  assert.match(sql, /'score-private-evidence'/);
  assert.match(sql, /false/);
  assert.match(sql, /1048576/);
  assert.match(sql, /application\/json/);

  assert.doesNotMatch(sql, /on\s+conflict/i);
  assert.doesNotMatch(sql, /update\s+storage\.buckets/i);
  assert.doesNotMatch(sql, /delete\s+from\s+storage\.buckets/i);
  assert.doesNotMatch(sql, /storage\.objects/i);
  assert.doesNotMatch(sql, /create\s+policy/i);
});

test('bucket verification SQL is read-only', async () => {
  const sql = await text(
    'provisioning/score-private-evidence-development/verify_bucket.sql',
  );

  assert.match(sql, /select[\s\S]*from storage\.buckets/i);
  assert.match(sql, /select[\s\S]*from storage\.objects/i);
  assert.doesNotMatch(sql, /\binsert\b/i);
  assert.doesNotMatch(sql, /\bupdate\b/i);
  assert.doesNotMatch(sql, /\bdelete\b/i);
  assert.doesNotMatch(sql, /\bdrop\b/i);
  assert.doesNotMatch(sql, /\balter\b/i);
});

test('rehearsal workflows are manual-only and least privilege', async () => {
  const workflows = [
    {
      path: '.github/workflows/score-private-evidence-write-rehearsal.yml',
      ref: WORKFLOW_REFS.write,
      operation: 'write',
    },
    {
      path: '.github/workflows/score-private-evidence-read-rehearsal.yml',
      ref: WORKFLOW_REFS.read,
      operation: 'read',
    },
  ];

  for (const workflow of workflows) {
    const source = await text(workflow.path);

    assert.equal(
      workflow.ref,
      `usdimpact/usd-impact-pipeline/${workflow.path}@refs/heads/main`,
    );

    assert.match(source, /^on:\n  workflow_dispatch:\s*$/m);
    assert.match(source, /contents:\s*read/);
    assert.match(source, /id-token:\s*write/);
    assert.match(source, /github\.ref == 'refs\/heads\/main'/);
    assert.match(source, /persist-credentials:\s*false/);
    assert.match(source, /SYNTHETIC_WEEK:\s*'2099-01-02'/);
    assert.match(source, /score-publication-rights-gate\.json/);
    assert.match(source, /score-public-rights-surface\.json/);
    assert.match(source, /production_change_authorized/);
    assert.match(
      source,
      /https:\/\/xakayexlzyrazuunqlxe\.supabase\.co\/functions\/v1\/score-private-evidence-broker/,
    );

    assert.doesNotMatch(source, /^\s*schedule:/m);
    assert.doesNotMatch(source, /^\s*push:/m);
    assert.doesNotMatch(source, /^\s*pull_request(?:_target)?:/m);
    assert.doesNotMatch(source, /secrets\./);
    assert.doesNotMatch(source, /SUPABASE_(?:SERVICE_ROLE|SECRET|ACCESS)_KEY/);

    const brokerUrls = [...source.matchAll(/https:\/\/[^\s"'\\]+\/functions\/v1\/score-private-evidence-broker/g)]
      .map((match) => match[0]);
    assert.deepEqual(
      [...new Set(brokerUrls)],
      ['https://xakayexlzyrazuunqlxe.supabase.co/functions/v1/score-private-evidence-broker'],
    );

    if (workflow.operation === 'write') {
      assert.match(
        source,
        /write:development:\$\{SYNTHETIC_WEEK\}:\$\{fixture_sha256\}/,
      );
      assert.match(source, /x-score-operation: write/);
      assert.match(source, /x-score-content-sha256: \$fixture_sha256/);
      assert.match(source, /actions\/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1/);
      assert.match(source, /python-version:\s*'3\.11'/);
      assert.match(source, /runtime\/requirements-2026-10-05\.lock/);
      assert.match(source, /python -m pip check/);
      assert.match(source, /python -m scripts\.build_synthetic_private_score_evidence/);
      assert.doesNotMatch(source, /python scripts\/build_synthetic_private_score_evidence\.py/);
    } else {
      assert.match(source, /read:development:\$\{SYNTHETIC_WEEK\}/);
      assert.match(source, /x-score-operation: read/);
      assert.doesNotMatch(source, /-H "x-score-content-sha256:/);
      assert.match(source, /x-score-content-sha256:/);
      assert.match(source, /stored bundle is not synthetic/);
    }
  }
});
