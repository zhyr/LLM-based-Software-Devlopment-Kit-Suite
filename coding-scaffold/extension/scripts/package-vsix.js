#!/usr/bin/env node
/**
 * Package vsix without relying on vsce secretlint (broken when os.cpus().length === 0).
 */
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const os = require('os');

const root = path.join(__dirname, '..');
process.chdir(root);

function run(cmd, args) {
  const r = spawnSync(cmd, args, { stdio: 'inherit', shell: false });
  if (r.status !== 0) process.exit(r.status ?? 1);
}

run('npm', ['run', 'prepare-resources']);
run('npm', ['run', 'compile']);

const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
const vsixName = `${pkg.name}-${pkg.version}.vsix`;

// Prefer vsce when CPU count is healthy
const cpuCount = (os.cpus() || []).length;
if (cpuCount > 0) {
  const r = spawnSync(
    process.execPath,
    [
      require.resolve('@vscode/vsce/vsce'),
      'package',
      '--no-dependencies',
      '--allow-missing-repository',
      '--skip-license',
    ],
    { stdio: 'inherit' }
  );
  if (r.status === 0 && fs.existsSync(vsixName)) {
    console.log('Packaged with vsce:', vsixName);
    const distDir = path.join(root, '..', 'dist');
    fs.mkdirSync(distDir, { recursive: true });
    fs.copyFileSync(path.join(root, vsixName), path.join(distDir, vsixName));
    console.log('Copied to', path.join(distDir, vsixName));
    process.exit(0);
  }
  console.warn('vsce failed; falling back to zip packaging');
}

const { mkdtempSync, rmSync, cpSync, mkdirSync, writeFileSync } = fs;
const staging = mkdtempSync(path.join(os.tmpdir(), 'haxitag-vsix-'));
const ext = path.join(staging, 'extension');
mkdirSync(ext, { recursive: true });
cpSync('package.json', path.join(ext, 'package.json'));
cpSync('out', path.join(ext, 'out'), { recursive: true });
cpSync('resources', path.join(ext, 'resources'), { recursive: true });
if (fs.existsSync('media')) {
  cpSync('media', path.join(ext, 'media'), { recursive: true });
}
if (fs.existsSync('README.md')) {
  cpSync('README.md', path.join(ext, 'README.md'));
}
if (fs.existsSync('CHANGELOG.md')) {
  cpSync('CHANGELOG.md', path.join(ext, 'CHANGELOG.md'));
}

const iconAsset = fs.existsSync(path.join(ext, 'media', 'icon.png'))
  ? `\n    <Asset Type="Microsoft.VisualStudio.Services.Icons.Default" Path="extension/media/icon.png" Addressable="true" />`
  : '';
const readmeAsset = fs.existsSync(path.join(ext, 'README.md'))
  ? `\n    <Asset Type="Microsoft.VisualStudio.Services.Content.Details" Path="extension/README.md" Addressable="true" />`
  : '';
const changelogAsset = fs.existsSync(path.join(ext, 'CHANGELOG.md'))
  ? `\n    <Asset Type="Microsoft.VisualStudio.Services.Content.Changelog" Path="extension/CHANGELOG.md" Addressable="true" />`
  : '';

const homepageProp = pkg.homepage
  ? `\n      <Property Id="Microsoft.VisualStudio.Services.Links.Learn" Value="${pkg.homepage}" />\n      <Property Id="Microsoft.VisualStudio.Services.Links.Getstarted" Value="${pkg.homepage}" />\n      <Property Id="Microsoft.VisualStudio.Services.Links.Support" Value="${pkg.homepage}" />\n      <Property Id="Microsoft.VisualStudio.Services.Links.Source" Value="${(pkg.repository && pkg.repository.url) || pkg.homepage}" />`
  : '';

writeFileSync(
  path.join(staging, 'extension.vsixmanifest'),
  `<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011" xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011">
  <Metadata>
    <Identity Language="en-US" Id="${pkg.name}" Version="${pkg.version}" Publisher="${pkg.publisher}" />
    <DisplayName>${pkg.displayName}</DisplayName>
    <Description xml:space="preserve">${String(pkg.description)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')}</Description>
    <Tags>${(pkg.keywords || []).join(',')}</Tags>
    <Categories>${(pkg.categories || ['Other']).join(',')}</Categories>
    <GalleryFlags>Public</GalleryFlags>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="${pkg.engines.vscode}" />
      <Property Id="Microsoft.VisualStudio.Code.ExtensionKind" Value="workspace" />${homepageProp}
    </Properties>
  </Metadata>
  <Installation><InstallationTarget Id="Microsoft.VisualStudio.Code"/></Installation>
  <Dependencies/>
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true" />${iconAsset}${readmeAsset}${changelogAsset}
  </Assets>
</PackageManifest>
`
);

writeFileSync(
  path.join(staging, '[Content_Types].xml'),
  `<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension=".json" ContentType="application/json"/>
  <Default Extension=".vsixmanifest" ContentType="text/xml"/>
  <Default Extension=".js" ContentType="application/javascript"/>
  <Default Extension=".py" ContentType="text/x-python"/>
  <Default Extension=".txt" ContentType="text/plain"/>
  <Default Extension=".map" ContentType="application/json"/>
  <Default Extension=".png" ContentType="image/png"/>
  <Default Extension=".md" ContentType="text/markdown"/>
  <Default Extension=".html" ContentType="text/html"/>
</Types>
`
);

const outPath = path.join(root, vsixName);
if (fs.existsSync(outPath)) fs.unlinkSync(outPath);
const zip = spawnSync('zip', ['-r', '-q', outPath, '.'], {
  cwd: staging,
  stdio: 'inherit',
});
rmSync(staging, { recursive: true, force: true });
if (zip.status !== 0) process.exit(zip.status ?? 1);
console.log('Packaged (zip fallback):', outPath, fs.statSync(outPath).size, 'bytes');
const distDir = path.join(root, '..', 'dist');
fs.mkdirSync(distDir, { recursive: true });
fs.copyFileSync(outPath, path.join(distDir, vsixName));
console.log('Copied to', path.join(distDir, vsixName));
