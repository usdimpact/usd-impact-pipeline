// Isolated in-memory Cloudflare Pages -> Supabase Edge broker -> Development
// RPC chain. No live network, account, secret or deployment mutation occurs.
import test from 'node:test';
import assert from 'node:assert/strict';
import { onRequest } from '../functions/_middleware.js';
import { onRequestPost } from '../functions/score-redeem.js';
import { handleScorePreviewBroker } from './score-preview-broker-server.mjs';
import { SCORE_PREVIEW_BROKER_URL } from './score-preview-broker-client.mjs';
import { SCORE_DIRECT_PREVIEW_HOST, SCORE_DIRECT_WEBSITE_ORIGIN } from './score-preview-dev-rpc.mjs';

const TICKET = 'T'.repeat(43);
const ACCOUNT = '11111111-1111-4111-8111-111111111111';
const SHARED = 's'.repeat(64);
const DB_KEY = 'sb_secret_' + 'd'.repeat(32);
const PREMIUM = 'ONLY_RESEARCH_MEMBERS_MAY_READ';
function machineJwt(overrides={}) {
  const encode=value=>Buffer.from(JSON.stringify(value)).toString('base64url');
  const payload={
    iss:'https://ycstrcvshdluovtuasjc.supabase.co/auth/v1',
    aud:'authenticated',
    role:'authenticated',
    sub:'11111111-1111-4111-8111-111111111111',
    is_anonymous:false,
    exp:Math.floor(Date.now()/1000)+600,
    ...overrides,
  };
  return encode({alg:'ES256',typ:'JWT'})+'.'+encode(payload)+'.'+'c'.repeat(64);
}
const MACHINE_JWT = machineJwt();

function fixture() {
  let unused = true, member = true, sessionDigest = null, premiumReads = 0;
  let brokerCalls = 0, dbCalls = 0, brokerUp = true;
  const env = {
    SCORE_DEV_BROKER_ENABLED: 'true',
    SCORE_EDGE_GATE_ENABLED: 'true',
    SCORE_EDGE_REDEMPTION_ENABLED: 'true',
    SCORE_PREVIEW_REDEMPTION_HOST: SCORE_DIRECT_PREVIEW_HOST,
    SCORE_EDGE_SHARED_SECRET: SHARED,
    SCORE_PREVIEW_MACHINE_JWT: MACHINE_JWT,
    SCORE_PREVIEW_MACHINE_SUB: '11111111-1111-4111-8111-111111111111',
    SCORE_BACKEND_URL: 'https://invalid-preview.example.test/api/score-edge-redeem',
    SCORE_VALIDATION_BACKEND_URL: 'https://invalid-preview.example.test/api/score-edge-validate',
  };
  async function dbFetch(url, options) {
    dbCalls++;
    assert.match(url, /^https:\/\/ycstrcvshdluovtuasjc\.supabase\.co\/rest\/v1\/rpc\//);
    assert.equal(options.headers.apikey, DB_KEY);
    assert.equal(options.headers.Authorization, undefined);
    const name = url.split('/').at(-1), body = JSON.parse(options.body);
    if (name === 'score_ticket_consume_atomic') {
      if (!unused) return Response.json(null);
      unused = false;
      return Response.json({
        digest:body.p_digest,account_id:ACCOUNT,audience:'score.usd-impact.com',path:'/en/',
        expires_at:new Date(Date.now()+40_000).toISOString(),
      });
    }
    if (name === 'score_membership_active') return Response.json(member);
    if (name === 'score_session_create') {
      sessionDigest=body.p_digest;
      return Response.json(member);
    }
    if (name === 'score_session_lookup') return Response.json(member && body.p_digest===sessionDigest ?
      {account_id:ACCOUNT,expires_at:new Date(Date.now()+10*60_000).toISOString()} : null);
    throw new Error('Unexpected database RPC: '+name);
  }
  async function cloudflareFetch(url, options) {
    brokerCalls++;
    assert.equal(url,SCORE_PREVIEW_BROKER_URL);
    assert.equal(options.headers['X-Score-Edge-Secret'],SHARED);
    assert.equal(options.headers.apikey,undefined,'Cloudflare must never hold the database key');
    assert.equal(options.headers.Authorization,'Bearer '+MACHINE_JWT);
    if (!brokerUp) throw new Error('Broker unreachable');
    const req=new Request(url,{method:'POST',headers:options.headers,body:options.body});
    return handleScorePreviewBroker(req,{
      enabled:'true',supabaseUrl:'https://ycstrcvshdluovtuasjc.supabase.co',
      sharedSecret:SHARED,supabaseSecretKey:DB_KEY,
      rateBudget:async()=>true,
    },dbFetch);
  }
  async function request(path, params={}) {
    const method=params.method||'GET';
    const headers={};
    if(params.cookie) headers.cookie=params.cookie;
    if(method==='POST'){
      headers['Content-Type']='application/x-www-form-urlencoded';
      if(params.origin!==undefined)headers.Origin=params.origin;
    }
    const req=new Request('https://'+(params.host||SCORE_DIRECT_PREVIEW_HOST)+path,{
      method,headers,...(method==='POST'?{body:new URLSearchParams({ticket:params.ticket||TICKET})}:{})
    });
    const selected={...env,...(params.override||{})};
    return onRequest({request:req,env:selected,next:()=>{
      if(path==='/score-redeem')return onRequestPost({request:req,env:selected});
      if(path==='/data/score_v2_methodology.json')return new Response('PUBLIC_METHOD',{status:200});
      premiumReads++;return new Response(PREMIUM,{status:200});
    }});
  }
  return {request,cloudflareFetch,get dbCalls(){return dbCalls;},
    get brokerCalls(){return brokerCalls;},get premiumReads(){return premiumReads;},
    revoke(){member=false},brokerDown(){brokerUp=false}};
}
test('Preview: opaque POST -> broker -> DB -> host-only session -> recheck -> revoke',async(t)=>{
  const f=fixture(),original=globalThis.fetch;
  globalThis.fetch=f.cloudflareFetch;t.after(()=>{globalThis.fetch=original;});
  assert.equal((await f.request('/en/')).status,403);
  assert.equal(f.premiumReads,0);
  const publicFile=await f.request('/data/score_v2_methodology.json');
  assert.equal(publicFile.status,200);
  assert.equal(await publicFile.text(),'PUBLIC_METHOD');
  const granted=await f.request('/score-redeem',{method:'POST',origin:SCORE_DIRECT_WEBSITE_ORIGIN});
  assert.equal(granted.status,303);
  assert.equal(granted.headers.get('Location'),'/en/');
  const setCookie=granted.headers.get('Set-Cookie');
  assert.match(setCookie,/^__Host-score_session=[A-Za-z0-9_-]{43};/);
  for(const s of ['Secure','HttpOnly','SameSite=Lax','Path=/'])assert.ok(setCookie.includes(s));
  assert.equal(setCookie.includes(TICKET),false);
  const cookie=setCookie.split(';')[0];
  const member=await f.request('/en/',{cookie});
  assert.equal(member.status,200);
  assert.equal(await member.text(),PREMIUM);
  assert.equal(member.headers.get('Cache-Control'),'private, no-store');
  assert.equal((await f.request('/archive/en/',{cookie})).status,200);
  assert.equal(f.premiumReads,2);
  assert.equal((await f.request('/score-redeem',{method:'POST',origin:SCORE_DIRECT_WEBSITE_ORIGIN})).status,403);
  f.revoke();
  const rejected=await f.request('/en/',{cookie});
  assert.equal(rejected.status,403);
  assert.equal((await rejected.text()).includes(PREMIUM),false);
  assert.equal(f.premiumReads,2);
  assert.ok(f.brokerCalls>=5);
  assert.ok(f.dbCalls>=5);
});
test('wrong host, wrong Origin, absent flags, broken broker all deny without serving premium content',async(t)=>{
  const f=fixture(),original=globalThis.fetch;
  globalThis.fetch=f.cloudflareFetch;t.after(()=>{globalThis.fetch=original;});
  for(const origin of [undefined,'https://attacker.test','null']){
    assert.equal((await f.request('/score-redeem',{method:'POST',origin})).status,403);
  }
  assert.equal(f.brokerCalls,0);
  assert.equal((await f.request('/score-redeem',{
    method:'POST',origin:SCORE_DIRECT_WEBSITE_ORIGIN,host:'score.usd-impact.com'})).status,403);
  assert.equal((await f.request('/score-redeem',{
    method:'POST',origin:SCORE_DIRECT_WEBSITE_ORIGIN,host:'other.usd-impact-pipeline.pages.dev'})).status,403);
  assert.equal((await f.request('/score-redeem',{
    method:'POST',origin:SCORE_DIRECT_WEBSITE_ORIGIN,override:{SCORE_EDGE_REDEMPTION_ENABLED:'false'}})).status,503);
  assert.equal((await f.request('/en/',{
    cookie:'__Host-score_session='+'S'.repeat(43),override:{SCORE_EDGE_GATE_ENABLED:'false'}})).status,403);
  f.brokerDown();
  assert.equal((await f.request('/score-redeem',{
    method:'POST',origin:SCORE_DIRECT_WEBSITE_ORIGIN})).status,503);
  assert.equal((await f.request('/en/',{
    cookie:'__Host-score_session='+'S'.repeat(43)})).status,403);
  assert.equal(f.premiumReads,0);
});
