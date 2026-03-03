import os
from collections import defaultdict


class ArchitectureSummarizer:
    def summarize(self, repo_path: str):
        layers = defaultdict(int)
        entry_points = []

        for root, _, files in os.walk(repo_path):
            for f in files:
                path = os.path.join(root, f)

                if f in ("main.py", "app.py", "index.js", "server.js"):
                    entry_points.append(path)

                folder = os.path.basename(root)
                layers[folder] += 1

        sorted_layers = sorted(
            layers.items(), key=lambda x: x[1], reverse=True
        )

        return {
            "layers": sorted_layers[:6],
            "entry_points": entry_points[:5],
        }