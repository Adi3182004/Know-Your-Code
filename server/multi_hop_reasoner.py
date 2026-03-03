class MultiHopReasoner:
    def __init__(self, dep_mapper, js_ast):
        self.dep_mapper = dep_mapper
        self.js_ast = js_ast

    def trace_impact(self, function_name: str, max_depth: int = 3):
        visited = set()
        frontier = [function_name]
        graph = {}
        depth = 0

        while frontier and depth < max_depth:
            next_frontier = []

            for fn in frontier:
                if fn in visited:
                    continue

                visited.add(fn)

                callers = self.dep_mapper.get_callers(fn) or []
                graph[fn] = callers

                for c in callers:
                    base = self._extract_symbol_from_path(c)
                    if base and base not in visited:
                        next_frontier.append(base)

            frontier = next_frontier
            depth += 1

        total_impact = sum(len(v) for v in graph.values())

        return {
            "root_function": function_name,
            "depth_explored": depth,
            "impact_graph": graph,
            "total_affected_sites": total_impact,
        }

    def _extract_symbol_from_path(self, path: str):
        try:
            name = path.split("\\")[-1]
            return name.split(".")[0]
        except Exception:
            return None