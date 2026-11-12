// Driver for the fake Quest (tools/xr_fake_quest.js): serves the repo, opens a built page in headless Chrome, enters VR, moves the head and hands, presses buttons. Needs puppeteer-core (NODE_PATH) and Chrome.
const puppeteer = require('puppeteer-core'), fs = require('fs'), path = require('path'), http = require('http');
const FAKE = fs.readFileSync(path.join(__dirname, 'xr_fake_quest.js'), 'utf8');
const THREE_LOCAL = fs.existsSync('/workspace/three128.min.js') ? fs.readFileSync('/workspace/three128.min.js') : null;
function serve(root, port) {
  return new Promise((res) => {
    const srv = http.createServer((q, r) => { let p = decodeURIComponent(q.url.split('?')[0]); if (p.endsWith('/')) p += 'index.html'; const f = path.join(root, p); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'content-type': f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'text/javascript' : 'application/octet-stream' }); r.end(d); }); });
    srv.listen(0, () => res(srv));
  });
}
const BTN = { trigger: 0, grip: 1, stick: 3, a: 4, x: 4, b: 5, y: 5 };
async function launch(o) {
  o = o || {};
  const srv = await serve(o.root); const port = srv.address().port;
  const browser = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new', args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--autoplay-policy=no-user-gesture-required', '--window-size=1600,800'] });
  const page = await browser.newPage();
  await page.setViewport({ width: o.w || 1400, height: o.h || 700 });
  const logs = [];
  page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') logs.push(m.type() + ': ' + m.text()); });
  page.on('pageerror', (e) => logs.push('pageerror: ' + e.message));
  await page.setRequestInterception(true);
  page.on('request', (r) => { const u = r.url(); if (/three\.min\.js/.test(u) && THREE_LOCAL) return r.respond({ status: 200, contentType: 'text/javascript', body: THREE_LOCAL }); if (/peerjs/.test(u)) return r.respond({ status: 200, contentType: 'text/javascript', body: 'window.__peerFailed=true' }); r.continue(); });
  await page.evaluateOnNewDocument(FAKE);
  await page.goto('http://localhost:' + port + '/' + (o.page || 'site/index.html') + (o.query !== undefined ? o.query : '?sandbox'), { waitUntil: 'load', timeout: 120000 });
  await page.waitForFunction(() => window.__game && document.getElementById('vrBtn') && !document.getElementById('vrBtn').hidden, { timeout: 120000 });
  const S = {
    page, browser, logs,
    async close() { await browser.close(); srv.close(); },
    ev: (fn, ...a) => page.evaluate(fn, ...a),
    async frames(n) { const f0 = await page.evaluate(() => window.__fx.frames); await page.waitForFunction((t) => window.__fx.frames >= t, { timeout: 120000, polling: 20 }, f0 + n); },
    async enterVR() { await page.click('#vrBtn'); await page.waitForFunction(() => window.__game.xr.presenting(), { timeout: 30000 }); await S.frames(20); },
    hand: (h, o) => page.evaluate((h, o) => { const d = window.__fx.hands[h]; if (o.p) d.p = o.p; if (o.q) d.q = o.q; if (o.ax) d.ax = o.ax; if (o.v) for (const k in o.v) d.v[k] = o.v[k]; }, h, o),
    head: (o) => page.evaluate((o) => { const d = window.__fx.head; if (o.p) d.p = o.p; if (o.q) d.q = o.q; }, o),
    async hold(h, b, on) { await S.hand(h, { v: { [BTN[b]]: on ? 1 : 0 } }); },
    async press(h, b, n) { await S.hold(h, b, true); await S.frames(n || 4); await S.hold(h, b, false); await S.frames(3); },
    async stick(h, x, y, n) { await S.hand(h, { ax: [0, 0, x, y] }); await S.frames(n || 10); await S.hand(h, { ax: [0, 0, 0, 0] }); await S.frames(2); },
    state: () => page.evaluate(() => { const s = window.__game.ref.snapshot(); return s; }),
    pulses: () => page.evaluate(() => { const p = window.__fx.pulses.slice(); window.__fx.pulses.length = 0; return p; }),
    // a button pattern played inside the page, frame by frame (exact timing, e.g. a double tap): pattern = [[on, frames], ...]
    seq: (h, b, pattern) => page.evaluate((h, i, pat) => new Promise((res) => { const d = window.__fx.hands[h]; let k = 0, until = window.__fx.frames; const tick = () => { if (window.__fx.frames >= until) { if (k >= pat.length) return res(); d.v[i] = pat[k][0] ? 1 : 0; until = window.__fx.frames + pat[k][1]; k++; } requestAnimationFrame(tick); }; tick(); }), h, BTN[b], pattern),
    async shot(file) { await page.screenshot({ path: file }); }
  };
  return S;
}
// a quaternion turning -z (forward) toward a direction (yaw about +y, then pitch about +x), as the XR runtime would report it
function quatYawPitch(yaw, pitch) {
  const cy = Math.cos(yaw / 2), sy = Math.sin(yaw / 2), cp = Math.cos(pitch / 2), sp = Math.sin(pitch / 2);
  return [cy * sp, sy * cp, -sy * sp, cy * cp];
}
module.exports = { launch, quatYawPitch, BTN };
