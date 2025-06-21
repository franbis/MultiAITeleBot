# Bot commands

### Debug & Info commands

* `/start` - Make the bot introduce themselves
* `/help` - Send a private message with the command list
* `/status` - Show the software status
* `/chatinfo` - Show the current chat's ID

### Configuration commands

* `/config <bot|ai> <get|set|reset|show> [key_path [value]]` - Show or modify a configuration file

### Whitelist commands

* `/wlist <has|add|remove|show> [id]` - Show or modify the whitelist

### Chat commands

* `/cansee` - Check if the messages in the chat contain images
* `/sysmsg <set|reset|show> [message]` - Show or modify the system message for the current chat
* `/forget` - Erase the bot's memory for the current chat
* `/purgechats` - Delete all the chats older than the days set in the bot configuration at `chat.purge_days`

### AI commands

**NOTE**: When replying to a bot's message, the interaction is treated as a `/chat` command for text replies or a `/achat` command for voice replies.

* `/chat <message>` - Chat with the LLM
* `/achat <message>` - Same as `/chat` but the AI replies with a voice message
* `/tts <text>` - Perform Text-to-Speech
* `/stt` - Transcribe the voice message you're replying to
* `/to <language>` - Translate the message you're replying to into the specified language
* `/img <description>` - Generate an image based on a description