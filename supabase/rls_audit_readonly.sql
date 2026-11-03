-- CozyLoops release audit: READ-ONLY. Run in Supabase SQL Editor as the project owner.
-- Does not alter policies, roles, data, functions, or storage.
-- Carefully inspect the results instead of treating an existing policy as proof of safety.

-- 1. Inspect active RLS and policy conditions for content, settings and storage.
SELECT
  c.table_schema, c.table_name,
  COALESCE(p.policyname, '(none)') AS policy_name,
  p.cmd AS command,
  p.roles::text AS roles,
  p.qual AS using_expression,
  p.with_check AS insert_update_check
FROM (
  VALUES
    ('public','articles'),
    ('public','site_settings'),
    ('public','social_links'),
    ('public','page_views'),
    ('storage','objects'),
    ('storage','buckets')
) AS c(table_schema, table_name)
LEFT JOIN pg_policies p
  ON p.schemaname = c.table_schema AND p.tablename = c.table_name
ORDER BY c.table_schema,c.table_name,p.cmd,p.policyname;

-- 2. Confirm RLS status (a table without RLS requires particular scrutiny).
SELECT n.nspname AS schema_name, cls.relname AS table_name,
       cls.relrowsecurity AS rls_enabled, cls.relforcerowsecurity AS rls_forced
FROM pg_class cls
JOIN pg_namespace n ON n.oid=cls.relnamespace
WHERE (n.nspname='public' AND cls.relname IN ('articles','site_settings','social_links','page_views'))
   OR (n.nspname='storage' AND cls.relname IN ('objects','buckets'))
ORDER BY schema_name,table_name;

-- 3. Review effective role privileges. Grants alone do not override RLS.
SELECT
  t.schemaname AS schema_name, t.tablename AS table_name,
  role_name.role_name,
  has_table_privilege(role_name.role_name, format('%I.%I',t.schemaname,t.tablename),'SELECT') AS can_select,
  has_table_privilege(role_name.role_name, format('%I.%I',t.schemaname,t.tablename),'INSERT') AS can_insert,
  has_table_privilege(role_name.role_name, format('%I.%I',t.schemaname,t.tablename),'UPDATE') AS can_update,
  has_table_privilege(role_name.role_name, format('%I.%I',t.schemaname,t.tablename),'DELETE') AS can_delete
FROM pg_tables t
CROSS JOIN (VALUES ('anon'),('authenticated')) role_name(role_name)
WHERE t.schemaname='public' AND t.tablename IN ('articles','site_settings','social_links','page_views')
ORDER BY t.tablename,role_name.role_name;

-- 4. Review SECURITY DEFINER functions and who can execute them.
SELECT n.nspname AS schema_name, p.proname AS function_name,
       pg_get_function_identity_arguments(p.oid) AS arguments,
       p.prosecdef AS security_definer,
       pg_get_userbyid(p.proowner) AS owner_name,
       has_function_privilege('anon',p.oid,'EXECUTE') AS anonymous_can_execute,
       has_function_privilege('authenticated',p.oid,'EXECUTE') AS authenticated_can_execute,
       p.proconfig AS function_configuration
FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
WHERE n.nspname='public'
  AND p.proname IN ('is_super_admin','record_cozyloop_view','cozyloop_analytics')
ORDER BY p.proname;

-- 5. Verify file-bucket visibility, size caps, and MIME restrictions.
SELECT name,public,file_size_limit,allowed_mime_types
FROM storage.buckets
WHERE name='ARTICLE IMAGE';
