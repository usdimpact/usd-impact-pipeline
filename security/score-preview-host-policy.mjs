// Credential-free Cloudflare Pages hostname policy for the isolated Score Preview.
// Keep database/RPC access out of Pages Function imports entirely.
export const SCORE_DIRECT_PREVIEW_HOST =
  'fix-score-membership-handoff.usd-impact-pipeline.pages.dev';
export const SCORE_DIRECT_WEBSITE_ORIGIN =
  'https://usd-impact-site-9tmyrftod-usd-impact.vercel.app';

export function scoreDevBrokerPreviewEnabled(request, env) {
  if (env?.SCORE_DEV_BROKER_ENABLED !== 'true') return false;
  try {
    const url = new URL(request.url);
    return url.protocol === 'https:' && url.hostname === SCORE_DIRECT_PREVIEW_HOST &&
      (url.port === '' || url.port === '443');
  } catch {
    return false;
  }
}
