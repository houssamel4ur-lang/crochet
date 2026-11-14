# CozyLoops visitor authentication — production activation checklist

The front-end is already published in `account/index.html` + `account/auth.js`; the account icon is inserted on the home page and generated article pages by `scripts/site_navigation.js`. These changes do **not** by themselves enable Google OAuth or production email delivery.

## 1. Verify ownership of the actual Supabase project

The application currently points to `https://yqmrunstyhrhnvxoyrap.supabase.co`, but this chat's Supabase connection lists **zero accessible projects**. Only the legitimate owner should perform these steps in the project dashboard; never share Client Secrets in chat, GitHub issues or this public repository.

## 2. Email sign-up, confirmation and password resets

- Supabase Dashboard > Authentication > Providers > Email: review that Email / Password sign-in and sign-up are enabled, and keep email confirmation enabled for new accounts.
- Dashboard > Authentication > URL Configuration: site URL `https://cozyloops.site/`; allow `https://cozyloops.site/account/` and `https://cozyloops.site/account/?mode=update` as redirect destinations. Follow Supabase redirect matching instructions if URL patterns are used.
- Configure a **verified custom SMTP provider** under Auth email settings before a public launch. Default Supabase email delivery is constrained and is not suitable for general public visitor sign-ups. Use your own sender domain.
- Customize the verification and recovery templates with CozyLoops identity and check that links actually return to the permitted URLs.
- Test: new sign-up > confirmation email > sign-in > sign-out > forgot password > reset link > new password > sign-in. Also test invalid/expired links and rate limits. Never test with actual member credentials.

## 3. Google sign-in

- In [Google Auth Platform](https://console.cloud.google.com/auth/overview), set up an OAuth consent screen appropriate for external users.
- Create a **Web application** OAuth client. Authorized JavaScript origin: `https://cozyloops.site`.
- Authorized redirect URI: use the exact callback shown under the Supabase Google provider. For this hosted project, it should be `https://yqmrunstyhrhnvxoyrap.supabase.co/auth/v1/callback`. Verify it in the dashboard rather than guessing.
- Add the client ID and client secret **in the Supabase dashboard Google provider settings**, never in frontend code; enable the provider.
- Configure Google application branding and publish the OAuth app beyond testing when ready. Test on mobile and desktop, sign out, and test repeat sign-in.

## 4. Security & privacy before inviting registrations

- The visitor account must **not** acquire Super Admin permissions. In Supabase verify that `is_super_admin()` trusts only owner-controlled membership, not user-editable metadata.
- Re-audit RLS on all public-schema tables and storage with the `authenticated` role. Some policies behave differently for anonymous vs signed-in users. Ensure ordinary visitors cannot write articles, access drafts, modify site settings, view private analytics or grant themselves admin rights.
- Check Supabase Auth email quotas, bot protection/CAPTCHA and abuse protection; avoid exposing account existence in error messages.
- Ensure the published Privacy Policy and contact details reflect Supabase Auth processing and provide an account deletion request channel.
- Run the repository's Quality Checks, Browser UI Smoke Tests and security workflow after any Auth or database policy changes.

## 5. Acceptance

The UI and browser logic can be checked in GitHub, but **live Google login, email verification, password reset emails, provider configuration, and security boundaries are not verified** until the owner completes the dashboard setup and uses a temporary non-admin test account.

Official Supabase guides:
- https://supabase.com/docs/guides/auth/social-sign-in/auth-google
- https://supabase.com/docs/guides/auth/passwords
- https://supabase.com/docs/guides/auth/redirect-urls
- https://supabase.com/docs/guides/auth/auth-smtp
