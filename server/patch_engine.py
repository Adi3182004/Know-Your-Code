import difflib
import os


class PatchEngine:
    def generate_patch(self, original_code: str, updated_code: str):
        diff = difflib.unified_diff(
            original_code.splitlines(keepends=True),
            updated_code.splitlines(keepends=True),
            fromfile="original",
            tofile="updated",
        )
        return "".join(diff)

    def apply_patch(self, file_path: str, new_code: str):
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_code)
            return True, "Patch applied successfully."
        except Exception as e:
            return False, str(e)

    def read_file(self, file_path: str):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""