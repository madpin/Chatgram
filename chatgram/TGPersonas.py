"""
# TGPersona Bot

**Description:** A Telegram bot that allows users to interact with different personas powered by a chatbot.

**Features:**

-   Loads personas from a YAML configuration file.
-   Presents users with a choice of personas via inline keyboards.
-   Maintains conversation context for each persona and chat.
-   Handles private and group chats.
-   Allows clearing chat context with a specific command.
-   Allows setting a persona for a specific group chat.

**Required Environment Variables:**

-   `TELEGRAM_BOT_TOKEN`: Your Telegram bot token.

**Required Packages:**

-   `python-telegram-bot`
-   `pyyaml`
-   `Chatbot` (Assuming this is a custom module you have)

**Usage:**

1. Set the `TELEGRAM_BOT_TOKEN` environment variable.
2. Create a `personas.yml` file with your desired personas and their configurations.
3. Run the script: `python tgpersona.py`

**Author:** tpinto
"""

import os
import yaml
import uuid
from typing import Optional
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    ParseMode,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)
from Chatbot import Chatbot  # Assuming this is your custom Chatbot module

class TGPersona:
    """
    A Telegram bot that manages different personas for interacting with users.
    """

    def __init__(self, token: str):
        """
        Initializes the TGPersona bot.

        Args:
            token: The Telegram bot token.
        """
        self.updater = Updater(token)
        self.dispatcher = self.updater.dispatcher
        self.personas = {}  # Store initialized Chatbot instances
        self.chat_instances = {}  # Track chat instances per chat ID and persona
        self.chat_personas = (
            {}
        )  # Track which persona is active in each chat (used for groups)
        self.personas_yaml = self.load_personas_config()
        self.initialize_personas()
        self.register_handlers()

    def load_personas_config(self) -> dict:
        """Loads personas configuration from YAML file."""
        try:
            with open("personas.yml", "r") as stream:
                return yaml.safe_load(stream)
        except FileNotFoundError:
            print("Error: personas.yml file not found.")
            return {}
        except yaml.YAMLError as exc:
            print(f"Error parsing personas.yml: {exc}")
            return {}

    def initialize_personas(self):
        """Initializes Chatbot instances for each persona."""
        for name, data in self.personas_yaml.items():
            try:
                allowed_users = (
                    None
                    if "allowed_users" not in data
                    else list(map(str.strip, data["allowed_users"].split(",")))
                )
                self.personas[name] = Chatbot(
                    **data["model"], allowed_users=allowed_users
                )
            except Exception as e:
                print(f"Error initializing persona {name}: {e}")

    def get_chat_instance(self, chat_id: int, persona_name: str) -> str:
        """
        Gets or creates a chat instance for a given chat ID and persona.

        Args:
            chat_id: The ID of the chat.
            persona_name: The name of the persona.

        Returns:
            The chat instance ID.
        """
        if chat_id not in self.chat_instances:
            self.chat_instances[chat_id] = {}
        if persona_name not in self.chat_instances[chat_id]:
            self.chat_instances[chat_id][persona_name] = str(uuid.uuid4())
        return self.chat_instances[chat_id][persona_name]

    def start(self, update: Update, context: CallbackContext) -> None:
        """Sends a welcome message and presents the persona selection keyboard."""
        keyboard = self.build_persona_keyboard()
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Who would you like to speak with today? Select a character to chat with:",
            reply_markup=reply_markup,
        )

    def build_persona_keyboard(self) -> list:
        """Builds the inline keyboard for persona selection."""
        keyboard = []
        persona_names = list(self.personas.keys())
        for i in range(0, len(persona_names), 2):
            row = [
                InlineKeyboardButton(persona_names[i], callback_data=persona_names[i])
            ]
            if i + 1 < len(persona_names):
                row.append(
                    InlineKeyboardButton(
                        persona_names[i + 1], callback_data=persona_names[i + 1]
                    )
                )
            keyboard.append(row)
        return keyboard

    def choose_persona(self, update: Update, context: CallbackContext) -> None:
        """Handles persona selection via callback query or command."""
        chat_id = update.effective_chat.id
        query = update.callback_query

        if query:
            # Persona selected via inline keyboard
            query.answer()
            persona_name = query.data
            message = f"You've chosen the {persona_name} persona!"
        elif context.args:
            # Persona set via /persona command (likely in a group)
            persona_name = context.args[0]
            message = f"Persona set to {persona_name} for this group."
        else:
            # Invalid usage
            context.bot.send_message(
                chat_id=chat_id,
                text="Invalid usage. Use /start or /persona <persona_name>",
            )
            return

        if persona_name in self.personas:
            self.chat_personas[chat_id] = persona_name
            self.get_chat_instance(
                chat_id, persona_name
            )  # Ensure chat instance exists
            context.bot.send_message(
                chat_id=chat_id,
                text=message,
            )
        else:
            context.bot.send_message(
                chat_id=chat_id,
                text="Invalid persona. Please choose a valid persona.",
            )

    def echo_all(self, update: Update, context: CallbackContext) -> None:
        """Handles incoming messages and generates responses."""
        chat_id = update.effective_chat.id
        message_text = update.message.text
        user_name = update.effective_user.username

        if message_text == "--":
            self.reset_chat_context(update, context)
            return

        current_persona_name = self.chat_personas.get(chat_id)

        if current_persona_name:
            current_persona = self.personas[current_persona_name]
            chat_instance = self.get_chat_instance(chat_id, current_persona_name)

            try:
                response = current_persona.generate_message(
                    chat_instance,
                    message_text,
                    user=user_name,
                    extra_info={
                        "chat_id": chat_id,
                        "chat_location": update.effective_chat.location,
                        "user_username": user_name,
                        "user_name": update.effective_user.name,
                        "user_id": update.effective_user.id,
                    },
                )
                context.bot.send_message(
                    chat_id=chat_id,
                    text=response,
                )
            except Exception as e:
                context.bot.send_message(
                    chat_id=chat_id,
                    text=f"Error generating response: {e}",
                )
        else:
            context.bot.send_message(
                chat_id=chat_id,
                text="Please choose a persona first using /start (private chat) or /persona <name> (group).",
            )

    def reset_chat_context(self, update: Update, context: CallbackContext) -> None:
        """Resets the chat context for the current chat and persona."""
        chat_id = update.effective_chat.id
        current_persona_name = self.chat_personas.get(chat_id)

        if current_persona_name and chat_id in self.chat_instances:
            if current_persona_name in self.chat_instances[chat_id]:
                del self.chat_instances[chat_id][current_persona_name]
                context.bot.send_message(
                    chat_id=chat_id,
                    text=f"Chat context for {current_persona_name} has been cleared.",
                )
            else:
                context.bot.send_message(
                    chat_id=chat_id,
                    text=f"No active chat context found for {current_persona_name}.",
                )
        else:
            context.bot.send_message(
                chat_id=chat_id,
                text="No active persona or chat context found.",
            )

    def register_handlers(self):
        """Registers Telegram bot handlers."""
        self.dispatcher.add_handler(CommandHandler("start", self.start))
        self.dispatcher.add_handler(CommandHandler("persona", self.choose_persona))
        self.dispatcher.add_handler(
            MessageHandler(Filters.text & ~Filters.command, self.echo_all)
        )
        self.dispatcher.add_handler(CallbackQueryHandler(self.choose_persona))

    def run(self):
        """Starts the Telegram bot."""
        self.updater.start_polling()
        self.updater.idle()

if __name__ == "__main__":
    telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not telegram_bot_token:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
    else:
        bot = TGPersona(telegram_bot_token)
        bot.run()
