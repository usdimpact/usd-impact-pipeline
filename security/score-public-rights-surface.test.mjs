import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

import { isPublicScorePath } from './score-public-paths.mjs';

const repoRoot = new URL('../', import.meta.url);
const allowlistSource = await readFile(new URL('security/score-public-paths.mjs', repoRoot), 'utf8');
const manifest = JSON.parse(
  await readFile(new URL('governance/score-public-rights-surface.json', repoRoot), 'utf8'),
);

function extractStaticAllowlistPaths(source) {
  const match = source.match(/const PUBLIC_PATHS = new Set\(\[([\s\S]*?)\]\);/);
  assert.ok(match, 'PUBLIC_PATHS Set not found');
  return [...match[1].matchAll(/'([^']+)'/g)].map((item) => item[1]);
}

function extractArchiveRegexSource(source) {
  const match = source.match(/const PUBLIC_DATED_ARCHIVE_RE = \/(.+)\/;/);
  assert.ok(match, 'PUBLIC_DATED_ARCHIVE_RE not found');
  return match[1].replaceAll('\\/', '/');
}

test('every explicit public Score path is classified exactly once', () => {
  const allowlist = extractStaticAllowlistPaths(allowlistSource).sort();
  const classified = manifest.static_paths.map((item) => item.path).sort();

  assert.deepEqual(classified, allowlist);
  assert.equal(new Set(classified).size, classified.length);

  for (const item of manifest.static_paths) {
    assert.ok(manifest.classes[item.class], `unknown class for ${item.path}`);
    assert.equal(isPublicScorePath(item.path), true, `${item.path} is not actually public`);
  }
});

test('dated public archive pattern is classified without broadening it', () => {
  assert.equal(manifest.dated_archive_patterns.length, 1);
  const item = manifest.dated_archive_patterns[0];

  assert.ok(manifest.classes[item.class]);
  assert.equal(item.class, 'C');
  assert.equal(item.regex, extractArchiveRegexSource(allowlistSource));

  const manifestRegex = new RegExp(item.regex);
  for (const example of item.examples) {
    assert.equal(manifestRegex.test(example), true, `manifest pattern rejects ${example}`);
    assert.equal(isPublicScorePath(example), true, `allowlist rejects ${example}`);
  }

  const rejected = [
    '/archive/2026-10-23/index.html',
    '/archive/2026-10-23/dashboard.json',
    '/archive/2026-10-23/score.csv',
    '/archive/latest/score.json',
    '/archive/2026-10-23/research.json',
  ];
  for (const candidate of rejected) {
    assert.equal(manifestRegex.test(candidate), false, `manifest unexpectedly accepts ${candidate}`);
    assert.equal(isPublicScorePath(candidate), false, `allowlist unexpectedly accepts ${candidate}`);
  }
});

test('rights manifest remains fail-closed while issue 155 is HOLD', () => {
  assert.equal(manifest.version, 1);
  assert.equal(manifest.state, 'hold');
  assert.equal(manifest.production_change_authorized, false);
  assert.match(manifest.issue, /\/issues\/155$/);

  const classNames = Object.keys(manifest.classes).sort();
  assert.deepEqual(classNames, ['A', 'B', 'C', 'D', 'E', 'F']);
  assert.deepEqual([...manifest.priority_order].sort(), classNames);

  for (const [name, definition] of Object.entries(manifest.classes)) {
    assert.equal(typeof definition.label, 'string', `class ${name} has no label`);
    assert.ok(definition.label.length > 0, `class ${name} label is empty`);
    assert.equal(
      typeof definition.default_treatment,
      'string',
      `class ${name} has no default treatment`,
    );
    assert.ok(
      definition.default_treatment.length > 0,
      `class ${name} default treatment is empty`,
    );
  }
});
