import logging
from pathlib import Path
from config import Config
from data.database import get_db, recreate_database
from personas.manager import PersonaManager
from personas.tg_adapter import TelegramAdapter


def setup_logging() -> None:
    """Configure logging for both file and console output."""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(logs_dir / "chatgram.log"),
            logging.StreamHandler()
        ]
    )


def main() -> None:
    """Entry point for the ChatGram application."""
    # 1. Setup Logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 2. Load Configuration
    logger.info("Loading configuration...")
    config = Config()

    # 3. Get Database Session
    logger.info("Initializing database connection...")
    db = next(get_db())
    # recreate_database()

    # 4. Initialize Persona Manager
    logger.info("Initializing persona manager...")
    persona_manager = PersonaManager(config, db)

    # 5. Initialize Telegram Adapter
    logger.info("Setting up Telegram adapter...")
    telegram_adapter = TelegramAdapter(config.telegram_bot_token, persona_manager)

    # 6. Run the Bot
    logger.info("Starting Telegram bot...")
    telegram_adapter.run()

    # Performance considerations:
    # - The main function initializes the core components of the application in the correct order.


if __name__ == "__main__":
    main()
