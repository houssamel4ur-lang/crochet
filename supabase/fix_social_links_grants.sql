-- CozyLoops: restore the *minimum* table permissions required by the public site
-- and Social/Contact admin forms. Run only after reviewing the RLS policies.
-- The existing RLS policies remain in control of visible rows and permitted writes.
--
-- Confirmed current policies:
--   SELECT anon/authenticated: is_visible = true
--   ALL authenticated: (select public.is_super_admin())
-- Confirmed before this patch: neither role has any table privilege on social_links.
--
-- No grants on admin_users/page_views. No DELETE privilege added.
BEGIN;
GRANT SELECT ON TABLE public.social_links TO anon, authenticated;
GRANT INSERT, UPDATE ON TABLE public.social_links TO authenticated;
-- For a SERIAL-based id, INSERT needs the sequence too; identity columns usually don't.
DO $$
DECLARE seq text;
BEGIN
  seq := pg_get_serial_sequence('public.social_links','id');
  IF seq IS NOT NULL THEN
    EXECUTE format('GRANT USAGE ON SEQUENCE %s TO authenticated', seq);
  END IF;
END $$;
COMMIT;

-- Verify the actual grants (note: RLS still applies separately).
SELECT r.rolname AS role_name,
       has_table_privilege(r.rolname, 'public.social_links', 'SELECT') AS can_select,
       has_table_privilege(r.rolname, 'public.social_links', 'INSERT') AS can_insert,
       has_table_privilege(r.rolname, 'public.social_links', 'UPDATE') AS can_update,
       has_table_privilege(r.rolname, 'public.social_links', 'DELETE') AS can_delete
FROM pg_roles r WHERE r.rolname IN ('anon','authenticated')
ORDER BY r.rolname;
