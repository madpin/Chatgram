from typing import Dict, TYPE_CHECKING
from sqlalchemy.orm import Session
import uuid
import logging

from data.models import Personas, ChatbotConfig, User, ChatInstance
from core.chatbot import Chatbot
from core.limits import LimitManager

if TYPE_CHECKING:
    from config import Config

logger = logging.getLogger(__name__)


class PersonaManager:
    """Manages loading, selecting, and configuring personas."""

    def __init__(self, config: "Config", db: Session):
        """Initializes the PersonaManager.

        Args:
            config (Config): The configuration object.
            db (Session): The database session.
        """
        self.config = config
        self.db = db
        self.personas: Dict[str, Chatbot] = {}
        self.chat_instances: Dict[str, Dict[str, ChatInstance]] = {}

        self.load_personas_from_config()

        # Performance considerations:
        # - The PersonaManager is initialized once at startup.
        # - Personas are loaded from the config file and the database during initialization.

    def load_personas_from_config(self) -> None:
        """Loads persona configurations from the YAML file and database."""
        logger.info("Loading personas from configuration")
        for persona_name, persona_data in self.config.personas.items():
            logger.debug(f"Processing persona: {persona_name}")
            # Check if the persona already exists in the database
            persona = self.db.query(Personas).filter_by(name=persona_name).first()

            if not persona:
                logger.info(f"Creating new persona: {persona_name}")
                # Create a new persona
                persona = Personas(
                    name=persona_name,
                    description=persona_data.get("description", ""),
                )
                self.db.add(persona)
                self.db.flush()  # Ensure persona.id is populated

                # Create a new chatbot configuration
                chatbot_config_data = persona_data.get("model", {})
                chatbot_config = ChatbotConfig(
                    persona_id=persona.id,
                    system_message=chatbot_config_data.get("system_message", ""),
                    model=chatbot_config_data.get("model", "gpt-4o-mini"),
                    tokens=chatbot_config_data.get("tokens", 750),
                    temperature=chatbot_config_data.get("temperature", 1),
                    presence_penalty=chatbot_config_data.get("presence_penalty", 0),
                    max_messages=chatbot_config_data.get("max_messages"),
                    max_tokens=chatbot_config_data.get("max_tokens"),
                    max_chars=chatbot_config_data.get("max_chars"),
                )
                self.db.add(chatbot_config)
                self.db.flush()  # Ensure chatbot_config.id is populated

                # Add allowed users
                allowed_users_data = persona_data.get("allowed_users", [])
                logger.debug(f"Processing allowed users for {persona_name}: {allowed_users_data}")
                for username in allowed_users_data:
                    user = self.db.query(User).filter_by(username=username).first()
                    if user:
                        persona.allowed_users.append(user)
                    else:
                        logger.info(f"Creating new user: {username}")
                        # Create the user if it doesn't exist
                        user = User(username=username)
                        self.db.add(user)
                        self.db.flush()  # Ensure user.id is populated
                        persona.allowed_users.append(user)

                self.db.commit()

            # Load the persona into the chatbot
            limit_manager = LimitManager(
                max_messages=persona.chatbot_config.max_messages,
                max_tokens=persona.chatbot_config.max_tokens,
                max_chars=persona.chatbot_config.max_chars,
            )
            self.personas[persona_name] = Chatbot(
                persona=persona,
                chatbot_config=persona.chatbot_config,
                limit_manager=limit_manager,
            )
            logger.debug(f"Loaded persona {persona_name} into chatbot")

    def get_persona(self, persona_name: str) -> "Chatbot":
        """Retrieves a Chatbot instance for the specified persona.

        Args:
            persona_name (str): The name of the persona.

        Returns:
            Chatbot: A Chatbot instance configured for the persona.
        """
        if persona_name not in self.personas:
            logger.error(f"Persona '{persona_name}' not found")
            raise ValueError(f"Persona '{persona_name}' not found.")
        logger.debug(f"Retrieved persona: {persona_name}")
        return self.personas[persona_name]

    def get_chat_instance(
        self, chat_id: str, persona_name: str, user: "User"
    ) -> "ChatInstance":
        """Gets or creates a unique chat instance ID for a given chat and persona."""
        logger.debug(f"Getting chat instance for chat_id: {chat_id}, persona: {persona_name}, user: {user.username}")
        if chat_id not in self.chat_instances:
            self.chat_instances[chat_id] = {}

        if persona_name not in self.chat_instances[chat_id]:
            persona_id = self.personas[persona_name].persona.id

            # Check if a chat instance already exists for this chat, persona, and user
            chat_instance = (
                self.db.query(ChatInstance)
                .filter_by(user_id=user.id, persona_id=persona_id)
                .first()
            )

            if not chat_instance:
                logger.info(f"Creating new chat instance for user {user.username} with persona {persona_name}")
                chat_instance_id = str(uuid.uuid4())
                chat_instance = ChatInstance(
                    id=chat_instance_id,
                    user_id=user.id,
                    persona_id=persona_id,
                )
                self.db.add(chat_instance)
                self.db.commit()

            self.chat_instances[chat_id][persona_name] = chat_instance

        return self.chat_instances[chat_id][persona_name]

    def get_user(self, user_id: int) -> "User":
        """Retrieves a user from the database based on their ID."""
        logger.debug(f"Getting user by ID: {user_id}")
        user = self.db.query(User).filter_by(id=user_id).first()
        if not user:
            logger.error(f"User with ID '{user_id}' not found")
            raise ValueError(f"User with ID '{user_id}' not found.")
        return user

    def get_user_by_username(self, username: str) -> "User":
        """Retrieves a user from the database based on their username."""
        logger.debug(f"Getting user by username: {username}")
        user = self.db.query(User).filter_by(username=username).first()
        if not user:
            logger.error(f"User with username '{username}' not found")
            raise ValueError(f"User with username '{username}' not found.")
        return user