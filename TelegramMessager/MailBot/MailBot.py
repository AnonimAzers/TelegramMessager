import asyncio
from email import message
from pyrogram import Client
from pyrogram.handlers import MessageHandler
from aiogram.dispatcher import FSMContext

class MailBot:
    def __init__(self, api_id, api_hash, chat_ids, chat_text, answer_text, time_out, wait):
        self.api_id = api_id
        self.api_hash = api_hash
        self.chat_ids = chat_ids
        self.chat_text = chat_text
        self.answer_text = answer_text
        self.wait = wait
        self.time_out = time_out
        self.in_mailing = []
        
        self.client = Client(name = f"sessions//{api_id}_session", api_id = api_id, api_hash = api_hash)       

    async def mailing(self, user_id):
        print("test")
        await asyncio.sleep(300)
        await self.client.send_message(user_id, self.answer_text[0])
        await asyncio.sleep(3600*24)
        await self.client.send_message(user_id, self.answer_text[1])
        self.in_mailing.remove(user_id)

    async def tracking_messages(self, client, message):
        if str(message.chat.type) == "ChatType.PRIVATE" and message.from_user.id != self.user_id:
            if message.from_user.id not in self.in_mailing:
                self.in_mailing.append(message.from_user.id)
                asyncio.create_task(self.mailing(message.from_user.id))

    async def mailing_by_chats(self, i):
        await asyncio.sleep(self.wait*i)
        while (True):
            for chat_id in self.chat_ids:
                try:
                    await self.client.send_message(chat_id, self.chat_text)
                except:
                    print("Проблема с отправкой сообщения")
                await asyncio.sleep(5)
            await asyncio.sleep(self.time_out)

    def change_answer_text(self, text, id):
        self.answer_text[id] = text

    async def __run(self,i):
        self.client.add_handler(MessageHandler(self.tracking_messages))
        await self.client.start()
        self.user_id = await self.client.get_me()
        self.user_id = self.user_id.id
        asyncio.create_task(self.mailing_by_chats(i))

        print(f"{self.api_id} bot started")

    def run(self, i):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__run(i))