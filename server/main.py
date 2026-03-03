from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
from history_engine import HistoryEngine
import numpy as np
from sentence_transformers import SentenceTransformer
import hashlib
import shutil
from semantic_search import initialize, query_code
from patch_engine import PatchEngine
from ai_code_modifier import AICodeModifier
from llm_phi3 import ask_phi3
from query_router import QueryRouter
from function_revert_engine import FunctionRevertEngine

_last_focus = None
_conversation_memory = []

app = FastAPI(
    title="Know Your Code - by Adi3182004",
    description="AI-powered repository intelligence and safe code modification engine",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

patch_engine = PatchEngine()
ai_modifier = AICodeModifier()
revert_engine = FunctionRevertEngine()
router = QueryRouter()
current_repo = None
_pending_patches = {}


# ===============================
# Models
# ===============================

class InitRequest(BaseModel):
    repo_path: str


class QueryRequest(BaseModel):
    question: str


class ChangeRequest(BaseModel):
    file_path: str
    instruction: str


class RestoreRequest(BaseModel):
    file_path: str
    function_name: str


# ===============================
# INIT
# ===============================

@app.post("/init")
def init_repo(req: InitRequest):
    global current_repo

    repo_path = req.repo_path

    if not os.path.exists(repo_path):
        return {"status": "failed", "message": "Invalid path"}

    initialize(repo_path)
    current_repo = repo_path

    return {
        "status": "indexed",
        "message": "Repository loaded successfully"
    }


# ===============================
# ASK
# ===============================

@app.post("/ask")
def ask(req: QueryRequest):
    global _last_focus
    global _conversation_memory

    question = req.question.strip()
    intent = router.classify(question)

    print("---- NEW REQUEST ----")
    print("QUESTION:", question)
    print("INTENT:", intent)
    print("LAST FOCUS:", _last_focus)

    # ===============================
    # Query semantic engine
    # ===============================

    data = query_code(question) or {}
    results = data.get("results") or []

    # =================================================
    # REVERT (handled fully in semantic layer)
    # =================================================
    if intent == "revert" and data.get("revert"):
        revert_info = data["revert"]

        if revert_info.get("error"):
            return {
                "answer": revert_info["error"],
                "sources": [],
                "intent": intent
            }

        return {
            "answer": revert_info.get("previous_code"),
            "sources": results[:1],
            "intent": intent
        }

    # =================================================
    # IMPACT
    # =================================================
    if data.get("impact"):
        impact = data["impact"]

        callers = impact.get("callers", [])
        defined = impact.get("defined_in", [])
        fn = impact.get("function")

        count = len(callers)

        if count == 0:
            risk = "LOW"
        elif count == 1:
            risk = "MEDIUM"
        else:
            risk = "HIGH"

        answer = (
            f"Impact Analysis for '{fn}':\n"
            f"Usage Count: {count}\n"
            f"Risk Level: {risk}"
        )

        if defined:
            answer += f"\nDefined in: {defined[0]}"

        return {
            "answer": answer,
            "sources": [],
            "intent": intent
        }

    # =================================================
    # ARCHITECTURE
    # =================================================
    if data.get("architecture"):
        return {
            "answer": data["architecture"],
            "sources": [],
            "intent": "architecture"
        }

    # =================================================
    # HISTORY (file-specific handled in semantic layer)
    # =================================================
    if intent in ("history_author", "history_change"):

        if not results:
            return {
                "answer": "No history found.",
                "sources": [],
                "intent": intent
            }

        top = results[0]
        blame = top.get("blame", [])
        history = top.get("history", [])
        diff_summary = top.get("diff_summary")
        semantic_history = top.get("semantic_history", [])

        if intent == "history_author":

            if not blame:
                return {
                    "answer": "No author information available.",
                    "sources": [],
                    "intent": intent
                }

            unique = []
            seen = set()

            for entry in blame:
                author = entry.get("author")
                if author and author not in seen:
                    seen.add(author)
                    unique.append(
                        f"Author: {author}\n"
                        f"Commit: {entry.get('commit')}\n"
                        f"Date: {entry.get('date')}\n"
                        f"Message: {entry.get('message')}"
                    )

            _last_focus = top

            return {
                "answer": "\n---\n".join(unique),
                "sources": [top],
                "intent": intent
            }

        if intent == "history_change":

            if not history:
                return {
                    "answer": "No change history available.",
                    "sources": [],
                    "intent": intent
                }

            latest = history[0]

            parts = [
                f"Latest Commit: {latest.get('commit')}",
                f"Author: {latest.get('author')}",
                f"Date: {latest.get('date')}",
                f"Message: {latest.get('message')}"
            ]

            if diff_summary:
                parts.append(f"\nDiff Summary:\n{diff_summary}")

            if semantic_history:
                summary = semantic_history[0].get("summary")
                if summary:
                    parts.append(f"\nSemantic Change:\n{summary}")

            _last_focus = top

            return {
                "answer": "\n".join(parts),
                "sources": [top],
                "intent": intent
            }

    # =================================================
    # NO RESULTS
    # =================================================
    if not results:
        return {
            "answer": "Not found in the indexed repository.",
            "sources": [],
            "intent": intent
        }

    # =================================================
    # DIRECT HIT
    # =================================================
    if len(results) == 1 or (
        len(results) > 1 and
        results[0]["confidence"] > results[1]["confidence"] + 0.08
    ):
        _last_focus = results[0]
        _conversation_memory.append(results[0])

        return {
            "answer": results[0]["snippet"],
            "sources": [results[0]],
            "intent": "direct_hit"
        }

    # =================================================
    # FALLBACK LLM
    # =================================================
    context = "\n\n".join(
        [
            f"File: {r['file']}\n"
            f"Lines: {r.get('line')}–{r.get('end_line')}\n"
            f"{r['snippet']}"
            for r in results[:3]
        ]
    )

    prompt = f"""
Answer the question using ONLY the code below.

Question:
{question}

Code:
{context}

Answer:
"""

    answer = ask_phi3(prompt)

    if not answer or "Ollama error" in answer:
        answer = "Model could not generate a reliable answer."

    _last_focus = results[0]
    _conversation_memory.append(results[0])

    return {
        "answer": answer.strip(),
        "sources": results[:3],
        "intent": intent
    }


@app.post("/propose-change")
def propose_change(req: ChangeRequest):
    original_code = patch_engine.read_file(req.file_path)

    if not original_code:
        return {"error": "File could not be read."}

    updated_code = ai_modifier.propose_change(
        req.instruction,
        original_code,
    )

    if not updated_code:
        return {"error": "AI failed to generate update."}

    diff = patch_engine.generate_patch(original_code, updated_code)

    patch_id = hashlib.sha256(
        (req.file_path + req.instruction).encode()
    ).hexdigest()[:16]

    _pending_patches[patch_id] = {
        "file": req.file_path,
        "updated_code": updated_code,
    }

    return {
        "patch_id": patch_id,
        "diff": diff,
        "message": "Review the patch and approve to apply.",
    }


@app.post("/apply-restore")
def apply_restore(req: RestoreRequest):
    if not getattr(revert_engine, "repo", None):
        return {"status": "failed", "message": "Repository not loaded."}
    try:
        prev_code, err = revert_engine.get_previous_function_version(
            req.file_path,
            req.function_name,
        )
        if err or not prev_code:
            return {"status": "failed", "message": err or "Previous version not found."}

        original_code = patch_engine.read_file(req.file_path)
        if not original_code:
            return {"status": "failed", "message": "Could not read file."}

        backup_path = req.file_path + ".bak"
        try:
            shutil.copy2(req.file_path, backup_path)
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Failed to create backup: {str(e)}",
            }

        updated_code = ai_modifier.merge_function(
            original_code,
            req.function_name,
            prev_code,
        )
        success, msg = patch_engine.apply_patch(
            req.file_path,
            updated_code,
        )
        return {
            "status": "applied" if success else "failed",
            "message": msg,
            "backup": backup_path if success else None,
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Restore failed: {str(e)}",
        }