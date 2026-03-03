import re
from git import Repo


class SurgicalReverter:
    def __init__(self):
        self.repo = None
        self.repo_path = None

    def load_repo(self, repo_path: str):
        try:
            self.repo = Repo(repo_path)
            self.repo_path = repo_path
        except Exception:
            self.repo = None

    def extract_function_from_commit(
        self,
        file_path: str,
        function_name: str,
        steps_back: int = 1,
    ):
        if not self.repo:
            return None

        try:
            rel_path = file_path.replace(self.repo_path + "\\", "")
            commits = list(self.repo.iter_commits(paths=rel_path))
        except Exception:
            return None

        if len(commits) <= steps_back:
            return None

        target_commit = commits[steps_back]

        try:
            blob = target_commit.tree / rel_path
            content = blob.data_stream.read().decode(errors="ignore")
        except Exception:
            return None

        pattern = rf"(function\s+{function_name}[\s\S]*?\n\}})"
        match = re.search(pattern, content)

        if match:
            return match.group(1)

        return None