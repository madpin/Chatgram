from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from data.models import ChatInstance, Message, User


class ChatbotInterface(ABC):
    """Interface for chatbot implementations."""

    @abstractmethod
    def generate_message(
        self,
        chat_instance: "ChatInstance",
        user_message: str,
        user: "User",
        extra_info: Optional[dict] = None,
    ) -> str:
        """Generates a response to a user message.

        Args:
            chat_instance (ChatInstance): The chat instance object.
            user_message (str): The message sent by the user.
            user (User): The user object.
            extra_info (Optional[dict], optional): Additional information. Defaults to None.

        Returns:
            str: The generated response.
        """
        # Error handling:
        # - Implementations should handle potential errors like API timeouts,
        #   invalid requests, and resource limits.
        # - Consider raising custom exceptions for specific error conditions.

        # Performance considerations:
        # - Minimize the number of API calls to the language model.
        # - Use asynchronous operations if possible to avoid blocking the main thread.
        pass


from abc import ABC, abstractmethod
from typing import List, Optional


class DocumentRetrieverInterface(ABC):
    """Interface for document retrieval implementations (RAG)."""

    @abstractmethod
    def retrieve_documents(
        self, query: str, context: Optional[str] = None
    ) -> List[str]:
        """Retrieves relevant documents based on a query.

        Args:
            query (str): The search query.
            context (Optional[str], optional): Additional context for retrieval. Defaults to None.

        Returns:
            List[str]: A list of relevant document excerpts.
        """
        # Error handling:
        # - Implementations should handle cases where no relevant documents are found.
        # - Consider raising exceptions for errors related to document access or indexing.

        # Performance considerations:
        # - Optimize the retrieval process for speed, especially for large document collections.
        # - Use efficient indexing and search algorithms.
        # - Consider caching frequently accessed documents.
        pass
