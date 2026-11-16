// The toolkit catalog's component APIs: names and property schemas, without the
// Lit elements, so the same schemas check messages in the browser and in node.
// Each schema takes exactly the properties catalog.json declares, with the same
// ones required; tests/package/test_desk_a2ui.py holds the two to that.
import { z } from 'zod';
import {
  ActionSchema,
  ChildListSchema,
  DynamicBooleanSchema,
  DynamicNumberSchema,
  DynamicStringListSchema,
  DynamicStringSchema,
} from '@a2ui/web_core/v1_0';

export const CATALOG_ID = 'https://github.com/MattArtzAnthro/AI-Anthropology-Toolkit/catalogs/desk/v1';

const tone6 = z.number().int().min(1).max(6);
const text = (what) => DynamicStringSchema.describe(what);

export const DecisionCardApi = {
  name: 'DecisionCard',
  schema: z
    .object({
      title: text('The decision the card asks for.'),
      eyebrow: text("A short line above the title, such as the card's place in the queue.").optional(),
      state: z.enum(['needs', 'started', 'done']).default('needs').optional(),
      open: DynamicBooleanSchema.describe('Whether this is the card being decided.').optional(),
      done: DynamicBooleanSchema.describe('Whether the card is decided.').optional(),
      statusLabel: text("Text for the card's status.").optional(),
      result: text('What was decided, shown when the card is done.').optional(),
      doneLabel: text('Text for the status of a done card.').optional(),
      children: ChildListSchema.describe("The card's content.").optional(),
      change: ActionSchema.describe('Reopens a done card for a new decision.').optional(),
    })
    .strict(),
};

export const PassageApi = {
  name: 'Passage',
  schema: z
    .object({
      text: text('The quoted passage, shown as the researcher will judge it.'),
      source: text('Where the passage comes from, e.g. a document and its lines.').optional(),
    })
    .strict(),
};

export const ProvenanceApi = {
  name: 'Provenance',
  schema: z
    .object({
      by: z.enum(['model', 'researcher']).default('model').optional(),
      label: text('A label replacing the default for `by`.').optional(),
      text: text('The content whose authorship is shown.'),
    })
    .strict(),
};

export const ChoiceGroupApi = {
  name: 'ChoiceGroup',
  schema: z
    .object({
      legend: text('The question the choices answer.'),
      hint: text('Help text under the legend.').optional(),
      options: z.array(
        z
          .object({
            value: z.string(),
            label: text('The text shown for this choice.'),
            description: text('A line explaining this choice.').optional(),
            tone: tone6.optional(),
          })
          .strict(),
      ),
      multiple: z.boolean().default(false).optional(),
      value: DynamicStringListSchema.describe('The selected values.'),
      wide: z.boolean().default(false).optional(),
      hideLegend: z.boolean().default(false).optional(),
      disabled: DynamicBooleanSchema.describe('Whether the choices are unavailable.').optional(),
    })
    .strict(),
};

export const StepApi = {
  name: 'Step',
  schema: z
    .object({
      n: z.number().int().min(1),
      label: text('What the step asks for.'),
      done: DynamicBooleanSchema.describe('Whether the step is complete.').optional(),
      children: ChildListSchema.describe("The step's content.").optional(),
    })
    .strict(),
};

export const StatusApi = {
  name: 'Status',
  schema: z
    .object({
      tone: z.enum(['needs', 'started', 'done', 'refused', 'model']).default('needs').optional(),
      text: text('The status text.'),
    })
    .strict(),
};

export const CodeTagApi = {
  name: 'CodeTag',
  schema: z
    .object({
      tone: tone6.optional(),
      bare: z.boolean().default(false).optional(),
      text: text("The code's name."),
    })
    .strict(),
};

export const ProgressApi = {
  name: 'Progress',
  schema: z
    .object({
      total: DynamicNumberSchema.describe('The number of items in the queue.'),
      done: DynamicNumberSchema.describe('How many are decided.'),
      current: DynamicNumberSchema.describe('The index of the item that needs the researcher.').optional(),
      label: text('An accessible name for the progress bar.').optional(),
    })
    .strict(),
};

export const NoticeApi = {
  name: 'Notice',
  schema: z
    .object({
      tone: z.enum(['info', 'refusal', 'done']).default('info').optional(),
      title: text("The notice's headline."),
      text: text("The notice's body.").optional(),
      children: ChildListSchema.describe('Controls offered with the notice.').optional(),
    })
    .strict(),
};

export const TallyApi = {
  name: 'Tally',
  schema: z
    .object({
      left: DynamicNumberSchema.describe('How many decisions remain.'),
      total: DynamicNumberSchema.describe('How many decisions there are.'),
      noun: text("What is counted, such as 'cards'.").optional(),
      sticky: z.boolean().default(false).optional(),
      doneText: text('Text shown when nothing remains.').optional(),
      next: ActionSchema.describe('Moves to the next open decision.').optional(),
    })
    .strict(),
};

export const TextFieldApi = {
  name: 'TextField',
  schema: z
    .object({
      label: text("The field's label."),
      hint: text('Help text under the label.').optional(),
      error: text('An error message for the field.').optional(),
      multiline: z.boolean().default(false).optional(),
      required: z.boolean().default(false).optional(),
      value: text("The field's value."),
    })
    .strict(),
};

export const BylineApi = {
  name: 'Byline',
  schema: z
    .object({
      version: z.string().min(1),
      full: z.boolean().default(false).optional(),
    })
    .strict(),
};

export const TOOLKIT_APIS = [
  DecisionCardApi,
  PassageApi,
  ProvenanceApi,
  ChoiceGroupApi,
  StepApi,
  StatusApi,
  CodeTagApi,
  ProgressApi,
  NoticeApi,
  TallyApi,
  TextFieldApi,
  BylineApi,
];
