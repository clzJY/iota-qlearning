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
    results.push({ width, actual_inner_width: dimensions.inner, horizontal_overflow: false });
    if (width === 390) {
      let screenshot = await command('GET', '/screenshot');
      fs.writeFileSync(path.join(options.previewDirectory, 'mobile.png'), Buffer.from(screenshot, 'base64'));
      await script("document.getElementById('case-original').scrollIntoView({behavior:'instant'})");
      await frame();
      screenshot = await command('GET', '/screenshot');
      fs.writeFileSync(path.join(options.previewDirectory, 'results-mobile.png'), Buffer.from(screenshot, 'base64'));
    }
  }
  await bidi('browsingContext.setViewport', { context, viewport: null });
  ws.close();
  clearTimeout(timeout);
  console.log(JSON.stringify(results));
}
main().catch(error => { console.error(error); process.exit(1); });
