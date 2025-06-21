from utils.messages import reply_error



def get_telegram_file_bytes(bot, file_id):
	"""Download a file stored in the Telegram servers and return its content."""
	cloud_file = bot.get_file(file_id)
	#url = f'https://api.telegram.org/file/bot{os.environ['TELEGRAM_API_KEY']}/{cloud_file.file_path}'
	return bot.download_file(cloud_file.file_path)


def parse_cmd_args(bot, msg, args_str, *parms_data):
	"""
	Parse a command arguments string into separate arguments, return
	the part of string that was not parsed and each parsed argument.
	
	Args:
		bot:			Telegram bot.
		msg:			Telegram message.
		args_str:		Command arguments string.
		parms_data:		A list of parameter data tuples, where each
						tuple contains:
						- Display name (str)
						- Allowed choices (list)
						- Type (type)
	"""

	args_str = args_str or ''

	split_args = args_str.split(' ', len(parms_data))
	# split() returns 1 element if there's no separator occurrence, so
	# use an empty list in that case.
	split_args = [] if split_args == [''] else split_args

	parsed_args = []

	for i, arg in enumerate(split_args[:len(parms_data)]):
		parm_name, parm_items, parm_type = parms_data[i]

		if parm_items and (arg not in parm_items):
			reply_error(bot, msg, f"{parm_name} must be one of these: [{', '.join(parm_items)}].")
			return
		
		if parm_type:
			try:
				arg = parm_type(arg)
			except ValueError:
				reply_error(bot, msg, f"{parm_name} must be of type '{parm_type.__name__}'.")
				return
			
		parsed_args.append(arg)

	if len(split_args) < len(parms_data):
		# Get the missing arg data.
		parm_name, _, _ = parms_data[len(split_args)]
		reply_error(bot, msg, f'You must specify the {parm_name}.')
		return

	return ' '.join(split_args[len(parsed_args):]), *parsed_args