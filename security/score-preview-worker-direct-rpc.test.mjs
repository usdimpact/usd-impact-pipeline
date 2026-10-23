import test from 'node:test';
import assert from 'node:assert/strict';
import { handleScoreWorkerPreview } from '../workers/score-preview/index.mjs';
import { SCORE_DIRECT_WEBSITE_ORIGIN } from './score-preview-host-policy.mjs';

const HOST='https://pr-148-usd-impact-score-isolated-dev.example.workers.dev';
const TICKET='T'.repeat(43);
const ACCOUNT='11111111-1111-4111-8111-111111111111';
const DB_KEY=['sb','secret','d'.repeat(32)].join('_');
const PREMIUM='PRIVATE_SCORE_BYTES';

function fixture(){
  let active=true, unused=true, sessionDigest=null, assetReads=0;
  const calls=[];
  const env={
    SCORE_WORKER_PREVIEW_ENABLED:'true',
    SCORE_WORKER_PREVIEW_ORIGIN:HOST,
    SCORE_DEV_DIRECT_RPC_ENABLED:'true',
    SCORE_EDGE_GATE_ENABLED:'true',
    SCORE_EDGE_REDEMPTION_ENABLED:'true',
    SCORE_PREVIEW_SUPABASE_SECRET_KEY:DB_KEY,
    SCORE_PREVIEW_REDEEM_LIMIT:{limit:async()=>({success:true})},
    SCORE_PREVIEW_VALIDATE_LIMIT:{limit:async()=>({success:true})},
    ASSETS:{fetch:async()=>{assetReads++;return new Response(PREMIUM,{status:200});}},
  };
  async function rpcFetch(url,opts){
    calls.push(url);
    assert.match(url,/^https:\/\/ycstrcvshdluovtuasjc\.supabase\.co\/rest\/v1\/rpc\//);
    assert.equal(url.includes('/functions/v1/'),false);
    assert.equal(opts.headers.apikey,DB_KEY);
    assert.equal(opts.headers.Authorization,undefined);
    assert.equal(opts.headers['X-Score-Edge-Secret'],undefined);
    const name=url.split('/').at(-1);
    const body=JSON.parse(opts.body);
    if(name==='score_ticket_consume_atomic'){
      if(!unused)return Response.json(null);
      unused=false;
      return Response.json({
        digest:body.p_digest,account_id:ACCOUNT,audience:'score.usd-impact.com',
        path:'/en/',expires_at:new Date(Date.now()+40_000).toISOString(),
      });
    }
    if(name==='score_membership_active')return Response.json(active);
    if(name==='score_session_create'){sessionDigest=body.p_digest;return Response.json(active);}
    if(name==='score_session_lookup')return Response.json(active&&body.p_digest===sessionDigest?{
      account_id:ACCOUNT,expires_at:new Date(Date.now()+10*60_000).toISOString(),
    }:null);
    throw new Error('unexpected RPC '+name);
  }
  function request(path,{method='GET',origin,token}={}){
    const headers={};
    if(origin)headers.Origin=origin;
    if(token)headers.Cookie='__Host-score_session='+token;
    if(method==='POST')headers['Content-Type']='application/x-www-form-urlencoded';
    return new Request(HOST+path,{method,headers,...(method==='POST'?{
      body:new URLSearchParams({ticket:TICKET}),
    }:{})});
  }
  return {env,request,rpcFetch,calls,get assetReads(){return assetReads;},revoke(){active=false;}};
}

test('isolated Worker uses direct Development RPC and never public Edge broker',async t=>{
  const f=fixture(), old=globalThis.fetch;
  globalThis.fetch=f.rpcFetch;
  t.after(()=>{globalThis.fetch=old;});

  const redeemed=await handleScoreWorkerPreview(f.request('/score-redeem',{
    method:'POST',origin:SCORE_DIRECT_WEBSITE_ORIGIN,
  }),f.env);
  assert.equal(redeemed.status,303);
  const setCookie=redeemed.headers.get('Set-Cookie');
  assert.match(setCookie,/^__Host-score_session=[A-Za-z0-9_-]{43};/);
  for(const attr of ['Secure','HttpOnly','SameSite=Lax','Path=/'])assert.ok(setCookie.includes(attr));
  const token=setCookie.match(/^__Host-score_session=([A-Za-z0-9_-]{43});/)[1];

  const allowed=await handleScoreWorkerPreview(f.request('/en/',{token}),f.env);
  assert.equal(allowed.status,200);
  assert.equal(await allowed.text(),PREMIUM);
  assert.equal(f.assetReads,1);

  const replay=await handleScoreWorkerPreview(f.request('/score-redeem',{
    method:'POST',origin:SCORE_DIRECT_WEBSITE_ORIGIN,
  }),f.env);
  assert.equal(replay.status,403);

  f.revoke();
  assert.equal((await handleScoreWorkerPreview(f.request('/en/',{token}),f.env)).status,403);
  assert.equal(f.assetReads,1);
  assert.ok(f.calls.length>=6);
  assert.equal(f.calls.some(x=>x.includes('/functions/v1/score-preview-broker')),false);
});

test('Cloudflare limiter failure blocks before any Development RPC',async t=>{
  const f=fixture(), old=globalThis.fetch;
  let network=0;
  globalThis.fetch=async()=>{network++;throw new Error('network must not run');};
  t.after(()=>{globalThis.fetch=old;});
  const env={...f.env,SCORE_PREVIEW_REDEEM_LIMIT:{limit:async()=>({success:false})}};
  const result=await handleScoreWorkerPreview(f.request('/score-redeem',{
    method:'POST',origin:SCORE_DIRECT_WEBSITE_ORIGIN,
  }),env);
  assert.equal(result.status,429);
  assert.equal(network,0);
});
