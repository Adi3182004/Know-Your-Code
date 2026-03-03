from structural_ranker import StructuralRanker

struct_ranker = StructuralRanker()


def rerank_results(query: str, results: list):
    if not results:
        return results

    q = query.lower()

    for r in results:
        boost = 0.0

        snippet = (r.get("snippet") or "").lower()
        filename = (r.get("file") or "").lower()

        if q in snippet:
            boost += 0.2

        if r.get("chunk_type") == "function":
            boost += 0.08

        for word in q.split():
            if word in filename:
                boost += 0.05

        boost += struct_ranker.score(r)

        base = r.get("confidence") or 0
        r["confidence"] = min(1.0, base + boost)

    results.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    return results