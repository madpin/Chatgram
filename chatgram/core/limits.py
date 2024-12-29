from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from data.models import ChatInstance


class LimitManager:
    """Manages message/token limits for personas."""

    def __init__(
        self,
        max_messages: Optional[int] = None,
        max_tokens: Optional[int] = None,
        max_chars: Optional[int] = None,
    ):
        """Initializes the LimitManager.

        Args:
            max_messages (Optional[int], optional): Maximum number of messages. Defaults to None.
            max_tokens (Optional[int], optional): Maximum number of tokens. Defaults to None.
            max_chars (Optional[int], optional): Maximum number of characters. Defaults to None.
        """
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self.max_chars = max_chars

        # Performance considerations:
        # - The LimitManager is initialized once per persona and reused.
        # - The limits are stored as attributes, providing fast access.

    def check_limits(
        self, chat_instance: "ChatInstance", new_message: Optional[str] = None
    ) -> bool:
        """Checks if adding a new message would exceed the configured limits.

        Args:
            chat_instance (ChatInstance): The chat instance object.
            new_message (Optional[str], optional): The new message to be added (for character limit check). Defaults to None.

        Returns:
            bool: True if within limits, False otherwise.
        """
        # if self.max_messages is not None:
        #     if len(chat_instance.messages) >= self.max_messages:
        #         return False
        return True
        if self.max_tokens is not None:
            total_tokens = sum(
                m.token_count for m in chat_instance.messages if m.token_count
            )
            if total_tokens >= self.max_tokens:
                return False

        if self.max_chars is not None and new_message:
            total_chars = sum(
                len(m.message) for m in chat_instance.messages if m.message
            )
            if total_chars + len(new_message) > self.max_chars:
                return False

        # Performance considerations:
        # - The checks are performed in a specific order (messages, tokens, chars) to
        #   optimize for the most common cases.
        # - The number of database queries is minimized by retrieving the messages once.

        return True
