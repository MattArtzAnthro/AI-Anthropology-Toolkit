// The toolkit catalog's components as Lit elements. Each draws the markup of the
// design system component of the same name (design/system/components), so the
// design system's stylesheet styles it; each renders in the light DOM for that reason.
import { css, html, nothing } from 'lit';
import { A2uiLitElement } from '@a2ui/lit';
import {
  BylineApi,
  ChoiceGroupApi,
  CodeTagApi,
  DecisionCardApi,
  NoticeApi,
  ProgressApi,
  ProvenanceApi,
  StatusApi,
  StepApi,
  TallyApi,
  TextFieldApi,
} from './apis.js';
import { Passage } from './passage.js';

const cx = (...names) => names.filter(Boolean).join(' ');
let uid = 0;
const nextId = (prefix) => `${prefix}-${++uid}`;

class ToolkitElement extends A2uiLitElement {
  // The element itself takes no box: its markup sits in the layout as the design system draws it.
  static styles = css`:host { display: contents; }`;

  createRenderRoot() {
    return this;
  }

  get props() {
    return this.controller?.props;
  }

  kids(children) {
    return Array.isArray(children) ? children.map((child) => this.renderNode(child)) : nothing;
  }
}

const STATUS_WORDS = { needs: 'Needs you', started: 'Started', done: 'Done', refused: "Can't continue", model: 'Model draft' };
const status = (tone, text) => html`<span class="aat-status aat-status--${tone}">${text || STATUS_WORDS[tone]}</span>`;
const quietButton = (label, onClick) =>
  html`<button type="button" class="aat-btn aat-btn--quiet" @click=${onClick}>${label}</button>`;
const codeTag = (tone, bare, label) =>
  html`<span class=${cx('aat-code', tone && `aat-code--${tone}`, bare && 'aat-code--bare')}>${label}</span>`;

export class AatDecisionCard extends ToolkitElement {
  api = DecisionCardApi;

  render() {
    const p = this.props;
    if (!p) return nothing;
    if (p.done) {
      return html`<article class="aat-card aat-card--done">
        <div class="aat-card__summary">
          ${status('done', p.doneLabel)}
          <h3 class="aat-card__title">${p.title}</h3>
          <span class="aat-card__result">${p.result ?? ''}</span>
          ${typeof p.change === 'function' ? quietButton('Change', () => p.change()) : nothing}
        </div>
      </article>`;
    }
    // A card neither open nor done waits in the queue, unseen.
    if (p.open === false) return nothing;
    const state = p.state || 'needs';
    return html`<article class="aat-card aat-card--${state}">
      <header class="aat-card__head">
        <div class="aat-card__titles">
          ${p.eyebrow ? html`<span class="aat-id">${p.eyebrow}</span>` : nothing}
          <h3 class="aat-card__title">${p.title}</h3>
        </div>
        ${status(state, p.statusLabel)}
      </header>
      ${this.kids(p.children)}
    </article>`;
  }
}
AatDecisionCard.tagName = 'aat-decision-card';

export class AatProvenance extends ToolkitElement {
  api = ProvenanceApi;

  render() {
    const p = this.props;
    if (!p) return nothing;
    const by = p.by || 'model';
    const who = p.label || (by === 'model' ? 'Model draft · not decided' : 'Your decision');
    return html`<section class="aat-prov aat-prov--${by}" aria-label=${who}>
      <p class="aat-prov__who">${who}</p>
      <div class="aat-prov__body">${p.text ?? ''}</div>
    </section>`;
  }
}
AatProvenance.tagName = 'aat-provenance';

export class AatChoiceGroup extends ToolkitElement {
  api = ChoiceGroupApi;
  name = nextId('aat-choice');

  render() {
    const p = this.props;
    if (!p) return nothing;
    const value = Array.isArray(p.value) ? p.value : typeof p.value === 'string' ? [p.value] : [];
    const set = (next) => typeof p.setValue === 'function' && p.setValue(next);
    const toggle = (v) => {
      if (!p.multiple) set([v]);
      else set(value.includes(v) ? value.filter((x) => x !== v) : [...value, v]);
    };
    const hintId = `${this.name}-hint`;
    return html`<fieldset class=${cx('aat-choices', p.wide && 'aat-choices--wide')} ?disabled=${p.disabled === true}
        aria-describedby=${p.hint ? hintId : nothing}>
      <legend class=${p.hideLegend ? 'aat-visually-hidden' : nothing}>${p.legend}</legend>
      ${p.hint ? html`<p class="aat-choices__hint" id=${hintId}>${p.hint}</p>` : nothing}
      <div class="aat-choices__list">
        ${(p.options || []).map(
          (o) => html`<label class="aat-choice">
            <input type=${p.multiple ? 'checkbox' : 'radio'} name=${this.name} value=${o.value}
              .checked=${value.includes(o.value)} @change=${() => toggle(o.value)}>
            <span class="aat-choice__text">${o.tone ? codeTag(o.tone, true, o.label) : o.label}
              ${o.description ? html`<span class="aat-choice__desc">${o.description}</span>` : nothing}</span>
          </label>`,
        )}
      </div>
    </fieldset>`;
  }
}
AatChoiceGroup.tagName = 'aat-choice-group';

export class AatStep extends ToolkitElement {
  api = StepApi;

  render() {
    const p = this.props;
    if (!p) return nothing;
    return html`<div class=${cx('aat-step', p.done && 'aat-step--done')}>
      <span class="aat-step__n" aria-hidden="true">${p.n}</span>
      <div class="aat-step__label">${p.label}</div>
      ${Array.isArray(p.children) && p.children.length ? html`<div class="aat-step__body">${this.kids(p.children)}</div>` : nothing}
    </div>`;
  }
}
AatStep.tagName = 'aat-step';

export class AatStatus extends ToolkitElement {
  api = StatusApi;

  render() {
    const p = this.props;
    return p ? status(p.tone || 'needs', p.text) : nothing;
  }
}
AatStatus.tagName = 'aat-status';

export class AatCodeTag extends ToolkitElement {
  api = CodeTagApi;

  render() {
    const p = this.props;
    return p ? codeTag(p.tone, p.bare, p.text) : nothing;
  }
}
AatCodeTag.tagName = 'aat-code-tag';

export class AatProgress extends ToolkitElement {
  api = ProgressApi;

  render() {
    const p = this.props;
    if (!p) return nothing;
    const total = Number(p.total) || 0;
    const done = Number(p.done) || 0;
    const segs = [];
    for (let i = 0; i < total; i++) {
      const state = i === p.current ? 'current' : i < done ? 'done' : null;
      segs.push(html`<li class=${cx('aat-progress__seg', state && `aat-progress__seg--${state}`)}></li>`);
    }
    return html`<ol class="aat-progress" role="img" aria-label=${`${p.label ? `${p.label}: ` : ''}${done} of ${total} decided`}>${segs}</ol>`;
  }
}
AatProgress.tagName = 'aat-progress';

export class AatNotice extends ToolkitElement {
  api = NoticeApi;

  render() {
    const p = this.props;
    if (!p) return nothing;
    const tone = p.tone || 'info';
    const kids = Array.isArray(p.children) && p.children.length;
    return html`<div class="aat-notice aat-notice--${tone}" role=${tone === 'refusal' ? 'alert' : 'status'}>
      <p class="aat-notice__title">${p.title}</p>
      ${p.text || kids ? html`<div class="aat-notice__body">${p.text ? html`<p>${p.text}</p>` : nothing}${kids ? this.kids(p.children) : nothing}</div>` : nothing}
    </div>`;
  }
}
AatNotice.tagName = 'aat-notice';

export class AatTally extends ToolkitElement {
  api = TallyApi;

  render() {
    const p = this.props;
    if (!p) return nothing;
    const left = Number(p.left) || 0;
    const text = left === 0 ? p.doneText || 'Nothing left to decide' : `${left} of ${p.total} ${p.noun || 'items'} need you`;
    return html`<div class=${cx('aat-tally', p.sticky && 'aat-tally--sticky')} role="status">
      <span class="aat-tally__count">${status(left ? 'needs' : 'done', left ? String(left) : 'Done')}<span class="aat-tally__text">${text}</span></span>
      <div class="aat-tally__actions">${left && typeof p.next === 'function' ? quietButton('Go to next', () => p.next()) : nothing}</div>
    </div>`;
  }
}
AatTally.tagName = 'aat-tally';

export class AatTextField extends ToolkitElement {
  api = TextFieldApi;
  fieldId = nextId('aat-field');

  render() {
    const p = this.props;
    if (!p) return nothing;
    const id = this.fieldId;
    const describedBy = [p.hint && `${id}-hint`, p.error && `${id}-err`].filter(Boolean).join(' ') || nothing;
    const onInput = (e) => typeof p.setValue === 'function' && p.setValue(e.target.value);
    const control = p.multiline
      ? html`<textarea id=${id} class="aat-input" .value=${p.value ?? ''} ?required=${p.required === true}
          aria-invalid=${p.error ? 'true' : nothing} aria-describedby=${describedBy} @input=${onInput}></textarea>`
      : html`<input id=${id} type="text" class="aat-input" .value=${p.value ?? ''} ?required=${p.required === true}
          aria-invalid=${p.error ? 'true' : nothing} aria-describedby=${describedBy} @input=${onInput}>`;
    return html`<div class=${cx('aat-field', p.error && 'aat-field--error')}>
      <label class="aat-field__label" for=${id}>${p.label}</label>
      ${p.hint ? html`<span class="aat-field__hint" id=${`${id}-hint`}>${p.hint}</span>` : nothing}
      ${control}
      ${p.error ? html`<span class="aat-field__error" id=${`${id}-err`}>${p.error}</span>` : nothing}
    </div>`;
  }
}
AatTextField.tagName = 'aat-text-field';

// The colophon. Every page this bundle runs in, the standalone desk and the MCP App
// shell, prints the colophon from brand.py around the desk, so the component marks
// where the desk ends and draws nothing: the credit has one source and appears once.
export class AatByline extends ToolkitElement {
  api = BylineApi;

  render() {
    return nothing;
  }
}
AatByline.tagName = 'aat-byline';

const entry = (api, element) => ({ ...api, tagName: element.tagName, element });

export const TOOLKIT_COMPONENTS = [
  entry(DecisionCardApi, AatDecisionCard),
  Passage,
  entry(ProvenanceApi, AatProvenance),
  entry(ChoiceGroupApi, AatChoiceGroup),
  entry(StepApi, AatStep),
  entry(StatusApi, AatStatus),
  entry(CodeTagApi, AatCodeTag),
  entry(ProgressApi, AatProgress),
  entry(NoticeApi, AatNotice),
  entry(TallyApi, AatTally),
  entry(TextFieldApi, AatTextField),
  entry(BylineApi, AatByline),
];
