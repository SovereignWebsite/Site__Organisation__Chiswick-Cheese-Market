// Make the "Choose a design" thumbnails: a screenshot of each design's home page (1280 x 800, light),
// saved as site/assets/designs/<n>.png, then shrunk to 640 x 400 WebP by tools/thumbs.py.
// Usage (from the repository root, after python3 tools/build.py):  node tools/thumbs.js && python3 tools/thumbs.py
// The pages load their pictures from chiswickcheesemarket.uk, so this needs the network.
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const SITE = path.resolve(__dirname, '..', 'site');
const OUT = path.join(SITE, 'assets', 'designs');

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  for (const n of ['1', '2', '3', '4', '5', '6']) {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 }, colorScheme: 'light', deviceScaleFactor: 1, reducedMotion: 'reduce' });
    const page = await ctx.newPage();
    await page.goto('file://' + path.join(SITE, 'designs', n, 'index.html'), { waitUntil: 'load' });
    await page.addStyleTag({ content: '.demo-strip{display:none!important}' }); // the thumbnail shows the design, not the strip
    await page.waitForTimeout(2500);
    await page.screenshot({ path: path.join(OUT, `${n}.png`) });
    await ctx.close();
    console.log('thumbnail', n);
  }
  await browser.close();
})();
