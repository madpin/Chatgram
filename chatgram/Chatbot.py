import os
from dotenv import load_dotenv
import sqlite3
from typing import List, Tuple
from datetime import datetime
import openai
from pprint import pprint

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
    ):
        """Initialize the chatbot.

        Args:
            system_message (str): The chatbot's intro message.
            model (str): The OpenAI model to use.
            tokens (int): The max number of tokens for OpenAI to generate.
            db_path (str): The path to the SQLite database.
        """
        self.system_message = system_message
        self.model = model
        self.tokens = tokens
        self.conn = sqlite3.connect(db_path, check_same_thread=False)

        self.conn.row_factory = sqlite3.Row
        self.setup_db()

    def setup_db(self):
        """Create the SQLite database table."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY,
            chat_instance TEXT NOT NULL,
            message TEXT NOT NULL,
            token_count INTEGER,
            role TEXT,
            user TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        )
        self.conn.commit()

    def save_message(
        self, chat_instance: str, message: str, token_count: int, role: str, user: str
    ):
        """Save a message to the database.

        Args:
            chat_instance (str): The ID of the chat instance.
            message (str): The message text.
            token_count (int): The number of tokens used to generate the message.
            role (str): Either "user" or "bot".
            user (str): The name of the user who sent the message.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
        INSERT INTO chats (chat_instance, message, token_count, role, user)
        VALUES (?, ?, ?, ?, ?)
        """,
            (chat_instance, message, token_count, role, user),
        )
        self.conn.commit()

    def get_recent_messages(
        self, chat_instance: str, max_chars: int = 12_500
    ) -> List[Tuple]:
        """Get the most recent messages for a chat instance.

        Args:
            chat_instance (str): The ID of the chat instance.
            max_chars (int): The maximum number of characters to return.

        Returns:
            List[Tuple]: A list of (message, role) tuples.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
        SELECT message, role
        FROM chats
        WHERE chat_instance = ?
        ORDER BY timestamp DESC
        """,
            (chat_instance,),
        )

        result = []
        total_chars = 0
        for row in cursor:
            total_chars += len(row["message"])
            if total_chars > max_chars:
                break
            result.append({"message": row["message"], "role": row["role"]})
        return result

    def generate_message(
        self, chat_instance: str, user_message: str, user: str = "user"
    ):
        """Generate a response to a user message.

        Args:
            chat_instance (str): The ID of the chat instance.
            user_message (str): The message from the user.
            user (str): The name of the user.

        Returns:
            str: The generated response.
        """

        # Generate response using OpenAI
        response = self.openai_generate_response(chat_instance, user_message)
        response_text = response["choices"][0]["message"]["content"]
        token_count = response["usage"]["total_tokens"]
        self.save_message(chat_instance, user_message, len(user_message), "user", user)

        self.save_message(chat_instance, response_text, token_count, "bot", "chatbot")

        return response_text

    def openai_generate_response(self, chat_instance: str, message: str):
        """Prompt OpenAI to generate a response.

        Args:
            chat_instance (str): The ID of the chat instance.
            message (str): The latest message in the conversation.

        Returns:
            dict: The response from the OpenAI API.
        """
        messages = self.get_recent_messages(chat_instance)

        formatted_messages = [{"role": "system", "content": self.system_message}]

        for msg in messages:
            role = "user" if msg["role"] == "user" else "assistant"
            formatted_messages.append({"role": role, "content": msg["message"]})

        formatted_messages.append({"role": "user", "content": message})
        pprint(formatted_messages)

        return openai.ChatCompletion.create(
            model=self.model, messages=formatted_messages, max_tokens=self.tokens
        )

    def close(self):
        """Close the database connection."""
        self.conn.close()


if __name__ == "__main__":
    cb = Chatbot()
    print(cb.generate_message("test3", "What's bigger, the earth or the sun?"))
