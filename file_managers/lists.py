import os



class ListManager:
    """
    A manager to handle a newline-separated list in a file.
    """

    def __init__(self, list_path):
        self.list_path = list_path
        self.list = []
        if os.path.exists(list_path):
            self._load_list()


    def _load_list(self):
        with open(self.list_path) as file:
            self.list = [int(id) for id in file.readlines()]


    def _save_list(self):
        self.list.sort()
        with open(self.list_path, 'w') as file:
            file.writelines([f'{id}\n' for id in self.list])


    def add(self, id):
        if id not in self.list:
            self.list.append(id)
            self._save_list()


    def remove(self, id):
        if id in self.list:
            self.list.remove(id)
            self._save_list()


    def has(self, id):
        return id in self.list
    

class TelegramWhitelistManager(ListManager):
    """
    A manager to handle a file containing whitelisted Telegram
    user or chat ids.
    """

    def can_use_bot(self, id):
        # There's no risk of id clashing, user ids are positive
        # while chat ones are negative.
        return id in [int(os.environ['TELEGRAM_ADMIN_ID'])] + self.list