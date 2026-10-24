import test from 'node:test';
import assert from 'node:assert/strict';
import { handleScorePreviewBroker } from './score-preview-broker-server.mjs';

const BROKER='https://ycstrcvshdluovtuasjc.supabase.co/functions/v1/score-preview-broker';
const SECRET='S'.repeat(64);
const config={
  enabled:'true',supabaseUrl:'https://ycstrcvshdluovtuasjc.supabase.co',
  supabaseSecretKey:'sb_secret_'+'B'.repeat(32),sharedSecret:SECRET,
  rateBudget: async () => true,
};
function request({ url=BROKER,method='POST',secret=SECRET,contentType='application/json',
  host=null,forwardedHost=null,forwardedProto=null,data={action:'validate',token:'T'.repeat(43)} }={}) {
  const headers={'Content-Type':contentType};
  if(secret!==null)headers['X-Score-Edge-Secret']=secret;
  if(host!==null)headers.Host=host;
  if(forwardedHost!==null)headers['X-Forwarded-Host']=forwardedHost;
  if(forwardedProto!==null)headers['X-Forwarded-Proto']=forwardedProto;
  return new Request(url,{method,headers,...(method==='POST'?{body:JSON.stringify(data)}:{})});
}
const failFetch=async()=>{throw Error('A failed authorization must never access Supabase RPC')};

test('closed by default: no authenticated POST can execute while broker is disabled',async()=>{
  const res=await handleScorePreviewBroker(request(),{...config,enabled:'false'},failFetch);
  assert.equal(res.status,503);
  assert.deepEqual(await res.json(),{allowed:false});
});
test('one exact Development hostname and function path only; no cross-project confusion',async()=>{
  for(const url of [
    'https://other.supabase.co/functions/v1/score-preview-broker',
    'https://ycstrcvshdluovtuasjc.supabase.co/rest/v1/rpc/score_membership_active',
    'https://ycstrcvshdluovtuasjc.supabase.co/functions/v1/score-preview-broker?redirect=1',
    'http://ycstrcvshdluovtuasjc.supabase.co/functions/v1/score-preview-broker',
  ]){
    assert.equal((await handleScorePreviewBroker(request({url}),config,failFetch)).status,403);
  }
  assert.equal((await handleScorePreviewBroker(request(),{...config,supabaseUrl:'https://other.supabase.co'},failFetch)).status,503);
});
test('Supabase Edge internal URL rewrite is accepted only with the documented runtime host over https',async()=>{
  const internal='https://edge-runtime.supabase.internal/score-preview-broker';
  const diagnosticConfig={...config,diagnostics:'true'};

  for(const headers of [
    {host:'edge-runtime.supabase.com'},
    {forwardedHost:'edge-runtime.supabase.com'},
  ]){
    const accepted=await handleScorePreviewBroker(request({
      url:internal,
      ...headers,
      forwardedProto:'https',
    }),diagnosticConfig,async()=>Response.json(null));
    assert.equal(accepted.status,403);
    assert.equal(accepted.headers.get('X-Score-Preview-Broker-Stage'),'broker-validate-denied');
  }

  for(const opts of [
    {url:internal,host:'other.supabase.com',forwardedProto:'https'},
    {url:internal,forwardedHost:'other.supabase.com',forwardedProto:'https'},
    {url:internal,host:'edge-runtime.supabase.com',forwardedProto:'http'},
    {url:'https://other.supabase.co/functions/v1/score-preview-broker',host:'other.supabase.com',forwardedProto:'https'},
  ]){
    const denied=await handleScorePreviewBroker(request(opts),diagnosticConfig,failFetch);
    assert.equal(denied.status,403);
    assert.equal(denied.headers.get('X-Score-Preview-Broker-Stage'),'broker-origin');
  }

  const wrongRuntimePath=await handleScorePreviewBroker(request({
    url:'https://edge-runtime.supabase.internal/functions/v1/score-preview-broker',
    host:'edge-runtime.supabase.com',
    forwardedProto:'https',
  }),diagnosticConfig,failFetch);
  assert.equal(wrongRuntimePath.status,403);
  assert.equal(wrongRuntimePath.headers.get('X-Score-Preview-Broker-Stage'),'broker-path');
});

test('external callers with no/malformed/incorrect shared secret have no database access',async()=>{
  for(const secret of [null,'','wrong', 'A'.repeat(64),SECRET+'A']){
    const res=await handleScorePreviewBroker(request({secret}),config,failFetch);
    assert.equal(res.status,403);
    assert.equal(res.headers.get('Cache-Control'),'private, no-store');
    assert.equal(res.headers.get('Set-Cookie'),null);
    assert.deepEqual(await res.json(),{allowed:false});
  }
  assert.equal((await handleScorePreviewBroker(request(),{...config,sharedSecret:'no-secret'},failFetch)).status,503);
});
test('POST JSON strict schema rejects arbitrary RPC, account IDs, invalid token and multiple operations',async()=>{
  for(const data of [
    {action:'rpc',name:'score_membership_active',p_account_id:'user'},
    {action:'validate',token:'T'.repeat(43),account_id:'a'},
    {action:'redeem',ticket:'invalid'},
    {action:'redeem',ticket:'T'.repeat(43),token:'A'.repeat(43)},
    {action:'validate',token:'T'.repeat(43),ticket:'A'.repeat(43)},
    {},
  ]){
    assert.equal((await handleScorePreviewBroker(request({data}),config,failFetch)).status,400);
  }
  assert.equal((await handleScorePreviewBroker(request({contentType:'text/plain'}),config,failFetch)).status,415);
  assert.equal((await handleScorePreviewBroker(request({method:'GET'}),config,failFetch)).status,405);
});
test('Dev key must remain inside the broker and errors never disclose it',async()=>{
  const fail=async()=>new Response('database error', {status:503});
  const res=await handleScorePreviewBroker(request(),config,fail);
  assert.equal(res.status,503);
  const text=await res.text();
  assert.equal(text.includes(config.supabaseSecretKey),false);
  assert.equal(text.includes(SECRET),false);
  assert.equal(text.includes('database error'),false);
});


test('streamed broker payload is bounded by actual UTF-8 byte size', async () => {
  const data = { action: 'validate', token: 'T'.repeat(43) };
  const bytes = new TextEncoder();
  const valid = bytes.encode(JSON.stringify(data));
  const good = new Request(BROKER, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Score-Edge-Secret': SECRET },
    body: new ReadableStream({
      start(controller) {
        controller.enqueue(valid.slice(0, 9));
        controller.enqueue(valid.slice(9));
        controller.close();
      },
    }),
    duplex: 'half',
  });
  const result = await handleScorePreviewBroker(good, config, async () => Response.json(null));
  assert.equal(result.status, 403); // valid body reaches RPC, then fails closed

  const tooLarge = new Request(BROKER, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Score-Edge-Secret': SECRET },
    body: new ReadableStream({
      start(controller) {
        controller.enqueue(bytes.encode(JSON.stringify({ action: 'validate', token: 'T'.repeat(43), padding: 'x'.repeat(600) })));
        controller.close();
      },
    }),
    duplex: 'half',
  });
  const rejected = await handleScorePreviewBroker(tooLarge, config, failFetch);
  assert.equal(rejected.status, 400);
  assert.deepEqual(await rejected.json(), { allowed: false });
});


test('strict media and declared size validation does not reach privileged RPC', async () => {
  const cases = [
    ['application/jsonx', null, 415],
    ['application/json; charset=utf-16', null, 415],
    ['text/plain;application/json', null, 415],
    ['application/json', 'invalid', 400],
    ['application/json', '513', 400],
    ['application/json', '-1', 400],
    ['application/json', '2.5', 400],
  ];
  for (const [media, length, status] of cases) {
    const request = new Request(BROKER, {
      method: 'POST',
      headers: {
        'Content-Type': media,
        'X-Score-Edge-Secret': SECRET,
        ...(length === null ? {} : {'Content-Length': length}),
      },
      body: JSON.stringify({ action: 'validate', token: 'T'.repeat(43) }),
    });
    const response = await handleScorePreviewBroker(request, config, failFetch);
    assert.equal(response.status, status, media + '/' + length);
    assert.deepEqual(await response.json(), { allowed: false });
  }
  const valid = request({contentType: 'application/json; charset=UTF-8'});
  const allowedToParse = await handleScorePreviewBroker(valid, config, async () => Response.json(null));
  assert.equal(allowedToParse.status, 403);
});

test('RPC timeout errors are sanitized and deny, without leaking configuration', async () => {
  const error = async () => { throw new DOMException('timed out: private backend detail', 'TimeoutError'); };
  const result = await handleScorePreviewBroker(request(), config, error);
  assert.equal(result.status, 503);
  assert.deepEqual(await result.json(), { allowed: false });
});

test('an authenticated broker request cannot reach privileged RPC without a global budget', async () => {
  assert.equal((await handleScorePreviewBroker(request(),{...config,rateBudget:undefined},failFetch)).status,503);
  let claims=0;
  const over=await handleScorePreviewBroker(request(),{...config,rateBudget:async(action)=>{
    assert.equal(action,'validate');claims++;return false;
  }},failFetch);
  assert.equal(over.status,429);
  assert.equal(over.headers.get('Retry-After'),'60');
  assert.deepEqual(await over.json(),{allowed:false});
  assert.equal(claims,1);
  const down=await handleScorePreviewBroker(request(),{...config,rateBudget:async()=>{throw Error('private database detail');}},failFetch);
  assert.equal(down.status,503);
  assert.deepEqual(await down.json(),{allowed:false});
  assert.equal(down.headers.get('Set-Cookie'),null);
});
test('invalid secrets and malformed requests never consume database budget', async () => {
  let claims=0;
  const cfg={...config,rateBudget:async()=>{claims++;return true}};
  assert.equal((await handleScorePreviewBroker(request({secret:'A'.repeat(64)}),cfg,failFetch)).status,403);
  assert.equal((await handleScorePreviewBroker(request({data:{action:'unknown'}}),cfg,failFetch)).status,400);
  assert.equal((await handleScorePreviewBroker(request({contentType:'text/plain'}),cfg,failFetch)).status,415);
  assert.equal((await handleScorePreviewBroker(request({method:'GET'}),cfg,failFetch)).status,405);
  assert.equal(claims,0);
});


test('Development diagnostics are opt-in, stage-only, and never leak secrets', async () => {
  const silent = await handleScorePreviewBroker(request({secret:'A'.repeat(64)}), config, failFetch);
  assert.equal(silent.status, 403);
  assert.equal(silent.headers.get('X-Score-Preview-Broker-Stage'), null);
  assert.deepEqual(await silent.json(), { allowed: false });

  const diagnosticConfig = {...config, diagnostics:'true'};
  const mismatch = await handleScorePreviewBroker(
    request({secret:'A'.repeat(64)}), diagnosticConfig, failFetch);
  assert.equal(mismatch.status, 403);
  assert.equal(mismatch.headers.get('X-Score-Preview-Broker-Stage'), 'broker-shared-secret');
  const body = await mismatch.json();
  assert.deepEqual(body, { allowed:false, stage:'broker-shared-secret' });
  const serialized = JSON.stringify(body);
  assert.equal(serialized.includes(SECRET), false);
  assert.equal(serialized.includes(config.supabaseSecretKey), false);

  const wrongUrl = await handleScorePreviewBroker(
    request({url:'https://other.supabase.co/functions/v1/score-preview-broker'}),
    diagnosticConfig, failFetch);
  assert.equal(wrongUrl.status, 403);
  assert.equal(wrongUrl.headers.get('X-Score-Preview-Broker-Stage'), 'broker-origin');

  const media = await handleScorePreviewBroker(
    request({contentType:'text/plain'}), diagnosticConfig, failFetch);
  assert.equal(media.status, 415);
  assert.equal(media.headers.get('X-Score-Preview-Broker-Stage'), 'broker-media-type');
});
