// Development-only broker, deployed with activation disabled. NEVER deploy to Production.
// Source edits require independent CI review before staging a replacement.
// Deployment MUST use verify_jwt=false because this is a server-to-server
// shared-secret protocol, not a user JWT flow. The handler validates its own
// high-entropy secret and is disabled unless explicitly enabled.
import { handleScorePreviewBroker } from '../../../security/score-preview-broker-server.mjs';
import { claimScoreDevBrokerBudget } from '../../../security/score-preview-dev-rpc.mjs';

Deno.serve((request: Request) => {
  let secretKey = '';
  try {
    const keys = JSON.parse(Deno.env.get('SUPABASE_SECRET_KEYS') || '{}');
    if (typeof keys.default === 'string') secretKey = keys.default;
  } catch { /* fail closed below */ }
  return handleScorePreviewBroker(request, {
    enabled: Deno.env.get('SCORE_PREVIEW_BROKER_ENABLED') || 'false',
    supabaseUrl: Deno.env.get('SUPABASE_URL') || '',
    supabaseSecretKey: secretKey,
    sharedSecret: Deno.env.get('SCORE_EDGE_SHARED_SECRET') || '',
    rateBudget: (action: string) => claimScoreDevBrokerBudget(action, {
      SCORE_PREVIEW_SUPABASE_SECRET_KEY: secretKey,
    }),
  });
});
