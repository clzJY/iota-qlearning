// Optional WebDriver BiDi helper. Node 22+ has WebSocket natively; this host's
// Node 18 provides it through its installed undici package. No browser download.
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { WebSocket } = globalThis.WebSocket ? globalThis : require('undici');

async function main() {
  let input = '';
  for await (const chunk of process.stdin) input += chunk;
  const options = JSON.parse(input);
  const ws = new WebSocket(options.webSocketUrl);
  const pending = new Map();
  let counter = 0;
  const timeout = setTimeout(() => { console.error('Viewport check timed out'); process.exit(1); }, 30000);
  ws.addEventListener('message', event => {
    const message = JSON.parse(event.data);
    if (!pending.has(message.id)) return;
    const { resolve, reject } = pending.get(message.id);
    pending.delete(message.id);
    message.type === 'error' ? reject(new Error(JSON.stringify(message))) : resolve(message.result);
  });
  await new Promise((resolve, reject) => { ws.addEventListener('open', resolve, { once: true }); ws.addEventListener('error', reject, { once: true }); });
  const bidi = (method, params) => new Promise((resolve, reject) => {
    const id = ++counter;
    pending.set(id, { resolve, reject });
    ws.send(JSON.stringify({ id, method, params }));
  });
  const command = async (method, route, payload) => {
    const response = await fetch(`${options.webdriverBase}/session/${options.sessionId}${route}`, {
      method, headers: { 'Content-Type': 'application/json' }, body: payload ? JSON.stringify(payload) : undefined
    });
    const result = await response.json();
    if (!response.ok) throw new Error(JSON.stringify(result));
    return result.value;
  };
  const script = source => command('POST', '/execute/sync', { script: source, args: [] });
  const frame = () => command('POST', '/execute/async', { script: 'const done=arguments[arguments.length-1];requestAnimationFrame(()=>requestAnimationFrame(()=>done(true)))', args: [] });
  const tree = await bidi('browsingContext.getTree', {});
  const context = tree.contexts[0].context;
  const results = [];
  for (const width of [390, 768, 1440]) {
    await bidi('browsingContext.setViewport', { context, viewport: { width, height: 1000 } });
    await script("window.scrollTo({top:0,behavior:'instant'})");
    await frame();
    const dimensions = await script('return {inner:window.innerWidth,viewport:document.documentElement.clientWidth,content:document.documentElement.scrollWidth}');
    if (dimensions.inner !== width || dimensions.content > dimensions.viewport + 1) throw new Error(JSON.stringify(dimensions));
    await script("document.getElementById('report-guide').scrollIntoView({behavior:'instant'})");
    await frame();
    const quickLinks = await script("const row=document.querySelector('.report-quick-links');const links=[...row.querySelectorAll('a')];return {tops:links.map(a=>a.getBoundingClientRect().top),scrollable:row.scrollWidth>row.clientWidth+1}");
    if (Math.max(...quickLinks.tops)-Math.min(...quickLinks.tops)>1) throw new Error('Quick links must stay in one row');
    if (width===390 && !quickLinks.scrollable) throw new Error('Mobile quick-link row must scroll');
    for (const [target, part] of [['method','1'],['setup','2'],['results','3'],['required-comparison','4'],['takeaways','5']]) {
      await script(`document.getElementById(${JSON.stringify(target)}).scrollIntoView({behavior:'instant'})`);
      await frame();
      const active = await script("return [...document.querySelectorAll('.reading-steps a[aria-current]')].map(a=>a.textContent).join('')");
      if (active!==part) throw new Error(`Reading indicator at ${width}px: ${target} expected ${part}, got ${active}`);
    }
    await script("document.getElementById('modified-convergence').scrollIntoView({behavior:'instant'})");
    await frame();
    const phaseLayout = await script("const sub=document.getElementById('reading-subphase');const main=document.getElementById('reading-current');const a=sub.getBoundingClientRect();const b=main.getBoundingClientRect();const summaries=[...document.querySelectorAll('#comparison>details>summary')];return {subphase:sub.textContent,mainphase:main.textContent,left:a.x,right:b.x,sameTitles:new Set(summaries.map(element=>getComputedStyle(element).fontSize)).size===1}");
    if (!phaseLayout.subphase.includes('Experiment 2') || phaseLayout.left>=phaseLayout.right || !phaseLayout.sameTitles) throw new Error(JSON.stringify(phaseLayout));
    if (width===390) {
      const shot = await command('GET', '/screenshot');
      fs.writeFileSync(path.join(options.previewDirectory, 'subsection-mobile.png'), Buffer.from(shot, 'base64'));
    }
    await script("document.getElementById('report-guide').scrollIntoView({behavior:'instant'})");
    await frame();
    results.push({ width, actual_inner_width: dimensions.inner, horizontal_overflow: false, quick_links_one_row: true, quick_links_scrollable: quickLinks.scrollable, five_reading_positions_checked: true, subsection_middle_main_part_right: true, part4_title_sizes_match: true });
    if (width === 390) {
      const shot = await command('GET', '/screenshot');
      fs.writeFileSync(path.join(options.previewDirectory, 'report-guide-mobile.png'), Buffer.from(shot, 'base64'));
    }
    await script("window.scrollTo({top:0,behavior:'instant'})");
    await frame();
    if (width === 390) {
      let screenshot = await command('GET', '/screenshot');
      fs.writeFileSync(path.join(options.previewDirectory, 'mobile.png'), Buffer.from(screenshot, 'base64'));
      await script("document.getElementById('case-original').scrollIntoView({behavior:'instant'})");
      await frame();
      screenshot = await command('GET', '/screenshot');
      fs.writeFileSync(path.join(options.previewDirectory, 'results-mobile.png'), Buffer.from(screenshot, 'base64'));
      await script("document.getElementById('case-modified').scrollIntoView({behavior:'instant'})");
      await frame();
      screenshot = await command('GET', '/screenshot');
      fs.writeFileSync(path.join(options.previewDirectory, 'experiment2-mobile.png'), Buffer.from(screenshot, 'base64'));
    }
  }
  await bidi('browsingContext.setViewport', { context, viewport: null });
  ws.close();
  clearTimeout(timeout);
  console.log(JSON.stringify(results));
}
main().catch(error => { console.error(error); process.exit(1); });
