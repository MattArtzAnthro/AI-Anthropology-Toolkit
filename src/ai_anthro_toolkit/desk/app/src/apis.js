// The toolkit catalog's component APIs: names and property schemas, without the
// Lit elements, so the same schemas check messages in the browser and in node.
import { z } from 'zod';
import { DynamicStringSchema } from '@a2ui/web_core/v1_0';

export const CATALOG_ID = 'https://github.com/MattArtzAnthro/AI-Anthropology-Toolkit/catalogs/desk/v1';

export const PassageApi = {
  name: 'Passage',
  schema: z
    .object({
      text: DynamicStringSchema.describe('The quoted passage, shown as the researcher will judge it.'),
      source: DynamicStringSchema.describe('Where the passage comes from, e.g. a document and its lines.').optional(),
    })
    .strict(),
};

export const TOOLKIT_APIS = [PassageApi];
