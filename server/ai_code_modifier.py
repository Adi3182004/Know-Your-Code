from llm_phi3 import ask_phi3
import re


class AICodeModifier:
    def propose_change(self, question: str, code_snippet: str):
        prompt = f"""
You are a senior software engineer.

User request:
{question}

Existing code:
{code_snippet}

Task:
- Modify the code to satisfy the request
- Return ONLY the full updated code
- Do NOT add explanations
- Do NOT use markdown
"""
        updated = ask_phi3(prompt)
        return updated.strip()

    def merge_function(self, original_code: str, function_name: str, new_function_code: str):
        patterns = [
            rf"function\s+{function_name}\s*\([^)]*\)\s*\{{[\s\S]*?\}}",
            rf"def\s+{function_name}\s*\([^)]*\):[\s\S]*?(?=\n\S|\Z)",
        ]

        for p in patterns:
            if re.search(p, original_code):
                return re.sub(p, new_function_code, original_code)

        return original_code