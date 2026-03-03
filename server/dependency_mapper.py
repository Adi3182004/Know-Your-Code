import os
import re
from collections import defaultdict


class DependencyMapper:
    def __init__(self):
        self.import_graph = defaultdict(set)
        self.symbol_usage = defaultdict(set)
        self.function_defs = defaultdict(set)
        self.function_calls = defaultdict(set)
        self.repo_path = None

    def scan_repo(self, repo_path: str):
        self.repo_path = repo_path
        self.import_graph.clear()
        self.symbol_usage.clear()
        self.function_defs.clear()
        self.function_calls.clear()

        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith((".py", ".js", ".ts", ".jsx")):
                    path = os.path.join(root, file)
                    self._process_file(path)

    def _process_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return

        self._extract_imports(path, content)
        self._extract_symbol_usage(path, content)
        self._extract_functions(path, content)
        self._extract_calls(path, content)

    def _extract_imports(self, path: str, content: str):
        py_imports = re.findall(
            r"^\s*(?:from\s+(\S+)\s+import|import\s+(\S+))",
            content,
            re.MULTILINE,
        )

        js_imports = re.findall(
            r'import\s+.*?from\s+[\'"](.+?)[\'"]',
            content,
        )

        require_imports = re.findall(
            r"require\(['\"](.+?)['\"]\)",
            content,
        )

        for grp in py_imports:
            mod = grp[0] or grp[1]
            if mod:
                self.import_graph[path].add(mod)

        for mod in js_imports:
            self.import_graph[path].add(mod)

        for mod in require_imports:
            self.import_graph[path].add(mod)

    def _extract_symbol_usage(self, path: str, content: str):
        words = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", content)
        for word in set(words):
            self.symbol_usage[word].add(path)

    def _extract_functions(self, path: str, content: str):
        func_patterns = [
            r"def\s+(\w+)\s*\(",
            r"function\s+(\w+)\s*\(",
            r"const\s+(\w+)\s*=\s*\(",
        ]

        for pattern in func_patterns:
            for fn in re.findall(pattern, content):
                self.function_defs[path].add(fn)

    def _extract_calls(self, path: str, content: str):
        call_pattern = r"(\w+)\s*\("
        for fn in re.findall(call_pattern, content):
            self.function_calls[path].add(fn)

    def find_related_files(self, file_path: str, limit: int = 5):
        related = set()

        imports = self.import_graph.get(file_path, set())
        related.update(imports)

        file_funcs = self.function_defs.get(file_path, set())

        for other, calls in self.function_calls.items():
            if file_funcs & calls:
                related.add(other)

        return list(related)[:limit]

    def find_symbol_references(self, symbol: str, limit: int = 10):
        return list(self.symbol_usage.get(symbol, []))[:limit]

    def get_callers(self, function_name: str):
        callers = []
        for file, calls in self.function_calls.items():
            if function_name in calls:
                callers.append(file)
        return callers

    def is_function_used(self, function_name: str):
        return len(self.get_callers(function_name)) > 0