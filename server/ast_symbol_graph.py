import ast
import os
from collections import defaultdict


class ASTSymbolGraph:
    def __init__(self):
        self.function_defs = defaultdict(list)
        self.function_calls = defaultdict(list)

    def scan_repo(self, repo_path: str):
        self.function_defs.clear()
        self.function_calls.clear()

        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    self._process_python_file(path)

    def _process_python_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
        except Exception:
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.function_defs[node.name].append({
                    "file": path,
                    "line": node.lineno,
                })

            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    self.function_calls[node.func.id].append({
                        "file": path,
                        "line": node.lineno,
                    })

    def get_definition(self, func_name: str):
        return self.function_defs.get(func_name, [])

    def get_call_sites(self, func_name: str):
        return self.function_calls.get(func_name, [])