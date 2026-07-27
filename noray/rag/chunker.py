import re
from typing import Any


class BaseChunker:
    def chunk(self, text: str) -> list[str]:
        raise NotImplementedError

class RecursiveCharacterChunker(BaseChunker):
    """Chunks text recursively trying delimiters from paragraphs to sentences to words."""
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.delimiters = ["\n\n", "\n", ". ", " ", ""]

    def chunk(self, text: str) -> list[str]:
        return self._split_text(text, self.delimiters)

    def _split_text(self, text: str, separators: list[str]) -> list[str]:
        final_chunks = []
        # Get the first separator to try
        if not separators:
            return [text]

        separator = separators[0]
        next_separators = separators[1:]

        # Split text by separator
        if separator:
            splits = text.split(separator)
        else:
            splits = list(text)

        current_doc = []
        current_len = 0

        for s in splits:
            s_len = len(s)
            if current_len + s_len > self.chunk_size:
                if current_doc:
                    joined = separator.join(current_doc)
                    if len(joined) > self.chunk_size and next_separators:
                        # Sub-split the overflow block using next separators
                        final_chunks.extend(self._split_text(joined, next_separators))
                    else:
                        final_chunks.append(joined)

                    # Manage overlap: Keep last elements of current doc that fit within overlap limit
                    overlap_doc = []
                    overlap_len = 0
                    for d in reversed(current_doc):
                        if overlap_len + len(d) <= self.chunk_overlap:
                            overlap_doc.insert(0, d)
                            overlap_len += len(d)
                        else:
                            break
                    current_doc = overlap_doc
                    current_len = overlap_len

            current_doc.append(s)
            current_len += s_len

        if current_doc:
            joined = separator.join(current_doc)
            final_chunks.append(joined)

        return [c.strip() for c in final_chunks if c.strip()]


class MarkdownChunker(BaseChunker):
    """Markdown header-aware chunker that groups text by markdown headers."""
    def __init__(self, chunk_size: int = 1500):
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        # Split by markdown headers
        lines = text.split("\n")
        chunks = []
        current_chunk = []
        current_len = 0

        for line in lines:
            # Check for header indicator
            if re.match(r"^#{1,6}\s+", line):
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = []
                    current_len = 0

            line_len = len(line)
            if current_len + line_len > self.chunk_size and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_len = line_len
            else:
                current_chunk.append(line)
                current_len += line_len

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return [c.strip() for c in chunks if c.strip()]


class CodeChunker(BaseChunker):
    """Code-aware chunker that keeps function/class boundaries together for programming files."""
    def __init__(self, chunk_size: int = 1200):
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        # Simple logical splitting for Python/JS by class/def block matching
        lines = text.split("\n")
        chunks = []
        current_chunk = []
        current_len = 0

        for line in lines:
            # Match top level python/js class or function definitions
            if re.match(r"^(def\s+|class\s+|function\s+|const\s+\w+\s*=\s*\([^)]*\)\s*=>|async\s+function)", line):
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = []
                    current_len = 0

            line_len = len(line)
            if current_len + line_len > self.chunk_size and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_len = line_len
            else:
                current_chunk.append(line)
                current_len += line_len

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return [c.strip() for c in chunks if c.strip()]


class SemanticChunker(BaseChunker):
    """Splits document based on semantic distance (embeddings distance) between adjacent sentences."""
    def __init__(self, embedding_model=None, threshold_percentile: float = 85.0):
        self.embedding_model = embedding_model
        self.threshold_percentile = threshold_percentile
        self.fallback_chunker = RecursiveCharacterChunker(chunk_size=800, chunk_overlap=150)

    def chunk(self, text: str) -> list[str]:
        # Split into sentences using a regex (handles punctuation and spacing)
        sentences = re.split(r"(?<=[.!?])\s+", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= 1:
            return sentences

        if not self.embedding_model:
            # No embedding model provided, use lexical/recursive fallback
            return self.fallback_chunker.chunk(text)

        try:
            # Generate embeddings for each sentence
            embeddings = self.embedding_model.embed(sentences)

            # Compute cosine similarities between consecutive sentences
            import numpy as np
            similarities = []
            for i in range(len(embeddings) - 1):
                vec1 = np.array(embeddings[i])
                vec2 = np.array(embeddings[i+1])
                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)
                if norm1 == 0 or norm2 == 0:
                    sim = 0.0
                else:
                    sim = float(np.dot(vec1, vec2) / (norm1 * norm2))
                similarities.append(sim)

            # Define cutoff threshold based on percentile of distances
            distances = [1.0 - s for s in similarities]
            if not distances:
                return [text]

            threshold = float(np.percentile(distances, self.threshold_percentile))

            chunks = []
            current_chunk = [sentences[0]]

            for i, distance in enumerate(distances):
                sentence = sentences[i + 1]
                if distance > threshold:
                    # Break point, write chunk and start new one
                    chunks.append(" ".join(current_chunk))
                    current_chunk = [sentence]
                else:
                    current_chunk.append(sentence)

            if current_chunk:
                chunks.append(" ".join(current_chunk))

            return chunks
        except Exception:
            # Fall back to recursive chunker on embedding errors
            return self.fallback_chunker.chunk(text)


def select_and_chunk(text: str, filename: str, embedding_model=None) -> list[dict[str, Any]]:
    """Automatically selects the best chunking strategy based on file type."""
    ext = filename.split(".")[-1].lower()

    if ext in ["md", "markdown"]:
        chunker = MarkdownChunker()
        strategy = "markdown"
    elif ext in ["py", "js", "ts", "tsx", "jsx", "cpp", "go", "rs", "java"]:
        chunker = CodeChunker()
        strategy = "code"
    elif embedding_model is not None:
        chunker = SemanticChunker(embedding_model)
        strategy = "semantic"
    else:
        chunker = RecursiveCharacterChunker()
        strategy = "recursive"

    chunk_strings = chunker.chunk(text)

    # Format chunks with indexing metadata
    result = []
    for idx, content in enumerate(chunk_strings):
        result.append({
            "chunk_index": idx,
            "content": content,
            "length": len(content),
            "strategy": strategy
        })
    return result
