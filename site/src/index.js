/**
 * The deployed workbench: Cloudflare serves the static export, and this
 * script counts page views into D1 and renders /stats.
 *
 * The script runs only for the page routes named in run_worker_first
 * (site/wrangler.toml). Asset fetches never invoke it. Every page view is
 * one row: (day, path, country, visitor). The visitor value is a truncated
 * salted hash of the client address and the browser string, so no raw
 * address is stored and no cookie is set.
 *
 * Counting must never break a page: the write goes through ctx.waitUntil
 * and its failure is swallowed.
 */

const STATS_DAYS = 30;

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === "/stats" || url.pathname === "/stats.json") {
      return statsResponse(env, url);
    }
    const response = await env.ASSETS.fetch(request);
    await countPageView(request, response, env, ctx);
    return response;
  },
};

async function countPageView(request, response, env, ctx) {
  if (request.method !== "GET" || response.status !== 200) return;
  const type = response.headers.get("content-type") || "";
  if (!type.includes("text/html")) return;
  const ua = request.headers.get("user-agent") || "";
  if (/bot|crawl|spider|slurp|monitor|uptime|deploy-check|curl|wget|http-client/i.test(ua)) {
    return;
  }
  if (!env.DB) return;
  const day = new Date().toISOString().slice(0, 10);
  const country = (request.cf && request.cf.country) || "XX";
  const path = new URL(request.url).pathname;
  const visitor = await visitorHash(request, env);
  ctx.waitUntil(
    env.DB.prepare(
      "INSERT INTO hits (day, path, country, visitor) VALUES (?1, ?2, ?3, ?4)"
    )
      .bind(day, path, country, visitor)
      .run()
      .catch(() => {})
  );
}

async function visitorHash(request, env) {
  const salt = env.COUNTER_SALT || "";
  const ip = request.headers.get("cf-connecting-ip") || "";
  const ua = request.headers.get("user-agent") || "";
  const bytes = new TextEncoder().encode(`${salt}|${ip}|${ua}`);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  const hex = [...new Uint8Array(digest)]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  return hex.slice(0, 24);
}

async function statsResponse(env, url) {
  if (!env.DB) {
    return new Response("stats: no D1 database is bound", { status: 500 });
  }
  try {
    const [daily, countries, paths, totals] = await env.DB.batch([
      env.DB.prepare(
        "SELECT day, count(*) AS pageviews, count(DISTINCT visitor) AS visitors " +
          "FROM hits GROUP BY day ORDER BY day DESC LIMIT ?1"
      ).bind(STATS_DAYS),
      env.DB.prepare(
        "SELECT country, count(*) AS pageviews, count(DISTINCT visitor) AS visitors " +
          "FROM hits GROUP BY country ORDER BY visitors DESC LIMIT 30"
      ),
      env.DB.prepare(
        "SELECT path, count(*) AS pageviews, count(DISTINCT visitor) AS visitors " +
          "FROM hits GROUP BY path ORDER BY pageviews DESC LIMIT 30"
      ),
      env.DB.prepare(
        "SELECT count(*) AS pageviews, count(DISTINCT visitor) AS visitors, " +
          "min(day) AS since FROM hits"
      ),
    ]);
    const data = {
      generated: new Date().toISOString(),
      totals: totals.results[0] || { pageviews: 0, visitors: 0, since: null },
      daily: daily.results,
      countries: countries.results,
      paths: paths.results,
    };
    if (url.pathname === "/stats.json") {
      return Response.json(data);
    }
    return new Response(statsHtml(data), {
      headers: { "content-type": "text/html; charset=utf-8" },
    });
  } catch (error) {
    return new Response("stats unavailable: " + error.message, { status: 500 });
  }
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[c]));
}

function table(head, rows) {
  return (
    `<table><thead><tr>${head.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead>` +
    `<tbody>${rows
      .map((row) => `<tr>${row.map((cell) => `<td>${esc(cell)}</td>`).join("")}</tr>`)
      .join("")}</tbody></table>`
  );
}

function statsHtml(data) {
  const totals = data.totals;
  return `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>visitors · protein design workbench</title>
<style>
  body { background: #0b0c14; color: #cbd2dd; font-family: system-ui, sans-serif;
         margin: 0 auto; max-width: 980px; padding: 40px 20px 80px; line-height: 1.6; }
  h1 { color: #fff; font-size: 24px; margin: 0 0 6px; }
  h2 { color: #fff; font-size: 17px; margin: 34px 0 8px; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #232c44; padding: 6px 10px; font-size: 13px; text-align: left; }
  th { background: #141829; color: #fff; }
  td { font-variant-numeric: tabular-nums; }
  .sub { color: #8b95a8; font-size: 12px; }
  a { color: #0da2e7; }
</style></head><body>
<h1>Visitors</h1>
<div class="sub">Page views of the workbench pages. Explorer frames and
static assets are not counted. "Visitors" counts distinct salted visitor
hashes: no cookies, no raw addresses. Generated ${esc(data.generated)}.</div>
<div class="sub" style="margin-top:8px">Total: ${esc(totals.pageviews)} page
views, ${esc(totals.visitors)} visitors since ${esc(totals.since ?? "no data yet")}.
<a href="/stats.json">JSON</a> · <a href="/">workbench</a></div>
<h2>Per day (last ${esc(data.daily.length)})</h2>
${table(["day", "page views", "visitors"], data.daily.map((d) => [d.day, d.pageviews, d.visitors]))}
<h2>Countries</h2>
${table(["country", "page views", "visitors"], data.countries.map((d) => [d.country, d.pageviews, d.visitors]))}
<h2>Top paths</h2>
${table(["path", "page views", "visitors"], data.paths.map((d) => [d.path, d.pageviews, d.visitors]))}
</body></html>`;
}
