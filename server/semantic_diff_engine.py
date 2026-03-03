import re
import os
from git import Repo


class SemanticDiffEngine:
    """Engine for analyzing semantic changes in code across git history."""

    def __init__(self):
        self.repo = None
        self.repo_path = None
        self.repo_url = None

    def load_repo(self, repo_path: str):
        """
        Load a git repository for analysis.
        
        Args:
            repo_path: Path to the repository
        """
        try:
            self.repo = Repo(repo_path)
            self.repo_path = os.path.abspath(repo_path)
            self._extract_repo_url()
        except Exception:
            self.repo = None
            self.repo_url = None

    def _extract_repo_url(self):
        """Extract repository URL from git remote origin."""
        try:
            if self.repo and "origin" in self.repo.remotes:
                self.repo_url = self.repo.remotes.origin.url
            else:
                self.repo_url = self._get_repo_name()
        except Exception:
            self.repo_url = None

    def _format_commit_datetime(self, commit) -> str:
        """
        Format commit datetime in readable format.
        
        Args:
            commit: GitPython commit object
            
        Returns:
            Formatted datetime string (YYYY-MM-DD HH:MM:SS) or empty string on error
        """
        try:
            dt = commit.committed_datetime
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return ""

    def _get_branch_name(self) -> str:
        """
        Get current branch name safely.
        
        Returns:
            Branch name or "unknown" if unable to determine
        """
        try:
            return self.repo.active_branch.name
        except Exception:
            return "unknown"

    def _get_repo_name(self) -> str:
        """
        Get repository name from working directory.
        
        Returns:
            Repo name or "unknown" if unable to determine
        """
        try:
            return os.path.basename(self.repo.working_tree_dir)
        except Exception:
            return "unknown"

    def find_function_history(
        self,
        file_path: str,
        function_name: str,
        max_commits: int = 10,
    ):
        """
        Find git history for a specific function in a file.
        
        Tracks semantic changes to a function across git commits,
        including author, date, branch, repository info, and detailed
        change summaries.
        
        Args:
            file_path: Path to the file
            function_name: Name of the function to track
            max_commits: Maximum number of commits to retrieve (default: 10)
            
        Returns:
            List of dicts with commit metadata and change summary, max 5 entries
        """
        if not self.repo:
            return []

        try:
            abs_file = os.path.abspath(file_path)
            rel_path = os.path.relpath(abs_file, self.repo_path)
        except Exception:
            rel_path = file_path

        history = []
        branch_name = self._get_branch_name()
        repo_url = self.repo_url or "repository"

        try:
            commits = list(
                self.repo.iter_commits(paths=rel_path, max_count=max_commits)
            )
        except Exception:
            return history

        for commit in commits:
            if not commit.parents:
                continue

            try:
                diffs = commit.diff(
                    commit.parents[0],
                    paths=rel_path,
                    create_patch=True,
                )
            except Exception:
                continue

            for d in diffs:
                try:
                    patch = d.diff.decode(errors="ignore")
                except Exception:
                    continue

                if function_name in patch:
                    history.append(
                        {
                            "commit": commit.hexsha[:8],
                            "author": commit.author.name,
                            "date": self._format_commit_datetime(commit),
                            "branch": branch_name,
                            "repo": repo_url,
                            "message": commit.message.strip(),
                            "summary": self._summarize_patch(
                                patch, function_name
                            ),
                        }
                    )

        return history[:5]

    def _summarize_patch(self, patch: str, fn: str) -> str:
        """
        Generate a human-readable summary of changes in a patch.
        
        Analyzes unified diff format to extract added/removed lines
        and provides a concise summary with examples.
        
        Args:
            patch: Unified diff patch string
            fn: Function name being analyzed
            
        Returns:
            Summary string describing the changes
        """
        added_lines = []
        removed_lines = []

        for line in patch.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                added_lines.append(line[1:].strip())
            elif line.startswith("-") and not line.startswith("---"):
                removed_lines.append(line[1:].strip())

        added_count = len(added_lines)
        removed_count = len(removed_lines)

        if added_count == 0 and removed_count == 0:
            return f"Function '{fn}' was touched but no functional changes detected."

        summary_parts = []

        if added_count:
            preview = added_lines[:1]
            summary_parts.append(
                f"{added_count} line(s) added"
                + (f" (e.g., `{preview[0]}`)" if preview else "")
            )

        if removed_count:
            preview = removed_lines[:1]
            summary_parts.append(
                f"{removed_count} line(s) removed"
                + (f" (e.g., `{preview[0]}`)" if preview else "")
            )

        change_summary = ", ".join(summary_parts)

        return f"Function '{fn}' changed: {change_summary}."

    def get_file_history(self, file_path: str, max_commits: int = 10):
        """
        Get complete git history for a file.
        
        Args:
            file_path: Path to the file
            max_commits: Maximum number of commits to retrieve
            
        Returns:
            List of dicts with commit metadata for the file
        """
        if not self.repo:
            return []

        try:
            abs_file = os.path.abspath(file_path)
            rel_path = os.path.relpath(abs_file, self.repo_path)
        except Exception:
            rel_path = file_path

        history = []
        branch_name = self._get_branch_name()
        repo_url = self.repo_url or "repository"

        try:
            commits = list(
                self.repo.iter_commits(paths=rel_path, max_count=max_commits)
            )
        except Exception:
            return history

        for commit in commits:
            history.append(
                {
                    "commit": commit.hexsha[:8],
                    "author": commit.author.name,
                    "date": self._format_commit_datetime(commit),
                    "branch": branch_name,
                    "repo": repo_url,
                    "message": commit.message.strip(),
                }
            )

        return history[:10]

    def get_file_blame(self, file_path: str):
        """
        Get blame information for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dict with blame statistics and recent contributors
        """
        if not self.repo:
            return {}

        try:
            abs_file = os.path.abspath(file_path)
            rel_path = os.path.relpath(abs_file, self.repo_path)
        except Exception:
            rel_path = file_path

        try:
            blame = self.repo.blame("HEAD", rel_path)
            authors = {}
            for commit, lines in blame:
                author = commit.author.name
                authors[author] = authors.get(author, 0) + len(lines)
            
            return {
                "total_lines": sum(len(lines) for _, lines in blame),
                "contributors": authors,
                "primary_author": max(authors.items(), key=lambda x: x[1])[0]
                if authors
                else "unknown",
            }
        except Exception:
            return {}

    def get_diff_summary(self, file_path: str):
        """
        Get summary of recent changes to a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dict with change statistics
        """
        if not self.repo:
            return {}

        try:
            abs_file = os.path.abspath(file_path)
            rel_path = os.path.relpath(abs_file, self.repo_path)
        except Exception:
            rel_path = file_path

        try:
            latest_commit = list(
                self.repo.iter_commits(paths=rel_path, max_count=1)
            )
            if not latest_commit:
                return {}

            commit = latest_commit[0]
            if not commit.parents:
                return {"status": "initial_commit"}

            diffs = commit.diff(
                commit.parents[0],
                paths=rel_path,
                create_patch=True,
            )

            total_added = 0
            total_removed = 0

            for d in diffs:
                try:
                    patch = d.diff.decode(errors="ignore")
                    for line in patch.splitlines():
                        if line.startswith("+") and not line.startswith("+++"):
                            total_added += 1
                        elif line.startswith("-") and not line.startswith("---"):
                            total_removed += 1
                except Exception:
                    pass

            return {
                "latest_commit": commit.hexsha[:8],
                "latest_author": commit.author.name,
                "latest_date": self._format_commit_datetime(commit),
                "lines_added": total_added,
                "lines_removed": total_removed,
            }
        except Exception:
            return {}

    def get_commit_patch(
        self, file_path: str, function_name: str, max_commits: int = 3
    ):
        """
        Get patch information for a specific function across commits.

        Retrieves unified diff patches for a given function from the most
        recent commits, useful for detailed review of changes to specific
        functions.

        Args:
            file_path: Path to the file
            function_name: Name of the function to track
            max_commits: Maximum number of commits to retrieve (default: 3)

        Returns:
            List of dicts with commit metadata and patch content (max 1200 chars per patch)
        """
        if not self.repo:
            return []

        try:
            abs_file = os.path.abspath(file_path)
            rel_path = os.path.relpath(abs_file, self.repo_path)
        except Exception:
            rel_path = file_path

        patches = []

        try:
            commits = list(
                self.repo.iter_commits(paths=rel_path, max_count=max_commits)
            )
        except Exception:
            return patches

        for commit in commits:
            if not commit.parents:
                continue

            try:
                diffs = commit.diff(
                    commit.parents[0],
                    paths=rel_path,
                    create_patch=True,
                )
            except Exception:
                continue

            for d in diffs:
                try:
                    patch = d.diff.decode(errors="ignore")
                except Exception:
                    continue

                if function_name in patch:
                    patches.append(
                        {
                            "commit": commit.hexsha[:8],
                            "author": commit.author.name,
                            "date": self._format_commit_datetime(commit),
                            "patch": patch[:1200],
                        }
                    )

        return patches