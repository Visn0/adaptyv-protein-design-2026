/**
 * Record a short walkthrough of the workbench for the READMEs.
 *
 * One take per route: the site index, or one challenge's page. Each take clicks and scrolls
 * the real page at a viewer's pace and captures the page itself with Playwright's own
 * recorder, so the result is the same on a headless box as on a laptop and has no window
 * chrome in it. The README's moving picture is a GIF, because GitHub will not play an MP4
 * that lives in the repository; the MP4 beside it is the same take at full size.
 *
 * Usage (the app must be serving already):
 *   .venv/bin/python -m tools.cli serve --port 8737 &
 *   npm --prefix site/scripts install
 *   node site/scripts/record-demo.mjs --route home
 *   node site/scripts/record-demo.mjs --route tour
 *   node site/scripts/record-demo.mjs --route 02-tnfa
 *
 * Options:
 *   --base <url>    the running app        (default http://127.0.0.1:8737/)
 *   --route <name>  home | tour | 01-egfr | 02-tnfa | 03-glp1r | 04-tfr1 | 05-pmhc
 *   --out <path>    where the take lands   (default site/demo/<route>.<ext>)
 *   --head          show the browser window
 *   --no-gif        skip the GIF encode (the MP4 alone is enough for a look)
 */
import { mkdir, readdir, rename, rm } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { chromium } from 'playwright-core';

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.join(here, '..', '..');

// ------------------------------------------------------------------- options
const argv = process.argv.slice(2);
const option = (name, fallback) => {
  const index = argv.indexOf(`--${name}`);
  return index === -1 ? fallback : argv[index + 1];
};

const BASE = option('base', 'http://127.0.0.1:8737/');
const ROUTE = option('route', 'home');
const HEADLESS = !argv.includes('--head');
const WITH_GIF = !argv.includes('--no-gif');

// 1280x800, 1x: the screencast is captured per CSS pixel, so a higher ratio only inflates the
// encode. `size` must be given explicitly — it defaults to the viewport scaled to fit 800x800.
const VIEWPORT = { width: 1280, height: 800 };

// The GIF is the README's moving picture. The numbers are measured, not chosen: the README
// renders the file at its own width, so a wider encode is a bigger picture on the page. The
// tour take (38 s) at 800px/6fps/40 colours is 8.8 MB, which is too heavy to open; the same
// take at 1.2x and 5fps is 6.7 MB, and 5 fps of a 1.2x timeline is 6 frames per content second,
// so the motion is as smooth as a straight 6 fps. The window is computed per take: a tour
// starts just before its first click, a single page just after it has painted.
const GIF_FPS = 5;
const GIF_WIDTH = 800;
const GIF_COLORS = 40;
const GIF_SECONDS = 10;
const GIF_SPEED = 1.2; // playback speed: shortens the file and sharpens the pacing
const GIF_LEAD = 3.0; // how long before the click the GIF starts: the recorder's clock runs ahead
// of the video file (the browser starts capturing after the page is created, and the click
// takes time to dispatch), so the window is generous and always opens on the index.

// The tour's stops, in order. One stop: the KRAS G12D pMHC challenge, whose page ends on the
// submitted designs. All three stops with that scroll made the GIF 12 MB, which is too heavy
// for a README, so the take tells one challenge's story in full instead.
const TOUR_STOPS = ['05-pmhc'];

// --------------------------------------------------------------------- pacing
// Every pause in one place, in milliseconds. Re-timing a take must never mean touching the
// flow below. Sum plus the page's own load time is the video's length.
const PACE = {
  settle: 700, // after the page has loaded and the fonts have landed
  hero: 1400, // the first screen of a challenge page, before the scroll starts
  toCard: 900, // the short glide that brings the challenge card into the viewport
  toViewer: 3600, // the glide from the hero down to the structure explorer
  viewer: 2800, // the explorer turning, with nothing moving it
  toDesigns: 4200, // the glide on down to the final-submission table
  designs: 1500, // the hold on the designs themselves
  end: 1900, // the final hold
  homeHero: 1500, // the index hero, before the scroll starts
  homeScroll: 7500, // the one continuous glide down the index
  homeEnd: 2000, // the final hold on the tools table
  // The tour runs the same story three times, so each stop is tighter than a solo take.
  tour: { settle: 400, hero: 0, toViewer: 1700, viewer: 800, toDesigns: 3600, designs: 1400 },
};

const beat = (page, ms) => page.waitForTimeout(ms);

// -------------------------------------------------------------------- cursor
/*
 * The recorder draws no pointer, so a click in the video looks like the page acting on its
 * own. This is a plain DOM element in the page that tracks the real mouse: injected at
 * document start, outside the app's own code, and it cannot change what the app does.
 * `translate` (not `transform`) carries the position, so the press animation scales the dot
 * around its own centre instead of flinging it towards the top-left corner.
 */
const CURSOR_SIZE = 26;
const CURSOR_CSS = `
.__demo-cursor {
  position: fixed;
  left: 0;
  top: 0;
  width: ${CURSOR_SIZE}px;
  height: ${CURSOR_SIZE}px;
  margin: ${-CURSOR_SIZE / 2}px 0 0 ${-CURSOR_SIZE / 2}px;
  border-radius: 50%;
  background: rgba(13, 162, 231, 0.35);
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.9), 0 3px 10px rgba(0, 0, 0, 0.4);
  pointer-events: none;
  z-index: 2147483647;
  translate: -60px -60px;
  transition: translate 70ms linear, scale 110ms ease, opacity 400ms ease;
}
.__demo-cursor[data-press] { scale: 0.65; }
.__demo-cursor[data-idle] { opacity: 0.25; }
`;

async function injectCursor(context) {
  await context.addInitScript((css) => {
    const style = document.createElement('style');
    style.textContent = css;
    const dot = document.createElement('div');
    dot.className = '__demo-cursor';
    document.addEventListener('DOMContentLoaded', () => {
      document.head.append(style);
      document.documentElement.append(dot);
    });
    // Capture phase: the app's own listeners must not be able to stop these.
    let idle = null;
    window.addEventListener(
      'mousemove',
      (event) => {
        dot.style.translate = `${event.clientX}px ${event.clientY}px`;
        dot.removeAttribute('data-idle');
        clearTimeout(idle);
        // A pointer that rests where it last clicked would sit over whatever the page scrolled
        // to behind it, which reads as a stray dot on the molecule.
        idle = setTimeout(() => dot.setAttribute('data-idle', ''), 2000);
      },
      true,
    );
    window.addEventListener('mousedown', () => dot.setAttribute('data-press', ''), true);
    window.addEventListener('mouseup', () => dot.removeAttribute('data-press'), true);
  }, CURSOR_CSS);
}

// -------------------------------------------------------------------- driving
/** Move the pointer to an element's centre over several steps, so the dot glides there. */
async function moveTo(page, selector) {
  const box = await page.locator(selector).first().boundingBox();
  if (!box) {
    return null;
  }
  const x = box.x + box.width / 2;
  const y = box.y + box.height / 2;
  // Fewer steps than it looks like it needs: every step repaints the page, and under software
  // rendering twenty of them cost seconds of the take.
  await page.mouse.move(x, y, { steps: 12 });
  return { x, y };
}

/** Document coordinate of the top edge of the element, measured against the live page. */
const topOf = (page, selector) =>
  page.evaluate((selector) => {
    const element = document.querySelector(selector);
    return element ? Math.round(element.getBoundingClientRect().top + window.scrollY) : null;
  }, selector);

/** Document coordinate of the heading whose text starts with `text` (h2 or h3), or null. */
const headingTop = (page, text) =>
  page.evaluate((text) => {
    const heading = [...document.querySelectorAll('main h2, main h3')].find((element) =>
      element.textContent.trim().startsWith(text),
    );
    return heading ? Math.round(heading.getBoundingClientRect().top + window.scrollY) : null;
  }, text);

/** The viewport's height in CSS pixels. */
const viewportHeight = (page) => page.evaluate(() => window.innerHeight);

/** Document coordinate of the bottom of everything on the page. */
const pageBottom = (page) =>
  page.evaluate(() =>
    Math.round(Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)),
  );

/**
 * Scroll like a person: eased, over `ms`, on the animation frames the page already runs. A
 * `window.scrollTo` jump reads as a cut. `behavior: 'instant'` is not decoration — with
 * `scroll-behavior: smooth` a bare scrollTo asks the browser to animate, the document lags the
 * target, and the next frame can land behind it and travel backwards.
 *
 * The sticky header's height is measured per take: scrolling to a section's top would hide it
 * underneath the header otherwise.
 */
async function glide(page, toY, ms, headerHeight) {
  if (toY === null) {
    return;
  }
  const target = Math.max(0, Math.round(toY) - headerHeight - 8);
  await page.evaluate(
    ([target, ms]) =>
      new Promise((resolve) => {
        const from = window.scrollY;
        const delta = target - from;
        if (Math.abs(delta) < 2) {
          resolve();
          return;
        }
        const started = performance.now();
        const ease = (t) => (t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2);
        const step = () => {
          const progress = Math.min(1, (performance.now() - started) / ms);
          window.scrollTo({ top: from + delta * ease(progress), behavior: 'instant' });
          if (progress < 1) {
            requestAnimationFrame(step);
          } else {
            resolve();
          }
        };
        requestAnimationFrame(step);
      }),
    [target, ms],
  );
}

const headerHeight = (page) =>
  page.evaluate(() => {
    const header = document.querySelector('.topnav');
    return header ? Math.round(header.getBoundingClientRect().height) : 0;
  });

// ------------------------------------------------------------------------ run
const names = {
  home: 'workbench-home',
  tour: 'workbench-tour',
  '01-egfr': 'challenge-01-egfr',
  '02-tnfa': 'challenge-02-tnfa',
  '03-glp1r': 'challenge-03-glp1r',
  '04-tfr1': 'challenge-04-tfr1',
  '05-pmhc': 'challenge-05-pmhc',
};
const name = names[ROUTE];
if (!name) {
  console.error(`unknown route: ${ROUTE} (known: ${Object.keys(names).join(', ')})`);
  process.exit(2);
}

const videoDir = path.join(repoRoot, 'site', 'demo', '.recordings');
await rm(videoDir, { recursive: true, force: true });
await mkdir(videoDir, { recursive: true });

const started = Date.now();
const browser = await chromium.launch({
  headless: HEADLESS,
  // Headless containers cannot use the browser's own sandbox.
  args: ['--no-sandbox', `--window-size=${VIEWPORT.width},${VIEWPORT.height}`],
});
const context = await browser.newContext({
  viewport: VIEWPORT,
  deviceScaleFactor: 1,
  recordVideo: { dir: videoDir, size: VIEWPORT },
});
await injectCursor(context);

const page = await context.newPage();
// The recorder starts writing when the page is created, so this is the video's zero.
const videoStart = Date.now();
const marks = {};
const stamp = (key) => {
  // The first value wins: a tour stamps the same key on every stop, and the GIF window must
  // open on the first click, not the last one.
  if (marks[key] === undefined) {
    marks[key] = (Date.now() - videoStart) / 1000;
  }
};
const problems = [];
page.on('console', (message) => {
  if (message.type() === 'error') {
    problems.push(`console: ${message.text()}`);
  }
});
page.on('pageerror', (error) => problems.push(`pageerror: ${error}`));
page.on('requestfailed', (request) =>
  problems.push(`requestfailed: ${request.url()} ${request.failure()?.errorText ?? ''}`),
);

const notes = [];

/** One stop of a take: click a challenge card on the index, wait for its page, let it answer. */
async function visitChallenge(page, route, pace, notes) {
  const card = `a.card[href='/ch/${route}']`;
  // The card can sit below the fold on the index. Bring it into the middle of the viewport
  // with a short glide first, exactly as a reader would, then click it where it now is.
  const cardTop = await topOf(page, card);
  if (cardTop !== null) {
    const target = Math.max(0, cardTop - (await viewportHeight(page)) * 0.42);
    await glide(page, target, PACE.toCard, await headerHeight(page));
  }
  const at = await moveTo(page, card);
  if (!at) {
    throw new Error(`challenge card not found: ${card}`);
  }
  await beat(page, 400);
  stamp('click');
  await Promise.all([
    page.waitForURL(`**/ch/${route}`, { timeout: 20_000 }),
    page.mouse.click(at.x, at.y),
  ]);
  await page.waitForLoadState('load');
  await page.evaluate(() => document.fonts.ready);
  await page.waitForSelector('main h1', { timeout: 15_000 });
  // The explorer fills in after its structure payload arrives; wait for it, but do not fail
  // the take if this challenge has none.
  try {
    await page.waitForSelector('.tgt3d:not(.viewer-loading)', { timeout: 25_000 });
  } catch {
    notes.push(`no structure explorer became ready on ${route}`);
  }
  // Put the pointer on the new page too, to the right of the text, so the cursor is present
  // while the page is read and then dims like a real pointer that is not moving.
  await page.mouse.move(1080, 330, { steps: 14 });
  await beat(page, pace.settle);
  await beat(page, pace.hero);
  const header = await headerHeight(page);
  // Aim at the structure explorer itself, so the stop ends with the 3D view in frame.
  const aim = async () => (await topOf(page, '.tgt3d')) ?? (await pageBottom(page));
  const first = await aim();
  await glide(page, first, pace.toViewer, header);
  // The page grows while it loads — the explorer's payload and the sequence block arrive late —
  // so the first glide lands past the target. Re-measure once and correct.
  await beat(page, 250);
  const settled = await aim();
  if (Math.abs(settled - first) > 30) {
    await glide(page, settled, 400, header);
  }
  await beat(page, pace.viewer);
  // The designs themselves are further down: the final-submission table.
  const designsTop = await headingTop(page, 'Final submission');
  if (designsTop !== null) {
    await glide(page, designsTop, pace.toDesigns, header);
    await beat(page, pace.designs);
  }
}

/** Back to the index through the sticky nav's Home button, wherever the page is scrolled. */
async function goHome(page) {
  const at = await moveTo(page, "a.navbtn[href='/']");
  if (!at) {
    throw new Error('home button not found');
  }
  await beat(page, 400);
  await Promise.all([
    page.waitForURL(BASE, { timeout: 20_000 }),
    page.mouse.click(at.x, at.y),
  ]);
  await page.waitForLoadState('load');
  await page.evaluate(() => document.fonts.ready);
  await page.waitForSelector('a.card', { timeout: 15_000 });
  await beat(page, 450);
}

try {
  // ------------------------------------------------------------- the flow
  await page.goto(BASE, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  await beat(page, PACE.settle);
  // The video opens on the browser's white before the app paints. The home GIF starts here
  // instead, so the first GIF frame is the page and not a flash of nothing.
  stamp('ready');

  if (ROUTE === 'home') {
    // The index: hold on the hero, then one glide through the challenge cards and the tools
    // table to the bottom of the page, and hold there.
    await beat(page, PACE.homeHero);
    await glide(page, await pageBottom(page), PACE.homeScroll, await headerHeight(page));
    await beat(page, PACE.homeEnd);
  } else if (ROUTE === 'tour') {
    // The tour: the index, then every stop in order — click the card, let the page and its
    // structure explorer answer, then go back to the index and repeat. The last stop ends on
    // its 3D view, which is the take's final shot.
    await beat(page, PACE.homeHero);
    for (const stop of TOUR_STOPS) {
      await visitChallenge(page, stop, PACE.tour, notes);
      if (stop !== TOUR_STOPS[TOUR_STOPS.length - 1]) {
        await goHome(page);
      }
    }
    await beat(page, PACE.end);
    stamp('end');
  } else {
    // One challenge: click its card, hold on the hero, glide to the structure explorer and let
    // it turn, then on down to the designs.
    await visitChallenge(page, ROUTE, PACE, notes);
    await beat(page, PACE.end);
  }
} finally {
  // Closing the context is what writes the video: the file only exists once the page is gone.
  await context.close();
  await browser.close();
}

const [recording] = (await readdir(videoDir)).filter((entry) => entry.endsWith('.webm'));
if (!recording) {
  console.error('The recorder produced no video.');
  process.exit(1);
}
const webm = path.join(videoDir, recording);
const mp4 = path.join(repoRoot, 'site', 'demo', `${name}.mp4`);
await mkdir(path.dirname(mp4), { recursive: true });
await rename(webm, mp4.replace(/\.mp4$/, '.webm'));
const source = mp4.replace(/\.mp4$/, '.webm');
console.log(`recorded ${((Date.now() - started) / 1000).toFixed(1)}s of ${BASE}${ROUTE} -> ${source}`);

// The webm is VP8 in a container plenty of tools will not open; ask ffmpeg for H.264 with the
// fast-start flag a browser needs to play it without downloading the whole file first.
const converted = spawnSync(
  'ffmpeg',
  ['-y', '-loglevel', 'error', '-i', source, '-c:v', 'libx264', '-crf', '22', '-pix_fmt',
   'yuv420p', '-movflags', '+faststart', '-an', mp4],
  { stdio: 'inherit' },
);
if (converted.status === 0) {
  await rm(source, { force: true });
  console.log(`converted -> ${mp4}`);
} else {
  console.warn('ffmpeg is not available; the .webm above plays in a browser as it is');
}

if (WITH_GIF) {
  // Two passes, because ffmpeg's single-pass GIF encoder builds a global palette from a handful
  // of frames and the result smears the dark UI. The window opens just before the click, which
  // the take measured, so the GIF is the story's best stretch and not the page's load time.
  const gif = path.join(repoRoot, 'site', 'demo', `${name}.gif`);
  const palette = path.join(videoDir, '.gif-palette.png');
  const gifStart = marks.click !== undefined
    ? Math.max(0, marks.click - GIF_LEAD)
    : (marks.ready ?? 0.9);
  // A tour is one long take: the window is the tour itself, from the first click to the end.
  const gifSeconds = ROUTE === 'tour' && marks.end !== undefined
    ? Math.max(4, Math.min(marks.end - gifStart, 55))
    : GIF_SECONDS;
  // `-t` before the input it belongs to: between the two `-i`s it would limit the palette
  // image instead of the video, and every GIF would run to the end of the take.
  const trim = ['-ss', gifStart.toFixed(2), '-t', String(gifSeconds), '-i', mp4];
  // `setpts` first: the playback speed is a timeline change, and fps resamples the new one.
  const speed = `setpts=${(1 / GIF_SPEED).toFixed(4)}*PTS,`;
  const scale = `${speed}fps=${GIF_FPS},scale=${GIF_WIDTH}:-1:flags=lanczos`;
  const first = spawnSync('ffmpeg',
    ['-y', '-loglevel', 'error', ...trim, '-vf',
     `${scale},palettegen=max_colors=${GIF_COLORS}:stats_mode=diff`, palette]);
  const second = spawnSync('ffmpeg',
    ['-y', '-loglevel', 'error', ...trim, '-i', palette, '-lavfi',
     `${scale}[x];[x][1:v]paletteuse=dither=none`, '-loop', '0', gif]);
  if (first.status === 0 && second.status === 0) {
    console.log(`gif       -> ${gif} (from ${gifStart.toFixed(1)}s, ${gifSeconds.toFixed(1)}s)`);
  } else {
    console.warn('the GIF was not written');
  }
  await rm(palette, { force: true });
}
await rm(videoDir, { recursive: true, force: true });

for (const note of notes) {
  console.warn(`note: ${note}`);
}
for (const problem of problems) {
  console.warn(`problem: ${problem}`);
}
