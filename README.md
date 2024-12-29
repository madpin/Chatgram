# Chatgram: Your Multi-Persona Chatbot

Hey folks, this is Chatgram! It's a fun little project I cooked up to play around with different AI personas. Basically, it's a chatbot that can switch between different personalities, each with its own unique way of talking and responding. Think of it like having multiple chat buddies rolled into one!

## What's the Gist?

Chatgram lets you chat with different AI personas through Telegram. Each persona has a distinct personality, defined by a system message and some configuration parameters. You can have a serious business discussion, get some jokes, or even have your text translated – all within the same bot.

## Personas Included

Here's a sneak peek at some of the personas you can chat with:

*   **Jokester:** This one's your go-to for dark humor. It'll crack jokes on any topic you give it.
*   **Summarizer:** Need to condense a long article or conversation? The Summarizer's got your back. It'll give you the gist in a clear, concise way.
*   **Business Rewriter:** This persona takes your text and converts it into professional medical or technical business language.
*   **Translator Pt-En:** Your personal translator between English and Portuguese. It not only translates but also explains the meaning and offers a pronunciation guide.

## Tech Stack

This project is built with Python (my main squeeze!) and uses a few different libraries and tools:

*   **Python 3.10:** The heart and soul of the project.
*   **OpenAI API:**  Powers the AI responses.
*   **Telegram Bot API:** For interacting with users on Telegram.
*   **SQLAlchemy:**  Handles database interactions.
*   **SQLite:** The database of choice for this project. It's simple and works great for this type of application.
*   **YAML:** Used for configuration files.
*   **Docker:** For containerization, making it easier to deploy and manage.

## Project Structure

Here's a quick rundown of the project's directory structure:

```
chatgram/
├── core/               # Core chatbot logic
│   ├── interfaces.py   # Abstract interfaces for Chatbot and DocumentRetriever
│   ├── limits.py       # Logic for managing limits (messages, tokens, chars)
│   └── chatbot.py      # Main Chatbot class
├── data/               # Database models and operations
│   ├── models.py       # SQLAlchemy models (User, ChatInstance, Personas, etc.)
│   └── database.py     # Database setup and session management
├── personas/          # Persona management and Telegram integration
│   ├── tg_adapter.py   # Telegram adapter for handling interactions
│   └── manager.py      # Manages personas, chat instances, and user interactions
├── rag/                # Retrieval-Augmented Generation (RAG) components
│   └── simple_retriever.py # Simple document retriever implementation
├── config.py           # Configuration management (loads from .env and personas.yml)
├── main.py             # Main application entry point
├── personas.yml        # Persona definitions (system messages, models, limits, etc.)
└── docker-compose.yml  # Docker Compose configuration
```

## Getting Started

1. **Clone the Repo:**

    ```bash
    git clone https://github.com/madpin/Chatgram
    cd chatgram
    ```

2. **Set Up Your Environment:**

    *   Create a `.env` file based on the provided template.
    *   Fill in your `TELEGRAM_BOT_TOKEN` and `OPENAI_API_KEY`.

3. **Configure Personas:**

    *   Edit the `personas.yml` file to customize the available personas, their system messages, and other settings.

4. **Run with Docker:**

    ```bash
    docker-compose up --build
    ```

    This will build the Docker image and start the chatbot.

## How to Use

1. Start a chat with your Telegram bot.
2. Use the `/start` command to see the available personas.
3. Choose a persona by clicking on its name or using the `/persona` command followed by the persona name (e.g., `/persona Jokester`).
4. Start chatting! The bot will respond according to the selected persona.
5. Use `/reset` to clear the chat history for the current persona.
6. Use `/help` to see a list of available commands.

## Contributing

Feel free to fork the repo and submit pull requests if you have any cool ideas for new features or improvements. I'm always open to collaboration!

## Note

This is a personal project, so expect some rough edges. Also, keep in mind that AI responses can be unpredictable, so take them with a grain of salt.

Enjoy chatting with your new AI buddies! Let me know if you have any questions or feedback. Cheers!

