/* Shared accessible, keyboard-friendly sliding side menu on homepage and article pages. */
(() => {
  'use strict';
  const drawer = document.getElementById('site-drawer');
  const toggle = document.querySelector('.nav-menu-toggle');
  const close = drawer?.querySelector('.drawer-close');
  if (!drawer || !toggle || !close) return;
  toggle.addEventListener('click', () => {
    if (drawer.open) return;
    drawer.showModal();
    toggle.setAttribute('aria-expanded', 'true');
    close.focus();
  });
  close.addEventListener('click', () => drawer.close());
  drawer.addEventListener('click', event => {
    if (event.target === drawer) drawer.close();
  });
  drawer.addEventListener('close', () => toggle.setAttribute('aria-expanded', 'false'));
  drawer.querySelectorAll('a[href]').forEach(link => {
    link.addEventListener('click', () => {
      drawer.close();
      if (link.hash && link.hash === location.hash && link.origin === location.origin && link.pathname === location.pathname) {
        requestAnimationFrame(() => window.dispatchEvent(new Event('hashchange')));
      }
    });
  });
})();
