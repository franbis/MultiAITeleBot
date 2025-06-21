# Telebot filters could be used but I feel like decorators give
# more control.

import os

from utils.prompt import get_prompt



def admin_only(func):
	"""Handle a Telegram bot event only if the message sender is the
	software administrator."""

	def wrapper(msg, *args, **kwargs):
		if msg.from_user.id == int(os.environ['TELEGRAM_ADMIN_ID']):
			return func(msg, *args, **kwargs)
		else:
			print(f'ERROR - Not an admin [{msg.from_user.id} ({msg.from_user.username})].')
	return wrapper


def wlisted_only(wlist_man):
	"""Handle a Telegram bot event only if the message sender or the
	chat is whitelisted."""

	def decorator(func):
		def wrapper(msg, *args, **kwargs):
			if wlist_man.can_use_bot(msg.chat.id)\
				or wlist_man.can_use_bot(msg.from_user.id):
				return func(msg, *args, **kwargs)
			else:
				print(f'ERROR - User/Chat not allowed [User: {msg.from_user.id}] [Chat: {msg.chat.id}].')
		return wrapper
	return decorator


def prompt_required(type='text', from_reply=False, bot=None, ai=None, config=None):
	"""
	Extract the prompt from the Telegram message passed to a Telegram bot
	event handler and pass it to the handler.
	
	Args:
		type:			Prompt type.
		from_reply:		If True, msg.reply_to_message will be checked instead.
		bot:			Telegram bot instance.
		ai:				AI instance.
		config:			Bot's configuration manager.
	"""

	def decor(func):
		def wrapper(msg, *args, **kwargs):
			prompt = get_prompt(msg, type=type, from_reply=from_reply, bot=bot, ai=ai, config=config)
			return func(msg, prompt, *args, **kwargs)
		return wrapper
	return decor


def split_cmd(func):
	"""Extract the command and arguments string from a Telegram
	bot event message's text and pass them to the event handler."""

	def wrapper(msg, *args, **kwargs):
		split_command = msg.text.split(' ', 1)
		cmd = split_command[0][1:]
		# Discard the bot id if any.
		cmd = cmd.split('@')[0]
		cmd_args = None
		if len(split_command) > 1:
			cmd_args = split_command[1]

		return func(msg, cmd, cmd_args, *args, **kwargs)
	return wrapper