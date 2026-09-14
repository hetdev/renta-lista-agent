const fs = require('fs');
const path = require('path');
const { chromium } = require('/Users/hetmini/.npm/_npx/e41f203b7505f1fb/node_modules/playwright');

const BASE = 'https://deuhmh4dvlr6i.cloudfront.net';
const DIR = __dirname;
const dur = JSON.parse(fs.readFileSync(path.join(DIR, 'durations.json'), 'utf8'));
const timeline = [];
let t0 = 0;
const now = () => (Date.now() - t0) / 1000;
const mark = (id) => timeline.push({ id, t: +now().toFixed(2) });
const hold = (id, extra = 700) => Math.round((dur[id] || 2) * 1000 + extra);
const log = (...a) => console.log(`[${now().toFixed(1)}s]`, ...a);

const OVERLAY = () => {
  if (document.getElementById('rl-cap')) return;
  const style = document.createElement('style');
  style.textContent = `
    #rl-cursor{position:fixed;left:0;top:0;width:24px;height:24px;pointer-events:none;z-index:2147483647;transform:translate(-2px,-2px)}
    #rl-cursor svg{display:block;filter:drop-shadow(0 1px 2px rgba(0,0,0,.55))}
    #rl-ripple{position:fixed;width:36px;height:36px;border-radius:50%;border:3px solid #2563eb;pointer-events:none;z-index:2147483646;opacity:0;transform:translate(-50%,-50%) scale(.4)}
    #rl-ripple.on{animation:rlr .5s ease-out}
    @keyframes rlr{0%{opacity:.95;transform:translate(-50%,-50%) scale(.4)}100%{opacity:0;transform:translate(-50%,-50%) scale(1.5)}}
    #rl-cap{pointer-events:none;position:fixed;left:50%;bottom:26px;transform:translateX(-50%);max-width:1120px;background:rgba(15,23,42,.93);color:#fff;font:600 23px/1.35 -apple-system,"Segoe UI",Helvetica,Arial,sans-serif;padding:12px 24px;border-radius:12px;z-index:2147483645;box-shadow:0 8px 30px rgba(0,0,0,.35);display:none;text-align:center}
    #rl-card{pointer-events:none;position:fixed;inset:0;background:rgba(15,23,42,.95);color:#fff;z-index:2147483644;display:none;flex-direction:column;justify-content:center;align-items:flex-start;padding:70px 120px;font-family:-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
    #rl-card h1{font-size:46px;margin:0 0 8px;font-weight:700}
    #rl-card h2{font-size:22px;margin:0 0 34px;font-weight:400;color:#bfdbfe}
    #rl-card p{font-size:24px;margin:0 0 16px;line-height:1.4;max-width:1040px}
    #rl-card p b{color:#93c5fd}
    #rl-card .small{font-size:18px;color:#cbd5e1;margin-top:26px}
  `;
  document.head.appendChild(style);
  const mk = (id, html) => { const d = document.createElement('div'); d.id = id; d.innerHTML = html || ''; document.body.appendChild(d); return d; };
  const cur = mk('rl-cursor', '<svg width="24" height="24" viewBox="0 0 24 24"><path d="M3 2l7.5 18 2.6-7.1L20 10.4z" fill="#fff" stroke="#111" stroke-width="1.6" stroke-linejoin="round"/></svg>');
  const rip = mk('rl-ripple');
  mk('rl-cap'); mk('rl-card');
  cur.style.left = (window.__rlx || 640) + 'px'; cur.style.top = (window.__rly || 360) + 'px';
  window.addEventListener('mousemove', e => { window.__rlx = e.clientX; window.__rly = e.clientY; cur.style.left = e.clientX + 'px'; cur.style.top = e.clientY + 'px'; }, true);
  window.addEventListener('mousedown', e => { rip.style.left = e.clientX + 'px'; rip.style.top = e.clientY + 'px'; rip.classList.remove('on'); void rip.offsetWidth; rip.classList.add('on'); }, true);
};

const PITCH = `
<h1>RentaLista</h1>
<h2>An evidence-first Colombian income tax agent · Form 210, tax year 2025</h2>
<p><b>Problem.</b> Reconciling Colombia's third-party tax report and assembling a Form 210 draft is slow and error-prone.</p>
<p><b>Who it's for.</b> A tax-resident person filing their own return, not an accounting firm.</p>
<p><b>Why it matters.</b> Missing certificates, silent zeros and unverified amounts create real filing risk. RentaLista keeps evidence and human control, and never files with DIAN.</p>
<p class="small">Public demo · synthetic data only · Draft for review only. Not filed with DIAN.</p>`;

const CLOSE = `
<h1>Try it</h1>
<h2>https://deuhmh4dvlr6i.cloudfront.net/en/</h2>
<p>Code (MIT): github.com/hetdev/renta-lista-agent</p>
<p><b>Evidence-first. Human-approved. Not filed with DIAN.</b></p>
<p class="small">Built with Strands Agents on Amazon Bedrock AgentCore · Agents for Humans hackathon</p>`;

async function overlay(page) { await page.evaluate(OVERLAY); }
async function caption(page, text, pos = 'bottom') {
  await page.evaluate(([t, p]) => { const c = document.getElementById('rl-cap'); if (!c) return; c.textContent = t; c.style.display = t ? 'block' : 'none'; if (p === 'top') { c.style.top = '26px'; c.style.bottom = 'auto'; } else { c.style.top = 'auto'; c.style.bottom = '26px'; } }, [text, pos]);
}
async function card(page, html) {
  await page.evaluate(h => { const c = document.getElementById('rl-card'); if (!c) return; c.innerHTML = h; c.style.display = h ? 'flex' : 'none'; }, html);
}
async function say(page, id, text, extra, pos = 'bottom') { await caption(page, text, pos); mark(id); log(id); await page.waitForTimeout(hold(id, extra)); }
async function moveClick(page, locator, settle = 700) {
  await locator.first().waitFor({ state: 'visible', timeout: 15000 });
  await locator.first().scrollIntoViewIfNeeded();
  await page.waitForTimeout(150);
  const box = await locator.first().boundingBox();
  if (!box) { await locator.first().click(); await page.waitForTimeout(settle); return; }
  const x = box.x + box.width / 2, y = box.y + box.height / 2;
  await page.mouse.move(x, y, { steps: 28 });
  await page.waitForTimeout(280);
  await page.mouse.down(); await page.waitForTimeout(90); await page.mouse.up();
  await page.waitForTimeout(settle);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1, locale: 'en-US',
    recordVideo: { dir: path.join(DIR, 'raw'), size: { width: 1280, height: 720 } },
  });
  const page = await context.newPage();
  t0 = Date.now();
  let videoPath = null;
  try {
    await page.goto(BASE + '/en/', { waitUntil: 'networkidle' });
    await overlay(page);
    await page.mouse.move(640, 380, { steps: 5 });
    // S0 pitch
    await page.mouse.move(1265, 705, { steps: 3 }); await caption(page, '');
    await card(page, PITCH); mark('pitch'); log('pitch'); await page.waitForTimeout(hold('pitch', 900));
    await card(page, '');
    await say(page, 'intro', 'Public demo · English and Spanish · synthetic data only');
    await page.mouse.wheel(0, 430); await page.waitForTimeout(400);
    await say(page, 'flow', 'Four steps: profile → documents → coverage → draft');
    await page.mouse.wheel(0, -430); await page.waitForTimeout(500);
    // S1 demo
    await caption(page, '');
    await moveClick(page, page.getByRole('link', { name: 'Try the demo' }));
    await page.waitForURL(/\/en\/demo\//, { timeout: 15000 }); await overlay(page);
    await say(page, 'create', 'Create a synthetic case: the API issues a case id and a token');
    await moveClick(page, page.getByRole('button', { name: 'Create demo case' }));
    await page.getByText('Case ready').first().waitFor({ timeout: 20000 });
    await say(page, 'created', 'Case created by the live API (badge: api)');
    // S2 profile
    await moveClick(page, page.getByRole('link', { name: 'Go to profile' }));
    await page.waitForURL(/case\/profile/, { timeout: 15000 }); await overlay(page);
    await say(page, 'profile', 'Ten admission questions, dependents and filing history');
    await moveClick(page, page.getByRole('button', { name: 'Save profile' }));
    await page.getByText('Profile admitted').first().waitFor({ timeout: 20000 });
    await say(page, 'saved', 'Saved through the API: profile admitted');
    await moveClick(page, page.getByRole('link', { name: 'Continue', exact: true }));
    await page.waitForURL(/case\/documents/, { timeout: 15000 }); await overlay(page);
    // S3 documents
    await say(page, 'docs', 'Certificate inventory: upload, or recover from the issuer portal');
    const upload = page.getByRole('button', { name: 'Mark as uploaded' });
    await moveClick(page, upload.nth(1)); await moveClick(page, upload.nth(2));
    await say(page, 'uploaded', 'Two certificates marked as uploaded');
    await moveClick(page, page.getByRole('button', { name: 'Recover in portal' }).nth(3));
    await say(page, 'recover', 'Portal recovery waits for human approval before any browsing · assisted handoff planned');
    await moveClick(page, page.getByRole('link', { name: 'Continue', exact: true }));
    await page.waitForURL(/case\/coverage/, { timeout: 15000 }); await overlay(page);
    // S4 coverage
    await say(page, 'coverage', 'Coverage: which income concepts are verified and which are missing');
    await moveClick(page, page.getByRole('link', { name: 'Continue to draft' }));
    await page.waitForURL(/case\/draft/, { timeout: 15000 }); await overlay(page);
    // S5 draft
    await say(page, 'draft', 'The Form 210 draft is computed by a deterministic engine, never by the LLM');
    await moveClick(page, page.getByRole('button', { name: 'Prepare draft' }));
    await page.getByText('Draft ready (demo)').first().waitFor({ timeout: 20000 });
    await say(page, 'ready', 'Income, taxable base, tax and settlement, straight from the engine');
    await moveClick(page, page.getByRole('button', { name: 'Taxable base' }));
    await say(page, 'explain', 'Each line explains its cell and formula');
    await moveClick(page, page.getByRole('button', { name: 'Income tax' }));
    await say(page, 'tax', 'Income tax: art. 241 progressive table · rule version ag2025');
    const ledger = page.getByText('Form 210 cell ledger').first();
    await ledger.scrollIntoViewIfNeeded(); await page.mouse.wheel(0, 260); await page.waitForTimeout(500);
    await page.mouse.move(1180, 300, { steps: 10 });
    await say(page, 'ledger', 'Cell ledger · credit balance 3,709,000 COP · rounded to thousands (art. 577)', 700, 'top');
    await page.mouse.wheel(0, -1400); await page.waitForTimeout(500);
    await say(page, 'disclaimer', 'Draft for review only. Not filed with DIAN.');
    // S6 Spanish
    const esUrl = page.url().replace('/en/', '/es/');
    await caption(page, '');
    await page.goto(esUrl, { waitUntil: 'networkidle' }); await overlay(page);
    await moveClick(page, page.getByRole('button', { name: 'Preparar borrador' }));
    await page.getByText('Borrador listo (demo)').first().waitFor({ timeout: 20000 });
    await say(page, 'spanish', 'Same engine, Spanish labels');
    // S7 architecture (local render of docs/architecture.md)
    await caption(page, '');
    await page.goto('file://' + path.join(DIR, 'arch.html'), { waitUntil: 'load' });
    try { await page.locator('svg').first().waitFor({ timeout: 20000 }); } catch (e) { log('mermaid svg not found:', e.message.split('\n')[0]); }
    await page.waitForTimeout(900);
    await overlay(page);
    await say(page, 'arch', 'Strands Agents + Amazon Bedrock orchestrate the engine tool · solid = implemented · dashed = planned');
    // S8 close
    await caption(page, ''); await page.mouse.move(1265, 705, { steps: 6 });
    await card(page, CLOSE); mark('close'); log('close'); await page.waitForTimeout(hold('close', 1800));
    mark('end');
  } catch (err) {
    log('ERROR', err.message);
    mark('error');
  } finally {
    const video = page.video();
    await context.close();
    videoPath = await video.path();
    await browser.close();
    fs.writeFileSync(path.join(DIR, 'timeline.json'), JSON.stringify({ video: videoPath, marks: timeline }, null, 2));
    log('video', videoPath);
  }
})();
