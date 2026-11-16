// Runs the standalone page's own reading of actions, and its moves of the desk, in node.
// Reads {local, cases} on stdin, each case {op: "action", name, context},
// {op: "check", saved}, {op: "after", saved, card_id}, {op: "restore", saved} or
// {op: "text", texts} (each text's strip, repr and line split); prints, for each,
// {ok: value} or {error: message}. tests/package/test_desk_local.py compares these
// with what ai_anthro_toolkit.desk.a2ui gives.
import { afterDecision, check, decisionFromAction, repr, restoreUpdates, splitLines, strip } from '../src/local.js';

let input = '';
for await (const chunk of process.stdin) input += chunk;
const { local, cases } = JSON.parse(input);
const RUN = {
  action: (c) => decisionFromAction(local, c.name, c.context),
  check: (c) => check(local, c.saved),
  text: (c) => c.texts.map((s) => [strip(s), repr(s), splitLines(s)]),
  after: (c) => afterDecision(local, c.saved, c.card_id),
  restore: (c) => restoreUpdates(local, c.saved),
};
const answers = cases.map((c) => {
  try {
    return { ok: RUN[c.op](c) };
  } catch (err) {
    return { error: err.message };
  }
});
console.log(JSON.stringify(answers));
