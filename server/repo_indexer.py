import os
import time
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from ast_chunker import ast_chunk_file
print("REPO INDEXER LOADED FROM:", __file__)
model = SentenceTransformer("all-MiniLM-L6-v2")


class RepoIndexer:
    def __init__(self):
        self.chunks = []
        self.metadata = []
        self.index = None
        self.file_count = 0
        self.files = []

    def scan_repo(self, repo_path):
        self.chunks = []
        self.metadata = []
        self.file_count = 0
        self.files = []

        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith((".py", ".js", ".ts", ".html", ".css", ".jsx")):
                    file_path = os.path.join(root, file)
                    self.file_count += 1
                    self._process_file(file_path)

    def _process_file(self, path):
        chunks = ast_chunk_file(path)
        self.files.append(path)

        print("Processing:", path)
        print("Chunks found:", len(chunks))

        # 🔥 Fallback if AST returns nothing
        if not chunks:
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                chunks = [{
                    "text": content,
                    "start_line": 1,
                    "end_line": content.count("\n") + 1,
                    "type": "full_file_fallback"
                }]

                print("Fallback applied for:", path)

            except Exception as e:
                print("Failed to read file:", path, str(e))
                return

        for chunk in chunks:
            text = chunk["text"].strip()
            if not text:
                continue

            self.chunks.append(text)
            self.metadata.append(
                {
                    "file": path,
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                    "type": chunk.get("type", "chunk"),
                }
            )

    def build_index(self):
        if not self.chunks:
            print("No chunks to index.")
            return

        print("Building index with", len(self.chunks), "chunks")

        embeddings = model.encode(self.chunks, show_progress_bar=True)
        dim = embeddings.shape[1]

        self.index = faiss.IndexFlatL2(dim)
        self.index.add(np.array(embeddings))

        print("Index built successfully.")

    def search(self, query, k=5):
        if self.index is None:
            print("Index is None. Search aborted.")
            return [], 0, 0

        start_time = time.time()

        q_emb = model.encode([query])
        distances, indices = self.index.search(np.array(q_emb), k)

        search_time = time.time() - start_time

        results = []
        seen = set()

        for rank, idx in enumerate(indices[0]):
            if idx < 0:
                continue

            meta = self.metadata[idx]
            key = (meta["file"], meta["start_line"])

            if key in seen:
                continue
            seen.add(key)

            confidence = float(1 / (1 + distances[0][rank]))

            results.append(
                {
                    "file": meta["file"],
                    "line": meta["start_line"],
                    "end_line": meta["end_line"],
                    "chunk_type": meta.get("type"),
                    "confidence": round(confidence, 4),
                    "snippet": self.chunks[idx][:400],
                }
            )

        return results, search_time, self.file_count