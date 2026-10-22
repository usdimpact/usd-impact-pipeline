import test from 'node:test';
import assert from 'node:assert/strict';
import { handleScorePreviewBroker } from './score-preview-broker-server.mjs';

const BROKER='https://ycstrcvshdluovtuasjc.supabase.co/functions/v1/score-preview-broker';
const SECRET='S'.repeat(64);
const config={
  enabled:'true',supabaseUrl:'https://ycstrcvshdluovtuasjc.supabase.co',
  supabaseSecretKey:'sb_secret_'+'B'.repeat(32),sharedSecret:SECRET,
};
function request({ url=BROKER,method='POST',secret=SECRET,contentType='application/json',
  data={action:'validate',token:'T'.repeat(43)} }={}) {
  const headers={'Content-Type':contentType};
  if(secret!==null)headers['X-Score-Edge-Secret']=secret;
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
