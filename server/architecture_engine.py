import os
from collections import defaultdict


class ArchitectureEngine:
    def __init__(self):
        self.repo_path = None

    def load_repo(self, repo_path: str):
        self.repo_path = repo_path

    def summarize(self):
        if not self.repo_path:
            return "Repository not initialized."

        file_types = defaultdict(int)
        entry_points = []

        for root, _, files in os.walk(self.repo_path):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                file_types[ext] += 1

                if f.lower() in ("main.py", "index.js", "app.js"):
                    entry_points.append(os.path.join(root, f))

        parts = []

        parts.append("Repository Architecture Overview:\n")

        if entry_points:
            parts.append(
                f"• Entry points detected: {len(entry_points)} file(s)"
            )
        else:
            parts.append("• No clear entry point detected")

        parts.append(
            f"• Primary file types: {dict(file_types)}"
        )

        parts.append(
            "• The repository appears to be a lightweight web/code project "
            "with logic distributed across the detected files."
        )

        return "\n".join(parts)