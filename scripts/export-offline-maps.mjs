import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const out = path.resolve(process.argv[2]);
fs.mkdirSync(out, { recursive: true });
const data = JSON.parse(fs.readFileSync(path.join(root, 'trip-data.json'), 'utf8'));
const context = vm.createContext({ state: { data } });
vm.runInContext(fs.readFileSync(path.join(root, 'overview-map.js'), 'utf8'), context);
const require = createRequire('/Users/glonk/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/package.json');
const sharp = require('sharp');
for (const original of data.routeMap.regions) {
  const region = structuredClone(original);
  const base = await sharp(path.join(root, region.baseImage)).png().toBuffer();
  region.baseImage = `data:image/png;base64,${base.toString('base64')}`;
  context.region = region;
  const svg = vm.runInContext('travelOverviewArtwork(state.data.days, region)', context);
  fs.writeFileSync(path.join(out, region.id + '.svg'), svg);
  await sharp(Buffer.from(svg)).resize(1800).flatten({ background: '#f5f5ee' }).jpeg({quality: 91, chromaSubsampling: '4:4:4'}).toFile(path.join(out, region.id + '.jpg'));
  console.log(region.id);
}
