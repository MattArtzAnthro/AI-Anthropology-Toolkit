// Builds the desk view in memory, as build.mjs does, and prints
// {packages: {name: version}, matches}: the npm packages esbuild put in the bundle, and
// whether the build equals the committed dist/desk-app.js. tests/package/test_desk_bundle.py
// holds VENDORED.md to the first and the committed bundle to the second.
import { readFileSync } from 'node:fs';
import { build } from 'esbuild';
import { options } from '../bundle.config.mjs';

const result = await build({ ...options, write: false, metafile: true });
const packages = {};
for (const path of Object.keys(result.metafile.inputs)) {
  const found = path.match(/node_modules\/((?:@[^/]+\/)?[^/]+)\//);
  if (found && !(found[1] in packages)) {
    packages[found[1]] = JSON.parse(readFileSync(`node_modules/${found[1]}/package.json`, 'utf8')).version;
  }
}
const committed = readFileSync(options.outfile, 'utf8');
console.log(JSON.stringify({ packages, matches: result.outputFiles[0].text === committed }));
