import logging
from typing import TYPE_CHECKING, List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

from data.models import User

if TYPE_CHECKING:
    from personas.manager import PersonaManager


logger = logging.getLogger(__name__)


class TelegramAdapter:
    """Manages Telegram bot interactions and persona selection."""

    def __init__(self, token: str, persona_manager: "PersonaManager"):
        """Initializes the Telegram bot.

        Args:
            token (str): The Telegram bot token.
            persona_manager (PersonaManager): The persona manager object.
        """
        self.updater = Updater(token)
        self.dispatcher = self.updater.dispatcher
        self.persona_manager = persona_manager
        self.chat_personas = {}  # Dictionary to track active persona per chat

        self.register_handlers()
        logger.info("TelegramAdapter initialized")

        # Performance considerations:
        # - The TelegramAdapter is initialized once at startup.
        # - The Updater and Dispatcher are created once and reused.

    def start(self, update: Update, context: CallbackContext) -> None:
        """Handles the /start command in Telegram."""
        user = update.effective_user
        logger.info(f"Start command received from user: {user.username}")

        try:
            # Try to get the user from the database
            db_user = self.persona_manager.get_user_by_username(user.username)
        except ValueError:
            # If the user doesn't exist, create a new one
            db = self.persona_manager.db
            db_user = User(username=user.username)
            db.add(db_user)
            db.commit()
            logger.info(f"Created new user: {user.username}")

        keyboard = self._build_persona_keyboard(db_user)
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = (
            "Hello! I'm a chatbot with multiple personalities. "
            "Please select a persona to start chatting:"
        )

        max_retries = 3
        for attempt in range(max_retries):
            try:
                update.message.reply_text(message, reply_markup=reply_markup)
                break
            except Exception as e:
                logger.error(f"Error sending start message (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    raise e
                continue

        # Performance considerations:
        # - The /start command is handled quickly by sending a message and a keyboard.
    def _build_persona_keyboard(self, db_user) -> List[List[InlineKeyboardButton]]:
        """Builds an inline keyboard for persona selection."""
        keyboard = []
        for persona_name, chatbot in self.persona_manager.personas.items():
            db_persona = chatbot.persona
            if not db_persona.allowed_users or db_user in db_persona.allowed_users:
                button = InlineKeyboardButton(persona_name, callback_data=persona_name)
                keyboard.append([button])

        # Add a "Help" button
        help_button = InlineKeyboardButton("❓ Help", callback_data="help")
        keyboard.append([help_button])

        logger.debug(f"Built keyboard with {len(keyboard)} options")
        return keyboard

        # Performance considerations:
        # - The keyboard is built dynamically based on the available personas.
        # - Consider caching the keyboard if the list of personas is large and doesn't
        #   change frequently.

    def choose_persona(self, update: Update, context: CallbackContext) -> None:
        """Handles persona selection via inline keyboard or /persona command."""
        query = update.callback_query
        if query:
            query.answer()
            persona_name = query.data
            chat_id = str(update.effective_chat.id)
            message = f"You've chosen the {persona_name} persona. Start chatting!"
            logger.info(f"User selected persona via callback: {persona_name}")
        else:
            try:
                if context and hasattr(context, 'args') and context.args:
                    persona_name = context.args[0]
                else:
                    raise IndexError
            except IndexError:
                try:
                    db_user = self.persona_manager.get_user_by_username(
                        update.effective_user.username
                    )
                except ValueError:
                    db = self.persona_manager.db
                    db_user = User(username=update.effective_user.username)
                    db.add(db_user)
                keyboard = self._build_persona_keyboard(db_user)
                reply_markup = InlineKeyboardMarkup(keyboard)
                update.message.reply_text(
                    "Please choose a persona:", reply_markup=reply_markup
                )
                logger.info("Sent persona selection keyboard due to missing args")
                return            

            chat_id = str(update.effective_chat.id)
            message = f"Persona set to {persona_name} for this chat."
            logger.info(f"User selected persona via command: {persona_name}")

        if persona_name == "help":
            self.help_command(update, context)
            return

        try:
            db_user = self.persona_manager.get_user_by_username(
                update.effective_user.username
            )
        except ValueError:
            db = self.persona_manager.db
            db_user = User(username=update.effective_user.username)
            db.add(db_user)
            db.commit()
            logger.info(f"Created new user during persona selection: {db_user.username}")

        if persona_name in self.persona_manager.personas:
            db_persona = self.persona_manager.personas[persona_name].persona
            if not db_persona.allowed_users or db_user in db_persona.allowed_users:
                self.chat_personas[chat_id] = persona_name
                self.persona_manager.get_chat_instance(chat_id, persona_name, db_user)
                if query:
                    query.edit_message_text(message)
                else:
                    update.message.reply_text(message)
                logger.info(f"Successfully set persona {persona_name} for chat {chat_id}")
            else:
                message = "Sorry, you don't have access to this persona."
                if query:
                    query.edit_message_text(message)
                else:
                    update.message.reply_text(message)
                logger.warning(f"User {db_user.username} denied access to persona {persona_name}")
        else:
            if query:
                query.edit_message_text(
                    "Invalid persona. Please choose a valid persona."
                )
            else:
                update.message.reply_text(
                    "Invalid persona. Please choose a valid persona."
                )
            logger.warning(f"Invalid persona selection attempted: {persona_name}")

    def _handle_message(self, update: Update, context: CallbackContext) -> None:
        """Handles all other non-command messages in Telegram."""
        chat_id = str(update.effective_chat.id)
        message_text = update.message.text
        user_name = update.effective_user.username

        if message_text == "/reset":
            self._reset_chat_context(update, context)
            return

        if chat_id in self.chat_personas:
            persona_name = self.chat_personas[chat_id]
            chatbot = self.persona_manager.get_persona(persona_name)
            try:
                db_user = self.persona_manager.get_user_by_username(user_name)
            except ValueError:
                db = self.persona_manager.db
                db_user = User(username=user_name)
                db.add(db_user)
                db.commit()
                logger.info(f"Created new user during message handling: {user_name}")

            chat_instance = self.persona_manager.get_chat_instance(
                chat_id, persona_name, db_user
            )

            extra_info = {
                "chat_id": chat_id,
                "chat_type": update.effective_chat.type,
                "chat_title": update.effective_chat.title,
                "user_id": update.effective_user.id,
                "user_first_name": update.effective_user.first_name,
                "user_last_name": update.effective_user.last_name,
                "user_username": update.effective_user.username,
                "user_language_code": update.effective_user.language_code,
                "message_id": update.message.message_id,
            }
            try:
                logger.debug(f"Generating response for message: {message_text[:50]}...")
                response = chatbot.generate_message(
                    chat_instance, message_text, db_user, extra_info=extra_info
                )

                if update.effective_chat.type in ["group", "supergroup"]:
                    update.message.reply_text(
                        response, reply_to_message_id=update.message.message_id
                    )
                else:
                    update.message.reply_text(response)

                self.persona_manager.db.commit()
                logger.debug("Response generated and sent successfully")

            except Exception as e:
                self.persona_manager.db.rollback()
                update.message.reply_text(f"Error generating response: {e}")
                logger.error(f"Error generating response: {e}", exc_info=True)
        else:
            logger.info(f"No active persona for chat {chat_id}, prompting selection")
            update.message.reply_text(
                "Please choose a persona first using /start or the inline keyboard."
            )
            self.choose_persona(update, None)

    def _reset_chat_context(self, update: Update, context: CallbackContext) -> None:
        """Resets the chat context for the current chat and persona."""
        chat_id = str(update.effective_chat.id)

        if chat_id in self.chat_personas:
            persona_name = self.chat_personas[chat_id]

            if (
                chat_id in self.persona_manager.chat_instances
                and persona_name in self.persona_manager.chat_instances[chat_id]
            ):
                chat_instance = self.persona_manager.chat_instances[chat_id][
                    persona_name
                ]
                db = self.persona_manager.db
                db.delete(chat_instance)
                db.commit()

                del self.persona_manager.chat_instances[chat_id][persona_name]
                logger.info(f"Reset chat context for chat {chat_id}, persona {persona_name}")

                update.message.reply_text(
                    f"Chat context for {persona_name} has been reset."
                )
            else:
                logger.warning(f"No active chat context found for {chat_id}, {persona_name}")
                update.message.reply_text(
                    f"No active chat context found for {persona_name}."
                )
        else:
            logger.warning(f"No active persona found for chat {chat_id}")
            update.message.reply_text("No active persona found for this chat.")

    def register_handlers(self) -> None:
        """Registers handlers for Telegram commands and messages."""
        self.dispatcher.add_handler(CommandHandler("start", self.start))
        self.dispatcher.add_handler(CommandHandler("persona", self.choose_persona))
        self.dispatcher.add_handler(CommandHandler("help", self.help_command))
        self.dispatcher.add_handler(
            MessageHandler(Filters.text & ~Filters.command, self._handle_message)
        )
        self.dispatcher.add_handler(CallbackQueryHandler(self.choose_persona))
        logger.info("Registered all handlers")

    def run(self) -> None:
        """Starts the Telegram bot and begins polling for updates."""
        logger.info("Starting Telegram bot")
        self.updater.start_polling()
        self.updater.idle()

    def help_command(self, update: Update, context: CallbackContext) -> None:
        """Handles the /help command."""
        help_text = (
            "Available commands:\n"
            "/start - Start the bot and select a persona\n"
            "/persona <persona_name> - Switch to a specific persona\n"
            "/reset - Reset the chat context for the current persona\n"
            "/list_personas - List all available personas\n"
            "/help - Display this help message"
        )
        update.message.reply_text(help_text)
        logger.debug("Sent help message")