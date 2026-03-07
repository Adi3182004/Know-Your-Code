import difflib
import os
import subprocess
import shutil
import time
import glob


class PatchEngine:

    HISTORY_DIR = ".kyc_history"

    def generate_patch(self, original_code: str, updated_code: str):
        diff = difflib.unified_diff(
            original_code.splitlines(keepends=True),
            updated_code.splitlines(keepends=True),
            fromfile="original",
            tofile="updated",
        )
        return "".join(diff)

    def apply_patch(self, file_path: str, new_code: str, commit_message=None):
        try:

            if not os.path.exists(file_path):
                return False, "File does not exist."

            original_code = self.read_file(file_path)

            backup_path = file_path + ".bak"

            try:
                shutil.copy2(file_path, backup_path)
            except Exception:
                pass

            self._save_snapshot(file_path, original_code)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_code)

            if commit_message:
                self._commit_change(file_path, commit_message)

            return True, "Patch applied successfully."

        except Exception as e:
            return False, str(e)

    def read_file(self, file_path: str):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    def restore_from_snapshot(self, file_path: str):

        try:

            repo_dir = os.path.dirname(file_path)
            history_dir = os.path.join(repo_dir, self.HISTORY_DIR)

            filename = os.path.basename(file_path)

            pattern = os.path.join(history_dir, f"{filename}.*.snap")

            snapshots = sorted(glob.glob(pattern))

            if len(snapshots) == 0:
                return None, "No previous snapshot available."

            latest = snapshots[-1]

            with open(latest, "r", encoding="utf-8") as f:
                code = f.read()

            os.remove(latest)

            return code, None

        except Exception as e:
            return None, str(e)

    def _save_snapshot(self, file_path, code):

        try:

            repo_dir = os.path.dirname(file_path)

            history_dir = os.path.join(repo_dir, self.HISTORY_DIR)

            os.makedirs(history_dir, exist_ok=True)

            filename = os.path.basename(file_path)

            timestamp = int(time.time())

            snapshot_file = os.path.join(
                history_dir,
                f"{filename}.{timestamp}.snap"
            )

            with open(snapshot_file, "w", encoding="utf-8") as f:
                f.write(code)

        except Exception:
            pass

    def _commit_change(self, file_path: str, message: str):

        try:

            repo_dir = os.path.dirname(file_path)

            subprocess.run(
                ["git", "add", file_path],
                cwd=repo_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=repo_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

        except Exception:
            pass