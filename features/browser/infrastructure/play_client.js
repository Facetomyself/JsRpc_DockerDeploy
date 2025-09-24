// Minimal Playwright-powered browser adapter for JsRpc
// Responsibility: launch a headless browser, open a page, inject JsRpc client, and
// connect back to the server via WebSocket so RPC becomes available without a manual browser.

/*
Environment variables:
  BROWSER        chromium|firefox|webkit (default: chromium)
  HEADLESS       true|false (default: true)
  TARGET_URL     URL to open (default: about:blank)
  JRPC_WS_URL    Full ws/wss URL. If empty, constructed from HOST/PORT/GROUP
  HOST           Host for ws URL when constructing (default: 127.0.0.1)
  PORT           Port for ws URL when constructing (default: 12080)
  JRPC_GROUP     Group name for ws URL (default: default)
  CLIENT_ID      Optional fixed clientId; if empty a random one is used
*/

/* eslint-disable no-console */
const fs = require('fs');
const path = require('path');

function getEnv(name, def) {
  const v = process.env[name];
  return (v === undefined || v === '') ? def : v;
}

async function run() {
  const browserName = getEnv('BROWSER', 'chromium');
  const headless = getEnv('HEADLESS', 'true') === 'true';
  const targetUrl = getEnv('TARGET_URL', 'about:blank');

  const host = getEnv('HOST', '127.0.0.1');
  const port = getEnv('PORT', '12080');
  const group = getEnv('JRPC_GROUP', 'default');
  const clientId = getEnv('CLIENT_ID', `hlc-${Date.now()}`);
  const explicitWs = getEnv('JRPC_WS_URL', '');
  const tlsEnabled = getEnv('JRPC_TLS', 'false') === 'true';
  const clientProto = getEnv('JRPC_CLIENT_PROTO', tlsEnabled ? 'wss' : 'ws');
  const tlsPort = getEnv('TLS_PORT', '12443');

  const { chromium, firefox, webkit } = require('playwright');
  const factory = { chromium, firefox, webkit }[browserName];
  if (!factory) {
    console.error(`Unsupported BROWSER: ${browserName}`);
    process.exit(2);
  }

  // Locate the JsRpc client script
  const clientJsPath = path.resolve(__dirname, '../../../resouces/JsEnv_Dev.js');
  if (!fs.existsSync(clientJsPath)) {
    console.error(`Client script not found: ${clientJsPath}`);
    process.exit(2);
  }
  const clientJs = fs.readFileSync(clientJsPath, 'utf-8');

  const scheme = clientProto;
  const finalPort = (scheme === 'wss') ? tlsPort : port;
  const wsURL = explicitWs || `${scheme}://${host}:${finalPort}/ws?group=${encodeURIComponent(group)}&clientId=${encodeURIComponent(clientId)}`;

  console.log(`[play_client] launching ${browserName} headless=${headless}`);
  const browser = await factory.launch({ headless });
  const context = await browser.newContext({ ignoreHTTPSErrors: tlsEnabled });

  // Ensure the JsRpc runtime is present before any page scripts
  await context.addInitScript({ content: clientJs });
  await context.addInitScript({
    content: `
      (function(){
        try {
          window.__JRPC_WS_URL__ = ${JSON.stringify(wsURL)};
        } catch (e) { console.error('inject ws url failed', e); }
      })();
    `,
  });

  const page = await context.newPage();
  page.on('console', (msg) => console.log(`[page] ${msg.type()}:`, msg.text()));
  page.on('pageerror', (err) => console.error('[pageerror]', err));

  console.log(`[play_client] navigating to ${targetUrl}`);
  await page.goto(targetUrl, { waitUntil: 'domcontentloaded' });

  // Instantiate Hlclient within the page to connect to the server.
  await page.evaluate((params) => {
    try {
      const { clientScript, wsUrl } = params;
      if (!wsUrl) {
        throw new Error('missing wsUrl');
      }

      // Execute the client script to define Hlclient
      eval(clientScript);

      // Now instantiate Hlclient
      window.__hlclient__ = new Hlclient(wsUrl);
      return true;
    } catch (e) {
      console.error('Failed to instantiate Hlclient:', e);
      return false;
    }
  }, { clientScript: clientJs, wsUrl: wsURL });

  console.log(`[play_client] connected to ${wsURL}. Waiting for RPC requests...`);

  const shutdown = async () => {
    console.log('[play_client] shutting down');
    try { await page.close({ runBeforeUnload: false }); } catch {}
    try { await context.close(); } catch {}
    try { await browser.close(); } catch {}
    process.exit(0);
  };
  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);

  // Keep process alive
  await new Promise(() => {});
}

run().catch((err) => {
  console.error('[play_client] fatal:', err);
  process.exit(1);
});
