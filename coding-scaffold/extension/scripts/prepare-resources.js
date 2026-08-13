const fs = require('fs');
const path = require('path');

const extRoot = path.join(__dirname, '..');
const scaffoldRoot = path.join(extRoot, '..');
const dest = path.join(extRoot, 'resources');

function copyDir(src, dst) {
  if (!fs.existsSync(src)) {
    console.warn('skip missing', src);
    return;
  }
  fs.mkdirSync(dst, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    if (entry.name === '__pycache__' || entry.name === 'node_modules') continue;
    const from = path.join(src, entry.name);
    const to = path.join(dst, entry.name);
    if (entry.isDirectory()) {
      copyDir(from, to);
    } else {
      fs.copyFileSync(from, to);
    }
  }
}

fs.rmSync(dest, { recursive: true, force: true });
fs.mkdirSync(dest, { recursive: true });
copyDir(path.join(scaffoldRoot, 'tools', 'legacy'), path.join(dest, 'scripts'));
// Canonical prompts (haxitag-coding-prompt-*.txt); skip nested legacy/rules dirs by file copy
(() => {
  const src = path.join(scaffoldRoot, 'prompts');
  const dst = path.join(dest, 'prompts');
  fs.mkdirSync(dst, { recursive: true });
  if (!fs.existsSync(src)) return;
  for (const name of fs.readdirSync(src)) {
    if (!name.startsWith('haxitag-coding-prompt-') || !name.endsWith('.txt')) continue;
    fs.copyFileSync(path.join(src, name), path.join(dst, name));
  }
})();
copyDir(path.join(scaffoldRoot, 'playground'), path.join(dest, 'playground'));
copyDir(path.join(scaffoldRoot, 'tools', 'inject'), path.join(dest, 'tools', 'inject'));
copyDir(path.join(scaffoldRoot, 'tools', 'privacy'), path.join(dest, 'tools', 'privacy'));
copyDir(path.join(scaffoldRoot, 'tools', 'policy'), path.join(dest, 'tools', 'policy'));
copyDir(path.join(scaffoldRoot, 'tools', 'llint'), path.join(dest, 'tools', 'llint'));
copyDir(path.join(scaffoldRoot, 'tools', 'align'), path.join(dest, 'tools', 'align'));
copyDir(path.join(scaffoldRoot, 'tools', 'enhance'), path.join(dest, 'tools', 'enhance'));
copyDir(path.join(scaffoldRoot, 'tools', 'sentinel'), path.join(dest, 'tools', 'sentinel'));
copyDir(
  path.join(scaffoldRoot, 'enterprise', 'profiles'),
  path.join(dest, 'enterprise', 'profiles')
);

// Keep extension icon in sync with docs/codingscoffold.png (128x128 for marketplace)
const mediaDir = path.join(extRoot, 'media');
const srcIcon = path.join(scaffoldRoot, 'docs', 'codingscoffold.png');
const dstIcon = path.join(mediaDir, 'icon.png');
fs.mkdirSync(mediaDir, { recursive: true });
if (fs.existsSync(srcIcon)) {
  const { spawnSync } = require('child_process');
  const r = spawnSync(
    'sips',
    ['-z', '128', '128', srcIcon, '--out', dstIcon],
    { encoding: 'utf8' }
  );
  if (r.status !== 0) {
    fs.copyFileSync(srcIcon, dstIcon);
    console.warn('sips resize failed; copied full-size icon');
  } else {
    console.log('Synced media/icon.png from docs/codingscoffold.png');
  }
}

console.log('Prepared resources from', scaffoldRoot);
