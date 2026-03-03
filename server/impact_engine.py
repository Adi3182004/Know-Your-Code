from dependency_mapper import DependencyMapper
from ast_js_parser import JSASTParser


class ImpactEngine:
    def __init__(self, dep_mapper: DependencyMapper, js_ast: JSASTParser):
        self.dep_mapper = dep_mapper
        self.js_ast = js_ast

    def analyze_function_impact(self, function_name: str):
        callers = self.dep_mapper.get_callers(function_name)
        is_used = self.dep_mapper.is_function_used(function_name)

        ast_defs = self.js_ast.get_definition(function_name)
        ast_calls = self.js_ast.get_call_sites(function_name)

        risk = self._compute_risk(callers, is_used)

        return {
            "function": function_name,
            "is_used": is_used,
            "impact_count": len(callers),
            "risk_level": risk,
            "callers": callers[:10],
            "defined_in": ast_defs[:5],
            "call_sites": ast_calls[:10],
        }

    def _compute_risk(self, callers, is_used):
        if not is_used:
            return "LOW"

        if len(callers) >= 5:
            return "HIGH"

        if len(callers) >= 2:
            return "MEDIUM"

        return "LOW"