from sentence_transformers import SentenceTransformer
import re


class QueryRouter:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        self.intent_keywords = {
            "search": [
                "find", "where", "what", "how", "show", "get", "list",
                "tell me", "look for", "search for", "locate"
            ],
            "explain": [
                "explain", "describe", "what does", "how does", "what is",
                "clarify", "understand", "what happens", "step through"
            ],
            "impact": [
                "impact", "affected", "dependency", "depends on", "uses",
                "called by", "calls", "references", "who uses", "where is used"
            ],
            "architecture": [
                "architecture", "structure", "overview", "design", "pattern",
                "organization", "modules", "components", "how organized"
            ],
            "history": [
                "history", "changed", "when", "who changed", "blame",
                "author", "commit", "git", "version", "evolution"
            ],
            "history_author": [
                "who", "author", "blame", "authored", "wrote", "created",
                "written by", "modified by"
            ],
            "history_change": [
                "changed", "diff", "commit", "version", "when changed",
                "what changed", "evolution"
            ],
            "revert": [
                "revert", "restore", "undo", "previous", "old version",
                "earlier version", "rollback", "go back"
            ]
        }

    def classify(self, question: str) -> str:
        """
        Classify the question intent using keyword matching and embeddings.
        """
        question_lower = question.lower()

        # =====================================================
        # KEYWORD-BASED FAST PATH
        # =====================================================
        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword in question_lower:
                    return intent

        # =====================================================
        # FALLBACK: EMBEDDING-BASED CLASSIFICATION
        # =====================================================
        intent_labels = list(self.intent_keywords.keys())
        intent_embeddings = self.model.encode(intent_labels, convert_to_tensor=True)

        question_embedding = self.model.encode(question, convert_to_tensor=True)

        from sentence_transformers.util import cos_sim

        similarities = cos_sim(question_embedding, intent_embeddings)[0]

        best_idx = similarities.argmax().item()
        best_intent = intent_labels[best_idx]
        best_score = similarities[best_idx].item()

        if best_score > 0.5:
            return best_intent

        return "search"