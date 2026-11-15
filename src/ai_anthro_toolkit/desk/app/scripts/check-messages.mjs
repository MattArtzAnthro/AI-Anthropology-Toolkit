// Runs A2UI message batches through the bundled renderer's own checks, in node.
// Reads a JSON array of batches on stdin; prints, for each, null when the strict
// renderer accepts it or the error it raises. The Python tests compare these
// verdicts with ai_anthro_toolkit.desk.a2ui.validate.
import { Catalog, MessageProcessor, basicCatalog, STRICT_VALIDATION } from '@a2ui/web_core/v1_0';
import { CATALOG_ID, TOOLKIT_APIS } from '../src/apis.js';

let input = '';
for await (const chunk of process.stdin) input += chunk;
const verdicts = JSON.parse(input).map((batch) => {
  const catalogs = [basicCatalog, new Catalog(CATALOG_ID, '1.0', TOOLKIT_APIS)];
  const processor = new MessageProcessor(catalogs, undefined, { validationConfig: STRICT_VALIDATION });
  try {
    processor.processMessages(batch);
    return null;
  } catch (err) {
    return `${err.constructor.name}: ${err.message}`;
  }
});
console.log(JSON.stringify(verdicts));
