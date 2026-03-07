from llm_phi3 import ask_phi3
import re


class AICodeModifier:

    def _try_simple_change(self, instruction: str, code: str):

        lowered = instruction.lower()

        interval_pattern = re.search(
            r'from\s+(\d+)\s*ms?\s+to\s+(\d+)\s*ms?',
            lowered
        )

        if "interval" in lowered and interval_pattern:
            old_val = interval_pattern.group(1)
            new_val = interval_pattern.group(2)

            updated = re.sub(
                rf"setInterval\(\s*autoColorChange\s*,\s*{old_val}\s*\)",
                f"setInterval(autoColorChange, {new_val})",
                code
            )

            if updated != code:
                return updated

        timeout_pattern = re.search(
            r'timeout.*from\s+(\d+)\s*ms?\s+to\s+(\d+)\s*ms?',
            lowered
        )

        if timeout_pattern:
            old_val = timeout_pattern.group(1)
            new_val = timeout_pattern.group(2)

            updated = code.replace(old_val, new_val)

            if updated != code:
                return updated

        return None


    def propose_change(self, instruction: str, original_code: str):

        simple = self._try_simple_change(instruction, original_code)

        if simple:
            return simple

        prompt = f"""
Modify the code according to instruction.

Rules:
Return ONLY the full updated code.
No markdown.
No explanations.
Preserve existing structure.

Instruction:
{instruction}

Code:
{original_code}
"""

        updated = ask_phi3(prompt)

        if not updated:
            return None

        updated = updated.strip()

        updated = updated.replace("```javascript", "")
        updated = updated.replace("```js", "")
        updated = updated.replace("```", "")

        if "Ollama error" in updated:
            return None

        if len(updated) < len(original_code) * 0.6:
            return None

        return updated


    def merge_function(self, original_code: str, function_name: str, new_function_code: str):

        pattern = rf"(function\s+{function_name}\s*[^)]*\s*\{{[\s\S]*?\}})"

        match = re.search(pattern, original_code)

        if not match:
            return original_code

        start = match.start()
        end = match.end()

        updated = (
            original_code[:start]
            + new_function_code.strip()
            + original_code[end:]
        )

        return updated