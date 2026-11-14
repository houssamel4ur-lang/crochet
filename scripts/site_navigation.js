/* Shared navigation: upgrade pre-existing static articles until the SEO build publishes them. */
(() => {
  'use strict';
  const nav = document.querySelector('header > nav.nav');
  if (!nav) return;
  if (!nav.classList.contains('top-nav')) {
    const brand = nav.querySelector('.brand');
    const search = nav.querySelector('.nav-search-trigger');
    if (!brand || !search) return;
    const prefix = (brand.getAttribute('href') || '').startsWith('#') ? '' : new URL('/', brand.href).href;
    const links = document.createElement('div');
    links.className = 'top-links';
    links.setAttribute('aria-label', 'Site pages');
    for (const [label, hash] of [['Home','#home'],['Articles','#articles'],['Categories','#categories'],['About','#about'],['Contact','#contact']]) {
      const link = document.createElement('a');
      link.href = prefix + hash;
      link.textContent = label;
      links.appendChild(link);
    }
    nav.replaceChildren(brand, links, search);
    nav.classList.add('top-nav');
    document.getElementById('site-drawer')?.remove();
    // Legacy generated pages still carry the old inline stylesheet until the next SEO rebuild.
    const sheet = document.createElement('style');
    sheet.id = 'cozy-top-nav-legacy-style';
    sheet.textContent = "/* CozyLoops: every destination visible in the top header, even on narrow phones. */\n.nav.top-nav{max-width:1200px;min-height:75px;margin:auto;padding:13px 22px;display:flex;align-items:center;justify-content:space-between;flex-wrap:nowrap;gap:clamp(10px,1.5vw,22px)}\n.top-nav .brand{flex:none;white-space:nowrap;font-size:clamp(24px,2.3vw,29px)}\n.top-links{display:flex;align-items:center;justify-content:center;gap:clamp(2px,.65vw,10px);min-width:0;margin-left:auto}\n.top-links a{display:inline-flex;align-items:center;justify-content:center;white-space:nowrap;min-height:42px;padding:9px 11px;border-radius:999px;font:650 14px/1.3 system-ui,-apple-system,Segoe UI,sans-serif;color:#3a4d40;text-align:center;transition:color .2s,background .2s}\n.top-links a:hover,.top-links a:focus-visible,.top-links a[aria-current=\"page\"]{background:#edf3e9;color:var(--green,#4f694c)}\n.top-nav .nav-search-trigger{display:inline-flex;align-items:center;justify-content:center;flex:none;margin-left:0;width:43px;height:43px;border:1px solid var(--line,#e5e7df);border-radius:999px;background:#fff;color:var(--green,#4f694c);transition:background .18s,color .18s}\n.top-nav .nav-search-trigger:hover{background:var(--green,#4f694c);color:#fff}\n.top-links a:focus-visible,.top-nav .nav-search-trigger:focus-visible{outline:3px solid #bd946e;outline-offset:3px}\n@media(max-width:760px){\n .nav.top-nav{display:grid;grid-template-columns:minmax(0,1fr) 44px;grid-template-areas:\"brand search\" \"links links\";align-items:center;gap:8px 10px;padding:10px 16px 11px;min-height:0}\n .top-nav .brand{grid-area:brand;font-size:25px;overflow:hidden;text-overflow:ellipsis}\n .top-nav .nav-search-trigger{grid-area:search;justify-self:end;width:42px;height:42px}\n .top-links{grid-area:links;display:grid;grid-template-columns:repeat(6,minmax(0,1fr));width:100%;margin:0;padding-top:8px;border-top:1px solid var(--line,#e5e7df);gap:6px}\n .top-links a{grid-column:span 2;width:100%;min-height:37px;padding:7px 3px;font-size:13px}\n .top-links a:nth-child(4),.top-links a:nth-child(5){grid-column:span 3}\n}\n@media(max-width:370px){.top-nav .brand{font-size:23px}.top-links a{font-size:12px}}\n@media(prefers-reduced-motion:reduce){.top-links a,.top-nav .nav-search-trigger{transition:none!important}}\n@media print{.top-nav .nav-search-trigger{display:none!important}}";
    document.head.appendChild(sheet);
  }
  function setActiveLink() {
    const active = /^\/posts\/[^/]+\//.test(location.pathname) ? '#articles' : (location.hash || '#home');
    nav.querySelectorAll('.top-links a').forEach(link => {
      if (link.hash === active) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
  }
  setActiveLink();
  window.addEventListener('hashchange', setActiveLink);
})();
