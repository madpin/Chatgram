import os
import sqlite3
from datetime import datetime
from pprint import pprint
from typing import List, Tuple

import openai
from dotenv import load_dotenv
from model import Message, session

# Load .env file
load_dotenv()

# Get API key from .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set OpenAI key
openai.api_key = OPENAI_API_KEY


class Chatbot:
    """A chatbot class powered by OpenAI's GPT-3 API."""

    def __init__(
        self,
        system_message="Your name is Turbo",
        model="gpt-3.5-turbo",
        tokens=750,
        db_path="chat.db",
        temperature=1,
        presence_penalty=0,
        allowed_users: List[str] = None,
    ):
        """Initialize the chatbot.

        Args:
            system_message (str): The chatbot's intro message.
            model (str): The OpenAI model to use.
            tokens (int): The max number of tokens for OpenAI to generate.
            db_path (str): The path to the SQLite database.
            temperature (float): The temperature for OpenAI to use.
                What sampling temperature to use, between 0 and 2.
                Higher values like 0.8 will make the output more random,
                while lower values like 0.2 will make it more
                focused and deterministic.
            presence_penalty (float): The presence penalty for OpenAI to use.
                Number between -2.0 and 2.0.
                Positive values penalize new tokens based on whether
                they appear in the text so far,
                increasing the model's likelihood to talk about new topics.
        """
        self.system_message = system_message
        self.model = model
        self.tokens = tokens
        self.temperature = temperature
        self.presence_penalty = presence_penalty
        self.allowed_users = allowed_users

        # self.conn = sqlite3.connect(db_path, check_same_thread=False)

        # self.conn.row_factory = sqlite3.Row
        # self.setup_db()

    # def setup_db(self):
    #     """Create the SQLite database table."""
    #     cursor = self.conn.cursor()
    #     cursor.execute(
    #         """
    #         CREATE TABLE IF NOT EXISTS chats (
    #             id INTEGER PRIMARY KEY,
    #             chat_instance TEXT NOT NULL,
    #             message TEXT NOT NULL,
    #             token_count INTEGER,
    #             role TEXT,
    #             user TEXT,
    #             timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    #         )
    #         """
    #     )
    #     self.conn.commit()

    def save_message(
        self,
        chat_instance: str,
        message: str,
        token_count: int,
        role: str,
        user: str,
        extra_info: dict = None,
    ):
        """Save a message to the database.

        Args:
            chat_instance (str): The ID of the chat instance.
            message (str): The message text.
            token_count (int): The number of tokens used to generate the message.
            role (str): Either "user" or "bot".
            user (str): The name of the user who sent the message.
        """
        message = Message(
            chat_instance=chat_instance,
            message=message,
            token_count=token_count,
            role=role,
            user=user,
            extra_info=extra_info,
        )
        session.add(message)
        session.commit()

    def get_recent_messages(
        self,
        chat_instance: str,
        max_chars: int = 12_500,
        user: str = "Unknown User",
    ) -> List[Tuple]:
        """Get the most recent messages for a chat instance.

        Args:
            chat_instance (str): The ID of the chat instance.
            max_chars (int): The maximum number of characters to return.

        Returns:
            List[Tuple]: A list of (message, role) tuples.
        """
        # cursor = self.conn.cursor()
        # cursor.execute(
        #     """
        # SELECT message, role
        # FROM chats
        # WHERE chat_instance = ?
        # and user = ?
        # ORDER BY timestamp DESC
        # """,
        #     (chat_instance, user),
        # )

        messages = (
            session.query(Message)
            .filter_by(chat_instance=chat_instance, user=user)
            .order_by(Message.created_at.desc())
            .limit(25)
        )

        result = []
        total_chars = 0
        for message in messages:
            total_chars += len(message.message)
            if total_chars > max_chars:
                break
            result.append(
                {
                    "message": message.message,
                    "role": message.role,
                }
            )
        return result

    def generate_message(
        self,
        chat_instance: str,
        user_message: str,
        user: str = "Unknown User",
        extra_info: dict = None,
    ):
        """Generate a response to a user message.

        Args:
            chat_instance (str): The ID of the chat instance.
            user_message (str): The message from the user.
            user (str): The name of the user.

        Returns:
            str: The generated response.
        """
        if self.allowed_users and user not in self.allowed_users:
            return "Sorry, you are not allowed to use this chatbot."
        recent_messages = self.get_recent_messages(chat_instance, user=user)
        # Generate response using OpenAI
        response = self.openai_generate_response(recent_messages, user_message)
        response_text = response["choices"][0]["message"]["content"]
        token_count = response["usage"]["total_tokens"]
        self.save_message(chat_instance, user_message, None, "user", user, extra_info)

        self.save_message(chat_instance, response_text, token_count, "bot", user)

        return response_text

    def openai_generate_response(self, recent_messages: List[Tuple], message: str):
        """Prompt OpenAI to generate a response.

        Args:
            chat_instance (str): The ID of the chat instance.
            message (str): The latest message in the conversation.

        Returns:
            dict: The response from the OpenAI API.
        """
        # messages = self.get_recent_messages(chat_instance)

        formatted_messages = [{"role": "system", "content": self.system_message}]

        for msg in recent_messages:
            role = "user" if msg["role"] == "user" else "assistant"
            formatted_messages.append({"role": role, "content": msg["message"]})

        formatted_messages.append({"role": "user", "content": message})
        print(formatted_messages)
        return openai.ChatCompletion.create(
            model=self.model,
            messages=formatted_messages,
            max_tokens=self.tokens,
            temperature=self.temperature,
            presence_penalty=self.presence_penalty,
        )

    # def close(self):
    #     """Close the database connection."""
    #     self.conn.close()


if __name__ == "__main__":
    cb = Chatbot()
    print(cb.generate_message("test3", "What's bigger, the earth or the sun?"))
