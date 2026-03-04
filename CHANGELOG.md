# Changelog

<br>

### 4.0.0 (2026-03-04)

* Improve text message streaming by maximizing delivery speed and using an adaptive chunk size to prevent hitting the Telegram API rate limits
* Change `stream` to `streaming` in the bot chat settings
* Enable `streaming` in the bot chat settings by default

### 3.2.0 (2026-01-04)

* Fix boolean values not being set correctly when editing a configuration

### 3.1.1 (2026-01-04)

* Disable textual response streaming for non-private chats as Telegram doesn't allow it

### 3.1.0 (2026-01-04)

* Add support for textual response streaming

### 3.0.0 (2026-01-04)

* Add support for chat threads

### 2.1.0 (2025-09-09)

* Use Markdown for chat messages

### 2.0.0 (2025-06-21)

* Major codebase refactoring
* Better database system
* Better configuration system
* Better whitelist system
* Add AI manager class
* Add /help command

<br>

### 1.0.0 (2022-26-03)

* Initial build