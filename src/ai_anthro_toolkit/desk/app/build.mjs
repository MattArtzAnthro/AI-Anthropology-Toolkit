// Bundles the desk view into one script, inlined into pages by desk.page.
import { build } from 'esbuild';

await build({
  entryPoints: ['src/main.js'],
  bundle: true,
  format: 'iife',
  minify: true,
  legalComments: 'eof',
  target: 'es2022',
  outfile: 'dist/desk-app.js',
});
