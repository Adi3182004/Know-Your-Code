import re
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

MODEL = SentenceTransformer("all-MiniLM-L6-v2")


class QueryRouter:

    def __init__(self):

        self.intent_keywords = {

            "modify": [
                "change",
                "modify",
                "update",
                "edit",
                "replace",
                "increase",
                "decrease",
                "set interval",
                "set value",
                "fix code"
            ],

            "explain": [
                "explain",
                "describe",
                "what does",
                "how does",
                "clarify"
            ],

            "impact": [
                "impact",
                "affected",
                "dependency",
                "depends on",
                "who uses",
                "where is used"
            ],

            "architecture": [
                "architecture",
                "structure",
                "design",
                "modules",
                "components",
                "overview"
            ],

            "history_author": [
                "who modified",
                "who wrote",
                "who created",
                "blame",
                "author"
            ],

            "history_change": [
                "what changed",
                "show diff",
                "commit history",
                "version history",
                "repository history"
            ],

            "revert": [
                "revert",
                "restore",
                "rollback",
                "undo",
                "previous version"
            ]
        }

        self.intents = list(self.intent_keywords.keys())
        self.intent_embeddings = MODEL.encode(self.intents, convert_to_tensor=True)

    def classify(self, question: str):

        question_lower = question.lower()

        if "who modified" in question_lower or "blame" in question_lower:
            return "history_author"

        if "what changed" in question_lower or "show diff" in question_lower:
            return "history_change"

        if "restore" in question_lower or "revert" in question_lower:
            return "revert"

        if (
            "change" in question_lower
            or "modify" in question_lower
            or "update" in question_lower
            or "edit" in question_lower
            or "increase" in question_lower
            or "decrease" in question_lower
        ):
            return "modify"

        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword in question_lower:
                    return intent

        question_embedding = MODEL.encode(question, convert_to_tensor=True)

        scores = cos_sim(question_embedding, self.intent_embeddings)[0]

        best_idx = scores.argmax().item()
        best_score = scores[best_idx].item()

        if best_score > 0.55:
            return self.intents[best_idx]

        return "search"