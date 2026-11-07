-- Run once in the CozyLoops project SQL Editor as the database owner.
-- Keeps pending posts as drafts under the existing published-only public RLS.
begin;
create extension if not exists pg_cron;
alter table public.articles add column if not exists scheduled_at timestamptz;
alter table public.articles add column if not exists published_at timestamptz;
create index if not exists articles_due_schedule_idx
  on public.articles (scheduled_at) where status = 'draft' and scheduled_at is not null;

-- A single atomic UPDATE handles due posts, including after downtime.
-- No privileged publishing endpoint or service key is exposed to browsers.
select cron.schedule(
  'cozyloops-publish-scheduled-articles', '* * * * *',
  $$update public.articles
    set status = 'published', published_at = scheduled_at,
        scheduled_at = null, updated_at = now()
    where status = 'draft' and scheduled_at <= now();$$
);

-- Only the existing Super Admin may inspect whether the scheduler is active.
create or replace function public.article_scheduler_status()
returns boolean language plpgsql security definer set search_path = '' as $$
begin
  if auth.uid() is null or public.is_super_admin() is not true then
    raise exception 'Super Admin access required' using errcode = '42501';
  end if;
  return exists (select 1 from cron.job
    where jobname = 'cozyloops-publish-scheduled-articles' and active);
end;
$$;
revoke all on function public.article_scheduler_status() from public, anon;
grant execute on function public.article_scheduler_status() to authenticated;
commit;

-- Verification: one active minute job; public RLS remains unchanged.
select jobname, schedule, active from cron.job
where jobname = 'cozyloops-publish-scheduled-articles';
select column_name, data_type from information_schema.columns
where table_schema = 'public' and table_name = 'articles'
  and column_name in ('scheduled_at', 'published_at');
select policyname, roles, cmd, qual from pg_policies
where schemaname = 'public' and tablename = 'articles';
