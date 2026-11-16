// Bundles the desk view into one script, inlined into pages by desk.page.
import { build } from 'esbuild';
import { options } from './bundle.config.mjs';

await build(options);
