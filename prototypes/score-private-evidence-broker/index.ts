import { createClient } from 'npm:@supabase/supabase-js@2.95.0';

import {
  BROKER_MODE,
  MAX_BODY_BYTES,
  STORAGE_BUCKET,
  buildOidcPolicy,
  objectPathForWeek,
  parseBearerToken,
  requireBrokerOperation,
  sha256Hex,
  validateBucketMetadata,
  validateDeclaredSha256,
  validateSyntheticBundleBytes,
  validateSyntheticWeek,
} from './broker-core.mjs';
import { verifyGithubOidcJwt } from './github-oidc.mjs';

const SECURITY_HEADERS = Object.freeze({
  'Cache-Control': 'private, no-store',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'no-referrer',
  'Content-Security-Policy': "default-src 'none'; base-uri 'none'; frame-ancestors 'none'",
});

function jsonResponse(status, payload) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      ...SECURITY_HEADERS,
      'Content-Type': 'application/json; charset=utf-8',
    },
  });
}

function errorResponse(status, code) {
  return jsonResponse(status, { error: code });
}

function audit({ operation, week, identity, sha256 = null, result }) {
  console.log(JSON.stringify({
    event: 'score-private-evidence-broker',
    operation,
    week,
    repository_id: identity?.repositoryId ?? null,
    run_id: identity?.runId ?? null,
    workflow_ref: identity?.workflowRef ?? null,
    commit_sha: identity?.sha ?? null,
    object_sha256: sha256,
    result,
  }));
}

function getAdminClient() {
  const url = Deno.env.get('SUPABASE_URL');
  const rawKeys = Deno.env.get('SUPABASE_SECRET_KEYS');
  if (!url || !rawKeys) throw new Error('broker_not_configured');

  let keys;
  try {
    keys = JSON.parse(rawKeys);
  } catch {
    throw new Error('broker_not_configured');
  }

  const secret = keys?.default;
  if (typeof secret !== 'string' || secret.length === 0) {
    throw new Error('broker_not_configured');
  }

  return createClient(url, secret, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
      detectSessionInUrl: false,
    },
  });
}

async function assertBucketSafety(client) {
  const { data, error } = await client.storage.getBucket(STORAGE_BUCKET);
  if (error || !data) throw new Error('bucket_policy_mismatch');
  validateBucketMetadata(data);
}

async function readStoredBytes(client, objectPath) {
  const { data, error } = await client.storage
    .from(STORAGE_BUCKET)
    .download(objectPath);
  if (error || !data) return { bytes: null, error: true };

  const bytes = new Uint8Array(await data.arrayBuffer());
  if (bytes.byteLength === 0 || bytes.byteLength > MAX_BODY_BYTES) {
    return { bytes: null, error: true };
  }
  return { bytes, error: false };
}

async function handleWrite(req, client, week, objectPath, identity) {
  const contentType = req.headers.get('content-type') ?? '';
  if (!contentType.toLowerCase().startsWith('application/json')) {
    return errorResponse(415, 'json_required');
  }

  const declaredLength = req.headers.get('content-length');
  if (declaredLength && Number(declaredLength) > MAX_BODY_BYTES) {
    return errorResponse(413, 'bundle_too_large');
  }

  const body = new Uint8Array(await req.arrayBuffer());
  if (body.byteLength > MAX_BODY_BYTES) {
    return errorResponse(413, 'bundle_too_large');
  }

  try {
    validateSyntheticBundleBytes(body, week);
  } catch {
    return errorResponse(400, 'synthetic_bundle_rejected');
  }

  let declaredSha;
  try {
    declaredSha = validateDeclaredSha256(req.headers.get('x-score-content-sha256'));
  } catch {
    return errorResponse(400, 'invalid_declared_sha256');
  }

  const actualSha = await sha256Hex(body);
  if (actualSha !== declaredSha) {
    return errorResponse(400, 'content_sha256_mismatch');
  }

  const { error: uploadError } = await client.storage
    .from(STORAGE_BUCKET)
    .upload(objectPath, body, {
      contentType: 'application/json',
      cacheControl: '0',
      upsert: false,
    });

  if (uploadError) {
    audit({ operation: 'write', week, identity, sha256: actualSha, result: 'create_refused' });
    return errorResponse(409, 'archive_create_refused');
  }

  const readback = await readStoredBytes(client, objectPath);
  if (readback.error) {
    audit({ operation: 'write', week, identity, sha256: actualSha, result: 'readback_failed' });
    return errorResponse(500, 'archive_readback_failed');
  }

  const readbackSha = await sha256Hex(readback.bytes);
  if (readbackSha !== actualSha) {
    audit({ operation: 'write', week, identity, sha256: actualSha, result: 'readback_hash_mismatch' });
    return errorResponse(500, 'archive_readback_hash_mismatch');
  }

  audit({ operation: 'write', week, identity, sha256: actualSha, result: 'created' });
  return jsonResponse(201, {
    schema_version: 'score-private-evidence-broker-receipt-v1',
    operation: 'write',
    synthetic_rehearsal: true,
    week,
    object_path: objectPath,
    sha256: actualSha,
    repository_id: identity.repositoryId,
    workflow_run_id: identity.runId,
    commit_sha: identity.sha,
  });
}

async function handleRead(req, client, week, objectPath, identity) {
  const declaredLength = req.headers.get('content-length');
  if (declaredLength && Number(declaredLength) > 0) {
    return errorResponse(400, 'read_body_not_allowed');
  }

  const stored = await readStoredBytes(client, objectPath);
  if (stored.error) {
    audit({ operation: 'read', week, identity, result: 'not_found' });
    return errorResponse(404, 'archive_not_found');
  }

  try {
    validateSyntheticBundleBytes(stored.bytes, week);
  } catch {
    audit({ operation: 'read', week, identity, result: 'stored_bundle_rejected' });
    return errorResponse(500, 'stored_bundle_rejected');
  }

  const sha = await sha256Hex(stored.bytes);
  audit({ operation: 'read', week, identity, sha256: sha, result: 'served' });

  return new Response(stored.bytes, {
    status: 200,
    headers: {
      ...SECURITY_HEADERS,
      'Content-Type': 'application/json',
      'Content-Length': String(stored.bytes.byteLength),
      'X-Score-Week': week,
      'X-Score-Content-Sha256': sha,
    },
  });
}

Deno.serve(async (req) => {
  if ((Deno.env.get('SCORE_BROKER_MODE') ?? BROKER_MODE) !== BROKER_MODE) {
    return errorResponse(503, 'unsupported_broker_mode');
  }
  if (req.method !== 'POST') return errorResponse(405, 'post_required');

  const url = new URL(req.url);
  if (url.search.length > 0) return errorResponse(400, 'query_parameters_not_allowed');

  let operation;
  let week;
  let token;
  try {
    operation = requireBrokerOperation(req.headers.get('x-score-operation'));
    week = validateSyntheticWeek(req.headers.get('x-score-week'));
    token = parseBearerToken(req.headers.get('authorization'));
  } catch {
    return errorResponse(400, 'invalid_request_headers');
  }

  let verification;
  try {
    verification = await verifyGithubOidcJwt(token, buildOidcPolicy(operation));
  } catch {
    audit({ operation, week, identity: null, result: 'oidc_rejected' });
    return errorResponse(401, 'oidc_rejected');
  }

  const objectPath = objectPathForWeek(week);

  let client;
  try {
    client = getAdminClient();
  } catch {
    audit({ operation, week, identity: verification.identity, result: 'broker_not_configured' });
    return errorResponse(503, 'broker_not_configured');
  }

  try {
    await assertBucketSafety(client);
  } catch {
    audit({ operation, week, identity: verification.identity, result: 'bucket_policy_mismatch' });
    return errorResponse(503, 'bucket_policy_mismatch');
  }

  if (operation === 'write') {
    return handleWrite(req, client, week, objectPath, verification.identity);
  }
  return handleRead(req, client, week, objectPath, verification.identity);
});
