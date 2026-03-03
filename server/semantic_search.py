import re
from repo_indexer import RepoIndexer
from reranker import rerank_results
from dependency_mapper import DependencyMapper
from history_engine import HistoryEngine
from ast_js_parser import JSASTParser
from impact_engine import ImpactEngine
from semantic_diff_engine import SemanticDiffEngine
from query_router import QueryRouter
from cache_layer import QueryCache
from cross_file_reasoner import CrossFileReasoner
from architecture_engine import ArchitectureEngine
from function_revert_engine import FunctionRevertEngine


# =========================================================
# FILE HINT EXTRACTION
# =========================================================

def _extract_file_from_question(question: str):
    match = re.search(
        r'([\w\-/\\]+\.(js|py|ts|css|html|jsx|tsx))',
        question,
        re.IGNORECASE
    )
    if match:
        return match.group(1)

    words = question.lower().split()
    for w in words:
        if w.endswith((".js", ".py", ".ts", ".css", ".html")):
            return w

    return None


# =========================================================
# GLOBAL ENGINES
# =========================================================

js_ast = JSASTParser()
history_engine = HistoryEngine()
dep_mapper = DependencyMapper()
indexer = RepoIndexer()
router = QueryRouter()
cache = QueryCache()
diff_engine = SemanticDiffEngine()
arch_engine = ArchitectureEngine()
impact_engine = ImpactEngine(dep_mapper, js_ast)
cross_reasoner = CrossFileReasoner(dep_mapper, js_ast)
revert_engine = FunctionRevertEngine()

_initialized = False
_repo_path = None


# =========================================================
# INIT
# =========================================================

def initialize(repo_path: str):
    global _initialized, _repo_path

    _repo_path = repo_path

    diff_engine.load_repo(repo_path)

    indexer.scan_repo(repo_path)
    indexer.build_index()

    history_engine.load_repo(repo_path)
    dep_mapper.scan_repo(repo_path)
    js_ast.scan_repo(repo_path)
    arch_engine.load_repo(repo_path)
    revert_engine.load_repo(repo_path)

    _initialized = True


# =========================================================
# FUNCTION NAME EXTRACTION
# =========================================================

def extract_function_name_from_snippet(snippet: str):
    patterns = [
        r"function\s+(\w+)",
        r"def\s+(\w+)",
        r"const\s+(\w+)\s*=\s*\(",
        r"(\w+)\s*=\s*\(.*?\)\s*=>",
    ]

    for p in patterns:
        m = re.search(p, snippet)
        if m:
            return m.group(1)

    return None


# =========================================================
# MAIN QUERY
# =========================================================

def query_code(question: str):
    try:
        if not _initialized:
            return {
                "results": [],
                "search_time": 0,
                "file_count": 0,
                "intent": "search",
            }

        cached = cache.get(question)
        if cached:
            return cached

        intent = router.classify(question)
        file_hint = _extract_file_from_question(question)

        # =====================================================
        # FILE-SPECIFIC HISTORY FAST PATH
        # =====================================================
        if intent in ("history_author", "history_change") and file_hint:

            for path in indexer.files:
                if path.lower().endswith(file_hint.lower()):

                    blame = history_engine.get_file_blame(path)
                    history = history_engine.get_file_history(path)
                    diff_summary = diff_engine.get_diff_summary(path)

                    response = {
                        "results": [{
                            "file": path,
                            "symbol": None,
                            "history": history,
                            "blame": blame,
                            "diff_summary": diff_summary,
                            "semantic_history": []
                        }],
                        "search_time": 0,
                        "file_count": indexer.file_count,
                        "intent": intent,
                    }

                    cache.set(question, response)
                    return response

        # =====================================================
        # IMPACT FAST PATH
        # =====================================================
        if intent == "impact":
            words = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", question)

            for w in words:
                impact = impact_engine.analyze_function_impact(w)

                if impact.get("defined_in") or impact.get("call_sites"):
                    response = {
                        "results": [],
                        "impact": impact,
                        "search_time": 0,
                        "file_count": indexer.file_count,
                        "intent": intent,
                    }
                    cache.set(question, response)
                    return response

        # =====================================================
        # ARCHITECTURE FAST PATH
        # =====================================================
        if intent == "architecture":
            summary = arch_engine.summarize()

            response = {
                "results": [],
                "architecture": summary,
                "search_time": 0,
                "file_count": indexer.file_count,
                "intent": intent,
            }

            cache.set(question, response)
            return response

        # =====================================================
        # FUNCTION REVERT FAST PATH
        # =====================================================
        if intent == "revert":
            words = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", question)

            target = words[-1] if words else None

            if target:
                results, _, _ = indexer.search(target)

                for r in results:
                    fn_name = extract_function_name_from_snippet(
                        r.get("snippet", "")
                    )

                    if fn_name == target:
                        prev_code, err = revert_engine.get_previous_function_version(
                            r["file"], target
                        )

                        response = {
                            "results": results[:1],
                            "revert": {
                                "function": target,
                                "previous_code": prev_code,
                                "error": err,
                                "file": r["file"],
                            },
                            "intent": intent,
                        }

                        cache.set(question, response)
                        return response

        # =====================================================
        # NORMAL SEMANTIC SEARCH
        # =====================================================
        results, search_time, file_count = indexer.search(question)

        cleaned = []
        seen = set()

        for r in results:
            key = (r["file"], r["line"])
            if key in seen:
                continue
            seen.add(key)

            snippet = r.get("snippet", "")
            fn_name = extract_function_name_from_snippet(snippet)

            # ================= SYMBOL ANALYSIS =================
            callers = []
            is_used = False
            cross_info = None
            reasoning = None

            if fn_name:
                callers = js_ast.get_call_sites(fn_name)
                is_used = len(callers) > 0
                cross_info = cross_reasoner.analyze_symbol(fn_name)
                
                # ================= REASONING ANALYSIS =================
                try:
                    if hasattr(cross_reasoner, "build_reasoning_summary"):
                        reasoning = cross_reasoner.build_reasoning_summary(question, cleaned)
                except Exception:
                    reasoning = None

            # ================= DEPENDENCY =================
            related = dep_mapper.find_related_files(r["file"])

            # ================= HISTORY =================
            blame = history_engine.get_file_blame(r["file"])
            history = history_engine.get_file_history(r["file"])
            diff_summary = diff_engine.get_diff_summary(r["file"])

            # ================= SEMANTIC FUNCTION HISTORY =================
            semantic_history = []
            if fn_name:
                semantic_history = diff_engine.find_function_history(
                    r["file"], fn_name
                )

            cleaned.append(
                {
                    "file": r["file"],
                    "line": r.get("line"),
                    "end_line": r.get("end_line"),
                    "chunk_type": r.get("chunk_type"),
                    "confidence": r.get("confidence"),
                    "snippet": snippet,
                    "related_files": related,
                    "callers": callers[:5],
                    "is_used": is_used,
                    "symbol": fn_name,
                    "cross_file_analysis": cross_info,
                    "blame": blame,
                    "history": history,
                    "diff_summary": diff_summary,
                    "semantic_history": semantic_history,
                    "reasoning": reasoning,
                }
            )

        # =====================================================
        # 🎯 RERANK
        # =====================================================
        cleaned = rerank_results(question, cleaned)

        response = {
            "results": cleaned,
            "search_time": search_time,
            "file_count": file_count,
            "intent": intent,
        }

        cache.set(question, response)
        return response

    except Exception as e:
        return {
            "results": [],
            "search_time": 0,
            "file_count": 0,
            "intent": "search",
            "error": str(e),
        }