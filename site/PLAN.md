# Cloudflare deployment: the plan

Status: built 2026-11-19, not deployed. The deploy is armed by the repository
variable `CF_DEPLOY` (section 7). This version covers the transfer reduction,
the observability stack and the About page.

The model is protein-with-rust: one Cloudflare Worker serves a static site.
GitHub Actions deploys on every push to `main`. Two repository secrets carry
the Cloudflare credentials.

## 1. The shape

The workbench is a Python app (`pdt serve`). A Worker cannot run the app,
because the app reads the local filesystem and imports Python packages.
Therefore the deployed site is a static export: the build renders the pages to
files. The export calls the app's own render functions (`_herohome`,
`page_challenge`, `page_lineage`, `page_about`), so the deployed pages are the
same pages the app serves today.

| Site part | Source | Size |
| --- | --- | --- |
| index | `_herohome()` | small |
| five challenge homes | `page_challenge()` | small |
| 33 campaign pages | `lineage.json`, per challenge | small |
| four complete histories | `challenges/<c>/docs/*.html` | 7 MB |
| Mol* explorers (34 pages ship) | `challenges/<c>/viewers/multiview/` | 63 MB |
| Mol* engine | one copy of `molstar-bundle.js` | 7 MB |
| 04 step figures | `challenges/04-tfr1/viewers/*.png` | 0.6 MB |
| static assets | `tools/serve/static/` | 0.7 MB |
| About page | `page_about()` | small |

About 88 MB and about 110 files. The first draft of this plan took about
120 MB. Section 3 gives the reductions.

Excluded, and why:

- the run folders (`challenges/*/runs/`): gitignored and local only.
- the media files and the video series (68 MB): not part of the app's pages.
- `challenges/02-tnfa/viewers/views/` (55 MB): screenshots, referenced by
  nothing the site serves.
- `challenges/*/docs/figures/` (5 MB): source files. Each history embeds its
  figures as data URIs and has no external image reference.
- the 02 `*_explorer.html` pages (1 MB): no page links to them today.
- `challenges/03-glp1r/viewers/assets/*.svg` (16 KB): referenced by nothing.

The free plan allows 20,000 files per Worker version and 25 MiB per file. The
largest served file is 13.8 MB. The margin is large.

## 2. The About page

A new page at `/about`, in the app and on the site, in the shape of the
protein-with-rust about page: a heading, the same two profile links, a short
biography, and a paragraph about this workspace. One new function
(`page_about()`) serves the app route and the export.

The page carries this text (edit it freely):

> **Anton Chernysh**
>
> I am a site reliability engineer in Zurich. This workbench is my entry for
> the Anthropic × Adaptyv 2026 protein-design competition.
>
> I build and scale infrastructure for startups, with five years of taking
> products from an early prototype to production systems that stay up under
> real traffic. I write production code in Go and Python, and I care about the
> whole lifecycle: architecture, observability, incident response, and the
> optimizations that make systems faster and cheaper to run.
>
> This workspace is the competition work itself: one folder per challenge,
> every campaign kept, the negative results included, and every number sourced
> from the dated records beside it. The site you are reading is built from the
> same files the local app serves.
>
> [LinkedIn](https://www.linkedin.com/in/anton-chernysh/) ·
> [GitHub](https://github.com/Visn0)

The top navigation gains one item, "About". The export writes `about.html`.
The smoke check fetches `/about`.

## 3. Transfer: smaller pages, less transfer

Two kinds of transfer matter: the upload on every deploy, and the download of
every visitor. Measured sizes (the gzip numbers are a close proxy for the
Zstandard compression that Cloudflare serves on the free plan):

| File | Written | Compressed | Ratio |
| --- | --- | --- | --- |
| `c12-rfd4-proteina.html` (largest explorer) | 13.8 MB | 2.9 MB | 22% |
| `c1-main-funnel.html` (typical explorer) | 529 KB | 130 KB | 24% |
| `molstar-bundle.js` | 7.2 MB | 1.3 MB | 17% |
| `challenge-5-complete-history.html` | 1.5 MB | 1.1 MB | 73% |

Cloudflare compresses compressible responses for visitors by default. The
histories compress poorly, because their bulk is embedded base64 images.

The build rules that cut the numbers:

1. **One engine copy.** All 34 shipped explorer pages reference the same engine file.
   The export writes it once at `/engine/molstar-bundle.js` and rewrites every
   `src` to point there. Upload: minus 22 MB. A visitor who opens explorers in
   two challenges downloads the engine once.
2. **Ship only referenced files.** The export copies a viewer asset only when
   a page references it. This removes the sources listed in section 1.
   Upload: minus 6 MB. Zero visitor impact.
3. **Count only page routes.** Section 5 keeps asset fetches out of the
   Worker script.

One bigger redesign stays for later (section 11): the explorer pages embed
every design's structure text in the page (the largest is one 13.8 MB line of
PDB text). A split into per-design files, loaded on demand, cuts the first
view of an explorer from megabytes to kilobytes. That changes the shared
generator, so it stays out of v1.

## 4. Observability: unique visitors and countries

Three layers, all free:

1. **Cloudflare Web Analytics** (the standard dashboard). No DNS change. One
   setup step: register the exact hostname
   `protein-design-workbench.antonchernysh.workers.dev` with "Add a site", and
   copy the site token into the export config. The token is public by design.
   The export injects the beacon snippet into every top-level page. Viewer
   iframe pages stay clean, so one visit is one page view. The dashboard
   gives: visits, page views, countries, paths, referrers, device, browser,
   operating system, navigation type, a bot filter, Core Web Vitals, and a
   weekly email report. It does not give unique-user counts, so layer 2
   covers that.
2. **A counter in the Worker** (the unique users, by country). The script
   runs for page routes only (section 5). Each page view writes one row to a
   D1 database: `(day, path, country, visitor)`. The country comes from
   `request.cf.country`. The visitor value is a truncated salted hash of the
   client address and the browser string. No cookies and no raw addresses.
   Unique visitors = `COUNT(DISTINCT visitor)`, per day and per country. The
   D1 free tier allows 100,000 writes per day, and one page view is one
   write. The Worker skips obvious bots and the smoke-check agent. A `/stats`
   page and `/stats.json` show the last 30 days: page views per day, unique
   visitors per day, unique visitors per country, and the top paths. Both are
   private: they open only with the STATS_KEY secret as a `?key=` parameter,
   and they return 404 without it.
3. **Workers Logs and an uptime check.** `[observability] enabled = true`
   collects request logs. The free tier carries 200,000 events per day with 3
   day retention until 2026-12-01, then 0.5 GB per day with 7 day retention.
   A scheduled GitHub Action fetches the site every six hours and fails
   loudly on a bad answer.

Metric definition, stated plainly: "unique users" is unique salted visitor
hashes. One person on three days counts as three daily visitors. If the site
becomes gated with Cloudflare Access, the Access logs give exact identities.

## 5. The Worker

`site/wrangler.toml` (sketch):

```toml
name = "protein-design-workbench"
main = "src/index.js"
compatibility_date = "2026-11-19"

[assets]
directory = "dist"
html_handling = "auto-trailing-slash"
not_found_handling = "404-page"
run_worker_first = ["/", "/ch/*", "/lineage/*", "/about*", "/stats*"]

[[d1_databases]]
binding = "DB"
database_name = "pdt-stats"
database_id = "REPLACE_WITH_THE_D1_ID"

[observability]
enabled = true
```

The script is small. Every request reaches `env.ASSETS.fetch(request)`. A page
view also writes one D1 row through `ctx.waitUntil`, so the write never
delays the response. `/stats` renders from D1. `/stats.json` returns the same
data as JSON. Both require the STATS_KEY secret as a `?key=` parameter and
answer 404 without it. The pattern list needs a check at build: every page
route must be covered, and asset fetches must stay out.

Costs: page views invoke the script and count against the free 100,000
requests per day. Asset fetches do not invoke the script.

- `site/package.json` pins `wrangler` as a devDependency (4.165.0; 4.135.0
  rejects the 2026-11-19 compatibility date locally). CI installs the pinned
  tool with `npm ci`.

## 6. The build: `pdt export`

New code: `tools/serve/export.py` and the command `pdt export --out site/dist`.

The route map:

| App route | File in `site/dist` |
| --- | --- |
| `/` | `index.html` |
| `/about` | `about.html` |
| `/ch/<c>` | `ch/<c>/index.html` |
| `/ch/<c>/history` | `ch/<c>/history/index.html` |
| `/lineage/<c>/<exp>` | `lineage/<c>/<exp>/index.html` |
| `/static/...` | `static/...` |
| `/engine/molstar-bundle.js` | one engine copy |
| `/viewer-asset/<c>/<rel>` | `viewer-asset/<c>/<rel>` |
| `/ch/<c>/target...` | `ch/<c>/target...`, extensionless files |
| any unknown path | `404.html` |

Build rules:

1. The export ignores run folders. A local build and a CI build produce the
   same files.
2. Every `href`, `src` and `data-src` in the generated pages must resolve to a
   file in dist, or to a Worker route (`/stats`). The export stops and lists
   the misses. This guard finds a source that is not committed yet.
3. Viewer assets are copied only when a page references them. The engine is
   deduped (section 3).
4. The beacon snippet is injected into top-level pages only.
5. `_headers` gives the extensionless target files the type `text/plain`.
6. `site/dist/` and `site/node_modules/` are gitignored.

## 7. CI: `.github/workflows/deploy.yml` (new, the repo has none today)

Build job, on every push and pull request:

1. Checkout, install uv, then `make install` (Python 3.12).
2. `pdt export --out site/dist`. The export runs its checker.
3. Upload `site/dist` as the artifact `site-dist`.

Deploy job, only on a push to `main`, after the build:

1. Download `site-dist` to `site/dist`.
2. `npm ci` in `site/`.
3. Guard: both secrets must be present, `site/dist/index.html` must exist,
   and `site/wrangler.toml` must not carry the placeholder D1 id. The job
   stops early with a clear message.
4. Apply the D1 schema:
   `wrangler d1 execute pdt-stats --remote --file=site/schema.sql`. The
   schema uses `CREATE TABLE IF NOT EXISTS`, so the step is safe to repeat.
5. `wrangler deploy --config site/wrangler.toml`, from the repository root.
6. Smoke check (section 9).

The job runs in the `deploy-production` concurrency group. It runs only when
the repository variable `CF_DEPLOY` is `1`. That variable is the go-live
switch, so a push cannot publish the site before you arm it.

## 8. One-time setup (your actions)

1. Add the repository secrets `CLOUDFLARE_API_TOKEN` and
   `CLOUDFLARE_ACCOUNT_ID` to `Visn0/adaptyv-protein-design-2026`. Same
   values as the protein-with-rust repository. The deploy stops with a clear
   message when they are missing.
2. Create the D1 database: `npx wrangler@4.165.0 d1 create pdt-stats`. Put
   the returned id into `site/wrangler.toml`.
3. Register the site in Cloudflare Web Analytics ("Add a site", with the
   exact hostname). Put the token into `site/config.json`.
4. Set the Worker secrets, once the Worker exists:
   `npx wrangler@4.165.0 secret put COUNTER_SALT --config site/wrangler.toml`
   (without it the counter stores unsalted hashes) and
   `npx wrangler@4.165.0 secret put STATS_KEY --config site/wrangler.toml`
   (the key that opens the private `/stats` page).
5. Set the repository variable `CF_DEPLOY` to `1` to arm the deploy.
6. Answer the open questions in section 10.

## 9. Verification

Local, before any deploy:

- `pdt export --out site/dist` and the checker.
- `npx wrangler dev --config site/wrangler.toml --port 8788` serves the dist
  the way Cloudflare will, including the Worker and a local D1. Check the
  index, one challenge home, one campaign page, one explorer, one history,
  the About page and `/stats` (start the dev Worker with
  `--var STATS_KEY:dev-local-key` and open `/stats?key=dev-local-key`).
  Port 8787 is the Hermes web UI.

The CI smoke check, after every deploy:

- `/` carries the brand "Protein design workbench" and the beacon snippet.
- `/ch/05-pmhc`, `/ch/05-pmhc/history`, `/lineage/05-pmhc/c1-main-funnel` and
  `/about` answer 200. The check follows redirects.
- `/engine/molstar-bundle.js` matches the built file byte for byte.
- `/stats.json` answers 404 without the key (the private counter gate).
- An unknown path answers the 404 page.
- The check sends a descriptive User-Agent, because workers.dev screens
  automated clients. It also retries, because a deploy takes time to reach
  every location.

## 10. The decisions

1. **Access.** The Worker is reachable by everyone with the URL. Options:
   - public: the protein-with-rust parity.
   - unlisted: no inbound links, plus `robots.txt` and a `noindex` header.
   - gated: Cloudflare Access can protect the workers.dev URL directly
     (documented). With Access, the counter still works, and the Access logs
     give per-user identity.
2. **The Worker name.** `protein-design-workbench` is the suggestion.
3. **Explorer loading.** Today an explorer starts loading when the reader
   scrolls it into view. A click-to-load variant (a button that names the
   size) cuts visitor transfer a lot and changes the reading flow. v1 keeps
   the current behavior.
4. **The stats page.** Unlisted by default. You can link it or keep the
   address private.

## 11. Phase 2 (not in this plan)

- Split the explorer data into per-design files, loaded on demand. This is
  the big remaining transfer item.
- Recompress the history figures (PNG to WebP) before embedding. Estimated
  saving: 3 to 5 MB of the histories.
- An R2 archive of every deploy (the protein-with-rust rollback pattern).
- The run pages, the media files and the video series.
- Preview builds for pull requests.
- Dedupe the engine inside the repository itself, not only at export.

## 12. Docs to update when the build lands

- `README.md`: a "Deploying" section.
- `AGENT.md`: a new rule. The app stays local. The public site is the static
  export, and only CI deploys it.
- `challenges/05-pmhc/notes/site-sync-playbook.md`: replace the "never deploy
  to a cloud" rule.
