import random

import yaml
import uuid
from Chatbot import Chatbot
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)


class TGPersona:
    def __init__(self, token):
        self.updater = Updater(token)
        self.dispatcher = self.updater.dispatcher
        self.current_persona = None
        self.chat_instance = None
        self.personas_yaml = None
        self.personas = self.load_personas()
        self.register_handlers()

    def load_personas(self):
        """Loads personas from YAML file."""

        with open("personas.yml", "r") as stream:
            try:
                self.personas_yaml = yaml.safe_load(stream)
                return {
                    name: Chatbot(
                        **data["model"],
                        allowed_users=None
                        if "allowed_users" not in data
                        else list(map(str.strip, data["allowed_users"].split(","))),
                    )
                    for name, data in self.personas_yaml.items()
                }
            except yaml.YAMLError as exc:
                print(exc)

    def get_chat_instance(self):
        return str(uuid.uuid4())

    def start(self, update: Update, context: CallbackContext) -> None:
        """Sends a welcome message to the user."""

        keyboard = []
        personas_per_column = len(self.personas_yaml) // 2
        remainder = len(self.personas_yaml) % 2

        for i in range(personas_per_column):
            keyboard.append(
                [
                    InlineKeyboardButton(
                        list(self.personas_yaml.keys())[i],
                        callback_data=list(self.personas_yaml.keys())[i],
                    ),
                    InlineKeyboardButton(
                        list(self.personas_yaml.keys())[i + personas_per_column],
                        callback_data=list(self.personas_yaml.keys())[
                            i + personas_per_column
                        ],
                    ),
                ]
            )

        # Add extra button for remainder
        if remainder == 1:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        list(self.personas_yaml.keys())[-1],
                        callback_data=list(self.personas_yaml.keys())[-1],
                    )
                ]
            )

        reply_markup = InlineKeyboardMarkup(keyboard)
        print(f"update.effective_chat.id: {update.effective_chat.id}")
        print(f"update.effective_user.username: {update.effective_user.username}")
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            # text="__________ Choose a persona: __________",
            text="Who would you like to speak with today? Select a character to chat with:",
            reply_markup=reply_markup,
        )

    def callback_query(self, update: Update, context: CallbackContext) -> None:
        print("callback_query")
        query = update.callback_query
        query.answer()

        for persona in self.personas_yaml:
            if query.data == persona:
                self.current_persona = Chatbot(**persona)
                # Set chat instance and send message...

    def choose_persona(self, update: Update, context: CallbackContext) -> None:
        persona_name = context.args[0] if context.args else None
        # If persona_name is not None, then the user has sent a command

        # If persona_name is None, then the user has clicked a button
        if persona_name is None:
            query = update.callback_query
            query.answer()
            persona_name = query.data

        if persona_name in self.personas:
            self.current_persona = self.personas[persona_name]
            self.chat_instance = self.get_chat_instance()
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"You've chosen the {persona_name} persona!",
            )
        else:
            print(f"Invalid persona: {persona_name}")
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Invalid persona. Please choose a valid persona.",
            )

    def echo_all(self, update: Update, context: CallbackContext) -> None:
        if update.message.text == "--":
            self.chat_instance = self.get_chat_instance()
            context.bot.send_message(
                chat_id=update.effective_chat.id, text="Chat context has been cleared."
            )
        elif self.current_persona:
            try:
                response = self.current_persona.generate_message(
                    self.chat_instance,
                    update.message.text,
                    user=update.effective_user.username,
                    extra_info={
                        "chat_id": update.effective_chat.id,
                        "chat_location": update.effective_chat.location,
                        "user_username": update.effective_user.username,
                        "user_name": update.effective_user.name,
                        "user_id": update.effective_user.id,
                    }
                )
            except Exception as e:
                response = f"Error: {e}"
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=response,
            )
        else:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Before you can chat, you need to ",
            )
            self.start(update, context)

    def register_handlers(self):
        self.dispatcher.add_handler(CommandHandler("start", self.start))
        self.dispatcher.add_handler(CommandHandler("persona", self.choose_persona))
        self.dispatcher.add_handler(
            MessageHandler(Filters.text & ~Filters.command, self.echo_all)
        )

        self.dispatcher.add_handler(CallbackQueryHandler(self.choose_persona))

    def run(self):
        self.updater.start_polling()
