import traceback

import telegramify_markdown

from telebot import apihelper
from telebot.apihelper import ApiTelegramException



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
	bot.send_message(
		msg.chat.id,
		build_info_text(text),
		message_thread_id=msg.message_thread_id,
		reply_to_message_id=msg.id
	)
	
	
def reply_error(bot, msg, text):
	bot.send_message(
		msg.chat.id,
		build_error_text(text),
		message_thread_id=msg.message_thread_id,
		reply_to_message_id=msg.id
	)


def print_exc(exc, bot, msg):
	traceback.print_exc()
	err_msg = exc.body['message']
	if exc.body['type'] == 'image_generation_user_error':
		# OpenAI returns this error to avoid exposing the moderation reason.
		err_msg = 'The server rejected the prompt'
	reply_error(bot, msg, err_msg)


def reply_chat_msg(bot, msg, text):
	text = process_text(text)
	return bot.reply_to(
		msg,
		text,
		message_thread_id=msg.message_thread_id,
		parse_mode='MarkdownV2'
	)


def reply_voice_msg(bot, msg, text, ai):
	return bot.send_voice(
		msg.chat.id,
		ai.tts(text),
		message_thread_id=msg.message_thread_id,
		reply_to_message_id=msg.id
	)


def edit_chat_msg(bot, msg, text):
	text = process_text(text)
	return bot.edit_message_text(text, msg.chat.id, msg.id, parse_mode='MarkdownV2')


def reply_chat_msg_stream(bot, msg, chunks):
	full_text = ''
	try:
		for chunk in chunks:
			full_text += chunk
			apihelper._make_request(
				bot.token,
				'sendMessageDraft',
				method='post',
				params={
					'chat_id': msg.chat.id,
					'message_thread_id': msg.message_thread_id,
					'draft_id': msg.id,
					'text': process_text(full_text),
					'parse_mode': 'MarkdownV2',
					# Drafts do not support replies.
					# 'reply_parameters': {
					# 	'message_id': msg.id,
					# 	'chat_id': msg.chat.id
					# }
				}
			)
	except ApiTelegramException as e:
		if e.error_code == 429:
			# A 'Too many requests' error was received, it's not
			# worth waiting 4 seconds (suggested by the Telegram API)
			# before retrying. So ignore it, send the text that was
			# built till now and tell the user what happened.
			full_text += '\n\n' + build_error_text('The "Too many requests" error was received from the Telegram API.')

	return bot.reply_to(
		msg,
		process_text(full_text),
		message_thread_id=msg.message_thread_id,
		parse_mode='MarkdownV2'
	)