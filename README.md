# Know Your Code – by Adi3182004

AI-powered codebase intelligence and surgical restore engine inside VS Code.

> Understand your repository. Trace history. Analyze impact. Restore safely.

---

## 🚀 Overview

Know Your Code is a developer intelligence tool that combines:

- Semantic code search
- Git history analysis
- Impact analysis
- Cross-file reasoning
- AI-assisted patch generation
- One-click safe function restore

All directly inside VS Code.

This is not just a chatbot — it is a structured code intelligence system.

---

## 🧠 Core Capabilities

### 🔍 Semantic Code Search

Search by intent, not exact keywords.

Examples:

- Where is `main` defined?
- Where is color logic implemented?
- Which file defines authentication?

---

### 📜 Git History Intelligence

Understand change history at function level.

Examples:

- Who modified `main`?
- What changed in `processData`?
- Show commit history for this file

Includes:

- Commit hash
- Author
- Date
- Semantic change summary

---

### 💥 Impact Analysis

Before modifying a function:

- Detect if it is used
- Count call sites
- Estimate risk level
- Show definition location

Prevents blind refactoring mistakes.

---

### 🔪 One-Click Safe Function Restore (ELITE)

Restore the previous version of a function from Git history safely.

Features:

- Extracts historical function version
- Merges into current file
- Creates automatic `.bak` backup
- Applies patch safely

This is surgical — not full file rollback.

---

### 🤖 AI-Assisted Code Modification

- Propose changes
- Review diff
- Approve or reject
- Safe patch application with backup

---

## 🏗 Architecture

### VS Code Extension Layer

- Command registration
- Webview UI
- File navigation
- Backend communication

### FastAPI Backend

- Semantic search engine
- Git integration
- Function revert engine
- Patch engine
- LLM routing layer

### Core Modules

- `semantic_search.py`
- `function_revert_engine.py`
- `patch_engine.py`
- `ai_code_modifier.py`
- `query_router.py`

---

## ⚙️ Installation (Local VSIX)

### 1️⃣ Package the extension

Inside `/extension`:

```
vsce package
```

This generates:

```
know-your-code-0.0.1.vsix
```

---

### 2️⃣ Install in VS Code

1. Open VS Code
2. Press `Ctrl + Shift + P`
3. Select: `Extensions: Install from VSIX`
4. Choose the generated `.vsix` file

---

### 3️⃣ Start Backend

Inside `/server`:

```
uvicorn main:app --reload
```

Backend runs at:

```
http://127.0.0.1:8000
```

---

## 🛠 Example Workflow

1. Open project in VS Code
2. Run command: `Know Your Code: Open Chat`
3. Ask:

```
Where is main defined?
```

4. Ask:

```
Who modified main?
```

5. Ask:

```
Restore previous version of main
```

6. Review and apply safely

---

## 🧩 Tech Stack

- Python 3.12
- FastAPI
- GitPython
- Sentence Transformers (MiniLM)
- VS Code Extension API
- Node.js
- Ollama (Phi-3 LLM)

---

## 🔐 Safety Features

- No destructive operations without confirmation
- Automatic backup before patch application
- Controlled restore scope (function-level only)
- Error-safe backend responses

---

## 🎯 Why This Project Matters

Most AI tools:

- Only generate code
- Do not understand repository structure
- Ignore Git history
- Cannot restore safely

Know Your Code integrates:

- Semantic reasoning
- Git intelligence
- Controlled modification
- Developer tooling workflow

This bridges AI and real software engineering practice.

---

## 📦 Project Structure

```
Know Your Code/
│
├── extension/          # VS Code extension
│   ├── extension.js
│   ├── package.json
│   └── webview/
│
├── server/             # FastAPI backend
│   ├── main.py
│   ├── semantic_search.py
│   ├── function_revert_engine.py
│   ├── patch_engine.py
│   └── ...
│
└── README.md
```

---

## 👨‍💻 Author

Adi3182004  
AI Systems & Developer Tooling Enthusiast

---

## 📄 License

MIT License
