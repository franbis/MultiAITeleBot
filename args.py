import argparse



parser = argparse.ArgumentParser(description='A Telegram bot that leverages AI')

parser.add_argument('--config', default='config.json', help='Configuration path')
parser.add_argument('--ai_options', default='ai_options.json', help='AI Options path')
parser.add_argument('--wlist', default='whitelist.txt', help='Whitelist path')
parser.add_argument('--no_introduce', action='store_true', help="Don't send a /start command automatically when the bot joins a group")
parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose mode')