// The desk view: the A2UI renderer with the toolkit catalog, and the controller that
// connects it to an MCP Apps host or runs the standalone page. In a host, the desk opens
// through the app-only tool desk_sync, which holds it for this view and restores what
// was saved; each decision the researcher saves goes to desk_sync as the renderer sends
// it, and Ratify goes to desk_finish. The model never sees either tool. On the standalone
// page, which carries its desk in a JSON block, the controller reads each decision itself
// (local.js) and keeps it in the browser's storage; Ratify there gives the decisions to
// copy, for record_desk_decisions. Every surface can copy the decisions as JSON.
import '@a2ui/lit';
import { Catalog, MessageProcessor, STRICT_VALIDATION, basicCatalog } from '@a2ui/web_core/v1_0';
import { CATALOG_ID } from './apis.js';
import { TOOLKIT_COMPONENTS } from './components.js';
import { afterDecision, check, decisionFromAction, document as decisionsDocument, left, restoreUpdates } from './local.js';

export { CATALOG_ID };
export const toolkitCatalog = new Catalog(CATALOG_ID, '1.0', TOOLKIT_COMPONENTS);

// Strict, as the server's own check (desk.a2ui.validate) is: a bad message is refused, never drawn in part.
const processor = new MessageProcessor([basicCatalog, toolkitCatalog], undefined, { validationConfig: STRICT_VALIDATION });
const mount = () => document.getElementById('desk');
const KINDS = { codebook: 'Codebook desk', rulings: 'Rulings desk' };
const SAVES = new Set(['save_decision', 'exclude_chunk', 'answer_exclusive']);
const block = document.getElementById('desk-data');
const hosted = !block && window.parent !== window;
// In a host, document is the decisions document desk_sync last returned. On the page,
// local is what a2ui.local put there, saved what the researcher has decided, and key
// where the browser keeps it; memory is set once the browser refuses to keep it.
const desk = { id: null, stage: null, finished: null, document: null };
const page = { local: null, saved: { decisions: {}, exclusive: null }, key: null, memory: false };
// How long the view waits for the host to answer a request before it says so.
const settings = { timeoutMs: 30000 };

processor.onSurfaceCreated((surface) => {
  const el = document.createElement('a2ui-surface');
  el.surface = surface;
  el.dataset.surfaceId = surface.id;
  mount().appendChild(el);
});
processor.onSurfaceDeleted((id) => {
  mount().querySelector(`a2ui-surface[data-surface-id="${CSS.escape(id)}"]`)?.remove();
});

// Notices the view writes itself (a refused save, a rejected message, a finished desk,
// copied decisions), drawn in the design system's Notice markup above the desk. The one
// saying the browser is not keeping decisions has a place of its own and stays.
function box(id) {
  // Prepended in reverse, so the storage notice comes first.
  for (const slot of ['desk-notices', 'desk-storage']) {
    if (document.getElementById(slot)) continue;
    const el = document.createElement('div');
    el.id = slot;
    mount().prepend(el);
  }
  return document.getElementById(id);
}

function noticeElement(tone, title, text, json) {
  const el = document.createElement('div');
  el.className = `aat-notice aat-notice--${tone}`;
  el.setAttribute('role', tone === 'refusal' ? 'alert' : 'status');
  const head = document.createElement('p');
  head.className = 'aat-notice__title';
  head.textContent = title;
  el.append(head);
  if (text || json) {
    const body = document.createElement('div');
    body.className = 'aat-notice__body';
    if (text) {
      const p = document.createElement('p');
      p.textContent = text;
      body.append(p);
    }
    if (json) {
      const area = document.createElement('textarea');
      area.className = 'aat-input';
      area.readOnly = true;
      area.rows = 8;
      area.setAttribute('aria-label', 'The decisions as JSON');
      area.value = json;
      body.append(area);
    }
    el.append(body);
  }
  return el;
}

function notice(tone, title, text, json) {
  box('desk-notices').replaceChildren(noticeElement(tone, title, text, json));
}

function clearNotices() {
  document.getElementById('desk-notices')?.replaceChildren();
}

/** Draw a batch of A2UI messages. A batch that creates a surface already drawn replaces
 * it. Returns false, with a notice, when the renderer refuses the batch. */
export function render(messages) {
  try {
    for (const m of messages) {
      const id = m && m.createSurface && m.createSurface.surfaceId;
      if (id && processor.getSurface(id)) processor.processMessages([{ version: 'v1.0', deleteSurface: { surfaceId: id } }]);
    }
    processor.processMessages(messages);
  } catch (err) {
    notice('refusal', 'The desk could not show this update.', String(err && err.message ? err.message : err));
    return false;
  }
  showTitle();
  return true;
}

function showTitle() {
  const surface = desk.id && processor.getSurface(desk.id);
  const title = surface ? String(surface.dataModel.getSignal('/title').value || '') : '';
  const kind = KINDS[desk.stage] || '';
  const heading = document.getElementById('desk-title');
  if (heading && !heading.textContent.trim()) heading.textContent = title || kind;
  const label = document.getElementById('desk-kind');
  if (label && title && !label.textContent.trim()) label.textContent = kind;
}

// MCP Apps bridge: JSON-RPC over postMessage with the host.
let nextId = 1;
const pending = new Map();
function request(method, params) {
  const id = nextId++;
  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      pending.delete(id);
      resolve({ isError: true, error: { message: 'The host did not answer. Nothing more was saved; try again.' } });
    }, settings.timeoutMs);
    pending.set(id, (answer) => {
      clearTimeout(timer);
      resolve(answer);
    });
    window.parent.postMessage({ jsonrpc: '2.0', id, method, params: params || {} }, '*');
  });
}
function notify(method, params) {
  window.parent.postMessage({ jsonrpc: '2.0', method, params: params || {} }, '*');
}

// A tool's answer: its structured content, or the same JSON in its text when a host
// passes on only the text.
function answerOf(res) {
  if (res.structuredContent && typeof res.structuredContent === 'object') return res.structuredContent;
  const text = res.content && res.content[0] && res.content[0].text;
  try {
    const data = JSON.parse(text);
    return data && typeof data === 'object' ? data : null;
  } catch {
    return null;
  }
}

/** Call one of the desk's app-only tools; returns {ok, data} or {ok: false, text}. */
async function callTool(name, args) {
  document.body.dataset.busy = 'true';
  try {
    const res = await request('tools/call', { name, arguments: args });
    if (!res || res.isError || res.error) {
      const text = res && res.content && res.content[0] && res.content[0].text;
      return { ok: false, text: text || (res && res.error && res.error.message) || `${name} failed.` };
    }
    const data = answerOf(res);
    return data ? { ok: true, data } : { ok: false, text: `${name} sent an answer the desk cannot read.` };
  } finally {
    document.body.dataset.busy = 'false';
  }
}

async function openDesk(result) {
  desk.id = result.desk_id;
  desk.stage = result.stage;
  const loaded = await callTool('desk_sync', { desk_id: desk.id });
  if (!loaded.ok) {
    render(result.a2ui);
    notice('refusal', 'Decisions cannot be saved in this view.', loaded.text);
    return;
  }
  desk.document = loaded.data.document || null;
  render(loaded.data.a2ui);
  if (loaded.data.finished) finished(loaded.data.finished);
}

// Copy the decisions document, and show it in the notice too, since a sandboxed frame or
// a file may refuse the clipboard.
async function copyDecisions(doc, tone, title, text) {
  const json = JSON.stringify(doc, null, 2);
  let copied = false;
  try {
    await navigator.clipboard.writeText(json);
    copied = true;
  } catch {
    copied = false;
  }
  notice(tone, title || (copied ? 'The decisions are copied as JSON.' : 'Copy the decisions below.'), text, json);
}

// ── The standalone page ──────────────────────────────────────────────────────

function keep() {
  try {
    localStorage.setItem(page.key, JSON.stringify(page.saved));
  } catch {
    forgetful();
  }
}

function forgetful() {
  if (page.memory) return;
  page.memory = true;
  box('desk-storage').replaceChildren(noticeElement('info', 'This browser is not keeping the decisions.',
    'They stay on this page until it closes. Copy them as JSON before you leave.'));
}

const isRecord = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);

// What this browser kept, as {decisions, exclusive}; refuses anything else.
function keptDecisions(saved) {
  const decisions = isRecord(saved) ? (saved.decisions ?? {}) : null;
  const exclusive = isRecord(saved) ? (saved.exclusive ?? null) : undefined;
  if (!isRecord(decisions) || !Object.values(decisions).every(isRecord) || ![true, false, null].includes(exclusive)) {
    throw new Error('What it kept is not a set of decisions.');
  }
  return { decisions, exclusive };
}

function openPage(data) {
  desk.id = data.desk_id;
  desk.stage = data.stage;
  page.local = data.local;
  page.key = `aat-desk:${data.desk_id}:${data.local.card_checksum}`;
  let kept = null;
  try {
    kept = localStorage.getItem(page.key);
  } catch {
    forgetful();
  }
  if (!render(data.messages) || !kept) return;
  try {
    const restored = keptDecisions(JSON.parse(kept));
    check(page.local, restored);
    const updates = restoreUpdates(page.local, restored);
    page.saved = restored;
    render(updates);
  } catch (err) {
    notice('refusal', 'The decisions this browser kept could not be restored.', err.message);
  }
}

function decideOnPage(name, context) {
  let cardId;
  let decision;
  try {
    [cardId, decision] = decisionFromAction(page.local, name, context);
  } catch (err) {
    return notice('refusal', 'This decision was not saved.', err.message);
  }
  const saved = page.saved;
  const candidate = cardId === 'exclusivity'
    ? { ...saved, exclusive: decision.exclusive }
    : { ...saved, decisions: { ...saved.decisions, [cardId]: decision } };
  try {
    check(page.local, candidate);
  } catch (err) {
    return notice('refusal', 'This decision was not saved.', err.message);
  }
  page.saved = candidate;
  keep();
  clearNotices();
  render(afterDecision(page.local, page.saved, cardId));
}

function finishOnPage() {
  const open = left(page.local, page.saved);
  if (open) {
    return notice('refusal', 'The desk is not finished.', `${open} ${open === 1 ? 'decision is' : 'decisions are'} still open.`);
  }
  return copyDecisions(decisionsDocument(page.local, page.saved), 'done', 'Every decision is made.',
    'To ratify, give these decisions to record_desk_decisions: paste them into the chat and ask for them to be recorded.');
}

// ── The MCP App ──────────────────────────────────────────────────────────────

function finished(outcome) {
  desk.finished = outcome;
  const id = outcome.ratification_id;
  const version = outcome.version ? `, version ${outcome.version}` : '';
  notice('done', 'The desk is finished.', `Recorded as ${id}${version}. Pass ${id} to start_coding_job.`);
}

// "Change" reopens a done card here, in the view; the server keeps the saved decision
// until a new one is saved over it.
function reopen(cardId) {
  const surface = processor.getSurface(desk.id);
  if (!surface) return;
  const cards = surface.dataModel.getSignal('/cards').value || [];
  const n = cards.findIndex((c) => c && c.card_id === cardId);
  const target = cardId === 'exclusivity' ? '/status/exclusivity' : n >= 0 ? `/status/cards/${n}` : null;
  if (!target) return;
  const set = (path, value) => ({ version: 'v1.0', updateDataModel: { surfaceId: desk.id, path, value } });
  const updates = cards.map((_, k) => set(`/status/cards/${k}/open`, false));
  if (surface.dataModel.getSignal('/status/exclusivity').value) updates.push(set('/status/exclusivity/open', false));
  updates.push(set(`${target}/open`, true), set(`${target}/done`, false));
  render(updates);
}

let working = false;
processor.model.onAction.subscribe(async (action) => {
  if (working) return;
  const { name, context } = action;
  if (name === 'copy_json') {
    const doc = block ? decisionsDocument(page.local, page.saved) : desk.document;
    if (!doc) return notice('refusal', 'There are no decisions to copy.', 'The decisions saved for this desk could not be read.');
    return copyDecisions(doc, 'info');
  }
  // A finished desk's decisions are recorded; the view keeps saying where, and changes nothing.
  if (desk.finished && (name === 'change_decision' || SAVES.has(name) || name === 'finish')) return finished(desk.finished);
  if (name === 'change_decision') return reopen(context.card_id);
  if (block) {
    if (SAVES.has(name)) return decideOnPage(name, context);
    if (name === 'finish') return finishOnPage();
    return undefined;
  }
  if (!desk.id) return undefined;
  working = true;
  try {
    if (SAVES.has(name)) {
      const saved = await callTool('desk_sync', { desk_id: desk.id, action: { name, context } });
      if (!saved.ok) return notice('refusal', 'This decision was not saved.', saved.text);
      desk.document = saved.data.document || desk.document;
      clearNotices();
      render(saved.data.a2ui);
    } else if (name === 'finish') {
      const done = await callTool('desk_finish', { desk_id: desk.id });
      if (!done.ok) return notice('refusal', 'The desk is not finished.', done.text);
      finished(done.data);
    }
  } finally {
    working = false;
  }
});

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
    if (!sc || !Array.isArray(sc.a2ui)) return;
    if (sc.desk_id) openDesk(sc);
    else render(sc.a2ui);
  } else if (m.method === 'ui/notifications/host-context-changed') {
    const theme = m.params && m.params.theme;
    if (theme) document.documentElement.dataset.theme = theme;
  }
});

if (block) {
  openPage(JSON.parse(block.textContent));
} else if (hosted) {
  request('ui/initialize', { appCapabilities: {} }).then((result) => {
    const theme = result && result.hostContext && result.hostContext.theme;
    if (theme) document.documentElement.dataset.theme = theme;
    notify('ui/notifications/initialized');
    reportHeight();
    const watch = new ResizeObserver(reportHeight);
    watch.observe(document.documentElement);
    watch.observe(document.body);
  });
}

// A host sizes an inline view from ui/notifications/size-changed; without it the desk
// sits in a short default frame. Report the content's own height, measured with the
// root at fit-content so a frame taller than the desk can shrink to it.
let reported = 0;
let measuring = false;
function reportHeight() {
  if (measuring) return;
  measuring = true;
  requestAnimationFrame(() => {
    measuring = false;
    const root = document.documentElement;
    const kept = root.style.height;
    root.style.height = 'fit-content';
    const height = Math.ceil(root.getBoundingClientRect().height);
    root.style.height = kept;
    if (height === reported) return;
    reported = height;
    notify('ui/notifications/size-changed', { height });
  });
}

window.DeskApp = { render, CATALOG_ID, settings };
