import os
from git import Repo, GitCommandError


class HistoryEngine:
    def __init__(self):
        self.repo = None
        self.repo_path = None

    def load_repo(self, repo_path: str):
        try:
            self.repo = Repo(repo_path)
            self.repo_path = repo_path
        except Exception:
            self.repo = None
            self.repo_path = None

    # =========================
    # REPO-LEVEL HISTORY
    # =========================
    def get_repo_history(self, max_commits: int = 5):
        if not self.repo:
            return []

        try:
            commits = list(self.repo.iter_commits(max_count=max_commits))

            history = []

            for c in commits:
                history.append(
                    {
                        "commit": c.hexsha[:8],
                        "author": c.author.name,
                        "date": c.committed_datetime.isoformat(),
                        "message": c.message.strip(),
                    }
                )

            return history

        except Exception:
            return []

    # =========================
    # FILE BLAME
    # =========================
    def get_file_blame(self, file_path: str, max_lines: int = 10):
        if not self.repo:
            return {"error": "Git repo not loaded"}

        try:
            rel_path = os.path.relpath(file_path, self.repo_path)
            blame_info = self.repo.blame("HEAD", rel_path)

            results = []

            for commit, lines in blame_info[:max_lines]:
                results.append(
                    {
                        "author": commit.author.name,
                        "commit": commit.hexsha[:8],
                        "date": commit.committed_datetime.isoformat(),
                        "message": commit.message.strip(),
                    }
                )

            return results

        except GitCommandError:
            return {"error": "Blame failed"}
        except Exception as e:
            return {"error": str(e)}

    # =========================
    # FILE HISTORY
    # =========================
    def get_file_history(self, file_path: str, max_commits: int = 5):
        if not self.repo:
            return []

        try:
            rel_path = os.path.relpath(file_path, self.repo_path)

            commits = list(
                self.repo.iter_commits(paths=rel_path, max_count=max_commits)
            )

            history = []

            for c in commits:
                history.append(
                    {
                        "commit": c.hexsha[:8],
                        "author": c.author.name,
                        "date": c.committed_datetime.isoformat(),
                        "message": c.message.strip(),
                    }
                )

            return history

        except Exception:
            return []

    # =========================
    # DIFF SUMMARY
    # =========================
    def get_diff_summary(self, file_path: str):
        if not self.repo:
            return "No git repo"

        try:
            rel_path = os.path.relpath(file_path, self.repo_path)
            commits = list(self.repo.iter_commits(paths=rel_path, max_count=2))

            if len(commits) < 2:
                return "No diff available"

            diff = commits[0].diff(commits[1], paths=rel_path)

            added = 0
            removed = 0

            for d in diff:
                if d.diff:
                    text = d.diff.decode(errors="ignore")
                    added += text.count("\n+")
                    removed += text.count("\n-")

            return f"Added lines: {added}, Removed lines: {removed}"

        except Exception:
            return "Diff analysis failed"