// Passage: the quoted chunk or case a decision is about, with its provenance.
import { html, nothing } from 'lit';
import { A2uiLitElement } from '@a2ui/lit';
import { PassageApi } from './apis.js';

export class AatPassage extends A2uiLitElement {
  api = PassageApi;

  // Light DOM, so the design system's stylesheet styles the passage.
  createRenderRoot() {
    return this;
  }

  render() {
    const props = this.controller?.props;
    if (!props) return nothing;
    return html`<figure class="passage">
      <blockquote>${props.text ?? ''}</blockquote>
      ${props.source ? html`<figcaption>${props.source}</figcaption>` : nothing}
    </figure>`;
  }
}
AatPassage.tagName = 'aat-passage';

export const Passage = { ...PassageApi, tagName: AatPassage.tagName, element: AatPassage };
