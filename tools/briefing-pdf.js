// Make site/briefing/chiswick-cheese-market-briefing.pdf from site/briefing/index.html (one 1280 x 720 page per slide).
//   node tools/briefing-pdf.js
// Serves site/ on a local port, prints the page with Chromium (Playwright), and writes the PDF beside it.
const { chromium } = require('playwright')
const http = require('http'), fs = require('fs'), path = require('path')
const ROOT = path.join(__dirname, '..', 'site')
const TYPES = { '.html': 'text/html', '.css': 'text/css', '.webp': 'image/webp', '.woff2': 'font/woff2', '.jpg': 'image/jpeg', '.png': 'image/png', '.svg': 'image/svg+xml' }
const server = http.createServer((q, r) => {
  let f = path.join(ROOT, decodeURI(q.url.split('?')[0]))
  if (fs.existsSync(f) && fs.statSync(f).isDirectory()) f = path.join(f, 'index.html')
  if (!f.startsWith(ROOT) || !fs.existsSync(f)) { r.writeHead(404); return r.end() }
  r.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' }); r.end(fs.readFileSync(f))
})
;(async () => {
  await new Promise(ok => server.listen(0, ok))
  const b = await chromium.launch(), p = await b.newPage()
  await p.goto(`http://127.0.0.1:${server.address().port}/briefing/`, { waitUntil: 'networkidle' })
  await p.evaluate(() => document.fonts.ready)
  const out = path.join(ROOT, 'briefing', 'chiswick-cheese-market-briefing.pdf')
  await p.pdf({ path: out, width: '1280px', height: '720px', printBackground: true, preferCSSPageSize: true })
  await b.close(); server.close()
  console.log('wrote', path.relative(process.cwd(), out), fs.statSync(out).size, 'bytes')
})()
