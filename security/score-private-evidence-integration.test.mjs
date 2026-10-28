import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';

import {
  objectPathForWeek,
  sha256Hex,
  validateSyntheticBundleBytes,
} from '../prototypes/score-private-evidence-broker/broker-core.mjs';

test('accepted Python synthetic fixture is byte-compatible with OIDC broker validation', async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'score-private-evidence-integration-'));
  try {
    const build = spawnSync(
      'python',
      [
        'scripts/build_synthetic_private_score_evidence.py',
        '--output-root',
        root,
      ],
      {
        cwd: process.cwd(),
        encoding: 'utf8',
        env: { ...process.env, PYTHONPATH: process.cwd() },
      },
    );

    assert.equal(
      build.status,
      0,
      `synthetic fixture builder failed: ${build.stderr || build.stdout}`,
    );

    const report = JSON.parse(build.stdout);
    assert.equal(report.synthetic_rehearsal, true);
    assert.equal(report.do_not_publish, true);
    assert.equal(report.provider_derived_values, false);
    assert.equal(report.latest_week, '2099-01-09');

    const weeks = ['2099-01-02', '2099-01-09'];
    for (const week of weeks) {
      const archivePath = path.join(root, 'archive', week, 'repro_bundle.json');
      const bytes = new Uint8Array(await readFile(archivePath));
      const payload = validateSyntheticBundleBytes(bytes, week);

      assert.equal(payload.score_week, week);
      assert.equal(payload.synthetic_rehearsal, true);
      assert.equal(payload.do_not_publish, true);
      assert.equal(
        objectPathForWeek(week),
        `rehearsal/score-v2/archive/${week}/repro_bundle.json`,
      );

      const digest = await sha256Hex(bytes);
      assert.match(digest, /^[0-9a-f]{64}$/);
    }

    const latest = new Uint8Array(
      await readFile(path.join(root, 'score_repro_bundle_latest.json')),
    );
    const latestArchive = new Uint8Array(
      await readFile(path.join(root, 'archive', report.latest_week, 'repro_bundle.json')),
    );
    assert.deepEqual(latest, latestArchive);
    assert.equal(await sha256Hex(latest), report.latest_sha256);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
