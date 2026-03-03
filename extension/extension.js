const vscode = require("vscode");
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

let backendProcess = null;
let activePort = null;

const HOST = "127.0.0.1";
const PORT_CANDIDATES = [8000, 8001, 8002, 8003, 8004, 8005];

const pythonCmd = process.platform === "win32" ? "py" : "python3";
async function checkOllama() {
  return new Promise((resolve) => {
    const proc = spawn("ollama", ["list"], { shell: true });

    proc.on("error", () => resolve(false));
    proc.on("exit", (code) => resolve(code === 0));
  });
}
function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function isPortAlive(port) {
  try {
    const res = await fetch(`http://${HOST}:${port}/docs`);
    return res.ok;
  } catch {
    return false;
  }
}

async function findRunningBackend() {
  for (const port of PORT_CANDIDATES) {
    if (await isPortAlive(port)) {
      console.log(`KYC: Found running backend on port ${port}`);
      activePort = port;
      return true;
    }
  }
  return false;
}

async function waitForBackend(port, retries = 15) {
  for (let i = 0; i < retries; i++) {
    if (await isPortAlive(port)) return true;
    await delay(1000);
  }
  return false;
}

async function startBackend(context) {
  if (await findRunningBackend()) return true;

  const serverPath = path.join(context.extensionPath, "server");

  for (const port of PORT_CANDIDATES) {
    console.log(`KYC: Trying port ${port}`);

    const processInstance = spawn(pythonCmd, ["run.py"], {
      cwd: serverPath,
      shell: true,
      env: {
        ...process.env,
        KYC_PORT: port.toString(),
      },
    });

    processInstance.stdout.on("data", (data) => {
      console.log("KYC BACKEND:", data.toString());
    });

    processInstance.stderr.on("data", (data) => {
      console.error("KYC BACKEND ERROR:", data.toString());
    });

    const started = await waitForBackend(port, 10);

    if (started) {
      console.log(`KYC: Backend started on port ${port}`);
      backendProcess = processInstance;
      activePort = port;
      return true;
    }

    processInstance.kill();
    await delay(500);
  }

  return false;
}

function activate(context) {
  const command = vscode.commands.registerCommand(
    "knowyourcode.openChat",
    async () => {
      const workspace = vscode.workspace.workspaceFolders;

      if (!workspace || workspace.length === 0) {
        vscode.window.showErrorMessage(
          "Please open a project folder before using Know Your Code.",
        );
        return;
      }

      let repoPath = workspace[0].uri.fsPath;
      repoPath = path.resolve(repoPath);
      repoPath = repoPath.replace(/\\/g, "\\\\");
      console.log("KYC: Repo path detected:", repoPath);
      const ollamaOk = await checkOllama();

      if (!ollamaOk) {
        vscode.window.showErrorMessage(
          "Ollama not found. Please install Ollama to use Know Your Code.",
        );
        return;
      }

      const started = await startBackend(context);

      if (!started) {
        vscode.window.showErrorMessage(
          "Know Your Code backend failed to start.",
        );
        return;
      }

      const BACKEND_URL = `http://${HOST}:${activePort}`;

      try {
        const response = await fetch(`${BACKEND_URL}/init`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ repo_path: repoPath }),
        });

        const data = await response.json();
        console.log("KYC: Init response:", data);
      } catch (err) {
        vscode.window.showErrorMessage("Repository initialization failed.");
        return;
      }

      const panel = vscode.window.createWebviewPanel(
        "kycChat",
        `Know Your Code - by Adi3182004 (Port ${activePort})`,
        vscode.ViewColumn.Beside,
        {
          enableScripts: true,
          localResourceRoots: [
            vscode.Uri.joinPath(context.extensionUri, "webview"),
          ],
        },
      );

      const htmlPath = vscode.Uri.joinPath(
        context.extensionUri,
        "webview",
        "index.html",
      );

      let html = fs.readFileSync(htmlPath.fsPath, "utf8");

      const webviewUri = panel.webview.asWebviewUri(
        vscode.Uri.joinPath(context.extensionUri, "webview"),
      );

      html = html
        .replace(/{{webviewUri}}/g, webviewUri)
        .replace(/{{cspSource}}/g, panel.webview.cspSource)
        .replace(/{{backendPort}}/g, activePort.toString());

      panel.webview.html = html;

      panel.webview.onDidReceiveMessage(
        async (message) => {
          if (message.command === "openFile") {
            try {
              const fileUri = vscode.Uri.file(message.file);

              const doc = await vscode.workspace.openTextDocument(fileUri);
              const editor = await vscode.window.showTextDocument(doc, {
                viewColumn: vscode.ViewColumn.One,
                preserveFocus: false,
                preview: false,
              });

              const line = Math.max(0, (message.line || 1) - 1);

              const position = new vscode.Position(line, 0);
              editor.selection = new vscode.Selection(position, position);
              editor.revealRange(
                new vscode.Range(position, position),
                vscode.TextEditorRevealType.InCenter,
              );
            } catch (err) {
              vscode.window.showErrorMessage(
                "Failed to open file: " + err.message,
              );
            }
          }
        },
        undefined,
        context.subscriptions,
      );
    },
  );

  context.subscriptions.push(command);

  context.subscriptions.push({
    dispose() {
      if (backendProcess) {
        backendProcess.kill();
        backendProcess = null;
        console.log("KYC: Backend stopped.");
      }
    },
  });
}

function deactivate() {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
    console.log("KYC: Backend stopped on deactivate.");
  }
}

module.exports = {
  activate,
  deactivate,
};
