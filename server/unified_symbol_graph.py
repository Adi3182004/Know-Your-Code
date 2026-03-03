class UnifiedSymbolGraph:
    def __init__(self, py_graph=None, js_graph=None):
        self.py_graph = py_graph
        self.js_graph = js_graph

    def get_definition(self, name: str):
        results = []

        if self.py_graph:
            results.extend(self.py_graph.get_definition(name))

        if self.js_graph:
            results.extend(self.js_graph.get_definition(name))

        return results

    def get_call_sites(self, name: str):
        results = []

        if self.py_graph:
            results.extend(self.py_graph.get_call_sites(name))

        if self.js_graph:
            results.extend(self.js_graph.get_call_sites(name))

        return results