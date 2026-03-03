import os
from tree_sitter import Language, Parser
import tree_sitter_javascript as ts_js

JS_LANGUAGE = Language(ts_js.language())

class JSASTParser:
    def __init__(self):
        self.parser = Parser()
        self.parser.language = JS_LANGUAGE
        self.function_defs = {}
        self.function_calls = {}

    def scan_repo(self, repo_path: str):
        self.function_defs.clear()
        self.function_calls.clear()

        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith((".js", ".ts", ".jsx")):
                    path = os.path.join(root, file)
                    self._scan_file(path)

    def _scan_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
        except:
            return

        tree = self.parser.parse(bytes(code, "utf8"))
        root = tree.root_node

        self.function_defs[path] = set()
        self.function_calls[path] = set()

        self._walk_tree(root, code, path)

    def _walk_tree(self, node, code: str, path: str):
        # ---------- function declarations ----------
        if node.type in ("function_declaration", "method_definition"):
            name_node = node.child_by_field_name("name")
            if name_node:
                fn_name = code[name_node.start_byte:name_node.end_byte]
                self.function_defs[path].add(fn_name)

        # ---------- call expressions ----------
        if node.type == "call_expression":
            fn_node = node.child_by_field_name("function")
            if fn_node:
                fn_name = code[fn_node.start_byte:fn_node.end_byte]
                self.function_calls[path].add(fn_name)

        for child in node.children:
            self._walk_tree(child, code, path)

    # 🔥 API methods

    def get_definition(self, function_name: str):
        files = []
        for file, funcs in self.function_defs.items():
            if function_name in funcs:
                files.append(file)
        return files

    def get_call_sites(self, function_name: str):
        files = []
        for file, calls in self.function_calls.items():
            if function_name in calls:
                files.append(file)
        return files