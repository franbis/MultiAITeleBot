import traceback



def process_text(text):
	"""Replaces a text with a representation of emptiness.
	Useful because Telegram will throw an error if the text in
	a message is empty."""
	return text if text else '[EMPTY]'


def build_info_text(text):
	return f'[INFO]\n{text}'
	
	
def build_error_text(text):
	return f'[ERROR]\n{text}'


def reply_info(bot, msg, text):
	bot.send_message(msg.chat.id, build_info_text(text), reply_to_message_id=msg.id)
	
	
def reply_error(bot, msg, text):
	bot.send_message(msg.chat.id, build_error_text(text), reply_to_message_id=msg.id)


def print_exc(exc, msg):
	traceback.print_exc()
	reply_error(msg, exc.body['message'])