/* @ds-bundle: {"format":4,"namespace":"AAT","components":[{"name":"Button"},{"name":"Status"},{"name":"Step"},{"name":"ChoiceGroup"},{"name":"TextField"},{"name":"Passage"},{"name":"Provenance"},{"name":"CodeTag"},{"name":"DecisionCard"},{"name":"Notice"},{"name":"Tally"},{"name":"Progress"},{"name":"Stages"},{"name":"Table"},{"name":"Byline"}]} */
(function () {
  var React = window.React, h = React.createElement, useState = React.useState, useId = React.useId;
  function cx() { return Array.prototype.filter.call(arguments, Boolean).join(" "); }

  /* Button. A disabled button always says why: pass `reason`. */
  function Button(p) {
    var variant = p.variant || "secondary", reasonId = useId();
    var rest = Object.assign({}, p); delete rest.variant; delete rest.reason; delete rest.className;
    var btn = h("button", Object.assign({ type: "button" }, rest, {
      className: cx("aat-btn", variant !== "secondary" && "aat-btn--" + variant, p.className),
      "aria-describedby": p.disabled && p.reason ? reasonId : undefined
    }), p.children);
    if (!p.reason || !p.disabled) return btn;
    return h("span", { className: "aat-action" }, btn, h("span", { className: "aat-action__reason", id: reasonId }, p.reason));
  }

  var STATUS_WORDS = { needs: "Needs you", started: "Started", done: "Done", refused: "Can't continue", model: "Model draft" };
  function Status(p) {
    var tone = p.tone || "needs";
    return h("span", { className: "aat-status aat-status--" + tone }, p.children || STATUS_WORDS[tone]);
  }

  function Step(p) {
    return h("div", { className: cx("aat-step", p.done && "aat-step--done") },
      h("span", { className: "aat-step__n", "aria-hidden": "true" }, p.n),
      h("div", { className: "aat-step__label" }, p.label),
      p.children ? h("div", { className: "aat-step__body" }, p.children) : null);
  }

  /* ChoiceGroup. Checkboxes when `multiple`, radios otherwise. Controlled (value + onChange) or not. */
  function ChoiceGroup(p) {
    var autoName = useId(), name = p.name || autoName;
    var initial = p.defaultValue !== undefined ? p.defaultValue : (p.multiple ? [] : null);
    var st = useState(initial), own = st[0], setOwn = st[1];
    var value = p.value !== undefined ? p.value : own;
    function toggle(v) {
      var next = p.multiple ? (value.indexOf(v) >= 0 ? value.filter(function (x) { return x !== v; }) : value.concat([v])) : v;
      if (p.value === undefined) setOwn(next);
      if (p.onChange) p.onChange(next);
    }
    var hintId = name + "-hint";
    return h("fieldset", { className: cx("aat-choices", p.wide && "aat-choices--wide"), disabled: p.disabled, "aria-describedby": p.hint ? hintId : undefined },
      h("legend", { className: p.hideLegend ? "aat-visually-hidden" : undefined }, p.legend),
      p.hint ? h("p", { className: "aat-choices__hint", id: hintId }, p.hint) : null,
      h("div", { className: "aat-choices__list" }, (p.options || []).map(function (o) {
        var on = p.multiple ? value.indexOf(o.value) >= 0 : value === o.value;
        return h("label", { className: "aat-choice", key: o.value },
          h("input", { type: p.multiple ? "checkbox" : "radio", name: name, value: o.value, checked: on, onChange: function () { toggle(o.value); } }),
          h("span", { className: "aat-choice__text" }, o.tone ? h(CodeTag, { tone: o.tone, bare: true }, o.label) : o.label,
            o.description ? h("span", { className: "aat-choice__desc" }, o.description) : null));
      })));
  }

  function TextField(p) {
    var id = useId(), hintId = id + "-hint", errId = id + "-err";
    var rest = Object.assign({}, p); ["label", "hint", "error", "multiline", "className"].forEach(function (k) { delete rest[k]; });
    var describedBy = [p.hint && hintId, p.error && errId].filter(Boolean).join(" ") || undefined;
    var control = h(p.multiline ? "textarea" : "input", Object.assign({ id: id, className: "aat-input", "aria-invalid": p.error ? "true" : undefined, "aria-describedby": describedBy }, p.multiline ? {} : { type: "text" }, rest));
    return h("div", { className: cx("aat-field", p.error && "aat-field--error", p.className) },
      h("label", { className: "aat-field__label", htmlFor: id }, p.label),
      p.hint ? h("span", { className: "aat-field__hint", id: hintId }, p.hint) : null,
      control,
      p.error ? h("span", { className: "aat-field__error", id: errId }, p.error) : null);
  }

  function Passage(p) {
    return h("figure", { className: "aat-passage" }, h("blockquote", null, p.children),
      p.source ? h("figcaption", null, p.source) : null);
  }

  /* Provenance. by="model": dashed, not decided. by="researcher": solid, decided. */
  function Provenance(p) {
    var by = p.by || "model";
    var who = p.label || (by === "model" ? "Model draft · not decided" : "Your decision");
    return h("section", { className: "aat-prov aat-prov--" + by, "aria-label": who },
      h("p", { className: "aat-prov__who" }, who), h("div", { className: "aat-prov__body" }, p.children));
  }

  function CodeTag(p) {
    var cls = cx("aat-code", p.tone && "aat-code--" + p.tone, p.bare && "aat-code--bare");
    return h("span", { className: cls }, p.children);
  }

  /* DecisionCard. state: needs | started | done. Done with a `result` collapses to one line with a Change button. */
  function DecisionCard(p) {
    var state = p.state || "needs";
    if (state === "done" && p.result !== undefined) {
      return h("article", { className: "aat-card aat-card--done", id: p.id },
        h("div", { className: "aat-card__summary" }, h(Status, { tone: "done" }, p.doneLabel),
          h("h3", { className: "aat-card__title" }, p.title), h("span", { className: "aat-card__result" }, p.result),
          p.onChange ? h(Button, { variant: "quiet", onClick: p.onChange }, "Change") : null));
    }
    var tone = state === "done" ? "done" : state;
    return h("article", { className: "aat-card aat-card--" + state, id: p.id },
      h("header", { className: "aat-card__head" },
        h("div", { className: "aat-card__titles" }, p.eyebrow ? h("span", { className: "aat-id" }, p.eyebrow) : null, h("h3", { className: "aat-card__title" }, p.title)),
        h(Status, { tone: tone }, p.statusLabel)),
      p.children);
  }

  function Notice(p) {
    var tone = p.tone || "info";
    return h("div", { className: "aat-notice aat-notice--" + tone, role: tone === "refusal" ? "alert" : "status" },
      h("p", { className: "aat-notice__title" }, p.title),
      p.children ? h("div", { className: "aat-notice__body" }, p.children) : null);
  }

  function Tally(p) {
    var left = p.left || 0, noun = p.noun || "items";
    var text = left === 0 ? (p.doneText || "Nothing left to decide") : left + " of " + p.total + " " + noun + " need you";
    return h("div", { className: cx("aat-tally", p.sticky && "aat-tally--sticky"), role: "status" },
      h("span", { className: "aat-tally__count" }, h(Status, { tone: left ? "needs" : "done" }, left ? String(left) : "Done"), h("span", { className: "aat-tally__text" }, text)),
      h("div", { className: "aat-tally__actions" },
        left && p.onNext ? h(Button, { variant: "quiet", onClick: p.onNext }, "Go to next") : null, p.sticky ? null : p.children));
  }

  /* Progress: one segment per item in a queue. `done` items are action, the `current` index is attention. */
  function Progress(p) {
    var total = p.total || 0, done = p.done || 0, segs = [];
    for (var i = 0; i < total; i++) {
      var state = i === p.current ? "current" : i < done ? "done" : null;
      segs.push(h("li", { key: i, className: cx("aat-progress__seg", state && "aat-progress__seg--" + state) }));
    }
    return h("ol", { className: "aat-progress", role: "img", "aria-label": p.label || (done + " of " + total + " decided") }, segs);
  }

  function Stages(p) {
    return h("nav", { "aria-label": p.label || "Stages" }, h("ol", { className: "aat-stages" }, (p.stages || []).map(function (s, i) {
      return h("li", { key: s.id }, h("button", { type: "button", className: "aat-stage", "aria-current": s.id === p.current ? "step" : undefined,
        onClick: function () { if (p.onSelect) p.onSelect(s.id); } },
        h("span", { className: "aat-stage__n", "aria-hidden": "true" }, i + 1), s.label, s.note ? h("span", { className: "aat-stage__note" }, s.note) : null));
    })));
  }

  function Table(p) {
    var cols = p.columns || [];
    return h("div", { className: "aat-table-wrap" }, h("table", { className: "aat-table" },
      p.caption ? h("caption", null, p.caption) : null,
      h("thead", null, h("tr", null, cols.map(function (c) { return h("th", { key: c.key, scope: "col", className: c.numeric ? "aat-num" : undefined }, c.label); }))),
      h("tbody", null, (p.rows || []).map(function (r, i) {
        return h("tr", { key: r.id || i }, cols.map(function (c) { return h("td", { key: c.key, className: c.numeric ? "aat-num" : undefined }, r[c.key]); }));
      }))));
  }

  var ABOUT = "Matt Artz is an AI anthropologist, designer, and technologist who works with AI to study, use, and contribute to the development and governance of AI, establishing AI anthropology as a field.";
  function Byline(p) {
    var link = function (href, text) { return h("a", { href: href, target: "_blank", rel: "noopener" }, text); };
    return h("footer", { className: "aat-byline" },
      h("span", null, h("b", null, "AI Anthropology Toolkit"), " by Matt Artz"),
      p.version ? h("span", { className: "aat-id" }, "v" + p.version) : null,
      link("https://doi.org/10.5281/zenodo.16728812", "Cite (DOI)"),
      link("https://github.com/MattArtzAnthro/AI-Anthropology-Toolkit", "GitHub"),
      link("https://www.mattartz.me", "mattartz.me"),
      p.full ? h("p", { className: "aat-byline__about" }, ABOUT) : null);
  }

  window.AAT = Object.assign(window.AAT || {}, { Button: Button, Status: Status, Step: Step, ChoiceGroup: ChoiceGroup, TextField: TextField, Passage: Passage,
    Provenance: Provenance, CodeTag: CodeTag, DecisionCard: DecisionCard, Notice: Notice, Tally: Tally, Progress: Progress, Stages: Stages, Table: Table, Byline: Byline });
})();
