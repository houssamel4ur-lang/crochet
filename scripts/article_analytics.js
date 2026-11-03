(() => {
  "use strict";
  const base = "https://yqmrunstyhrhnvxoyrap.supabase.co/rest/v1/rpc/record_cozyloop_view";
  const apikey = "sb_publishable_BpOaWu4aKoE5saOhdjaT-g_c9vTG3o8";
  const match = location.pathname.match(/\/posts\/([a-z0-9]+(?:-[a-z0-9]+)*)\/?$/);
  if (!match) return;
  const page = "post/" + match[1];
  const backToTop = document.getElementById("back-to-top");
  const updateBackToTop = () => {
    if (backToTop) backToTop.hidden = window.scrollY < 450;
  };
  if (backToTop) {
    backToTop.addEventListener("click", () => window.scrollTo({
      top:0,behavior:matchMedia("(prefers-reduced-motion: reduce)").matches?"instant":"smooth"
    }));
  }
  updateBackToTop();
  // Update once per frame and avoid blocking scrolling on long patterns.
  const progress = document.getElementById("reading-progress");
  const article = document.querySelector("main article.article");
  if (progress && article) {
    let queued = false;
    const update = () => {
      queued = false;
      const total = Math.max(1, article.offsetHeight - window.innerHeight);
      const scrolled = Math.max(0, -article.getBoundingClientRect().top);
      const percentage = Math.max(0, Math.min(100, Math.round(scrolled / total * 100)));
      if (progress.firstElementChild) progress.firstElementChild.style.width = percentage + "%";
      progress.setAttribute("aria-valuenow", String(percentage));
      updateBackToTop();
    };
    const schedule = () => {
      if (queued) return;
      queued = true;
      requestAnimationFrame(update);
    };
    addEventListener("scroll", schedule, {passive:true});
    addEventListener("resize", schedule, {passive:true});
    schedule();
  } else if (backToTop) {
    addEventListener("scroll", updateBackToTop, {passive:true});
  }

  const printButton = document.getElementById("article-print-button");
  if (printButton) printButton.addEventListener("click", () => window.print());
  const shareButton = document.getElementById("article-share-button");
  if (shareButton) shareButton.addEventListener("click", async () => {
    const status = document.getElementById("article-share-status");
    const url = location.href.split("#")[0];
    try {
      if (navigator.share) {
        try { await navigator.share({title:document.title,url}); if (status) status.textContent="Article shared."; return; }
        catch (error) { if (error.name === "AbortError") return; }
      }
      await navigator.clipboard.writeText(url);
      if (status) status.textContent="Article link copied!";
    } catch {
      if (status) status.textContent="Copy this article URL from your address bar.";
    }
  });
  const banner = document.getElementById("privacy-choice");
  if (!banner) return;
  const consent = () => { try { return localStorage.getItem("cozyloops_analytics_consent") || ""; } catch { return ""; } };
  const visitorId = () => {
    const day = new Date().toISOString().slice(0,10);
    const key = "cozyloops_visitor_day";
    try {
      const existing = JSON.parse(localStorage.getItem(key) || "null");
      if (existing?.day === day && existing.id) return existing.id;
      const id = crypto.randomUUID();
      localStorage.setItem(key, JSON.stringify({day,id}));
      return id;
    } catch { return null; }
  };
  const record = async () => {
    if (consent() !== "yes" || navigator.doNotTrack === "1") return;
    const key = "cozyloops_counted_" + new Date().toISOString().slice(0,10) + "_" + page;
    try { if (sessionStorage.getItem(key)) return; } catch {}
    const id = visitorId();
    if (!id) return;
    try {
      const response = await fetch(base, {
        method:"POST",
        headers:{apikey,"Content-Type":"application/json"},
        body:JSON.stringify({p_page:page,p_visitor:id})
      });
      if (response.ok && await response.json() === true) {
        try { sessionStorage.setItem(key,"1"); } catch {}
      }
    } catch { /* Stats must never interrupt reading the article. */ }
  };
  const status = document.getElementById("article-consent-status");
  const optOut = document.getElementById("article-privacy-opt-out");
  if (status) status.textContent = consent() === "yes" ? "Optional analytics: enabled." : "Optional analytics: disabled.";
  if (optOut) optOut.addEventListener("click", () => {
    try {
      localStorage.setItem("cozyloops_analytics_consent", "no");
      localStorage.removeItem("cozyloops_visitor_day");
    } catch { /* Still update the visible state. */ }
    banner.hidden = true;
    if (status) status.textContent = "Optional analytics: disabled. No further visits will be counted from this browser.";
  });
  if (!consent() && navigator.doNotTrack !== "1") banner.hidden = false;
  document.getElementById("privacy-accept")?.addEventListener("click", () => {
    try { localStorage.setItem("cozyloops_analytics_consent","yes"); } catch {}
    banner.hidden = true;
    if (status) status.textContent = "Optional analytics: enabled.";
    record();
  });
  document.getElementById("privacy-decline")?.addEventListener("click", () => {
    try { localStorage.setItem("cozyloops_analytics_consent","no"); } catch {}
    banner.hidden = true;
    if (status) status.textContent = "Optional analytics: disabled.";
  });
  record();
})();
