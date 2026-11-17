/**
 * Optional Cloudflare Worker for the CozyLoops custom domain.
 *
 * Deploy on the proxied cozyloops.site/* route ONLY after the domain
 * has been moved behind Cloudflare and HTTPS to GitHub Pages works.
 * GitHub Pages alone does not process this file.
 *
 * Keep CSP conservative while third-party advertising scripts are in use.
 * A stricter script-src must first be tested against ads, admin auth and images.
 */
const sharedCsp = [
  "base-uri 'none'",
  "object-src 'none'",
  "frame-ancestors 'none'",
  "upgrade-insecure-requests",
];

function cspForPath(pathname) {
  // Keep FormSubmit reachable without relaxing form submissions site-wide.
  // GitHub Pages accepts both /contact and /contact/ URLs.
  const isContactForm = /^\\/contact(?:\\/index\\.html|\\/)?$/.test(pathname);
  const action = isContactForm ? "form-action 'self' https://formsubmit.co" : "form-action 'self'";
  return [...sharedCsp, action].join('; ');
}

export default {
  async fetch(request) {
    const url = new URL(request.url);
    if (url.protocol === 'http:') {
      url.protocol = 'https:';
      return Response.redirect(url.toString(), 308);
    }

    // With a Cloudflare route over a valid GitHub Pages DNS origin this
    // fetches the normal origin response; do not change existing ad resources.
    const upstream = await fetch(request);
    const response = new Response(upstream.body, upstream);
    const h = response.headers;

    h.set('X-Content-Type-Options', 'nosniff');
    h.set('Referrer-Policy', 'strict-origin-when-cross-origin');
    h.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
    // Start with a one-day HSTS policy. Increase only after HTTPS has been
    // verified across every necessary host and rollback has been tested.
    h.set('Strict-Transport-Security', 'max-age=86400');

    if (/\btext\/html\b/i.test(h.get('content-type') || '')) {
      h.set('Content-Security-Policy', cspForPath(url.pathname));
      h.set('X-Frame-Options', 'DENY');
    }
    const privateRoute = url.pathname === '/admin' || url.pathname.startsWith('/admin/');
    const contactReceipt = url.pathname === '/contact/thanks' || url.pathname.startsWith('/contact/thanks/');
    if (privateRoute || contactReceipt) {
      h.set('X-Robots-Tag', 'noindex, nofollow');
      h.set('Cache-Control', 'no-store');
    }

    return response;
  },
};
