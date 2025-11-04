import os
from base64 import b64decode

from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from telebot import TeleBot
from telebot.types import BotCommand

# OpenAIError, APIError, APIStatusError.
from openai import APIError


from models.chat import Base,  Message, MessageRole

from utils.versioning import get_version_str
from utils.prompt import extract_img_urls
from utils.messages import edit_chat_msg, print_exc, process_text, reply_error, reply_info, reply_chat_msg, reply_voice_msg
from utils.chat import get_chat, get_or_create_chat, add_telegram_msg, purge_old_chats

from file_managers.config import ConfigurationManager
from file_managers.lists import TelegramWhitelistManager
from ai.managers import OpenAIManager

from decorators.telegram import admin_only, split_cmd, wlisted_only, prompt_required
from args import parser
from utils.telegram import parse_cmd_args



args = parser.parse_args()

# Load the db models.
engine = create_engine(os.environ['DATABASE_URL'], echo=args.verbose)

# SQLite ignores foreign keys. Enable it since referential
# integrity is needed to avoid leaving orphan messages when deleting
# chats.
@event.listens_for(Engine, 'connect')
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
	if 'sqlite' in str(dbapi_connection.__class__):
		cursor = dbapi_connection.cursor()
		cursor.execute("PRAGMA foreign_keys=ON")
		cursor.close()

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Load the config and AI managers.
config = ConfigurationManager(config_path=args.config)
wlist = TelegramWhitelistManager(list_path=args.wlist)
ai = OpenAIManager(api_key=os.environ['OPENAI_API_KEY'], options_path=args.ai_options)

print('Bot configuration path:', args.config)
print('Whitelist path:', args.wlist)
print('AI options path:', args.ai_options)

bot = TeleBot(os.environ['TELEGRAM_API_KEY'], parse_mode=None)

bot_short_descr = "I'm a bot that lets you use various AI models."

bot.set_my_commands([
	BotCommand('help', 'Receive the list of commands in a private chat')
])
bot.set_my_description((
	f'{bot_short_descr}\n'
	'Click the START button or use /start for more details.'
))


# Debug and info ops.


@bot.message_handler(commands=['start'])
@split_cmd
def bot_start(msg, cmd, cmd_args):
	"""Inform about the capabilities of this bot."""
	
	if not cmd_args:
		help_text = (
			f'{bot_short_descr}\n'
			'Click '
			f'[here](https://t.me/{bot.get_me().username}?start=commands)'
			' or use /help to get a list of user commands in a private chat.'
		)
		bot.send_message(msg.chat.id, help_text, parse_mode='Markdown')

	elif cmd_args == 'commands':
		msg.text = '/help'
		send_help(msg)


@bot.message_handler(commands=['help'])
def send_help(msg):
	version_str = get_version_str()
	if version_str:
		version_str = f'{get_version_str()}\n\n'
	else:
		version_str = ''

	cmds = (
		f'{version_str}'

		'User Commands:\n\n'

		'/sysmsg	-	Change the system message for this chat\n'
		'/forget	-	Make the bot forget all the messages from this chat.\n'
		'/chat		-	Chat with the AI\n'
		'/achat		-	Chat with the AI and receive a voice message\n'
		'/oldmsg	-	Show the oldest message the bot remembers\n'
		'/to		-	Translate a message\n'
		'/stt		-	Transcribe a message\n'
		'/tts		-	Make a voice message out of a textual one\n'
		'/img		-	Generate an image\n'

		"\n**NOTE**: You don't need to use /chat or /achat, simply reply with text or voice instead."

		'\n\nYou can find the full list of commands '
		'[here](https://github.com/franbis/MultiAITeleBot/blob/main/commands.md)'
		'.'
	)
	bot.send_message(
		msg.from_user.id,
		cmds,
		parse_mode='Markdown',
		disable_web_page_preview=True
	)


@bot.message_handler(commands=['status'])
@wlisted_only(wlist)
def bot_status(msg):
	"""Show the bot's status."""
	bot.send_message(msg.chat.id, 'ONLINE')


@bot.message_handler(commands=['chatinfo'])
@admin_only
def bot_get_chat_info(msg):
	"""Show the id of the chat the message was sent in."""
	reply_info(bot, msg, f'Chat ID: {msg.chat.id}')


# Config ops.


@bot.message_handler(commands=['config', 'conf'])
@split_cmd
@admin_only
def bot_config(msg, cmd, cmd_args):
	"""
	Handle a configuration file.
	Format: /config <bot|ai> <get|set|reset|show> [key_path [value]]
	"""

	parsed_cmd_args = parse_cmd_args(
		bot, msg, cmd_args,
		('configuration type', ['bot', 'ai'], None),
		('operation type', ['get', 'set', 'reset', 'show'], None)
	)
	if not parsed_cmd_args:
		return

	cmd_args, cfg_type, op = parsed_cmd_args

	cfg = None
	if cfg_type == 'bot':
		cfg = config
	elif cfg_type == 'ai':
		cfg = ai.options

	if op == 'show':
		bot.send_message(
			msg.chat.id,
			f'```json\n{cfg.to_json(indent=4, sort_keys=True)}\n```',
			parse_mode='Markdown'
		)
		return
	
	else:
		parsed_cmd_args = parse_cmd_args(bot, msg, cmd_args, ('key path', None, None))
		if not parsed_cmd_args:
			return

		cmd_args, key_path = parsed_cmd_args

		try:
			if op == 'get':
				reply_info(bot, msg, f'The value at "{key_path}" is set to: {cfg.get(key_path)}')
			
			elif op == 'reset':
				cfg.reset(key_path)
				reply_info(bot, msg, f'"{key_path}" was reset to its default value ({cfg.get(key_path)}).')

			elif op == 'set':
				if parse_cmd_args(bot, msg, cmd_args, ('value', None, None)):
					try:
						cfg.set(key_path, cmd_args, match_type=True)
						reply_info(bot, msg, f'"{key_path}" was set to: {cfg.get(key_path)}')
					except ValueError:
						reply_error(bot, msg, f'The value you specified for "{key_path}" is invalid.')

		except KeyError:
			reply_error(bot, msg, f'"{key_path}" is not present in the "{cfg_type}" configuration.')


@bot.message_handler(commands=['wlist'])
@split_cmd
@admin_only
def bot_wlist(msg, cmd, cmd_args):
	"""
	Handle the whitelist.
	Format: /wlist <has|add|remove|show> [id]
	"""

	parsed_cmd_args = parse_cmd_args(
		bot, msg, cmd_args,
		('operation type', ['has', 'add', 'remove', 'show'], None)
	)
	if not parsed_cmd_args:
		return

	cmd_args, op = parsed_cmd_args

	if op == 'show':
		list_str = '\n'.join([str(id) for id in wlist.list])
		bot.send_message(
			msg.chat.id,
			f"```\n{list_str}\n```",
			parse_mode='Markdown'
		)
		return
	
	else:
		parsed_cmd_args = parse_cmd_args(bot, msg, cmd_args, ('id', None, int))
		if not parsed_cmd_args:
			return

		_, id = parsed_cmd_args

		if op == 'has':
			reply_info(bot, msg, f'"{id}" is{" not" if not wlist.has(id) else ""} present in the whitelist.')

		if op == 'add':
			wlist.add(id)
			reply_info(bot, msg, f'"{id}" was added to the whitelist.')

		elif op == 'remove':
			wlist.remove(id)
			reply_info(bot, msg, f'"{id}" was removed from the whitelist.')

			
# Chat ops.


@bot.message_handler(commands=['sysmsg'])
@split_cmd
@wlisted_only(wlist)
def bot_set_sys_msg(msg, cmd, cmd_args):
	"""
	Handle the chat's system message.
	Format: /sysmsg <set|reset|show> [message]
	"""

	parsed_cmd_args = parse_cmd_args(
		bot, msg, cmd_args,
		('operation type', ['set', 'reset', 'show'], None)
	)
	if not parsed_cmd_args:
		return

	cmd_args, op = parsed_cmd_args

	with Session() as ses:
		chat = get_chat(ses, msg.chat.id)

		if op == 'show':
			if chat:
				reply_info(bot, msg, f"Current system message: {chat.sys_msg}")
			else:
				reply_info(bot, msg, f"This chat hasn't been registered yet.")

		elif op == 'reset':
			default_sys_msg = config.get('chat.default_sys_msg')
			if chat:
				chat.sys_msg = default_sys_msg
				ses.commit()
			reply_info(bot, msg, f"The system message was reset to default: {default_sys_msg}")

		elif op == 'set':
			if parse_cmd_args(bot, msg, cmd_args, ('message', None, None)):
				chat = get_or_create_chat(ses, msg.chat.id, config)
				chat.sys_msg = cmd_args
				ses.commit()

				reply_info(bot, msg, f"The system message was set to: {chat.sys_msg}")


@bot.message_handler(commands=['purgechats'])
@admin_only
def bot_purge_chats(msg):
	with Session() as ses:
		purge_old_chats(ses, config)
		ses.commit()
		reply_info(bot, msg, 'Old chats were purged.')


@bot.message_handler(commands=['cansee'])
@wlisted_only(wlist)
def bot_cansee(msg):
	"""Tell if there are images in the chat's messages as that means the
	vision model may be used."""

	has_visual_content = False
	with Session() as ses:
		if chat := get_chat(ses, msg.chat.id):
			has_visual_content = ai.check_for_visual_content(chat.messages)
	
	if has_visual_content:
		reply_info(bot, msg, 'Images were referenced in the conversation.')
	else:
		reply_info(bot, msg, 'No images were referenced in the conversation.')


@bot.message_handler(commands=['forget'])
@wlisted_only(wlist)
def bot_forget(msg):
	"""Erase the bot's memory for this chat."""

	with Session() as ses:
		if chat := get_chat(ses, msg.chat.id):
			chat.erase()
			ses.commit()

	reply_info(bot, msg, f"Past messages from this chat erased from the bot's memory.")


@bot.message_handler(commands=['chat', 'llm', 'gpt', 'achat', 'allm', 'agpt'])
@prompt_required(bot=bot, ai=ai, config=config)
@wlisted_only(wlist)
def bot_chat(msg, prompt):
	"""Chat with the AI, by either a textual or a voice message, and show
	the response."""

	def reply(text):
		if msg.text.startswith('/a'):
			# /allm (audio prompt).
			return reply_voice_msg(bot, msg, text, ai)
		else:
			# /llm (text prompt).
			return reply_chat_msg(bot, msg, text)
		
	
	def stream_text(msg, content_chunk):
		return edit_chat_msg(bot, msg, content_chunk)
		

	if prompt:
		text, img_urls = extract_img_urls(bot, msg, prompt)
		content = ai.build_msg_content([text], img_urls)

		with Session() as ses:
			# Don't commit until there is absolute certainty that the AI
			# replied.
			add_telegram_msg(
				ses,
				msg,
				config,
				content=content,
				role=MessageRole.user
			)
			chat = get_or_create_chat(ses, msg.chat.id, config)
			model, max_tokens = ai.get_preferred_model_settings(chat.messages)

			try:
				should_stream = config.get('chat.stream') and not msg.text.startswith('/a')

				resp = ai.chat(
					chat.get_context(),
					model=model,
					max_tokens=max_tokens,
					stream=should_stream
				)

				resp_msg_content = ''
				if should_stream:
					telegram_resp_msg = None
					for chunk in ai.get_choice_stream_chunks(resp):
						# TODO - Stream each chunk using the upcoming Telegram
						#			response streaming feature announced here:
						#			https://telegram.org/blog/comments-in-video-chats-threads-for-bots#threads-and-streaming-responses-for-ai-bots
						#			The documentation for that feature will
						#			be published here:
						#			https://core.telegram.org/bots/api
						resp_msg_content += ai.get_content(chunk)
						if not telegram_resp_msg:
							telegram_resp_msg = reply(resp_msg_content)
						else:
							# TODO - Pass the text chunk rather than the whole text (Assuming
							#			the Telegram stream feature will automatically append
							#			the chunk to the pre-existing text).
							telegram_resp_msg = stream_text(telegram_resp_msg, resp_msg_content)
				else:
					resp_msg_content = ai.get_content(resp)
					telegram_resp_msg = reply(resp_msg_content)
				

				# Add the AI's reply to the db and commit.
				add_telegram_msg(
					ses,
					telegram_resp_msg,
					config,
					process_text(resp_msg_content),
					MessageRole.assistant
				)

				ses.commit()
			
			except APIError as e:
				print_exc(e, bot, msg)


@bot.message_handler(commands=['oldmsg'])
@wlisted_only(wlist)
def bot_oldmsg(msg):
	"""Show the oldest message in the chat that the bot has access
	to."""

	# Get the oldest message.
	oldest_msg = None
	with Session() as ses:
		if chat := get_chat(ses, msg.chat.id):
			oldest_msg = chat.messages.order_by(Message.id.asc()).first()

	# Show the oldest message.
	if oldest_msg:
		bot.send_message(
			msg.chat.id,
			'☝ This is the oldest message the bot has access to',
			reply_to_message_id=oldest_msg.id
		)
	else:
		bot.reply_to(msg, 'Could not find any message on this chat.')


# Other AI ops.


@bot.message_handler(commands=['translate', 'to'])
@prompt_required(from_reply=True, bot=bot, ai=ai, config=config)
@wlisted_only(wlist)
def bot_translate(msg, prompt):
	"""
	Translate the quoted message's text to the specified language.
	Format: /to <language>
	"""

	lang = msg.text.split(' ', 1)[1]

	try:
		resp = ai.translate(prompt, lang)
		trans = resp.choices[0].message.parsed
		trans.translated_text = process_text(trans.translated_text)
		
		# Show the translated text.
		bot.send_message(
			msg.chat.id,
			f'[{trans.src_lang}->{trans.dst_lang}] {trans.translated_text}',
			reply_to_message_id=msg.reply_to_message.id
		)
		
	except APIError as e:
		print_exc(e, bot, msg)


@bot.message_handler(commands=['stt'])
@prompt_required(type='audio', from_reply=True, bot=bot, config=config)
@wlisted_only(wlist)
def bot_stt(msg, prompt):
	"""Transcribe the quoted message's text."""

	if prompt:
		try:
			stt_resp = ai.stt(prompt)
			bot.send_message(msg.chat.id, stt_resp.text, reply_to_message_id=msg.id)
			
		except APIError as e:
			print_exc(e, bot, msg)


@bot.message_handler(commands=['tts'])
@prompt_required(from_reply=True)
@wlisted_only(wlist)
def bot_tts(msg, prompt):
	"""Turn the quoted message's text to speech."""
	if prompt:
		try:
			tts_resp = ai.tts(prompt)
			bot.send_voice(msg.chat.id, tts_resp, reply_to_message_id=msg.id)
			
		except APIError as e:
			print_exc(e, bot, msg)


@bot.message_handler(commands=['image', 'img', 'picture', 'pic'])
@prompt_required()
@wlisted_only(wlist)
def bot_dalle(msg, prompt):		
	"""Generate an image based on the prompt."""
	if prompt:
		try:
			resp = ai.gen_imgs(
				prompt,
				n=1,
				response_format='b64_json'
			)
			img_data = b64decode(resp.data[0].b64_json)
			
			bot.send_photo(
				msg.chat.id,
				#images_response.data[0].url,
				img_data,
				caption=prompt,
				reply_to_message_id=msg.id
			)
			
		except APIError as e:
			print_exc(e, bot, msg)


# Non-command ops.
# The events below are for messages either received from a private
# chat or that are replies to a bot's message.
# Redirect them to simulate a command message.


@bot.message_handler(content_types=['text'])
@wlisted_only(wlist)
def text_msg_event(msg):
	if (msg.chat.type == 'private')\
		or (msg.reply_to_message and (msg.reply_to_message.from_user.id == bot.user.id)):
		if not msg.text.startswith('/'):
			# Simulate a command message.
			msg.text = f'/chat {msg.text}'
			bot_chat(msg)


@bot.message_handler(content_types=['voice'])
@wlisted_only(wlist)
def msg_event(msg):
	if (msg.chat.type == 'private')\
		or (msg.reply_to_message and (msg.reply_to_message.from_user.id == bot.user.id)):
		if msg.voice:
			# Simulate a command message.
			msg.text = '/achat'
			# Reply to itself since /allm needs a quoted audio.
			msg.reply_to_message = msg
			bot_chat(msg)


@bot.message_handler(content_types=['photo'])
@wlisted_only(wlist)
def handle_photo(msg):
	if (msg.chat.type == 'private')\
		or (msg.reply_to_message and (msg.reply_to_message.from_user.id == bot.user.id)):
		if not msg.caption.startswith('/'):
			# Simulate a command message.
			msg.text = f'/chat {msg.caption}'
			# Reply to itself since bot_chat() checks for images
			# in the quoted msg.
			msg.reply_to_message = msg
			bot_chat(msg)


# Misc ops.


@bot.my_chat_member_handler()
def handle_my_chat_member(msg):
	status = msg.new_chat_member.status

	if status == 'member':
		if not args.no_introduce:
			# The bot joined a group, simulate a /start command.
			msg.text = '/start'
			bot_start(msg)

	elif status == 'left':
		# The bot left the group, delete the chat and its messages
		# from the database.
		with Session() as ses:
			if chat := get_chat(ses, msg.chat.id):
				ses.delete(chat)
				ses.commit()
		

bot.infinity_polling()