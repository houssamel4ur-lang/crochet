-- CozyLoops: privacy-aware daily page counters.
-- Run in Supabase SQL Editor. This does not modify articles or existing settings.
CREATE TABLE IF NOT EXISTS public.page_views (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  view_date date NOT NULL DEFAULT (now() AT TIME ZONE 'utc')::date,
  page_key text NOT NULL,
  visitor_hash text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT page_views_unique_daily UNIQUE(view_date,page_key,visitor_hash)
);
CREATE INDEX IF NOT EXISTS page_views_page_date_idx ON public.page_views(page_key,view_date);
ALTER TABLE public.page_views ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.page_views FROM PUBLIC, anon, authenticated;
REVOKE ALL ON SEQUENCE public.page_views_id_seq FROM PUBLIC, anon, authenticated;

CREATE OR REPLACE FUNCTION public.record_cozyloop_view(p_page text, p_visitor uuid)
RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER SET search_path = ''
AS $$
DECLARE allowed boolean;
BEGIN
  IF p_page IS NULL OR length(p_page)>190 OR p_visitor IS NULL THEN RETURN false; END IF;
  IF p_page = 'home' THEN
    allowed := true;
  ELSIF p_page ~ '^post/[a-z0-9]+(-[a-z0-9]+)*$' THEN
    SELECT EXISTS (
      SELECT 1 FROM public.articles
      WHERE slug = substr(p_page,6) AND status = 'published'
    ) INTO allowed;
  ELSE
    allowed := false;
  END IF;
  IF NOT allowed THEN RETURN false; END IF;
  INSERT INTO public.page_views(view_date,page_key,visitor_hash)
  VALUES ((now() AT TIME ZONE 'utc')::date,p_page,md5(p_visitor::text))
  ON CONFLICT(view_date,page_key,visitor_hash) DO NOTHING;
  RETURN true;
END $$;

REVOKE ALL ON FUNCTION public.record_cozyloop_view(text,uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.record_cozyloop_view(text,uuid) TO anon, authenticated;

CREATE OR REPLACE FUNCTION public.cozyloop_analytics()
RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path = ''
AS $$
DECLARE answer jsonb;
BEGIN
  IF NOT (SELECT public.is_super_admin()) THEN
    RAISE EXCEPTION 'Not authorized' USING ERRCODE = '42501';
  END IF;
  SELECT jsonb_build_object(
    'total_page_views', (SELECT count(*) FROM public.page_views),
    'home_views', (SELECT count(*) FROM public.page_views WHERE page_key='home'),
    'article_views', (SELECT count(*) FROM public.page_views WHERE page_key LIKE 'post/%'),
    'today_page_views', (SELECT count(*) FROM public.page_views WHERE view_date=(now() AT TIME ZONE 'utc')::date),
    'top_articles', COALESCE((
      SELECT jsonb_agg(jsonb_build_object('slug',slug,'views',views) ORDER BY views DESC,slug)
      FROM (SELECT substr(page_key,6) AS slug,count(*) AS views
            FROM public.page_views WHERE page_key LIKE 'post/%'
            GROUP BY page_key ORDER BY count(*) DESC, page_key LIMIT 10) top
    ), '[]'::jsonb)
  ) INTO answer;
  RETURN answer;
END $$;

REVOKE ALL ON FUNCTION public.cozyloop_analytics() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.cozyloop_analytics() TO authenticated;
