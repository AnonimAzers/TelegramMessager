from aiogram.utils import executor
from MailBot.MailBot import MailBot
from ChatBot.ChatBot import ChatBot
import json

import os
import sys

def restart_script():
    python = sys.executable
    script = os.path.abspath(__file__)
    os.execv(python, [python, script])

def main():
    print("main")
    with open("settings.json", "r+", encoding="utf-8") as settings_file:
        settings = json.load(settings_file)
    bot_list = [MailBot(account["api_id"], account["api_hash"], settings["chat_ids"], account["chat_text"], account["answer_text"], settings["time_out"], settings["wait"]) for account in settings["accounts"]]
    chat_bot = ChatBot(settings["ChatBotToken"], bot_list, settings, restart_script)
    for i, bot in enumerate(bot_list):
        bot.run(i)
    chat_bot.run()

if __name__ == "__main__":
    main()