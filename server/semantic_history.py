from git import Repo


class SemanticHistory:
    def __init__(self):
        self.repo = None

    def load(self, repo_path: str):
        try:
            self.repo = Repo(repo_path)
        except:
            self.repo = None

    def get_recent_changes(self, file_path: str, limit: int = 3):
        if not self.repo:
            return []

        rel_path = file_path.replace(
            self.repo.working_tree_dir + "\\", ""
        )

        commits = list(self.repo.iter_commits(paths=rel_path, max_count=limit))

        results = []
        for c in commits:
            results.append(
                {
                    "commit": c.hexsha[:8],
                    "author": c.author.name,
                    "summary": c.summary,
                }
            )

        return results