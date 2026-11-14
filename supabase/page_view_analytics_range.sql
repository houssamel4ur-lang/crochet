-- CozyLoops owner-only Pinterest-style traffic trend analytics.
-- Prerequisite: run supabase/page_view_analytics.sql first, if not already installed.
-- Run once in the Supabase SQL Editor; safe to run again.
-- Records remain daily-deduplicated, consent-based page views, not ad impressions.
-- The 7/15/30-day views use UTC calendar-day buckets; 24h uses hourly
-- buckets, and 1h uses 5-minute buckets.
-- A normal authenticated account cannot access the results: is_super_admin()
-- is checked inside the function in addition to restricted EXECUTE grants.

CREATE INDEX IF NOT EXISTS page_views_created_at_idx
  ON public.page_views (created_at DESC);

CREATE OR REPLACE FUNCTION public.cozyloop_analytics_range(p_period text DEFAULT '30d')
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $analytics$
DECLARE
  v_step interval;
  v_bins integer;
  v_start timestamptz;
  v_answer jsonb;
BEGIN
  IF NOT COALESCE(public.is_super_admin(), false) THEN
    RAISE EXCEPTION 'Not authorized' USING ERRCODE = '42501';
  END IF;

  CASE p_period
    WHEN '1h' THEN v_step := interval '5 minutes'; v_bins := 12;
    WHEN '1d' THEN v_step := interval '1 hour'; v_bins := 24;
    WHEN '7d' THEN v_step := interval '1 day'; v_bins := 7;
    WHEN '15d' THEN v_step := interval '1 day'; v_bins := 15;
    WHEN '30d' THEN v_step := interval '1 day'; v_bins := 30;
    ELSE RAISE EXCEPTION 'Unsupported analytics period' USING ERRCODE = '22023';
  END CASE;

  -- Align to UTC buckets. This includes the current (possibly partial) bucket.
  v_start := date_bin(v_step, now(), '2000-01-01 00:00:00+00'::timestamptz)
             - ((v_bins - 1) * v_step);

  SELECT jsonb_build_object(
    'period', p_period,
    'bucket_minutes', (EXTRACT(EPOCH FROM v_step) / 60)::integer,
    'start_at', v_start,
    'end_at', now(),
    'total_page_views', (
      SELECT count(*) FROM public.page_views WHERE created_at >= v_start
    ),
    'home_views', (
      SELECT count(*) FROM public.page_views
      WHERE created_at >= v_start AND page_key = 'home'
    ),
    'article_views', (
      SELECT count(*) FROM public.page_views
      WHERE created_at >= v_start AND page_key LIKE 'post/%'
    ),
    'previous_page_views', (
      SELECT count(*) FROM public.page_views
      WHERE created_at >= v_start - (v_bins * v_step) AND created_at < v_start
    ),
    'series', COALESCE((
      SELECT jsonb_agg(
        jsonb_build_object('at', b.bucket_at, 'views', COALESCE(a.views, 0))
        ORDER BY b.bucket_at
      )
      FROM (
        SELECT v_start + (n * v_step) AS bucket_at
        FROM generate_series(0, v_bins - 1) AS n
      ) b
      LEFT JOIN (
        SELECT date_bin(v_step, created_at, '2000-01-01 00:00:00+00'::timestamptz) AS bucket_at,
               count(*)::integer AS views
        FROM public.page_views
        WHERE created_at >= v_start AND created_at <= now()
        GROUP BY 1
      ) a USING (bucket_at)
    ), '[]'::jsonb),
    'top_articles', COALESCE((
      SELECT jsonb_agg(jsonb_build_object('slug', t.slug, 'views', t.views)
                       ORDER BY t.views DESC, t.slug)
      FROM (
        SELECT substr(page_key, 6) AS slug, count(*) AS views
        FROM public.page_views
        WHERE created_at >= v_start AND page_key LIKE 'post/%'
        GROUP BY page_key
        ORDER BY count(*) DESC, page_key
        LIMIT 10
      ) t
    ), '[]'::jsonb)
  ) INTO v_answer;

  RETURN v_answer;
END
$analytics$;

REVOKE ALL ON FUNCTION public.cozyloop_analytics_range(text) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.cozyloop_analytics_range(text) TO authenticated;

-- Verification after running SQL while signed in as the owner:
-- select public.cozyloop_analytics_range('7d');
-- In application sessions, the RPC additionally enforces is_super_admin().
