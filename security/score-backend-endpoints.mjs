// Exact backend allowlist for the Score membership handshake (issue #147).
// No arbitrary HTTPS origin may receive the encrypted edge shared secret.
// The pinned Preview deployment changes only after a reviewed update to this
// contract, never by untrusted request input or an accidental env typo.
const SCORE_BACKEND_HOSTS = new Set([
  'www.usd-impact.com',
  'usd-impact-site-qjfsh5lm7-usd-impact.vercel.app',
]);
const SCORE_BACKEND_PATHS = new Set([
  '/api/score-edge-redeem',
  '/api/score-edge-validate',
]);

export function scoreBackendEndpoint(value, requiredPath) {
  if (typeof value !== 'string' || !SCORE_BACKEND_PATHS.has(requiredPath)) return null;
  try {
    const url = new URL(value);
    if (url.protocol !== 'https:' || !SCORE_BACKEND_HOSTS.has(url.hostname) ||
        url.pathname !== requiredPath || url.username || url.password ||
        url.search || url.hash || url.port) return null;
    return url.href;
  } catch {
    return null;
  }
}
