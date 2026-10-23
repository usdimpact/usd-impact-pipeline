import test from 'node:test';
import assert from 'node:assert/strict';
import {
  SCORE_PREVIEW_BROKER_URL,
  redeemScoreBrokerTicket,
  scoreBrokerSessionAllowed,
} from './score-preview-broker-client.mjs';

const TICKET='T'.repeat(43);
const SESSION='S'.repeat(43);
const SECRET='s'.repeat(64);
const MACHINE_JWT='aaaaaaaa.bbbbbbbb.cccccccccccccccccc';

test('a disabled or malformed broker call cannot send any credential to the network',async()=>{
  let called=0;
  const stub=async()=>{called++;throw Error('network prohibited');};
  await assert.rejects(()=>redeemScoreBrokerTicket(TICKET,{},stub));
  await assert.rejects(()=>redeemScoreBrokerTicket(TICKET,{SCORE_DEV_BROKER_ENABLED:'true'},stub));
  await assert.rejects(()=>redeemScoreBrokerTicket('invalid',{
    SCORE_DEV_BROKER_ENABLED:'true',SCORE_EDGE_SHARED_SECRET:SECRET,
    SCORE_PREVIEW_MACHINE_JWT:MACHINE_JWT,
  },stub));
  await assert.rejects(()=>redeemScoreBrokerTicket(TICKET,{
    SCORE_DEV_BROKER_ENABLED:'true',SCORE_EDGE_SHARED_SECRET:SECRET,
    SCORE_PREVIEW_MACHINE_JWT:'not-a-jwt',
  },stub));
  assert.equal(called,0);
});

test('only the pinned Development broker receives a bounded authenticated POST',async()=>{
  let calls=0;
  const env={SCORE_DEV_BROKER_ENABLED:'true',SCORE_EDGE_SHARED_SECRET:SECRET,SCORE_PREVIEW_MACHINE_JWT:MACHINE_JWT};
  const fake=async(url,opts)=>{
    calls++;
    assert.equal(url,SCORE_PREVIEW_BROKER_URL);
    assert.equal(opts.method,'POST');
    assert.equal(opts.redirect,'error');
    assert.equal(opts.cache,'no-store');
    assert.ok(opts.signal instanceof AbortSignal);
    assert.equal(opts.signal.aborted,false);
    assert.equal(opts.headers['X-Score-Edge-Secret'],SECRET);
    assert.equal(opts.headers.apikey,undefined);
    assert.equal(opts.headers.Authorization,'Bearer '+MACHINE_JWT);
    assert.equal(opts.headers['Content-Type'],'application/json');
    const body=JSON.parse(opts.body);
    assert.ok(['redeem','validate'].includes(body.action));
    if(body.action==='redeem'){
      assert.deepEqual(body,{action:'redeem',ticket:TICKET});
      return Response.json({allowed:true,token:SESSION,path:'/en/',expiresAtMs:Date.now()+9*60_000});
    }
    assert.deepEqual(body,{action:'validate',token:SESSION});
    return Response.json({allowed:true});
  };
  const ticket=await redeemScoreBrokerTicket(TICKET,env,fake);
  assert.equal(ticket.token,SESSION);
  assert.equal(await scoreBrokerSessionAllowed(SESSION,env,fake),true);
  assert.equal(calls,2);
});

test('broker denials, invalid grants and outages all deny member access',async()=>{
  const env={SCORE_DEV_BROKER_ENABLED:'true',SCORE_EDGE_SHARED_SECRET:SECRET,SCORE_PREVIEW_MACHINE_JWT:MACHINE_JWT};
  const forbidden=async()=>new Response('denied',{status:403});
  assert.equal(await redeemScoreBrokerTicket(TICKET,env,forbidden),null);
  assert.equal(await scoreBrokerSessionAllowed(SESSION,env,forbidden),false);
  const malformed=async()=>Response.json({
    allowed:true,token:SESSION,path:'https://evil.example.test',expiresAtMs:Date.now()+60_000,
  });
  assert.equal(await redeemScoreBrokerTicket(TICKET,env,malformed),null);
  const upstreamError=async()=>new Response('unavailable',{status:503});
  await assert.rejects(()=>scoreBrokerSessionAllowed(SESSION,env,upstreamError),/unavailable/i);
});
