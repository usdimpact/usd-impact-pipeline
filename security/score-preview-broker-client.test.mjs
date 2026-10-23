import test from 'node:test';
import assert from 'node:assert/strict';
import {
  SCORE_PREVIEW_BROKER_URL,
  redeemScoreBrokerTicket,
  scoreBrokerSessionAllowed,
} from './score-preview-broker-client.mjs';

const AUTH_URL='https://ycstrcvshdluovtuasjc.supabase.co/auth/v1/token?grant_type=password';
const TICKET='T'.repeat(43);
const SESSION='S'.repeat(43);
const SECRET='s'.repeat(64);
const PUBLISHABLE='sb_publishable_'+'p'.repeat(32);
const PASSWORD='P'.repeat(48);
const SUB='11111111-1111-4111-8111-111111111111';
const ENV={
  SCORE_DEV_BROKER_ENABLED:'true',
  SCORE_EDGE_SHARED_SECRET:SECRET,
  SCORE_PREVIEW_SUPABASE_PUBLISHABLE_KEY:PUBLISHABLE,
  SCORE_PREVIEW_MACHINE_PASSWORD:PASSWORD,
  SCORE_PREVIEW_MACHINE_SUB:SUB,
};
function machineJwt(overrides={}) {
  const encode=value=>Buffer.from(JSON.stringify(value)).toString('base64url');
  const payload={
    iss:'https://ycstrcvshdluovtuasjc.supabase.co/auth/v1',
    aud:'authenticated',
    role:'authenticated',
    sub:SUB,
    is_anonymous:false,
    exp:Math.floor(Date.now()/1000)+600,
    ...overrides,
  };
  return encode({alg:'ES256',typ:'JWT'})+'.'+encode(payload)+'.'+'c'.repeat(64);
}
const MACHINE_JWT=machineJwt();

test('disabled or malformed configuration cannot send credentials to the network',async()=>{
  let called=0;
  const stub=async()=>{called++;throw Error('network prohibited');};
  await assert.rejects(()=>redeemScoreBrokerTicket(TICKET,{},stub));
  await assert.rejects(()=>redeemScoreBrokerTicket(TICKET,{SCORE_DEV_BROKER_ENABLED:'true'},stub));
  await assert.rejects(()=>redeemScoreBrokerTicket('invalid',ENV,stub));
  await assert.rejects(()=>redeemScoreBrokerTicket(TICKET,{...ENV,SCORE_PREVIEW_MACHINE_PASSWORD:'short'},stub));
  await assert.rejects(()=>redeemScoreBrokerTicket(TICKET,{...ENV,SCORE_PREVIEW_SUPABASE_PUBLISHABLE_KEY:'bad'},stub));
  await assert.rejects(()=>redeemScoreBrokerTicket(TICKET,{...ENV,SCORE_PREVIEW_MACHINE_SUB:'bad'},stub));
  assert.equal(called,0);
});

test('minted JWT must match the pinned least-privilege Development identity before broker use',async()=>{
  for(const badJwt of [
    'not-a-jwt',
    machineJwt({role:'service_role'}),
    machineJwt({aud:'anon'}),
    machineJwt({is_anonymous:true}),
    machineJwt({sub:'22222222-2222-4222-8222-222222222222'}),
    machineJwt({exp:Math.floor(Date.now()/1000)-1}),
  ]){
    let brokerCalls=0;
    const fake=async(url,opts)=>{
      if(url===AUTH_URL){
        assert.equal(opts.method,'POST');
        assert.equal(opts.headers.apikey,PUBLISHABLE);
        assert.equal(opts.headers.Authorization,undefined);
        assert.deepEqual(JSON.parse(opts.body),{
          email:'score-preview-machine@usd-impact.com',
          password:PASSWORD,
        });
        return Response.json({access_token:badJwt,refresh_token:'must-not-be-used'});
      }
      brokerCalls++;
      throw new Error('broker must not run');
    };
    await assert.rejects(()=>redeemScoreBrokerTicket(TICKET,ENV,fake),/authentication/i);
    assert.equal(brokerCalls,0);
  }
});

test('only the pinned Development broker receives a bounded POST with an internally minted JWT',async()=>{
  let authCalls=0,brokerCalls=0;
  const fake=async(url,opts)=>{
    if(url===AUTH_URL){
      authCalls++;
      assert.equal(opts.method,'POST');
      assert.equal(opts.redirect,'error');
      assert.equal(opts.cache,'no-store');
      assert.ok(opts.signal instanceof AbortSignal);
      assert.equal(opts.headers.apikey,PUBLISHABLE);
      assert.equal(opts.headers.Authorization,undefined);
      assert.deepEqual(JSON.parse(opts.body),{
        email:'score-preview-machine@usd-impact.com',
        password:PASSWORD,
      });
      return Response.json({access_token:MACHINE_JWT,refresh_token:'ignored'});
    }
    brokerCalls++;
    assert.equal(url,SCORE_PREVIEW_BROKER_URL);
    assert.equal(opts.method,'POST');
    assert.equal(opts.redirect,'error');
    assert.equal(opts.cache,'no-store');
    assert.ok(opts.signal instanceof AbortSignal);
    assert.equal(opts.headers['X-Score-Edge-Secret'],SECRET);
    assert.equal(opts.headers.apikey,undefined);
    assert.equal(opts.headers.Authorization,'Bearer '+MACHINE_JWT);
    assert.equal(opts.headers['Content-Type'],'application/json');
    const body=JSON.parse(opts.body);
    if(body.action==='redeem'){
      assert.deepEqual(body,{action:'redeem',ticket:TICKET});
      return Response.json({allowed:true,token:SESSION,path:'/en/',expiresAtMs:Date.now()+9*60_000});
    }
    assert.deepEqual(body,{action:'validate',token:SESSION});
    return Response.json({allowed:true});
  };
  const ticket=await redeemScoreBrokerTicket(TICKET,ENV,fake);
  assert.equal(ticket.token,SESSION);
  assert.equal(await scoreBrokerSessionAllowed(SESSION,ENV,fake),true);
  assert.equal(authCalls,2);
  assert.equal(brokerCalls,2);
});

test('auth failure, broker denials, malformed grants and broker outages all fail closed',async()=>{
  const authFail=async(url)=>url===AUTH_URL?new Response('denied',{status:400}):Response.json({allowed:true});
  await assert.rejects(()=>redeemScoreBrokerTicket(TICKET,ENV,authFail),/authentication/i);

  const makeFake=brokerResponse=>async(url)=>{
    if(url===AUTH_URL)return Response.json({access_token:MACHINE_JWT});
    return brokerResponse();
  };
  const forbidden=makeFake(()=>new Response('denied',{status:403}));
  assert.equal(await redeemScoreBrokerTicket(TICKET,ENV,forbidden),null);
  assert.equal(await scoreBrokerSessionAllowed(SESSION,ENV,forbidden),false);

  const malformed=makeFake(()=>Response.json({
    allowed:true,token:SESSION,path:'https://evil.example.test',expiresAtMs:Date.now()+60_000,
  }));
  assert.equal(await redeemScoreBrokerTicket(TICKET,ENV,malformed),null);

  const upstreamError=makeFake(()=>new Response('unavailable',{status:503}));
  await assert.rejects(()=>scoreBrokerSessionAllowed(SESSION,ENV,upstreamError),/unavailable/i);
});
