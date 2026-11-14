/* Shared navigation: upgrade pre-existing static articles until the SEO build publishes them. */
(() => {
  'use strict';
  const nav = document.querySelector('header > nav.nav');
  if (!nav) return;
  // Existing SEO articles can have the prior inline CSS until the rebuild.
  // Always ensure the compact layout wins, including on already-modern nav markup.
  if (![...document.querySelectorAll('style')].some(el => el.textContent.includes('/* CozyLoops: compact static header; all five links on a single phone row. */'))) {
    const correction = document.createElement('style');
    correction.id = 'cozy-top-nav-legacy-style';
    correction.textContent = "/* CozyLoops: compact static header; all five links on a single phone row. */\nheader{position:relative;top:auto}\n.nav.top-nav{max-width:1200px;min-height:64px;margin:auto;padding:10px 22px;display:flex;align-items:center;justify-content:space-between;flex-wrap:nowrap;gap:clamp(8px,1.2vw,16px)}\n.top-nav .brand{flex:none;white-space:nowrap;font-size:clamp(23px,2.2vw,28px)}\n.top-links{display:flex;align-items:center;justify-content:center;gap:clamp(1px,.45vw,7px);min-width:0;margin-left:auto}\n.top-links a{display:inline-flex;align-items:center;justify-content:center;white-space:nowrap;min-height:38px;padding:7px 9px;border-radius:999px;font:650 13px/1.25 system-ui,-apple-system,Segoe UI,sans-serif;color:#3a4d40;text-align:center;transition:color .2s,background .2s}\n.top-links a:hover,.top-links a:focus-visible,.top-links a[aria-current=\"page\"]{background:#edf3e9;color:var(--green,#4f694c)}\n.top-nav .nav-search-trigger{display:inline-flex;align-items:center;justify-content:center;flex:none;margin-left:0;width:40px;height:40px;border:1px solid var(--line,#e5e7df);border-radius:999px;background:#fff;color:var(--green,#4f694c);transition:background .18s,color .18s}\n.top-nav .nav-search-trigger:hover{background:var(--green,#4f694c);color:#fff}\n.top-links a:focus-visible,.top-nav .nav-search-trigger:focus-visible{outline:3px solid #bd946e;outline-offset:3px}\n#home,#articles,#categories,#about,#contact,#search-articles{scroll-margin-top:16px}\n@media(max-width:760px){\n .nav.top-nav{display:grid;grid-template-columns:minmax(0,1fr) 38px;grid-template-areas:\"brand search\" \"links links\";align-items:center;gap:5px 8px;padding:8px 12px 7px;min-height:0}\n .top-nav .brand{grid-area:brand;font-size:clamp(20px,5.5vw,23px);overflow:hidden;text-overflow:ellipsis}\n .top-nav .nav-search-trigger{grid-area:search;justify-self:end;width:37px;height:37px}\n .top-nav .nav-search-trigger svg{width:19px;height:19px}\n .top-links{grid-area:links;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));width:100%;margin:0;padding-top:4px;border-top:1px solid var(--line,#e5e7df);gap:1px}\n .top-links a{grid-column:auto;min-width:0;width:100%;min-height:32px;padding:6px 1px;border-radius:999px;font-size:clamp(9px,2.7vw,11.5px);line-height:1.2;letter-spacing:-.15px}\n}\n@media(prefers-reduced-motion:reduce){.top-links a,.top-nav .nav-search-trigger{transition:none!important}}\n@media print{.top-nav .nav-search-trigger{display:none!important}}";
    document.head.appendChild(correction);
  }
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
  }

  // Public member entry stays compact on phones and never changes the five navigation links.
  if (!nav.querySelector('.nav-account-trigger')) {
    const account=document.createElement('a');
    account.className='nav-account-trigger';
    account.href=new URL('/account/',location.href).href;
    account.setAttribute('aria-label','Log in or create an account');
    account.setAttribute('title','Log in or register');
    account.innerHTML='<svg viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="8" r="3.5"></circle><path d="M5 20v-2.4a7 7 0 0 1 14 0V20z"></path></svg><span>Login / Register</span>';
    nav.append(account);
  }
  if (!document.getElementById('cozy-account-nav-style')) {
    const authStyle=document.createElement('style');
    authStyle.id='cozy-account-nav-style';
    authStyle.textContent='.top-nav .nav-account-trigger{display:inline-flex;align-items:center;justify-content:center;flex:none;gap:7px;padding:9px 13px;border-radius:999px;min-height:40px;border:1px solid #dfe7db;background:#edf3e9;color:#375641;font:700 12px/1.2 system-ui,-apple-system,Segoe UI,sans-serif;white-space:nowrap}.top-nav .nav-account-trigger:hover{background:#dfeadd}.top-nav .nav-account-trigger:focus-visible{outline:3px solid #bd946e;outline-offset:3px}@media(max-width:760px){.nav.top-nav{grid-template-columns:minmax(0,1fr) 38px 38px;grid-template-areas:"brand search account" "links links links"}.top-nav .nav-account-trigger{grid-area:account;width:37px;height:37px;min-height:37px;padding:0;justify-self:end;border-radius:50%}.top-nav .nav-account-trigger span{display:none}}@media print{.top-nav .nav-account-trigger{display:none!important}}';
    document.head.append(authStyle);
  }
  function setActiveLink() {
    const active = location.pathname.startsWith('/posts/') ? '#articles' : (location.hash || '#home');
    nav.querySelectorAll('.top-links a').forEach(link => {
      if (link.hash === active) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
  }
  setActiveLink();
  window.addEventListener('hashchange', setActiveLink);
})();
