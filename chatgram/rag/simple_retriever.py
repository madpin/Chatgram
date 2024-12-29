from typing import Optional, List
from core.interfaces import DocumentRetrieverInterface


class SimpleRetriever(DocumentRetrieverInterface):
    """A basic implementation of document retrieval (placeholder)."""

    def retrieve_documents(
        self, query: str, context: Optional[str] = None
    ) -> List[str]:
        """Retrieves documents based on a query (basic implementation).

        Args:
            query (str): The search query.
            context (Optional[str], optional): Additional context. Defaults to None.

        Returns:
            List[str]: A list of relevant document excerpts.
        """
        # Placeholder implementation (replace with actual document retrieval logic)
        sample_documents = {
            "doc1": "This is the first document. It talks about cats.",
            "doc2": "The second document is about dogs and their behavior.",
            "doc3": "This document discusses the history of computer science.",
        }

        if query.lower() in "cats":
            return [sample_documents["doc1"]]
        elif query.lower() in "dogs":
            return [sample_documents["doc2"]]
        elif query.lower() in "computer science":
            return [sample_documents["doc3"]]
        else:
            return []

        # Error handling:
        # - Handle cases where no relevant documents are found.

        # Performance considerations:
        # - This is a placeholder implementation with very basic retrieval logic.
        # - A real implementation would use more sophisticated techniques like TF-IDF,
        #   BM25, or semantic search using embeddings.
