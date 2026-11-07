# Scheduled articles

Run `supabase/article_scheduling.sql` in the CozyLoops Supabase project's SQL Editor.
The final results must show the active `* * * * *` job and both timestamp columns.
Review the existing public SELECT policy: it must only expose published articles.
This setup does not alter existing RLS policies or grant access to article data.

Admin checks the server job before allowing scheduling. Until activation, the
Scheduled option is disabled and normal draft and published saves still work.

In Admin → Posts, create a post or edit an unpublished draft, choose Scheduled,
select a future date and time, and save. Times use the browser's named timezone
and are stored in UTC. To reschedule, change the date and save. To cancel, choose
Draft and save. Published GitHub editorials cannot be scheduled retroactively:
their static pages are already public.

The server checks every minute, even with Admin closed, and publishes all overdue
drafts. Homepage requests pick up the published post immediately after that job;
an already-open homepage needs a refresh. Static SEO pages and sitemap update on
the existing hourly GitHub build, which can be delayed by GitHub Actions.

## Owner verification after activation

Use a new temporary draft with a unique slug. Schedule it at least two minutes
ahead; confirm it is absent from the public API and homepage before the time.
Close Admin, wait for the next minute job after the selected time, and confirm
the post appears publicly with `published_at` set and `scheduled_at` cleared.
Verify rescheduling and cancellation on a second draft. Remove temporary test
posts through Admin after checking. No real article is scheduled by this setup.

## Recovery

`select cron.unschedule('cozyloops-publish-scheduled-articles');` stops future
automatic publishing without changing any articles. Existing pending drafts stay
private. Re-run the setup SQL to restore the named job.
