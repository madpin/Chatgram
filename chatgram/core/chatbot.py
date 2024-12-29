from datetime import datetime
from typing import Optional, List, Dict, TYPE_CHECKING
import logging
from openai import OpenAI
from config import Config

from core.interfaces import ChatbotInterface
from core.limits import LimitManager
from data.database import get_db
from data.models import Message

if TYPE_CHECKING:
    from data.models import ChatInstance, User, Personas, ChatbotConfig


class Chatbot(ChatbotInterface):
    """Core chatbot implementation using a language model."""

    def __init__(
        self,
        persona: "Personas",
        chatbot_config: "ChatbotConfig",
        limit_manager: "LimitManager",
    ):
        """Initializes the Chatbot.

        Args:
            persona (Personas): The persona object.
            chatbot_config (ChatbotConfig): The chatbot configuration object.
            limit_manager (LimitManager): The message/token limit manager.
        """
        self.persona = persona
        self.chatbot_config = chatbot_config
        self.limit_manager = limit_manager
        self.logger = logging.getLogger(__name__)

        # Performance considerations:
        # - The Chatbot object is initialized once per persona and reused for multiple
        #   interactions.
        # - LimitManager is also initialized once and reused.

    def generate_message(
        self,
        chat_instance: "ChatInstance",
        user_message: str,
        user: "User",
        extra_info: Optional[dict] = None,
    ) -> str:
        """Generates a response using the configured language model.

        Args:
            chat_instance (ChatInstance): The chat instance object.
            user_message (str): The message sent by the user.
            user (User): The user object.
            extra_info (Optional[dict], optional): Additional information. Defaults to None.

        Returns:
            str: The generated response.
        """
        db = next(get_db())

        if not self.limit_manager.check_limits(chat_instance):
            self.logger.warning(f"Message limit reached for chat instance {chat_instance.id}")
            return "Sorry, I can't answer that. The maximum number of messages or tokens for this persona has been reached."

        recent_messages = self.get_recent_messages(chat_instance)

        if not self.limit_manager.check_limits(chat_instance, user_message):
            self.logger.warning(f"Message too long for chat instance {chat_instance.id}")
            return "Sorry, I can't answer that. The message is too long."

        try:
            response = self._openai_generate_response(recent_messages, user_message)
            response_text = response.choices[0].message.content
            token_count = response.usage.total_tokens
        except Exception as e:
            # Error handling:
            # - Catch exceptions during API calls (e.g., network issues, API errors).
            # - Log the error for debugging.
            # - Return a user-friendly error message.
            self.logger.error(f"Error during OpenAI API call: {str(e)}", exc_info=True)
            return "Sorry, I encountered an error while processing your request."

        # Save the messages to the database
        self.save_message(
            db, chat_instance, user_message, None, "user", user.username, extra_info
        )
        self.save_message(
            db, chat_instance, response_text, token_count, "assistant", user.username
        )

        # Performance considerations:
        # - The actual message generation is delegated to the `_openai_generate_response` method.
        # - Error handling is implemented to catch potential exceptions during API calls.
        # - Database operations are kept to a minimum (saving the message and response).
        return response_text

    def _openai_generate_response(
        self, recent_messages: List[dict], message: str
    ) -> dict:
        """Generates a response using the OpenAI API.

        Args:
            recent_messages (List[dict]): A list of recent messages.
            message (str): The current user message.

        Returns:
            dict: The response from the OpenAI API.
        """
        config = Config()
        formatted_messages = [
            {"role": "system", "content": self.chatbot_config.system_message}
        ]
        for msg in recent_messages:
            formatted_messages.append({"role": msg["role"], "content": msg["message"]})
        formatted_messages.append({"role": "user", "content": message})

        try:
            openai_client = OpenAI(
                api_key=config.openai_api_key,
                base_url=config.openai_api_base,
                organization="Chatgram",
            )
            response = openai_client.chat.completions.create(
                model=self.chatbot_config.model,
                messages=formatted_messages,
                max_tokens=self.chatbot_config.tokens,
                temperature=self.chatbot_config.temperature,
                presence_penalty=self.chatbot_config.presence_penalty,
            )
        except Exception as e:
            self.logger.error(f"OpenAI API call failed: {str(e)}", exc_info=True)
            raise Exception(f"Error during OpenAI API call: {e}")

        # Error handling:
        # - Handle potential errors during the API call (e.g., invalid API key,
        #   rate limits, server errors).
        # - Consider retrying the request with exponential backoff if appropriate.

        # Performance considerations:
        # - This method is responsible for the actual interaction with the OpenAI API,
        #   which can be slow.
        # - Asynchronous API calls could be used to improve responsiveness.
        # - Minimize the number of messages sent in each request to reduce latency.
        return response

    def save_message(
        self,
        db,
        chat_instance: "ChatInstance",
        message: str,
        token_count: int,
        role: str,
        user: str,
        extra_info: Optional[dict] = None,
    ):
        """Saves a message to the database."""

        message = Message(
            chat_instance_id=chat_instance.id,
            message=message,
            response=None if role == "user" else message,
            token_count=token_count,
            role=role,
            user=user,
            extra_info=extra_info,
        )

        try:
            db.add(message)
            db.commit()
        except Exception as e:
            self.logger.error(f"Failed to save message to database: {str(e)}", exc_info=True)
            db.rollback()
            raise

    def get_recent_messages(self, chat_instance: "ChatInstance") -> List[Dict]:
        """Retrieves recent messages for a given chat instance."""
        db = next(get_db())
        try:
            messages = (
                db.query(Message)
                .filter_by(chat_instance_id=chat_instance.id)
                .order_by(Message.created_at.desc())
                .limit(self.limit_manager.max_messages)
                .all()
            )
        except Exception as e:
            self.logger.error(f"Failed to retrieve recent messages: {str(e)}", exc_info=True)
            raise

        result = []
        today = datetime.now().date()

        for message in reversed(messages):
            message_date = message.created_at.date()
            days_diff = (today - message_date).days

            if days_diff > 7:
                continue
            elif days_diff > 0 and days_diff <= 7:
                if len(result) >= 2:
                    continue
            elif days_diff == 0:
                if len(result) >= self.limit_manager.max_messages:
                    continue

            if message.role == "user":
                result.append({"message": message.message, "role": message.role})
            elif message.role == "assistant":
                result.append({"message": message.response, "role": message.role})

        return result