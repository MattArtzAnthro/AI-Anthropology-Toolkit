// The standalone desk page with no server behind it. It reads each action into a
// decision, checks the desk it would leave as the server checks a save, and moves the
// desk exactly as the server does for the MCP App view (ai_anthro_toolkit.desk.a2ui:
// decision_from_action, after_decision, restore; ai_anthro_toolkit.desk.gate.check_save),
// from what a2ui.local(desk) puts in the page. tests/package/test_desk_local.py holds the
// two to the same answers, refusals word for word.

const VERSION = 'v1.0';
const NO_CODE = '(no code applies)';
const CODE_RESULTS = { adopt: 'Adopted', reword: 'Reworded', delete: 'Deleted' };
const YES_NO = { yes: true, no: false };
const SAVE = 'This decision cannot be saved:';

// What Python's str.isspace() is true for, which str.strip() takes off. JavaScript's trim()
// differs: it takes off U+FEFF and leaves U+001C to U+001F and U+0085.
const SPACE = '[\\t\\n\\v\\f\\r\\x1c-\\x1f \\x85\\xa0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000]';
const EDGES = new RegExp(`^${SPACE}+|${SPACE}+$`, 'g');
// What Python's repr() escapes: every character str.isprintable() is false for.
const UNPRINTABLE = /[\p{Cc}\p{Cf}\p{Cs}\p{Co}\p{Cn}\p{Zl}\p{Zp}\p{Zs}]/u;

/** Python's str.strip(). */
export const strip = (s) => s.replace(EDGES, '');

function escaped(code) {
  if (code < 0x100) return `\\x${code.toString(16).padStart(2, '0')}`;
  if (code < 0x10000) return `\\u${code.toString(16).padStart(4, '0')}`;
  return `\\U${code.toString(16).padStart(8, '0')}`;
}

/** Python's repr() of a value, as the server's refusals quote what they refuse. */
export function repr(value) {
  if (value == null) return 'None';
  if (typeof value === 'boolean') return value ? 'True' : 'False';
  if (typeof value === 'number') return String(value);
  const s = String(value);
  const quote = s.includes("'") && !s.includes('"') ? '"' : "'";
  const body = [...s]
    .map((ch) => {
      if (ch === '\\') return '\\\\';
      if (ch === quote) return `\\${quote}`;
      if (ch === '\n') return '\\n';
      if (ch === '\r') return '\\r';
      if (ch === '\t') return '\\t';
      if (ch !== ' ' && UNPRINTABLE.test(ch)) return escaped(ch.codePointAt(0));
      return ch;
    })
    .join('');
  return `${quote}${body}${quote}`;
}

const isObject = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);
const clean = (value) => (value == null ? '' : strip(String(value)));
const chosen = (value) => (Array.isArray(value) ? value.map(String) : []);
// The line breaks Python's str.splitlines() splits on.
const LINES = /\r\n|[\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029]/;
/** Python's str.splitlines(), but keeping a last empty line, which a split skips anyway. */
export const splitLines = (s) => s.split(LINES);

function yesNo(value, what) {
  if (!Object.prototype.hasOwnProperty.call(YES_NO, value)) throw new Error(`${what} is answered yes or no, not ${repr(value)}.`);
  return YES_NO[value];
}

function splitParts(text, cardId) {
  const parts = [];
  for (const line of splitLines(clean(text))) {
    if (!strip(line)) continue;
    const at = line.indexOf(':');
    const label = at < 0 ? line : line.slice(0, at);
    if (at < 0 || !strip(label)) {
      throw new Error(
        'Each part of a split takes one line: its label, a colon, then its definition. ' +
          `A part of ${cardId} reads ${repr(strip(line))}.`,
      );
    }
    parts.push({ label: strip(label), definition: strip(line.slice(at + 1)) });
  }
  return parts;
}

function codeDecision(view, cardId) {
  const picked = chosen(view.action);
  if (!picked.length) throw new Error(`Choose what to do with ${cardId} before saving.`);
  const decision = { action: picked[0] };
  if (picked[0] === 'reword') {
    decision.definition = clean(view.definition);
    if (clean(view.label)) decision.label = clean(view.label);
  } else if (picked[0] === 'merge') {
    const targets = chosen(view.target);
    decision.target = targets.length ? targets[0] : '';
  } else if (picked[0] === 'split') {
    decision.parts = splitParts(view.parts, cardId);
  }
  return decision;
}

function rulingDecision(view, cardId) {
  const codes = chosen(view.codes);
  if (!codes.length) throw new Error(`Choose a ruling for ${cardId} before saving, or exclude the chunk.`);
  let decision;
  if (codes.includes(NO_CODE)) {
    if (codes.length > 1) {
      throw new Error(`The ruling on ${cardId} chooses No code applies alongside a code; choose one or the other.`);
    }
    decision = { none_apply: true };
  } else {
    decision = { codes };
  }
  const answer = chosen(view.is_rule);
  if (answer.length) decision.is_rule = yesNo(answer[0], 'Whether a ruling states a rule');
  if (clean(view.rule_text)) decision.rule_text = clean(view.rule_text);
  return decision;
}

/** The [card_id, decision] an action records, or an Error with the server's refusal. */
export function decisionFromAction(local, name, context) {
  const stage = local.stage;
  context = isObject(context) ? context : {};
  if (name === 'answer_exclusive' && stage === 'codebook') {
    const answer = chosen(context.exclusive);
    if (!answer.length) throw new Error('Choose an answer to whether the codes are mutually exclusive before saving.');
    return ['exclusivity', { exclusive: yesNo(answer[0], 'Whether the codes are mutually exclusive') }];
  }
  if (!['save_decision', 'exclude_chunk'].includes(name) || (name === 'exclude_chunk' && stage !== 'rulings')) {
    throw new Error(`${repr(name)} is not an action that records a decision on a ${stage} desk.`);
  }
  const cardId = clean(context.card_id);
  if (!local.cards.some((card) => card.card_id === cardId)) throw new Error(`${cardId} is not a card on this desk.`);
  if (name === 'exclude_chunk') return [cardId, { exclude: { reason: clean(context.reason) } }];
  const view = isObject(context.decision) ? context.decision : {};
  const decision = stage === 'codebook' ? codeDecision(view, cardId) : rulingDecision(view, cardId);
  if (clean(view.note)) decision.note = clean(view.note);
  return [cardId, decision];
}

// Whether a ruling departs from its card's proposal (decisions.differs).
function differs(card, decision) {
  if (card.proposal == null || 'exclude' in decision) return false;
  const ruled = new Set(decision.codes || []);
  const proposed = new Set(card.proposal);
  return ruled.size !== proposed.size || [...ruled].some((code) => !proposed.has(code));
}

// ── The checks a save passes (decisions.validate, gate.problem_lines, apply._check_labels) ──
//
// Only what the page can hold is checked: its documents always name their own desk and
// card checksum, so those two document checks cannot fail here.

const ACTIONS = ['adopt', 'reword', 'merge', 'split', 'delete'];
const ACTION_CHOICES = `${ACTIONS.slice(0, -1).join(', ')} or ${ACTIONS[ACTIONS.length - 1]}`;
const ACTION_FIELDS = {
  adopt: ['action', 'note'],
  reword: ['action', 'definition', 'label', 'note'],
  merge: ['action', 'target', 'note'],
  split: ['action', 'parts', 'note'],
  delete: ['action', 'note'],
};
const RULING_FIELDS = ['codes', 'none_apply', 'exclude', 'is_rule', 'rule_text', 'note'];
const RULING_KINDS = ['codes', 'none_apply', 'exclude'];

const has = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
const blank = (value) => typeof value !== 'string' || !strip(value);
const extraFields = (decision, fields) => Object.keys(decision).filter((key) => !fields.includes(key)).sort();
const untypedFields = (decision, keys) =>
  keys.filter((key) => decision[key] != null && typeof decision[key] !== 'string').map((key) => `${key} must be text.`);

function codeProblems(card, decision, chosen, labels) {
  const label = card.code_label;
  const action = decision.action;
  if (action == null) return [`The decision on ${label} gives no action; choose ${ACTION_CHOICES}.`];
  if (!ACTIONS.includes(action)) return [`${repr(action)} is not an action; choose ${ACTION_CHOICES}.`];
  const extra = extraFields(decision, ACTION_FIELDS[action]);
  if (extra.length) return [`${action} does not take ${extra.join(', ')}.`];
  const untyped = untypedFields(decision, ['definition', 'label', 'target', 'note']);
  if (untyped.length) return untyped;
  if (action === 'reword' && blank(decision.definition)) return [`The reword of ${label} has an empty definition.`];
  if (action === 'merge') return mergeProblems(label, decision.target, chosen, labels);
  if (action === 'split') return splitProblems(label, decision.parts);
  return [];
}

function mergeProblems(label, target, chosen, labels) {
  if (target === label) return [`${label} cannot be merged into itself.`];
  if (!labels.has(target)) return [`${label} is merged into ${repr(target)}, which is not a code in this codebook.`];
  const into = labels.get(target);
  const fate = has(chosen, into) ? chosen[into].action : undefined;
  if (fate === 'delete') return [`${label} is merged into ${target}, which is deleted.`];
  if (fate === 'merge' || fate === 'split') {
    return [`${label} is merged into ${target}, which is itself ${fate === 'merge' ? 'merged' : 'split'}.`];
  }
  return [];
}

function splitProblems(label, parts) {
  parts = parts == null ? [] : parts;
  if (!Array.isArray(parts) || !parts.every(isObject)) return [`Each part of the split of ${label} needs a label and a definition.`];
  if (parts.length < 2) return [`A split needs at least two parts; ${label} has ${parts.length}.`];
  const found = [];
  const seen = new Set();
  parts.forEach((part, k) => {
    const n = k + 1;
    if (blank(part.label)) found.push(`Part ${n} of the split of ${label} has no label.`);
    else if (seen.has(strip(part.label))) found.push(`The split of ${label} names ${repr(strip(part.label))} twice.`);
    else seen.add(strip(part.label));
    if (blank(part.definition)) found.push(`Part ${n} of the split of ${label} has no definition.`);
  });
  return found;
}

function rulingProblems(local, decision) {
  const extra = extraFields(decision, RULING_FIELDS);
  if (extra.length) return [`A ruling does not take ${extra.join(', ')}.`];
  const kinds = RULING_KINDS.filter((kind) => has(decision, kind));
  if (kinds.length !== 1) {
    return [`A ruling gives codes, no code applies, or an exclusion; this one gives ${kinds.join(' and ') || 'none'}.`];
  }
  const untyped = untypedFields(decision, ['rule_text', 'note']);
  if (untyped.length) return untyped;
  if (has(decision, 'exclude')) {
    const exclude = decision.exclude;
    const found = isObject(exclude) && !blank(exclude.reason) ? [] : ['An exclusion needs a reason.'];
    if (has(decision, 'is_rule') || has(decision, 'rule_text')) {
      found.push('An exclusion does not state a rule; take out is_rule and rule_text.');
    }
    return found;
  }
  const found = ruledProblems(local, decision);
  if (has(decision, 'is_rule') && typeof decision.is_rule !== 'boolean') found.push('is_rule must be true or false.');
  else if (decision.is_rule === true && blank(decision.rule_text)) {
    found.push('The ruling is marked as a rule but gives no rule text.');
  }
  return found;
}

function ruledProblems(local, decision) {
  const exclusive = Boolean(local.exclusive);
  if (has(decision, 'none_apply')) {
    if (decision.none_apply !== true) return ['none_apply is true when given.'];
    if (exclusive) return ['The codes are mutually exclusive, so a ruling takes exactly one code, not No code applies.'];
    return [];
  }
  const codes = decision.codes;
  if (!Array.isArray(codes) || !codes.every((code) => typeof code === 'string')) return ['codes must be a list of code labels.'];
  if (!codes.length) return ['A ruling with codes names at least one; for none, give none_apply.'];
  const twice = new Set(codes.filter((code) => codes.indexOf(code) !== codes.lastIndexOf(code)));
  const found = [...twice].map((code) => `The ruling names ${repr(code)} twice.`);
  for (const code of codes) {
    if (!local.codes.includes(code)) found.push(`The ruling names ${repr(code)}, which is not in the codebook in force.`);
  }
  const distinct = new Set(codes).size;
  if (exclusive && distinct > 1) {
    found.push(`The codes are mutually exclusive, so a ruling takes exactly one code; this one takes ${distinct}.`);
  }
  return found;
}

// gate.problem_lines: each problem names its card unless its message already does, or it
// is the document's or the exclusivity question's.
function problemLines(heading, problems) {
  const lines = problems.map(([cardId, message]) =>
    cardId === 'desk' || cardId === 'exclusivity' || message.startsWith(cardId) ? message : `${cardId}: ${message}`,
  );
  return `${heading}\n${lines.map((line) => `- ${line}`).join('\n')}`;
}

// apply._check_labels: the labels kept as they are are claimed first, then each new label
// in card order, so a clash names the card that brings the second copy.
function checkLabels(cards, chosen) {
  const decisionOf = (card) => (has(chosen, card.card_id) ? chosen[card.card_id] : { action: 'adopt' });
  const newLabel = (card, decision) => clean(decision.label) || card.code_label;
  const kept = new Set(
    cards
      .filter((card) => {
        const decision = decisionOf(card);
        return ['adopt', 'reword'].includes(decision.action) && newLabel(card, decision) === card.code_label;
      })
      .map((card) => card.code_label),
  );
  for (const card of cards) {
    const decision = decisionOf(card);
    let fresh;
    if (decision.action === 'reword' && newLabel(card, decision) !== card.code_label) fresh = [newLabel(card, decision)];
    else if (decision.action === 'split') fresh = decision.parts.map((part) => clean(part.label));
    else continue;
    for (const label of fresh) {
      if (kept.has(label)) {
        throw new Error(`${SAVE}\n- ${card.card_id} gives the label ${repr(label)}, which the ratified codebook already has.`);
      }
      kept.add(label);
    }
  }
}

/** Refuses, with the server's words, the desk saved would be after a save; else null. */
export function check(local, saved) {
  const chosen = isObject(saved.decisions) ? saved.decisions : {};
  const found = [];
  if (local.stage === 'rulings' && saved.exclusive != null && saved.exclusive !== Boolean(local.exclusive)) {
    const [said, holds] = saved.exclusive ? ['are', 'are not'] : ['are not', 'are'];
    found.push(['desk', `These rulings say the codes ${said} mutually exclusive; the codebook in force says they ${holds}.`]);
  }
  const labels = new Map(local.stage === 'codebook' ? local.cards.map((card) => [card.code_label, card.card_id]) : []);
  for (const card of local.cards) {
    if (!has(chosen, card.card_id)) continue;
    const decision = chosen[card.card_id];
    const messages = local.stage === 'codebook' ? codeProblems(card, decision, chosen, labels) : rulingProblems(local, decision);
    found.push(...messages.map((message) => [card.card_id, message]));
  }
  const onDesk = new Set(local.cards.map((card) => card.card_id));
  for (const cardId of Object.keys(chosen)) {
    if (!onDesk.has(cardId)) found.push([cardId, `${cardId} is not a card on this desk.`]);
  }
  if (found.length) throw new Error(problemLines(SAVE, found));
  if (local.stage === 'codebook') checkLabels(local.cards, chosen);
  return null;
}

function result(local, decision) {
  if (local.stage === 'codebook') {
    const action = decision.action ?? '';
    if (action === 'merge') return `Merged into ${decision.target ?? ''}`;
    if (action === 'split') return `Split into ${(decision.parts || []).length} codes`;
    return CODE_RESULTS[action] ?? String(action);
  }
  if ('exclude' in decision) return 'Excluded';
  const ruled = decision.none_apply ? 'No code applies' : (decision.codes || []).join(', ');
  return decision.is_rule ? `${ruled} · states a rule` : ruled;
}

function status(local, saved, after) {
  const decisions = saved.decisions || {};
  const items = local.cards.map((card) => {
    const decision = decisions[card.card_id];
    const complete = decision != null && (!differs(card, decision) || 'is_rule' in decision);
    return [card.card_id, complete, complete ? result(local, decision) : ''];
  });
  if (local.stage === 'codebook') {
    const exclusive = saved.exclusive ?? null;
    const answer = exclusive === null ? '' : exclusive ? 'Mutually exclusive' : 'Not mutually exclusive';
    items.push(['exclusivity', exclusive !== null, answer]);
  }
  const ids = items.map((item) => item[0]);
  const start = after != null ? ids.indexOf(after) : -1;
  let current;
  if (after != null && start >= 0 && !items[start][1]) {
    current = start; // the decided item still needs an answer, so it stays open
  } else {
    const order = [];
    for (let k = start + 1; k < items.length; k++) order.push(k);
    for (let k = 0; k <= start; k++) order.push(k);
    current = order.find((k) => !items[k][1]) ?? items.length;
  }
  const flags = items.map(([, done, res], k) => ({ open: k === current, done, result: res }));
  const done = items.filter((item) => item[1]).length;
  const out = { cards: flags.slice(0, local.cards.length), progress: { done, current, left: items.length - done } };
  if (local.stage === 'codebook') out.exclusivity = flags[flags.length - 1];
  return out;
}

const statusMessage = (local, value) => ({
  version: VERSION,
  updateDataModel: { surfaceId: local.desk_id, path: '/status', value },
});

function released(local, card, decision) {
  const drawn = local.release[card.card_id];
  if (!drawn) return [];
  const components = differs(card, decision) ? drawn.rule : drawn.plain;
  return [{ version: VERSION, updateComponents: { surfaceId: local.desk_id, components } }];
}

/** The messages that follow saving the decision on cardId, as after_decision gives them. */
export function afterDecision(local, saved, cardId) {
  const decisions = saved.decisions || {};
  const card = local.cards.find((c) => c.card_id === cardId);
  const messages = [];
  if (local.stage === 'codebook' && cardId === 'exclusivity') {
    if (saved.exclusive == null) throw new Error('The exclusivity question has no saved answer.');
  } else if (!card) {
    throw new Error(`${cardId} is not a card on this desk.`);
  } else if (!(cardId in decisions)) {
    throw new Error(`${cardId} has no saved decision.`);
  } else if (local.stage === 'rulings') {
    messages.push(...released(local, card, decisions[cardId]));
  }
  messages.push(statusMessage(local, status(local, saved, cardId)));
  return messages;
}

/** What restore adds to the desk's own messages for the decisions in saved. */
export function restoreUpdates(local, saved) {
  const decisions = saved.decisions || {};
  const unknown = Object.keys(decisions).filter((id) => !local.cards.some((card) => card.card_id === id));
  if (unknown.length) throw new Error(`The saved decisions name cards this desk lacks: ${unknown.join(', ')}.`);
  const messages = [];
  if (local.stage === 'rulings') {
    for (const card of local.cards) {
      if (card.card_id in decisions) messages.push(...released(local, card, decisions[card.card_id]));
    }
  }
  if (Object.keys(decisions).length || saved.exclusive != null) messages.push(statusMessage(local, status(local, saved, null)));
  return messages;
}

/** How many items are still undecided. */
export function left(local, saved) {
  return status(local, saved, null).progress.left;
}

/** The decisions document every surface copies and record_desk_decisions takes. */
export function document(local, saved) {
  return {
    schema: 'aat/desk-decisions@1',
    desk_id: local.desk_id,
    card_checksum: local.card_checksum,
    exclusive: saved.exclusive ?? null,
    decisions: saved.decisions || {},
  };
}
