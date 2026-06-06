"""
Vector Memory
=============
Long-term memory store using Pinecone vector database.
Allows the agent to recall results from similar past tasks.
"""

import hashlib
from typing import Optional
from ...config import settings
from ...utils.logger import get_logger

logger = get_logger(__name__)


class VectorMemory:
    """
    Long-term semantic memory using Pinecone.
    Stores task → result pairs and retrieves similar past results.

    Falls back gracefully if Pinecone is not configured.
    """

    def __init__(self):
        self._index = None
        self._embeddings = None
        self._enabled = False
        self._init()

    def _init(self):
        """Initialize Pinecone connection."""
        try:
            if not settings.PINECONE_API_KEY:
                logger.info("Pinecone not configured — long-term memory disabled")
                return

            from pinecone import Pinecone
            from langchain_openai import OpenAIEmbeddings

            pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            self._index = pc.Index(settings.PINECONE_INDEX)
            self._embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=settings.OPENAI_API_KEY,
            )
            self._enabled = True
            logger.info("Vector memory (Pinecone) initialized")

        except Exception as e:
            logger.warning(f"Vector memory init failed: {e}. Running without long-term memory.")

    async def store(self, task: str, result: str):
        """Store a task-result pair in the vector store."""
        if not self._enabled:
            return

        try:
            task_id = hashlib.md5(task.encode()).hexdigest()
            embedding = self._embeddings.embed_query(task)
            self._index.upsert(vectors=[{
                "id": task_id,
                "values": embedding,
                "metadata": {
                    "task": task[:500],
                    "result": result[:1000],
                }
            }])
            logger.info(f"Stored memory for task: {task[:40]}...")
        except Exception as e:
            logger.warning(f"Memory store failed: {e}")

    async def search(self, task: str, top_k: int = 3) -> Optional[str]:
        """Search for similar past tasks and return their results."""
        if not self._enabled:
            return None

        try:
            embedding = self._embeddings.embed_query(task)
            results = self._index.query(
                vector=embedding,
                top_k=top_k,
                include_metadata=True,
            )

            matches = results.get("matches", [])
            high_confidence = [m for m in matches if m.get("score", 0) > 0.85]

            if not high_confidence:
                return None

            context_parts = []
            for match in high_confidence[:2]:
                meta = match.get("metadata", {})
                context_parts.append(
                    f"Similar past task: \"{meta.get('task', '')[:100]}\" "
                    f"→ Result: {meta.get('result', '')[:300]}"
                )

            return "\n".join(context_parts) if context_parts else None

        except Exception as e:
            logger.warning(f"Memory search failed: {e}")
            return None
