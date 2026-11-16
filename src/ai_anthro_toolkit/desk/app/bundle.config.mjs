// How the desk view is bundled: build.mjs writes it to dist/, and
// scripts/bundle-check.mjs builds it in memory to compare.
export const options = {
  entryPoints: ['src/main.js'],
  bundle: true,
  format: 'iife',
  minify: true,
  legalComments: 'eof',
  target: 'es2022',
  outfile: 'dist/desk-app.js',
};
