// The desk view: an MCP Apps bridge feeding A2UI messages to the Lit renderer.
import '@a2ui/lit';
import { Catalog, MessageProcessor, STRICT_VALIDATION, basicCatalog } from '@a2ui/web_core/v1_0';
import { CATALOG_ID } from './apis.js';
import { Passage } from './passage.js';

export { CATALOG_ID };
export const toolkitCatalog = new Catalog(CATALOG_ID, '1.0', [Passage]);

// Strict, as the server's own check (desk.a2ui.validate) is: a bad message is refused, never drawn in part.
const processor = new MessageProcessor([basicCatalog, toolkitCatalog], undefined, { validationConfig: STRICT_VALIDATION });
const mount = () => document.getElementById('desk');

processor.onSurfaceCreated((surface) => {
  const el = document.createElement('a2ui-surface');
  el.surface = surface;
  mount().appendChild(el);
});

export function render(messages) {
  processor.processMessages(messages);
}

// MCP Apps bridge: ui/initialize, then A2UI messages arrive in tool results.
let nextId = 1;
const pending = new Map();
function request(method, params) {
  const id = nextId++;
  return new Promise((resolve) => {
    pending.set(id, resolve);
    window.parent.postMessage({ jsonrpc: '2.0', id, method, params: params || {} }, '*');
  });
}
function notify(method, params) {
  window.parent.postMessage({ jsonrpc: '2.0', method, params: params || {} }, '*');
}
window.addEventListener('message', (ev) => {
  const m = ev.data;
  if (!m || m.jsonrpc !== '2.0') return;
  if (m.id != null && pending.has(m.id)) {
    const resolve = pending.get(m.id);
    pending.delete(m.id);
    resolve(m.error ? { isError: true, error: m.error } : m.result);
    return;
  }
  if (m.method === 'ui/notifications/tool-result') {
    const sc = m.params && m.params.structuredContent;
    if (sc && Array.isArray(sc.a2ui)) render(sc.a2ui);
  }
});

if (window.parent !== window) {
  request('ui/initialize', { appCapabilities: {} }).then((result) => {
    const theme = result && result.hostContext && result.hostContext.theme;
    if (theme) document.documentElement.dataset.theme = theme;
    notify('ui/notifications/initialized');
  });
}

window.DeskApp = { render, CATALOG_ID };
