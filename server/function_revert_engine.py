import re
import os
from git import Repo


class FunctionRevertEngine:
    def __init__(self):
        self.repo = None
        self.repo_path = None

    def load_repo(self, repo_path: str):
        try:
            self.repo_path = os.path.abspath(repo_path)
            self.repo = Repo(self.repo_path)
            print("✅ REVERT ENGINE LOADED:", self.repo_path)
        except Exception as e:
            print("❌ REVERT LOAD FAILED:", str(e))
            self.repo = None

    def _to_relative_path(self, file_path: str):
        try:
            abs_file = os.path.abspath(file_path)
            rel_path = os.path.relpath(abs_file, self.repo_path)
            return rel_path.replace("\\", "/")
        except Exception:
            return None

    def _extract_function(self, content: str, function_name: str):
        patterns = [
            rf"function\s+{function_name}\s*\([^)]*\)\s*\{{[\s\S]*?\}}",
            rf"def\s+{function_name}\s*\([^)]*\):[\s\S]*?(?=\n\S|\Z)",
        ]

        for p in patterns:
            m = re.search(p, content)
            if m:
                return m.group(0)

        return None

    def get_previous_function_version(self, file_path: str, function_name: str):
        if not self.repo:
            return None, "Repository not loaded."

        rel_path = self._to_relative_path(file_path)
        if not rel_path:
            return None, "Path normalization failed."

        try:
            commits = list(self.repo.iter_commits(paths=rel_path, max_count=20))
        except Exception as e:
            return None, f"Failed to read git history: {str(e)}"

        if len(commits) <= 1:
            return None, "No previous version found."

        for commit in commits[1:]:
            try:
                blob = commit.tree / rel_path
                content = blob.data_stream.read().decode(errors="ignore")
                fn_code = self._extract_function(content, function_name)
                if fn_code:
                    return fn_code, None
            except Exception:
                continue

        return None, "No previous version found."