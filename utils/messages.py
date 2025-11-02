import traceback

import telegramify_markdown



def process_text(text):
	"""Format text to prevent the Telegram API from throwing errors
	caused by unproperly formatted text."""
	
	# A message must not be empty, replace the text with a
	# representation of emptiness.
	text = text or '[EMPTY]'

	# Markdown must be properly formatted.
	text = telegramify_markdown.markdownify(text)

	return text


def build_info_text(text):
	return f'[INFO]\n{text}'
	
	
def build_error_text(text):
	return f'[ERROR]\n{text}'


def reply_info(bot, msg, text):
	bot.send_message(msg.chat.id, build_info_text(text), reply_to_message_id=msg.id)
	
	
def reply_error(bot, msg, text):
	bot.send_message(msg.chat.id, build_error_text(text), reply_to_message_id=msg.id)


def print_exc(exc, bot, msg):
	traceback.print_exc()
	err_msg = exc.body['message']
	if exc.body['type'] == 'image_generation_user_error':
		# OpenAI returns this error to avoid exposing the moderation reason.
		err_msg = 'The server rejected the prompt'
	reply_error(bot, msg, err_msg)


def reply_chat_msg(bot, msg, text):
	text = process_text(text)
	return bot.reply_to(msg, text, parse_mode='MarkdownV2')


def reply_voice_msg(bot, msg, text, ai):
	return bot.send_voice(msg.chat.id, ai.tts(text), reply_to_message_id=msg.id)