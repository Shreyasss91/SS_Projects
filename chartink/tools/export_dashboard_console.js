/**
 * Paste into Chrome DevTools Console on a logged-in Chartink page
 * (preferably https://chartink.com/scan_dashboard).
 * Downloads chartink_dashboard_pages.json
 *
 * Fixes Inertia 409 by sending X-Inertia-Version from the live page,
 * and falls back to full HTML parse when needed.
 */
(async () => {
  const pages = 10;
  const perPage = 50;

  function decodeEntities(s) {
    const ta = document.createElement("textarea");
    ta.innerHTML = s;
    return ta.value;
  }

  function parseInertiaFromHtml(html) {
    const m = html.match(/data-page="([^"]+)"/);
    if (!m) return null;
    return JSON.parse(decodeEntities(m[1]));
  }

  function getPageVersion() {
    const el = document.querySelector("[data-page]");
    if (!el) return null;
    try {
      const data = JSON.parse(decodeEntities(el.getAttribute("data-page")));
      return data.version || null;
    } catch (_) {
      return null;
    }
  }

  async function fetchDashboardPage(page, version) {
    const url = `https://chartink.com/scan_dashboard?page=${page}&per_page=${perPage}`;

    // 1) Inertia JSON request (fast path)
    const headers = {
      Accept: "text/html, application/xhtml+xml",
      "X-Requested-With": "XMLHttpRequest",
      "X-Inertia": "true",
    };
    if (version) headers["X-Inertia-Version"] = version;

    let r = await fetch(url, { credentials: "include", headers });

    // 409 = version mismatch → refresh version from current document / HTML and retry once
    if (r.status === 409) {
      console.warn(`page ${page}: Inertia 409, retrying with fresh version/HTML`);
      const htmlProbe = await fetch(url, {
        credentials: "include",
        headers: { Accept: "text/html" },
      });
      const html = await htmlProbe.text();
      const fromHtml = parseInertiaFromHtml(html);
      if (fromHtml) return fromHtml;

      // retry inertia with version from probe if present
      const m = html.match(/data-page="([^"]+)"/);
      if (m) {
        try {
          const v = JSON.parse(decodeEntities(m[1])).version;
          if (v) {
            r = await fetch(url, {
              credentials: "include",
              headers: {
                ...headers,
                "X-Inertia-Version": v,
              },
            });
          }
        } catch (_) {}
      }
    }

    if (r.status === 409 || !r.ok) {
      // 2) Full document fetch (always works when session is valid)
      const htmlR = await fetch(url, {
        credentials: "include",
        headers: { Accept: "text/html" },
      });
      if (!htmlR.ok) {
        throw new Error(`Page ${page}: HTTP ${htmlR.status} ${htmlR.url}`);
      }
      const html = await htmlR.text();
      const data = parseInertiaFromHtml(html);
      if (!data) {
        throw new Error(
          `Page ${page}: no inertia payload (login expired? final=${htmlR.url})`
        );
      }
      return data;
    }

    const text = (await r.text()).trim();
    if (text.startsWith("{")) return JSON.parse(text);

    const data = parseInertiaFromHtml(text);
    if (!data) {
      throw new Error(`Page ${page}: could not parse response`);
    }
    return data;
  }

  // Prefer version from the page you already have open
  let version = getPageVersion();
  console.log("Inertia version:", version);

  // If already on page 1 of dashboard, capture current DOM first (no network)
  const all = [];
  const current = document.querySelector("[data-page]");
  let startPage = 1;
  if (current && location.pathname.includes("scan_dashboard")) {
    try {
      const curData = JSON.parse(decodeEntities(current.getAttribute("data-page")));
      if (
        curData &&
        !String(curData.component || "").includes("Login") &&
        !String(curData.url || "").includes("login")
      ) {
        const params = new URLSearchParams(location.search);
        const curPage = Number(params.get("page") || "1");
        if (curPage === 1) {
          console.log("page 1 from current DOM", curData.component);
          all.push(curData);
          version = curData.version || version;
          startPage = 2;
        }
      }
    } catch (e) {
      console.warn("could not use current DOM page", e);
    }
  }

  for (let page = startPage; page <= pages; page++) {
    const data = await fetchDashboardPage(page, version);
    version = data.version || version;
    console.log(
      `page ${page}`,
      data.component,
      Object.keys(data.props || {}),
      data.url
    );
    if (
      String(data.component || "").includes("Login") ||
      String(data.url || "").includes("/login")
    ) {
      throw new Error("Not logged in — complete Chartink login and re-run.");
    }
    all.push(data);
    // keep page order stable
    all.sort((a, b) => {
      const pa = Number(String(a.url || "").match(/page=(\d+)/)?.[1] || 0);
      const pb = Number(String(b.url || "").match(/page=(\d+)/)?.[1] || 0);
      return pa - pb;
    });
    await new Promise((res) => setTimeout(res, 250));
  }

  // de-dupe by url
  const seen = new Set();
  const unique = [];
  for (const d of all) {
    const key = d.url || JSON.stringify(d).slice(0, 80);
    if (seen.has(key)) continue;
    seen.add(key);
    unique.push(d);
  }

  const blob = new Blob([JSON.stringify(unique, null, 2)], {
    type: "application/json",
  });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "chartink_dashboard_pages.json";
  document.body.appendChild(a);
  a.click();
  a.remove();
  console.log(
    "Downloaded chartink_dashboard_pages.json with",
    unique.length,
    "page payloads"
  );
})();
