import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { handleScoreWorkerPreview } from '../workers/score-preview/index.mjs';
import { SCORE_DIRECT_WEBSITE_ORIGIN } from './score-preview-host-policy.mjs';

const HOST = 'https://pr-148-usd-impact-score-isolated-dev.example.workers.dev';
const TOKEN = 'T'.repeat(43);
const SESSION = 'S'.repeat(43);
const SECRET = 's'.repeat(64);
const PREMIUM = 'PRIVATE_SCORE_DASHBOARD_DATA';

function setup(overrides = {}) {
  let assetReads = 0;
  const rateCalls = [];
  const env = {
    SCORE_WORKER_PREVIEW_ENABLED: 'true',
    SCORE_WORKER_PREVIEW_ORIGIN: HOST,
    SCORE_DEV_BROKER_ENABLED: 'false',
    SCORE_EDGE_GATE_ENABLED: 'false',
    SCORE_EDGE_REDEMPTION_ENABLED: 'false',
    SCORE_EDGE_SHARED_SECRET: SECRET,
    ASSETS: {
      async fetch() {
        assetReads++;
        return new Response(PREMIUM, {status:200,headers:{'Content-Type':'text/plain'}});
      },
    },
    SCORE_PREVIEW_REDEEM_LIMIT: {
      async limit({key}) { rateCalls.push(['redeem', key]); return {success:true}; },
    },
    SCORE_PREVIEW_VALIDATE_LIMIT: {
      async limit({key}) { rateCalls.push(['validate', key]); return {success:true}; },
    },
    ...overrides,
  };
  function request(path, {method='GET',origin,token,body,host=HOST} = {}) {
    const headers = {};
    if (origin !== undefined) headers.Origin = origin;
    if (token) headers.Cookie = '__Host-score_session=' + token;
    if (method === 'POST') headers['Content-Type'] = 'application/x-www-form-urlencoded';
    return new Request(host + path, {method,headers,...(method==='POST'?{body:body??new URLSearchParams({ticket:TOKEN})}:{})});
  }
  return {
    env,request,
    get assetReads() {return assetReads;},
    rateCalls,
  };
}

test('Worker Preview is closed by default even for published static assets', async () => {
  const f = setup({SCORE_WORKER_PREVIEW_ENABLED:'false'});
  for (const path of ['/en/','/data/score_v2_methodology.json','/archive/en/']) {
    const response = await handleScoreWorkerPreview(f.request(path), f.env);
    assert.equal(response.status, 503);
    assert.equal(response.headers.get('Set-Cookie'), null);
  }
  assert.equal(f.assetReads,0);
});

test('Worker Preview permits only one explicitly configured workers.dev origin', async () => {
  const f = setup();
  for (const host of [
    'https://score.usd-impact.com',
    'https://usd-impact-pipeline.pages.dev',
    'https://other.example.workers.dev',
    'http://pr-148-usd-impact-score-isolated-dev.example.workers.dev',
  ]) {
    assert.equal((await handleScoreWorkerPreview(f.request('/data/score_v2_methodology.json',{host}),f.env)).status,403,host);
  }
  assert.equal((await handleScoreWorkerPreview(f.request('/data/score_v2_methodology.json?x=1'),f.env)).status,403);
  assert.equal((await handleScoreWorkerPreview(f.request('/data/score_v2_methodology.json'),
    {...f.env,SCORE_WORKER_PREVIEW_ORIGIN:'https://score.usd-impact.com'})).status,403);
  assert.equal(f.assetReads,0);
});

test('public allowlisted research assets remain accessible but premium HTML is protected', async () => {
  const f=setup();
  const publicAsset=await handleScoreWorkerPreview(f.request('/data/score_v2_methodology.json'), f.env);
  assert.equal(publicAsset.status,200);
  assert.equal(await publicAsset.text(),PREMIUM);
  assert.equal(publicAsset.headers.get('Cache-Control'),'public, max-age=300');
  assert.match(publicAsset.headers.get('Content-Security-Policy'),/frame-ancestors/);
  assert.equal((await handleScoreWorkerPreview(f.request('/en/'),f.env)).status,403);
  assert.equal((await handleScoreWorkerPreview(f.request('/archive/es/'),f.env)).status,403);
  assert.equal((await handleScoreWorkerPreview(f.request('/data/private_unreleased.json'),f.env)).status,403);
  assert.equal((await handleScoreWorkerPreview(f.request('/data/research/score_v2_robustness_latest.json'),f.env)).status,200);
  assert.equal(f.assetReads,2);
});

test('rate limit binding absence and exhaustion deny before any ticket/network operation', async () => {
  const f=setup({SCORE_EDGE_REDEMPTION_ENABLED:'true',SCORE_DEV_BROKER_ENABLED:'true'});
  const post=f.request('/score-redeem',{method:'POST',origin:SCORE_DIRECT_WEBSITE_ORIGIN});
  assert.equal((await handleScoreWorkerPreview(post,{...f.env,SCORE_PREVIEW_REDEEM_LIMIT:null})).status,503);
  const blocked = await handleScoreWorkerPreview(
    f.request('/score-redeem',{method:'POST',origin:SCORE_DIRECT_WEBSITE_ORIGIN}),
    {...f.env,SCORE_PREVIEW_REDEEM_LIMIT:{limit:async()=>({success:false})}}
  );
  assert.equal(blocked.status,429);
  assert.equal(blocked.headers.get('Retry-After'),'60');
  const noOrigin = await handleScoreWorkerPreview(
    f.request('/score-redeem',{method:'POST',origin:'https://wrong.example.test'}),f.env);
  assert.equal(noOrigin.status,403);
  assert.equal(f.assetReads,0);
});

test('mock authenticated redemption, cookie validation, revocation and replay stay server-side',async t=>{
  const f=setup({SCORE_EDGE_REDEMPTION_ENABLED:'true',SCORE_DEV_BROKER_ENABLED:'true',SCORE_EDGE_GATE_ENABLED:'true'});
  const original=globalThis.fetch;
  t.after(()=>{globalThis.fetch=original;});
  let member=true, unconsumed=true, calls=0;
  globalThis.fetch=async(url,opts)=>{
    calls++;
    assert.equal(url,'https://ycstrcvshdluovtuasjc.supabase.co/functions/v1/score-preview-broker');
    assert.equal(opts.headers['X-Score-Edge-Secret'],SECRET);
    assert.equal(opts.headers.apikey,undefined);
    const body=JSON.parse(opts.body);
    if(body.action==='redeem'){
      if(!unconsumed)return Response.json({allowed:false},{status:403});
      unconsumed=false;
      assert.equal(body.ticket,TOKEN);
      return Response.json({allowed:true,token:SESSION,path:'/en/',expiresAtMs:Date.now()+8*60_000});
    }
    assert.equal(body.action,'validate');
    assert.equal(body.token,SESSION);
    return member?Response.json({allowed:true}):Response.json({allowed:false},{status:403});
  };
  const redeemed=await handleScoreWorkerPreview(f.request('/score-redeem',{
    method:'POST',origin:SCORE_DIRECT_WEBSITE_ORIGIN}),f.env);
  assert.equal(redeemed.status,303);
  assert.equal(redeemed.headers.get('Location'),'/en/');
  const cookie=redeemed.headers.get('Set-Cookie');
  assert.match(cookie,/^__Host-score_session=[A-Za-z0-9_-]{43};/);
  for(const flag of ['HttpOnly','Secure','SameSite=Lax','Path=/'])assert.ok(cookie.includes(flag));
  assert.ok(!cookie.includes(TOKEN));
  assert.equal(f.assetReads,0);
  const session=await handleScoreWorkerPreview(f.request('/en/',{token:SESSION}),f.env);
  assert.equal(session.status,200);
  assert.equal(await session.text(),PREMIUM);
  assert.equal(session.headers.get('Cache-Control'),'private, no-store');
  assert.equal(f.assetReads,1);
  const replay=await handleScoreWorkerPreview(f.request('/score-redeem',{
    method:'POST',origin:SCORE_DIRECT_WEBSITE_ORIGIN}),f.env);
  assert.equal(replay.status,403);
  member=false;
  const revoked=await handleScoreWorkerPreview(f.request('/en/',{token:SESSION}),f.env);
  assert.equal(revoked.status,403);
  assert.equal(f.assetReads,1);
  assert.equal(calls,4);
  assert.ok(f.rateCalls.some(([k])=>k==='redeem'));
  assert.ok(f.rateCalls.some(([k])=>k==='validate'));
  assert.ok(f.rateCalls.every(([k,v])=>k==='validate'?v.startsWith('session:')&&!v.includes(SESSION):true));
});

test('preview-only rate limiting configuration and asset-first bypass are statically forbidden',()=>{
  const config=JSON.parse(readFileSync(new URL('../workers/score-preview/wrangler.jsonc',import.meta.url),'utf8'));
  assert.equal(config.workers_dev,false);
  assert.equal(config.preview_urls,true);
  assert.equal(config.assets.run_worker_first,true);
  assert.equal(config.assets.binding,'ASSETS');
  assert.equal(config.assets.directory,'../../public');
  assert.equal(config.routes,undefined);
  assert.equal(config.previews.vars.SCORE_WORKER_PREVIEW_ENABLED,'false');
  for(const key of ['SCORE_DEV_BROKER_ENABLED','SCORE_EDGE_GATE_ENABLED','SCORE_EDGE_REDEMPTION_ENABLED']){
    assert.equal(config.previews.vars[key],'false');
    assert.equal(config.vars[key],'false');
  }
  assert.equal(config.previews.ratelimits.length,2);
  assert.equal(new Set(config.previews.ratelimits.map(x=>x.namespace_id)).size,2);
  for(const limiter of config.previews.ratelimits){
    assert.match(limiter.namespace_id,/^\d+$/);
    assert.equal(limiter.simple.period,60);
  }
  const ignore=readFileSync(new URL('../public/.assetsignore',import.meta.url),'utf8');
  assert.ok(ignore.includes('_headers'));
  assert.ok(ignore.includes('_redirects'));
});

test('Worker Preview dependency graph excludes private Supabase RPC modules',()=>{
  const root=fileURLToPath(new URL('../',import.meta.url));
  const allowed=new Set([
    'workers/score-preview/index.mjs',
    'security/score-preview-broker-client.mjs',
    'security/score-session-cookie.mjs',
    'security/score-preview-host-policy.mjs',
    'security/score-public-paths.mjs',
    'security/score-ticket-form.mjs',
  ]);
  const seen=new Set(),queue=['workers/score-preview/index.mjs'];
  while(queue.length){
    const file=queue.pop();
    assert.ok(allowed.has(file),'unexpected Worker import '+file);
    if(seen.has(file))continue;
    seen.add(file);
    const source=readFileSync(resolve(root,file),'utf8');
    assert.doesNotMatch(source,/\b(?:require|import)\s*\(/);
    assert.doesNotMatch(source,/SCORE_PREVIEW_SUPABASE_SECRET_KEY|SUPABASE_SECRET_KEYS|\/rest\/v1\/rpc\//);
    for(const match of source.matchAll(/(?:\b(?:import|export)\s+[\s\S]{0,200}?\s+from\s*|\bimport\s*)['"](\.{1,2}\/[^'"]+)['"]/g)){
      const dependency=relative(root,resolve(dirname(resolve(root,file)),match[1])).split(sep).join('/');
      assert.ok(allowed.has(dependency),'unknown Worker's dependency: '+file+' => '+dependency);
      queue.push(dependency);
    }
  }
  assert.deepEqual([...seen].sort(),[...allowed].sort());
});
