class CrossFileReasoner:
    def __init__(self, dep_mapper, js_ast):
        self.dep_mapper = dep_mapper
        self.js_ast = js_ast

    # =====================================================
    # BASIC SYMBOL ANALYSIS
    # =====================================================
    def analyze_symbol(self, symbol: str):
        try:
            callers = self.js_ast.get_call_sites(symbol) or []
            defs = self.js_ast.get_definition(symbol) or []

            return {
                "definition_count": len(defs),
                "caller_count": len(callers),
                "risk_hint": self._risk_hint(len(callers)),
            }
        except Exception:
            return None

    # =====================================================
    # CONTEXT ANALYSIS
    # =====================================================
    def analyze_symbol_context(self, symbol: str, file_path: str):
        try:
            related = self.dep_mapper.find_related_files(file_path) or []
            callers = self.js_ast.get_call_sites(symbol) or []

            return {
                "related_files": related[:5],
                "call_sites": callers[:5],
            }
        except Exception:
            return {}

    # =====================================================
    # HUMAN SUMMARY
    # =====================================================
    def build_reasoning_summary(self, symbol: str, reasoning: dict):
        if not reasoning:
            return ""

        callers = reasoning.get("call_sites") or []
        related = reasoning.get("related_files") or []

        parts = []

        if callers:
            parts.append(
                f"Function '{symbol}' is invoked in {len(callers)} location(s)."
            )

        if related:
            parts.append(
                f"It is structurally connected to {len(related)} related file(s)."
            )

        return " ".join(parts)

    # =====================================================
    # IMPACT EXPLANATION
    # =====================================================
    def explain_impact(self, symbol: str):
        try:
            callers = self.js_ast.get_call_sites(symbol) or []

            if not callers:
                return "No cross-file dependencies detected."

            return (
                f"Cross-file analysis shows {len(callers)} dependent call site(s)."
            )
        except Exception:
            return None

    # =====================================================
    # INTERNAL RISK HEURISTIC
    # =====================================================
    def _risk_hint(self, caller_count: int):
        if caller_count >= 5:
            return "high"
        if caller_count >= 2:
            return "medium"
        return "low"