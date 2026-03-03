import difflib


class DeepDiffViewer:
    def generate(self, old_code: str, new_code: str):
        diff = difflib.unified_diff(
            old_code.splitlines(),
            new_code.splitlines(),
            lineterm="",
        )

        return "\n".join(diff)