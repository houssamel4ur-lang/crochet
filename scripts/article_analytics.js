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
  if (printButton) printButton.addEventListener("click", () => {
    let dialog = document.getElementById("article-pdf-ad-dialog");
    if (!dialog) {
      dialog = document.createElement("dialog");
      dialog.id = "article-pdf-ad-dialog";
      dialog.setAttribute("aria-labelledby", "article-pdf-ad-title");
      dialog.style.cssText = "width:min(92vw,560px);border:1px solid #e5e7df;border-radius:16px;padding:24px;color:#29342d;box-shadow:0 16px 48px #0003";
      dialog.innerHTML = '<h2 id="article-pdf-ad-title">Before you save this article</h2><p>A quick ad helps support free crochet guides.</p><div id="hbagency_space_351114"></div><button type="button" id="article-pdf-continue" style="min-height:44px;margin-top:16px;padding:10px 18px;border:0;border-radius:24px;background:#4f694c;color:#fff;font:600 15px system-ui,sans-serif;cursor:pointer">Continue to PDF</button>';
      document.body.appendChild(dialog);
      dialog.addEventListener("click", event => { if (event.target === dialog) dialog.close(); });
      dialog.querySelector("#article-pdf-continue").addEventListener("click", () => {
        dialog.close();
        window.setTimeout(() => window.print(), 300);
      });
    }
    if (typeof dialog.showModal === "function") dialog.showModal();
    else { dialog.setAttribute("open", ""); }
  });
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
  const manage = document.createElement("button");
  manage.type = "button"; manage.textContent = "Cookie settings";
  manage.style.cssText = "min-height:44px;padding:9px 13px;margin:10px;border-radius:10px";
  manage.addEventListener("click", () => { banner.hidden = false; });
  document.querySelector("footer")?.appendChild(manage);
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
  if (!consent()) banner.hidden = false;
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
