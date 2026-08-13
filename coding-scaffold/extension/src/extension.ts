import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { spawn } from 'child_process';

function scaffoldRoot(context: vscode.ExtensionContext): string {
  const packaged = path.join(context.extensionPath, 'resources');
  if (fs.existsSync(path.join(packaged, 'tools', 'inject'))) {
    return packaged;
  }
  return path.join(context.extensionPath, '..');
}

function toolsRoot(context: vscode.ExtensionContext): string {
  const root = scaffoldRoot(context);
  const packaged = path.join(root, 'tools');
  if (fs.existsSync(path.join(packaged, 'inject'))) {
    return packaged;
  }
  return path.join(root, 'tools');
}

function scriptsDir(context: vscode.ExtensionContext): string {
  const root = scaffoldRoot(context);
  const packaged = path.join(root, 'scripts');
  if (fs.existsSync(packaged)) {
    return packaged;
  }
  return path.join(root, 'tools', 'legacy');
}

function promptsDir(context: vscode.ExtensionContext): string {
  const root = scaffoldRoot(context);
  const packaged = path.join(root, 'prompts');
  if (
    fs.existsSync(packaged) &&
    fs.existsSync(path.join(packaged, 'haxitag-coding-prompt-6-coding.txt'))
  ) {
    return packaged;
  }
  // Dev: coding-scaffold/prompts next to extension/
  const canonical = path.join(context.extensionPath, '..', 'prompts');
  if (
    fs.existsSync(canonical) &&
    fs.existsSync(path.join(canonical, 'haxitag-coding-prompt-6-coding.txt'))
  ) {
    return canonical;
  }
  return packaged;
}

function playgroundFile(
  context: vscode.ExtensionContext,
  name: 'markdown.html' | 'mermaid.html'
): string | undefined {
  const candidates = [
    path.join(scaffoldRoot(context), 'playground', name),
    path.join(context.extensionPath, 'resources', 'playground', name),
    path.join(context.extensionPath, '..', 'playground', name),
  ];
  for (const p of candidates) {
    if (fs.existsSync(p)) return p;
  }
  return undefined;
}

async function openPlayground(
  context: vscode.ExtensionContext,
  name: 'markdown.html' | 'mermaid.html'
): Promise<void> {
  const file = playgroundFile(context, name);
  if (!file) {
    vscode.window.showErrorMessage(`Playground not found: ${name}`);
    return;
  }
  await vscode.env.openExternal(vscode.Uri.file(file));
}

function defaultPolicyPath(context: vscode.ExtensionContext, root: string): string {
  const inRepo = path.join(root, '.haxitag', 'workspace-policy.yaml');
  if (fs.existsSync(inRepo)) {
    return inRepo;
  }
  const scaffold = scaffoldRoot(context);
  return path.join(
    scaffold,
    'enterprise',
    'profiles',
    'local-dev.example.yaml'
  );
}

function workspaceRoot(): string | undefined {
  return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
}

function resolveTargetDir(uri?: vscode.Uri): string | undefined {
  if (uri?.fsPath) {
    const stat = fs.statSync(uri.fsPath);
    return stat.isDirectory() ? uri.fsPath : path.dirname(uri.fsPath);
  }
  return workspaceRoot();
}

function runPython(
  scriptPath: string,
  args: string[],
  cwd: string
): Thenable<void> {
  const channel = vscode.window.createOutputChannel('HaxiTAG Coding Scaffold');
  channel.show(true);
  channel.appendLine(`$ python3 ${scriptPath} ${args.join(' ')}`);

  return new Promise((resolve, reject) => {
    const child = spawn('python3', [scriptPath, ...args], {
      cwd,
      env: process.env,
    });
    child.stdout.on('data', (d) => channel.append(d.toString()));
    child.stderr.on('data', (d) => channel.append(d.toString()));
    child.on('error', (err) => {
      vscode.window.showErrorMessage(`Failed to start python3: ${err.message}`);
      reject(err);
    });
    child.on('close', (code) => {
      if (code === 0) {
        vscode.window.showInformationMessage('HaxiTAG scaffold finished.');
        resolve();
      } else {
        vscode.window.showErrorMessage(`Script exited with code ${code}`);
        reject(new Error(`exit ${code}`));
      }
    });
  });
}

function runPythonCapture(
  scriptPath: string,
  args: string[],
  cwd: string
): Thenable<{ code: number; stdout: string; stderr: string }> {
  return new Promise((resolve, reject) => {
    const child = spawn('python3', [scriptPath, ...args], {
      cwd,
      env: process.env,
    });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (d) => {
      stdout += d.toString();
    });
    child.stderr.on('data', (d) => {
      stderr += d.toString();
    });
    child.on('error', reject);
    child.on('close', (code) => {
      resolve({ code: code ?? 1, stdout, stderr });
    });
  });
}

function collectRelativeFiles(root: string, uris: vscode.Uri[]): string[] {
  const files: string[] = [];
  for (const uri of uris) {
    const st = fs.statSync(uri.fsPath);
    if (st.isFile()) {
      files.push(path.relative(root, uri.fsPath));
    } else if (st.isDirectory()) {
      const walk = (dir: string): void => {
        for (const name of fs.readdirSync(dir)) {
          if (
            name === 'node_modules' ||
            name === '.git' ||
            name === 'dist' ||
            name === '.next'
          ) {
            continue;
          }
          const full = path.join(dir, name);
          const s = fs.statSync(full);
          if (s.isDirectory()) walk(full);
          else files.push(path.relative(root, full));
        }
      };
      walk(uri.fsPath);
    }
  }
  return files.filter(Boolean).slice(0, 40);
}

function selectedUris(
  uri?: vscode.Uri,
  uris?: vscode.Uri[]
): vscode.Uri[] {
  if (uris && uris.length) return uris;
  if (uri) return [uri];
  if (vscode.window.activeTextEditor) {
    return [vscode.window.activeTextEditor.document.uri];
  }
  return [];
}

async function openPackResult(
  stdout: string,
  stderr: string,
  code: number,
  label: string,
  fileCount: number
): Promise<void> {
  const channel = vscode.window.createOutputChannel('HaxiTAG Coding Scaffold');
  if (stderr) channel.appendLine(stderr);
  if (!stdout.trim()) {
    vscode.window.showErrorMessage(
      `${label} failed (exit ${code}). See output channel.`
    );
    channel.show(true);
    return;
  }
  const doc = await vscode.workspace.openTextDocument({
    content: stdout,
    language: 'markdown',
  });
  await vscode.window.showTextDocument(doc, { preview: false });
  await vscode.env.clipboard.writeText(stdout);
  vscode.window.showInformationMessage(
    `HaxiTAG: ${label} — ${fileCount} file(s), source unchanged; copied to clipboard.`
  );
}

export function activate(context: vscode.ExtensionContext): void {
  context.subscriptions.push(
    vscode.commands.registerCommand(
      'haxitagCodingScaffold.composeInput',
      async (uri?: vscode.Uri, uris?: vscode.Uri[]) => {
        const root = workspaceRoot();
        if (!root) {
          vscode.window.showWarningMessage('Open a workspace folder first.');
          return;
        }
        const selected = selectedUris(uri, uris);
        if (!selected.length) {
          vscode.window.showWarningMessage(
            'Select file(s) in the explorer, or open an editor.'
          );
          return;
        }
        const relFiles = collectRelativeFiles(root, selected);
        if (!relFiles.length) {
          vscode.window.showWarningMessage('No files to compose.');
          return;
        }
        const task = await vscode.window.showInputBox({
          prompt: 'Task for prompt shell (optional)',
          placeHolder: '例如：修复登录校验边界条件',
        });
        const withSentinel = await vscode.window.showQuickPick(
          [
            { label: 'Compose only (privacy + llint + align + enhance)', id: 'no' },
            { label: 'Compose + Sentinel precheck', id: 'yes' },
          ],
          { placeHolder: 'Include Sentinel / supply-chain notes?' }
        );
        if (!withSentinel) return;

        const script = path.join(toolsRoot(context), 'inject', 'compose_input.py');
        const policy = defaultPolicyPath(context, root);
        const args = [
          '--root',
          root,
          '--policy',
          policy,
          '--format',
          'markdown',
          '--files',
          ...relFiles,
        ];
        if (task?.trim()) {
          args.push('--task', task.trim());
        }
        if (withSentinel.id === 'yes') {
          args.push('--sentinel');
        } else {
          args.push('--no-sentinel');
        }
        const result = await runPythonCapture(script, args, root);
        await openPackResult(
          result.stdout,
          result.stderr,
          result.code,
          'Compose Input',
          relFiles.length
        );
      }
    )
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      'haxitagCodingScaffold.injectContext',
      async (uri?: vscode.Uri, uris?: vscode.Uri[]) => {
        const root = workspaceRoot();
        if (!root) {
          vscode.window.showWarningMessage('Open a workspace folder first.');
          return;
        }
        const selected = selectedUris(uri, uris);
        if (!selected.length) {
          vscode.window.showWarningMessage(
            'Select file(s) in the explorer, or open an editor.'
          );
          return;
        }
        const relFiles = collectRelativeFiles(root, selected);
        if (!relFiles.length) {
          vscode.window.showWarningMessage('No files to inject.');
          return;
        }
        const script = path.join(
          toolsRoot(context),
          'inject',
          'resolve_context.py'
        );
        const policy = defaultPolicyPath(context, root);
        const result = await runPythonCapture(
          script,
          [
            '--root',
            root,
            '--policy',
            policy,
            '--format',
            'markdown',
            '--files',
            ...relFiles,
          ],
          root
        );
        await openPackResult(
          result.stdout,
          result.stderr,
          result.code,
          'Inject',
          relFiles.length
        );
      }
    )
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      'haxitagCodingScaffold.pathAnnotate',
      async (uri?: vscode.Uri) => {
        const root = workspaceRoot();
        const target = resolveTargetDir(uri);
        if (!root || !target) {
          vscode.window.showWarningMessage('Open a workspace folder first.');
          return;
        }
        const ok = await vscode.window.showWarningMessage(
          'Path Annotate writes into source files (legacy). Prefer Compose Input.',
          'Run legacy anyway'
        );
        if (ok !== 'Run legacy anyway') return;
        const script = path.join(scriptsDir(context), 'haxitag-path-annotator.py');
        await runPython(script, ['-d', target, '--root', root], root);
      }
    )
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      'haxitagCodingScaffold.structureExplore',
      async (uri?: vscode.Uri) => {
        const target = resolveTargetDir(uri) ?? workspaceRoot();
        if (!target) {
          vscode.window.showWarningMessage('Open a workspace folder first.');
          return;
        }
        const script = path.join(
          scriptsDir(context),
          'haxitag-structure-Explorer.py'
        );
        await runPython(script, ['-d', target], target);
      }
    )
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      'haxitagCodingScaffold.contextBuild',
      async (uri?: vscode.Uri) => {
        const root = workspaceRoot();
        if (!root) {
          vscode.window.showWarningMessage('Open a workspace folder first.');
          return;
        }
        const ok = await vscode.window.showWarningMessage(
          'Legacy context builder writes a merge file. Prefer Compose Input.',
          'Run legacy anyway'
        );
        if (ok !== 'Run legacy anyway') return;
        const target = uri?.fsPath ?? root;
        const script = path.join(
          scriptsDir(context),
          'haxitag-context-builder.py'
        );
        const outName = `haxitag-context-${Date.now()}.txt`;
        await runPython(script, ['-d', target, '-n', outName], root);
      }
    )
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      'haxitagCodingScaffold.openPrompt',
      async () => {
        const dir = promptsDir(context);
        if (!fs.existsSync(dir)) {
          vscode.window.showErrorMessage(`Prompts not found: ${dir}`);
          return;
        }
        const files = fs
          .readdirSync(dir)
          .filter(
            (f) =>
              f.startsWith('haxitag-coding-prompt-') && f.endsWith('.txt')
          )
          .sort();
        if (!files.length) {
          vscode.window.showErrorMessage(
            `No haxitag-coding-prompt-*.txt in ${dir}`
          );
          return;
        }
        const picked = await vscode.window.showQuickPick(files, {
          placeHolder: 'Select a HaxiTAG coding prompt template',
        });
        if (!picked) {
          return;
        }
        const doc = await vscode.workspace.openTextDocument(
          path.join(dir, picked)
        );
        await vscode.window.showTextDocument(doc);
      }
    )
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      'haxitagCodingScaffold.openMarkdownPlayground',
      async () => {
        await openPlayground(context, 'markdown.html');
      }
    )
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      'haxitagCodingScaffold.openMermaidPlayground',
      async () => {
        await openPlayground(context, 'mermaid.html');
      }
    )
  );
}

export function deactivate(): void {}
