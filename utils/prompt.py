import re
from utils.media import create_image_url, speed_up_audio
from utils.telegram import get_telegram_file_bytes



def find_msg_audio(msg):
	"""Find audio content in a Telegram message."""
	return msg.audio if msg.audio else msg.voice


def prepare_audio(bot, msg_audio, config):
	"""Build an audio data tuple to pass as "audio" argument to the AI."""
	file_info = bot.get_file(msg_audio.file_id)
	file_bytes = bot.download_file(file_info.file_path)
	
	# Speed-up the audio wave to save on bandwidth and reduce API usage.
	file_bytes = speed_up_audio(
		file_bytes,
		speed=config.get('prompt.audio.speed'),
		chunk_size=config.get('prompt.audio.chunk_size'),
		crossfade=config.get('prompt.audio.crossfade')
	)
	
	# NOTE: OpenAI infers the file format by reading the filename extension.
	#		So we use OGG as that's the format audio files are compressed
	#		into when recording within Telegram.
	return '.ogg', file_bytes


def get_prompt(msg, type='text', from_reply=False, bot=None, ai=None, config=None):
	"""
	Get the prompt from a Telegram message or quoted message.
	The prompt can be either textual or an audio file. If the text starts
	with a command then the right part of the text will be considered to
	be the prompt.
	
	Args:
		msg:			Telegram message.
		type:			Prompt type.
		from_reply:		If True, msg.reply_to_message will be checked instead.
		bot:			Telegram bot instance.
		ai:				AI instance.
		config:			Bot's configuration manager.
	"""
	
	prompt = None

	if from_reply:
		msg = msg.reply_to_message
	
	if msg:
		msg_audio = find_msg_audio(msg)
		if msg_audio:
			audio = prepare_audio(bot, msg_audio, config=config)
			if type == 'text':
				prompt = ai.stt(audio).text
			elif type == 'audio':
				prompt = audio
			
		else:
			if type == 'text':
				prompt = msg.text
				if msg.text.startswith('/'):
					# Get the part after the command.
					prompt = ''.join(msg.text.split(' ', 1)[1:])
	
	return prompt if prompt else None


def gen_indices(index_start=0):
	"""Indices generator. Useful to reference images in text when passing
	them to the AI."""

	i = index_start
	while True:
		yield i
		i += 1

	
def find_e_replace_img_urls(text, index_start=1):
	"""Find URLs within a string, return the URLs found and the string with the
	URLs replaced by indexed image labels."""
	urls_regex = 'https?:\/\/\S+'
	indeces = gen_indices(index_start)
	url_matches = re.findall(urls_regex, text)
	in_text_w_refs = re.sub(urls_regex, lambda m: f'[image {next(indeces)}]', text)
	
	return url_matches, in_text_w_refs


def extract_img_urls(bot, msg, text):
	"""
	Return a touple with the text with URLs replaced by indexed image labels and
	the image URLs found in the text or the URL referencing an image present
	in a Telegram message.

	NOTE: There can only be one medium attachment per Telegram message, as media
			are actually sent through multiple messages and linked together by the
			media_group_id. In order to download media from a media group we'd need
			to write a system that catches the media as they get sent.
			See https://github.com/python-telegram-bot/python-telegram-bot/wiki/Frequently-requested-design-patterns#how-do-i-deal-with-a-media-group
			for further information.

	Args:
		bot:	Telegram bot instance.
		msg:	Telegram message containing images.
		text:	String containing image URLs.
	"""
	
	img_urls = []
	if msg.reply_to_message and (msg.reply_to_message.content_type == 'photo'):
		# NOTE: 'photo'' is a list where each item is a version of the same photo with
		#		a different resolution, with the last one having the highest resolution.
		#		See https://stackoverflow.com/questions/58674646/telegram-bot-api-using-getfile-with-a-high-quality-photos-file-id-yields
		#		for further information.
		
		# NOTE: file_unique_id can't be used to download media.

		# The first item from the 'photo' list is what gets used as media preview, pick it
		# as the AI is good at analyzing even low-res images.
		file_bytes = get_telegram_file_bytes(bot, msg.reply_to_message.photo[0].file_id)
		url = create_image_url(file_bytes)
		img_urls.append(str(url))
	
	text_img_urls, text = find_e_replace_img_urls(text, index_start=len(img_urls) + 1)
	img_urls += text_img_urls

	return text, img_urls
