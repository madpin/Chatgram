import os
import yaml
import logging
from typing import Dict, Any
from dotenv import load_dotenv


class Config:
    """Configuration class for the ChatGram application."""

    def __init__(
        self, dotenv_path: str = ".env", personas_file_path: str = "personas.yml"
    ):
        """Initializes the Config class."""
        self.logger = logging.getLogger(__name__)
        self.dotenv_path = dotenv_path
        self.personas_file_path = personas_file_path
        self.telegram_bot_token: str = ""
        self.openai_api_key: str = ""
        self.openai_api_base: str = ""
        self.personas: Dict[str, Any] = {}

        self.load_from_env()
        self.load_personas()

    def load_from_env(self) -> None:
        """Loads configuration from environment variables."""
        load_dotenv(dotenv_path=self.dotenv_path)
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_api_base = os.getenv("OPENAI_API_BASE", "")

        # Performance considerations:
        # - Environment variable access can be slow. Loading them once during
        #   initialization is more efficient than accessing them repeatedly.

    def load_personas(self) -> None:
        """Loads persona configurations from a YAML file.

        Args:
            file_path (str): Path to the personas YAML file.

        Returns:
            dict: Dictionary containing persona configurations.
        """
        try:
            with open(self.personas_file_path, "r") as stream:
                self.personas = yaml.safe_load(stream)
            self.logger.info(f"Loaded {len(self.personas)} personas from {self.personas_file_path}")
        except FileNotFoundError:
            self.logger.error(f"Personas configuration file not found at {self.personas_file_path}")
            self.personas = {}
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing personas YAML file: {e}")
            self.personas = {}

        # Performance considerations:
        # - YAML parsing can be slow for large files. Consider caching the parsed
        #   data if it's accessed frequently and doesn't change often.
        # - Use `yaml.safe_load` for security reasons to avoid arbitrary code execution.