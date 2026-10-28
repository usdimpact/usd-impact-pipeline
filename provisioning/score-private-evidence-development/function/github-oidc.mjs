const GITHUB_OIDC_ISSUER = 'https://token.actions.githubusercontent.com';
const GITHUB_OIDC_JWKS_URL = 'https://token.actions.githubusercontent.com/.well-known/jwks';

function base64UrlToBytes(value) {
  if (typeof value !== 'string' || value.length === 0) {
    throw new Error('JWT segment must be a non-empty string');
  }
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
  const padded = normalized + '='.repeat((4 - (normalized.length % 4)) % 4);
  let binary;
  try {
    binary = atob(padded);
  } catch {
    throw new Error('JWT segment is not valid base64url');
  }
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return bytes;
}

function decodeJsonSegment(value, label) {
  try {
    const decoded = new TextDecoder().decode(base64UrlToBytes(value));
    const parsed = JSON.parse(decoded);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      throw new Error('not an object');
    }
    return parsed;
  } catch {
    throw new Error(`JWT ${label} is not valid JSON`);
  }
}

function audienceMatches(actual, expected) {
  if (typeof actual === 'string') return actual === expected;
  if (Array.isArray(actual)) return actual.includes(expected);
  return false;
}

function requireClaimString(claims, key) {
  const value = claims[key];
  if (typeof value !== 'string' || value.length === 0) {
    throw new Error(`Missing or invalid GitHub OIDC claim: ${key}`);
  }
  return value;
}

function requireIntegerClaim(claims, key) {
  const value = claims[key];
  if (!Number.isInteger(value)) {
    throw new Error(`Missing or invalid GitHub OIDC claim: ${key}`);
  }
  return value;
}

export function parseJwt(token) {
  if (typeof token !== 'string') throw new Error('OIDC token must be a string');
  const parts = token.split('.');
  if (parts.length !== 3 || parts.some((part) => part.length === 0)) {
    throw new Error('OIDC token must contain exactly three JWT segments');
  }

  const header = decodeJsonSegment(parts[0], 'header');
  const claims = decodeJsonSegment(parts[1], 'payload');
  const signature = base64UrlToBytes(parts[2]);
  const signedBytes = new TextEncoder().encode(`${parts[0]}.${parts[1]}`);

  return { header, claims, signature, signedBytes };
}

export function validateGithubOidcClaims(claims, policy, nowSeconds = Math.floor(Date.now() / 1000)) {
  if (!policy || typeof policy !== 'object') throw new Error('OIDC policy is required');

  const issuer = requireClaimString(claims, 'iss');
  if (issuer !== GITHUB_OIDC_ISSUER) throw new Error('Unexpected GitHub OIDC issuer');

  if (!audienceMatches(claims.aud, policy.audience)) {
    throw new Error('Unexpected GitHub OIDC audience');
  }

  const repository = requireClaimString(claims, 'repository');
  if (repository !== policy.repository) throw new Error('Unexpected GitHub repository');

  if (String(claims.repository_id ?? '') !== String(policy.repositoryId)) {
    throw new Error('Unexpected GitHub repository ID');
  }
  if (String(claims.repository_owner_id ?? '') !== String(policy.repositoryOwnerId)) {
    throw new Error('Unexpected GitHub repository owner ID');
  }

  const ref = requireClaimString(claims, 'ref');
  if (ref !== policy.ref) throw new Error('Unexpected GitHub ref');

  const refType = requireClaimString(claims, 'ref_type');
  if (refType !== policy.refType) throw new Error('Unexpected GitHub ref type');

  const workflowRef = requireClaimString(claims, 'workflow_ref');
  if (workflowRef !== policy.workflowRef) throw new Error('Unexpected GitHub workflow ref');

  const eventName = requireClaimString(claims, 'event_name');
  if (!policy.allowedEvents.includes(eventName)) throw new Error('Unexpected GitHub event');

  const runnerEnvironment = requireClaimString(claims, 'runner_environment');
  if (runnerEnvironment !== policy.runnerEnvironment) {
    throw new Error('Unexpected GitHub runner environment');
  }

  const subject = requireClaimString(claims, 'sub');
  if (!subject.startsWith(policy.subjectPrefix)) {
    throw new Error('Unexpected GitHub OIDC subject');
  }

  const sha = requireClaimString(claims, 'sha');
  if (!/^[0-9a-f]{40}$/i.test(sha)) throw new Error('Invalid GitHub commit SHA claim');

  const runId = requireClaimString(claims, 'run_id');
  if (!/^[0-9]+$/.test(runId)) throw new Error('Invalid GitHub run ID claim');

  requireClaimString(claims, 'jti');

  const exp = requireIntegerClaim(claims, 'exp');
  const iat = requireIntegerClaim(claims, 'iat');
  const nbf = requireIntegerClaim(claims, 'nbf');

  const skew = policy.clockSkewSeconds ?? 30;
  if (exp < nowSeconds - skew) throw new Error('GitHub OIDC token is expired');
  if (nbf > nowSeconds + skew) throw new Error('GitHub OIDC token is not active yet');
  if (iat > nowSeconds + skew) throw new Error('GitHub OIDC token issued-at time is in the future');
  if (nowSeconds - iat > policy.maxTokenAgeSeconds + skew) {
    throw new Error('GitHub OIDC token is too old');
  }
  if (exp - iat > policy.maxTokenLifetimeSeconds) {
    throw new Error('GitHub OIDC token lifetime is unexpectedly long');
  }

  return {
    repository,
    repositoryId: String(claims.repository_id),
    repositoryOwnerId: String(claims.repository_owner_id),
    ref,
    workflowRef,
    eventName,
    runnerEnvironment,
    sha,
    runId,
    jti: claims.jti,
    subject,
  };
}

async function loadGithubJwks(fetchImpl) {
  const response = await fetchImpl(GITHUB_OIDC_JWKS_URL, {
    method: 'GET',
    headers: { Accept: 'application/json' },
    redirect: 'error',
  });
  if (!response.ok) throw new Error('GitHub OIDC JWKS fetch failed');

  const payload = await response.json();
  if (!payload || !Array.isArray(payload.keys)) {
    throw new Error('GitHub OIDC JWKS response is malformed');
  }
  return payload;
}

export async function verifyGithubOidcJwt(
  token,
  policy,
  {
    fetchImpl = fetch,
    jwks = null,
    nowSeconds = Math.floor(Date.now() / 1000),
  } = {},
) {
  const parsed = parseJwt(token);
  if (parsed.header.alg !== 'RS256') throw new Error('GitHub OIDC token must use RS256');
  if (parsed.header.typ !== 'JWT') throw new Error('GitHub OIDC token must use JWT type');
  if (typeof parsed.header.kid !== 'string' || parsed.header.kid.length === 0) {
    throw new Error('GitHub OIDC token is missing kid');
  }

  const keySet = jwks ?? await loadGithubJwks(fetchImpl);
  const jwk = keySet.keys.find((candidate) =>
    candidate
    && candidate.kid === parsed.header.kid
    && candidate.kty === 'RSA'
    && (!candidate.alg || candidate.alg === 'RS256')
  );
  if (!jwk) throw new Error('GitHub OIDC signing key not found');

  const key = await crypto.subtle.importKey(
    'jwk',
    jwk,
    { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' },
    false,
    ['verify'],
  );
  const valid = await crypto.subtle.verify(
    { name: 'RSASSA-PKCS1-v1_5' },
    key,
    parsed.signature,
    parsed.signedBytes,
  );
  if (!valid) throw new Error('GitHub OIDC signature verification failed');

  const identity = validateGithubOidcClaims(parsed.claims, policy, nowSeconds);
  return { header: parsed.header, claims: parsed.claims, identity };
}

export { GITHUB_OIDC_ISSUER, GITHUB_OIDC_JWKS_URL };
