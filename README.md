# MultiAITeleBot

A Telegram bot that lets you use different AI models.


## Features

* Text/Voice chat
* Text/Voice translation
* Speech-to-Text (*Transcription*)
* Text-to-Speech
* Image generation
* Image analysis


## How to Install and Run

### Requirements

* Python

Steps:

* `pip install -r requirements.txt`
* Set the environment variables below:
    * `TELEGRAM_API_KEY`
    * `TELEGRAM_ADMIN_ID`
    * `OPENAI_API_KEY`
    * `DATABASE_URL` - E.g. `sqlite:///chats.db`
* `python bot.py`


## Configuration

**NOTE**: The bot relies on the files ending with `.default.json` to get default settings.
<br>
Non-default configuration files will be created automatically once a setting is edited through the bot interface.

There are two types of configuration files:
* `bot` (*`config.json`*) - Contains the bot settings
* `ai` (*`ai_options.json`*) - Contains the options to be sent when calling the AI APIs

To change a setting use the `/config` command.

**NOTE**: AI options are shared between chats, while the AI system message is set per chat.

To change the system message for a chat use the `/sysmsg` command.

### Whitelist

The bot reads a **whitelist** to determine who can send certain commands, each line in the whitelist must be the *Telegram ID* of either a user or a group chat.
<br>
Without a whitelist, only the bot's admin can interact with the bot.


## Bot usage:

You can find the full list of commands [here](/commands.md).

**NOTE**: When chatting with the AI, there's no need to use the commands `/chat` or `/achat` each time, simply reply to a bot's message with text or voice.

**NOTE**: The command `/help` displays the bot version only if the `.git` directory is present in the root.


## Supported AI platforms

Although multiple AI platforms can be implemented through the `AIManager` class, currently only the `OpenAI` platform is implemented.


## Response streaming

Telegram added support for response streaming for textual messages on *2026-12-31*. You can try it out by setting `stream` to `true` in the bot configuration file (`config.json`) tho, the feature provided by the API is still experimental, the stream is slow and the "Too many requests" error is hit regularly just like when using the `editMessageText` endpoint.