import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import {
  SCORE_DIRECT_PREVIEW_HOST, SCORE_DIRECT_WEBSITE_ORIGIN,
  scoreDirectDevEnabled, scoreDigest, redeemScoreDevTicket,
  scoreDevSessionAllowed,
} from './score-preview-dev-rpc.mjs';

const ticket = 'T'.repeat(43);
const ACCOUNT = '11111111-1111-4111-8111-111111111111';
const KEY = 'sb_secret_' + 'A'.repeat(36);
const env = Object.freeze({
  SCORE_DIRECT_DEV_BACKEND_ENABLED: 'true',
  SCORE_PREVIEW_SUPABASE_SECRET_KEY: KEY,
});
const sha = s => createHash('sha256').update(s).digest('hex');

function buildRpcFixture() {
  let active = true;
  let unconsumed = true;
  let sessionDigest = null;
  let reads = 0;
  const requests = [];
  async function fetchStub(url, options) {
    requests.push({url, options});
    assert.equal(options.method, 'POST');
    assert.equal(options.redirect, 'error');
    assert.equal(options.cache, 'no-store');
    assert.equal(options.headers.apikey, KEY);
    assert.equal(options.headers.Authorization, undefined);
    assert.equal(options.headers['Content-Type'], 'application/json');
    assert.match(url, /^https:\/\/ycstrcvshdluovtuasjc\.supabase\.co\/rest\/v1\/rpc\//);
    const rpc = url.split('/').at(-1);
    const data = JSON.parse(options.body);
    if (rpc === 'score_ticket_consume_atomic') {
      assert.equal(data.p_digest, sha(ticket));
      if (!unconsumed) return Response.json(null);
      unconsumed = false;
      return Response.json({
        digest: sha(ticket), account_id: ACCOUNT,
        audience: 'score.usd-impact.com', path: '/en/',
        expires_at: new Date(Date.now() + 40_000).toISOString(),
      });
    }
    if (rpc === 'score_membership_active') {
      assert.equal(data.p_account_id, ACCOUNT);
      return Response.json(active);
    }
    if (rpc === 'score_session_create') {
      assert.equal(data.p_account_id, ACCOUNT);
      assert.match(data.p_digest, /^[0-9a-f]{64}$/);
      assert.ok(Date.parse(data.p_expires_at) > Date.now());
      sessionDigest = data.p_digest;
      return Response.json(active);
    }
    if (rpc === 'score_session_lookup') {
      reads++;
      return Response.json(active && sessionDigest === data.p_digest ? {
        account_id: ACCOUNT,
        expires_at: new Date(Date.now() + 12 * 60_000).toISOString(),
      } : null);
    }
    throw new Error('Unexpected RPC call');
  }
  return {fetchStub, requests, get reads(){return reads;}, revoke(){active=false;}};
}

test('direct Development mode is isolated to one exact HTTPS Cloudflare Preview host', () => {
  const req = url => new Request(url);
  assert.equal(scoreDirectDevEnabled(req('https://' + SCORE_DIRECT_PREVIEW_HOST + '/en/'), env), true);
  for (const url of [
    'https://score.usd-impact.com/en/',
    'https://usd-impact-pipeline.pages.dev/en/',
    'https://evil.usd-impact-pipeline.pages.dev/en/',
    'http://' + SCORE_DIRECT_PREVIEW_HOST + '/en/',
    'https://' + SCORE_DIRECT_PREVIEW_HOST + '.attacker.test/en/',
  ]) assert.equal(scoreDirectDevEnabled(req(url), env), false);
  assert.equal(scoreDirectDevEnabled(req('https://' + SCORE_DIRECT_PREVIEW_HOST), {...env,SCORE_DIRECT_DEV_BACKEND_ENABLED:'false'}),false);
  assert.equal(SCORE_DIRECT_WEBSITE_ORIGIN, 'https://usd-impact-site-qjfsh5lm7-usd-impact.vercel.app');
});

test('SHA-256 digests match existing Vercel ticket/session contract', async () => {
  assert.equal(await scoreDigest(ticket), sha(ticket));
  assert.equal(await scoreDigest('bad'), null);
  assert.equal(await scoreDigest(''), null);
});

test('one-use redemption creates independent bearer session, revalidates on each request and revokes', async () => {
  const f=buildRpcFixture();
  const created=await redeemScoreDevTicket(ticket,env,f.fetchStub);
  assert.equal(created.allowed,true);
  assert.equal(created.path,'/en/');
  assert.match(created.token,/^[A-Za-z0-9_-]{43}$/);
  assert.notEqual(created.token,ticket);
  assert.equal(created.expiresAtMs>Date.now(),true);
  assert.equal(f.requests.length,3);
  assert.equal(await scoreDevSessionAllowed(created.token,env,f.fetchStub),true);
  assert.equal(await scoreDevSessionAllowed(created.token,env,f.fetchStub),true);
  assert.equal(f.reads,2);
  assert.equal(await redeemScoreDevTicket(ticket,env,f.fetchStub),null,'replay must fail');
  f.revoke();
  assert.equal(await scoreDevSessionAllowed(created.token,env,f.fetchStub),false);
});

test('missing or malformed Development key fails without a credential-bearing request', async () => {
  let calls=0;
  const stub=async()=>{calls++;throw Error('no network allowed')};
  for(const invalid of [undefined, '', 'sk_live_'+'x'.repeat(32),'sb_secret_short']) {
    await assert.rejects(()=>redeemScoreDevTicket(ticket,{...env,SCORE_PREVIEW_SUPABASE_SECRET_KEY:invalid},stub));
  }
  assert.equal(calls,0);
});

test('wrong ticket and upstream failures fail closed', async () => {
  const f=buildRpcFixture();
  assert.equal(await redeemScoreDevTicket('bad',env,f.fetchStub),null);
  assert.equal(await scoreDevSessionAllowed('bad',env,f.fetchStub),false);
  assert.equal(f.requests.length,0);
  await assert.rejects(()=>redeemScoreDevTicket(ticket,env,async()=>new Response('outage',{status:503})));
  await assert.rejects(()=>redeemScoreDevTicket(ticket,env,async()=>{throw Error('offline')}));
});

test('a ticket that is not an active Research member cannot mint a session', async () => {
  let calls=0;
  const fake=async(url,options)=>{
    calls++;
    const name=url.split('/').at(-1);
    if(name==='score_ticket_consume_atomic')return Response.json({
      digest:sha(ticket),account_id:ACCOUNT,audience:'score.usd-impact.com',path:'/en/',
      expires_at:new Date(Date.now()+40_000).toISOString(),
    });
    if(name==='score_membership_active')return Response.json(false);
    throw Error('session must not be minted');
  };
  assert.equal(await redeemScoreDevTicket(ticket,env,fake),null);
  assert.equal(calls,2);
});
