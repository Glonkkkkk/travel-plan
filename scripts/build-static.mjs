import fs from 'node:fs';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const out = path.join(root, 'dist');
fs.mkdirSync(out, { recursive: true });
const files = ['index.html', 'styles.css', 'ledger.css', 'runtime-storage.js', 'overview-map.js', 'route-ui.js', 'app.js', 'ticket-pdf-preview.js', 'ledger.js', 'site-navigation.js', 'trip-data.json', '_headers'];
for (const file of files) fs.copyFileSync(path.join(root, file), path.join(out, file));
fs.cpSync(path.join(root, 'assets'), path.join(out, 'assets'), { recursive: true });
// Public revision stamp lets us verify which Git commit actually reached production.
let commit = null;
try { commit = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim(); } catch {}
fs.writeFileSync(path.join(out, 'build-info.json'), JSON.stringify({ commit, builtAt: new Date().toISOString() }) + '\n');
console.log('Static site output ready.');
