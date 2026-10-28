export const BROKER_MODE = 'synthetic-only';
export const MAX_BODY_BYTES = 1024 * 1024;
export const STORAGE_BUCKET = 'score-private-evidence';
export const WORKFLOW_REFS = Object.freeze({
  write: 'usdimpact/usd-impact-pipeline/.github/workflows/score-private-evidence-write-rehearsal.yml@refs/heads/main',
  read: 'usdimpact/usd-impact-pipeline/.github/workflows/score-private-evidence-read-rehearsal.yml@refs/heads/main',
});

const BASE_POLICY = Object.freeze({
  repository: 'usdimpact/usd-impact-pipeline',
  repositoryId: '1207104487',
  repositoryOwnerId: '275107298',
  ref: 'refs/heads/main',
  refType: 'branch',
  allowedEvents: ['workflow_dispatch'],
  runnerEnvironment: 'github-hosted',
  subjectPrefix: 'repo:usdimpact/usd-impact-pipeline',
  clockSkewSeconds: 30,
  maxTokenAgeSeconds: 600,
  maxTokenLifetimeSeconds: 600,
});

const AUDIENCE_PREFIXES = Object.freeze({
  write: 'urn:usd-impact:score-private-evidence:write:development',
  read: 'urn:usd-impact:score-private-evidence:read:development',
});

const PROVIDER_MARKERS = [
  'yahoo',
  'finance.yahoo',
  'fred',
  'spglobal',
  'cboe',
  'cmegroup',
  'intercontinentalexchange',
  'source_url',
  'source_provenance',
  'provider_code',
];

const REQUIRED_COMPONENTS = [
  'DXY',
  'WTI',
  'SPX',
  'VIX',
  'BTC',
  'GOLD',
  'UST_2Y',
  'UST_10Y',
];

export function validateBucketMetadata(data) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    throw new Error('bucket_policy_mismatch');
  }

  const bucketId = data.id ?? data.name;
  const fileSizeLimit = Number(data.file_size_limit ?? data.fileSizeLimit);
  const allowedMimeTypes = data.allowed_mime_types ?? data.allowedMimeTypes;

  if (bucketId !== STORAGE_BUCKET) throw new Error('bucket_policy_mismatch');
  if (data.public !== false) throw new Error('bucket_policy_mismatch');
  if (!Number.isFinite(fileSizeLimit) || fileSizeLimit !== MAX_BODY_BYTES) {
    throw new Error('bucket_policy_mismatch');
  }
  if (
    !Array.isArray(allowedMimeTypes)
    || allowedMimeTypes.length !== 1
    || allowedMimeTypes[0] !== 'application/json'
  ) {
    throw new Error('bucket_policy_mismatch');
  }

  return true;
}

export function buildOidcAudience(operation, { week, sha256 = null } = {}) {
  if (!(operation in AUDIENCE_PREFIXES)) throw new Error('Unsupported broker operation');
  validateSyntheticWeek(week);

  if (operation === 'write') {
    validateDeclaredSha256(sha256);
    return `${AUDIENCE_PREFIXES.write}:${week}:${sha256}`;
  }
  return `${AUDIENCE_PREFIXES.read}:${week}`;
}

export function buildOidcPolicy(operation, binding) {
  return {
    ...BASE_POLICY,
    audience: buildOidcAudience(operation, binding),
    workflowRef: WORKFLOW_REFS[operation],
  };
}

export function parseBearerToken(headerValue) {
  if (typeof headerValue !== 'string') throw new Error('Missing Authorization header');
  const match = headerValue.match(/^Bearer ([A-Za-z0-9._~-]+)$/);
  if (!match) throw new Error('Authorization must contain one Bearer token');
  return match[1];
}

export function requireBrokerOperation(value) {
  if (value !== 'write' && value !== 'read') {
    throw new Error('x-score-operation must be read or write');
  }
  return value;
}

function parseIsoDate(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    throw new Error('Score week must be YYYY-MM-DD');
  }
  const date = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(date.getTime()) || date.toISOString().slice(0, 10) !== value) {
    throw new Error('Score week is not a valid calendar date');
  }
  return date;
}

export function validateSyntheticWeek(value) {
  const date = parseIsoDate(value);
  if (date.getUTCDay() !== 5) throw new Error('Score week must be a Friday');
  if (date.getUTCFullYear() < 2099) {
    throw new Error('Synthetic-only broker refuses non-synthetic calendar years');
  }
  return value;
}

export function objectPathForWeek(week) {
  validateSyntheticWeek(week);
  return `rehearsal/score-v2/archive/${week}/repro_bundle.json`;
}

function assertPlainObject(value, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`${label} must be an object`);
  }
}

function walkForProviderMarkers(value, path = '$') {
  if (Array.isArray(value)) {
    value.forEach((item, index) => walkForProviderMarkers(item, `${path}[${index}]`));
    return;
  }
  if (value && typeof value === 'object') {
    for (const [key, child] of Object.entries(value)) {
      const lowerKey = key.toLowerCase();
      if (PROVIDER_MARKERS.some((marker) => lowerKey.includes(marker))) {
        throw new Error(`Synthetic rehearsal contains provider marker at ${path}.${key}`);
      }
      walkForProviderMarkers(child, `${path}.${key}`);
    }
    return;
  }
  if (typeof value === 'string') {
    const lower = value.toLowerCase();
    if (PROVIDER_MARKERS.some((marker) => lower.includes(marker))) {
      throw new Error(`Synthetic rehearsal contains provider marker at ${path}`);
    }
    if (/https?:\/\//i.test(value)) {
      throw new Error(`Synthetic rehearsal contains a URL at ${path}`);
    }
  }
}

export function validateSyntheticBundleBytes(bytes, week) {
  if (!(bytes instanceof Uint8Array)) throw new Error('Bundle body must be bytes');
  if (bytes.byteLength === 0) throw new Error('Bundle body must not be empty');
  if (bytes.byteLength > MAX_BODY_BYTES) throw new Error('Bundle body exceeds size limit');
  validateSyntheticWeek(week);

  let payload;
  try {
    payload = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
  } catch {
    throw new Error('Bundle body must be valid UTF-8 JSON');
  }

  assertPlainObject(payload, 'Synthetic bundle');
  if (payload.synthetic_rehearsal !== true) {
    throw new Error('Synthetic bundle must declare synthetic_rehearsal=true');
  }
  if (payload.do_not_publish !== true) {
    throw new Error('Synthetic bundle must declare do_not_publish=true');
  }
  if (payload.score_week !== week) throw new Error('Synthetic bundle week mismatch');
  if (typeof payload.synthetic_fixture_version !== 'string' || payload.synthetic_fixture_version.length === 0) {
    throw new Error('Synthetic bundle is missing fixture version');
  }
  if (payload.pipeline_git_sha !== '0'.repeat(40)) {
    throw new Error('Synthetic bundle must use zeroed pipeline SHA');
  }
  if (payload.requirements_lock_sha256 !== '0'.repeat(64)) {
    throw new Error('Synthetic bundle must use zeroed requirements hash');
  }

  assertPlainObject(payload.components, 'Synthetic components');
  const componentNames = Object.keys(payload.components).sort();
  if (JSON.stringify(componentNames) !== JSON.stringify([...REQUIRED_COMPONENTS].sort())) {
    throw new Error('Synthetic bundle component set is unexpected');
  }

  if ('provider_derived_values' in payload && payload.provider_derived_values !== false) {
    throw new Error('Synthetic bundle cannot declare provider-derived values');
  }

  walkForProviderMarkers(payload);
  return payload;
}

export async function sha256Hex(bytes) {
  const digest = new Uint8Array(await crypto.subtle.digest('SHA-256', bytes));
  return [...digest].map((value) => value.toString(16).padStart(2, '0')).join('');
}

export function validateDeclaredSha256(value) {
  if (typeof value !== 'string' || !/^[0-9a-f]{64}$/.test(value)) {
    throw new Error('x-score-content-sha256 must be a lowercase SHA-256 hex digest');
  }
  return value;
}
