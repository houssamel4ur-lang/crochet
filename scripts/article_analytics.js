(() => {
  "use strict";
  const base = "https://yqmrunstyhrhnvxoyrap.supabase.co/rest/v1/rpc/record_cozyloop_view";
  const apikey = "sb_publishable_HqkcpvBz8P8KJTZFgefrWQ_rFxKPMNh";
  const match = location.pathname.match(/\/posts\/([a-z0-9]+(?:-[a-z0-9]+)*)\/?$/);
  if (!match) return;
  const page = "post/" + match[1];
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
  if (!consent() && navigator.doNotTrack !== "1") banner.hidden = false;
  document.getElementById("privacy-accept").addEventListener("click", () => {
    try { localStorage.setItem("cozyloops_analytics_consent","yes"); } catch {}
    banner.hidden = true;
    record();
  });
  document.getElementById("privacy-decline").addEventListener("click", () => {
    try { localStorage.setItem("cozyloops_analytics_consent","no"); } catch {}
    banner.hidden = true;
  });
  record();
})();
