-- Development-only Score broker budget. PR #148. Never run in Production.
-- This limits valid, shared-secret-authenticated operations globally.
-- It is NOT a pre-Edge WAF; direct anonymous requests still reach Edge.
create table public.score_preview_broker_budget (
  action text primary key check (action in ('redeem', 'validate')),
  window_started_at timestamptz not null,
  hits integer not null check (hits between 1 and 181)
);
alter table public.score_preview_broker_budget enable row level security;
revoke all on table public.score_preview_broker_budget from public, anon, authenticated;
grant select, insert, update on table public.score_preview_broker_budget to service_role;

create function public.score_preview_broker_claim_budget(p_action text)
returns boolean
language plpgsql
security invoker
set search_path to ''
as $function$
declare
  v_limit integer;
  v_count integer;
  v_now timestamptz := statement_timestamp();
begin
  v_limit := case p_action
    when 'redeem' then 30
    when 'validate' then 180
    else null
  end;
  if v_limit is null then return false; end if;
  insert into public.score_preview_broker_budget (action, window_started_at, hits)
  values (p_action, v_now, 1)
  on conflict (action) do update
  set hits = case
      when score_preview_broker_budget.window_started_at <= v_now - interval '60 seconds'
        then 1
      else least(score_preview_broker_budget.hits + 1, v_limit + 1)
    end,
    window_started_at = case
      when score_preview_broker_budget.window_started_at <= v_now - interval '60 seconds'
        then v_now
      else score_preview_broker_budget.window_started_at
    end
  returning hits into v_count;
  return v_count <= v_limit;
end;
$function$;

revoke all on function public.score_preview_broker_claim_budget(text) from public, anon, authenticated;
grant execute on function public.score_preview_broker_claim_budget(text) to service_role;
