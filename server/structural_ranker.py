import math


class StructuralRanker:
    def score(self, result: dict):
        score = 0.0

        if result.get("symbol"):
            score += 0.15

        callers = result.get("callers") or []
        depth_boost = min(len(callers) * 0.03, 0.15)
        score += depth_boost

        if result.get("is_used"):
            score += 0.08

        related = result.get("related_files") or []
        importance = min(len(related) * 0.02, 0.12)
        score += importance

        return score