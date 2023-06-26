from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import executor
from aiogram.utils.callback_data import CallbackData
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
import json

from pyrogram.raw.types import text_concat

class ChatBot:
    def __init__(self, token, bot_list, settings_dump, restart):
        self.token = token
        self.bot_list = bot_list
        self.settings_dump = settings_dump
        self.restart = restart

        self.bot = Bot(self.token)
        self.storage = MemoryStorage()
        self.dp = Dispatcher(self.bot, storage=self.storage)
        
        self.settings_callback = CallbackData("type", "item_name", "bot")
        self.type_callback = CallbackData("type", "item_name")
        self.remove_callback = CallbackData("type", "item_name", "channel", "remove")

        self.register_handlers()

    def register_handlers(self):
        self.dp.register_message_handler(
            self.handle_start_command,
            commands=['start'],
            state="*"
        )
        self.dp.register_message_handler(
            self.handle_restart_command,
            commands=['restart'],
            state = "*"
        )
        self.dp.register_callback_query_handler(
            self.bot_settings_menu,
            text_contains="settings",
        )
        self.dp.register_callback_query_handler(
            self.bot_settings_post_text,
            text_contains="post_text",
        )
        self.dp.register_callback_query_handler(
            self.bot_settings_answer_text,
            text_contains="answer_text",
        )

        self.dp.register_callback_query_handler(
            self.account_settings,
            text_contains="account")

        self.dp.register_callback_query_handler(
            self.bot_settings_channel,
            text_contains="schannels")

        self.dp.register_callback_query_handler(
            self.handle_change_time_out,
            text_contains="time_out")

        self.dp.register_callback_query_handler(
            self.remove_channel,
            text_contains="remove_channel")

    async def handle_start_command(self, message: types.Message, state: FSMContext):
        await state.finish()
        # Обработка команды /start
        choice_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="Добавить/удалить канал",
                    callback_data=self.type_callback.new(item_name="schannels")
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="Настройки аккаунтов",
                    callback_data=self.type_callback.new(item_name="account")
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="Изменить время задержки между циклами",
                    callback_data=self.type_callback.new(item_name="time_out")
                )
            ]
        ])
        await message.answer("Выберите действие:", reply_markup=choice_keyboard)

    async def handle_change_time_out(self, call: types.CallbackQuery):
        await call.message.edit_text(f"Сейчас задержка между циклами рассылки:\n{self.settings_dump['time_out']}\nВведите новое время задержки:")
        state = self.dp.current_state(user=call.from_user.id, chat=call.message.chat.id)
        await state.set_state("change_time_out")
        self.dp.register_message_handler(self.change_time_out, state="change_time_out")

    async def change_time_out(self, message: types.Message, state: FSMContext):
        try:
            self.settings_dump["time_out"] = int(message.text)
            await message.answer("Время задержки успешно изменено (Перезапустите бота для применения настроек)")
            await state.finish()
            with open("settings.json", 'w', encoding="utf-8") as file:
                json.dump(self.settings_dump, file, indent=4)
        except:
            await message.answer("Что-то не так")

    async def bot_settings_channel(self, call: types.CallbackQuery):
        choise_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text=f"{i+1}. {channel}", callback_data=self.settings_callback.new(item_name="sdfsdf", bot=channel))] for i, channel in enumerate(self.settings_dump["chat_ids"])])
        await call.message.edit_text("Чтобы удалить чат введите id/username из списка. Чтобы добавить новый - введите его id/username", reply_markup=choise_keyboard)
        state = self.dp.current_state(user=call.from_user.id, chat=call.message.chat.id)
        await state.set_state("add_channel")
        self.dp.register_message_handler(self.add_channel, state="add_channel")

    async def remove_channel(self, call: types.CallbackQuery):
        channel = call.data.split(":")[2]
        remove = call.data.split(":")[3]
        if remove == "1":
            self.settings_dump["chat_ids"].remove(channel)
            await call.message.edit_text("Канал удален (Перезапустите бота для применения настроек)")
        else:
            await call.message.edit_text("Вы отменили удаление канала")

    async def add_channel(self, message: types.Message, state: FSMContext):
        try:
            await state.finish()
            if message.text in self.settings_dump["chat_ids"]:
                choise_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="Да", callback_data=self.remove_callback.new(item_name="remove_channel", channel=message.text, remove="1")), 
                     types.InlineKeyboardButton(text="Нет", callback_data=self.remove_callback.new(item_name="remove_channel", channel=message.text, remove="0"))]])
                await message.answer("Этот чат уже был ранее введён. Хотите его удалить?", reply_markup=choise_keyboard)
                return
            else:
                self.settings_dump["chat_ids"].append(message.text)
                await message.answer("Канал добавлен (Перезапустите бота для применения настроек)")
            with open("settings.json", 'w', encoding="utf-8") as file:
                json.dump(self.settings_dump, file, indent=4)
        except Exception as ex:
            print(ex)
            await message.answer("Что-то не так")

    async def account_settings(self, call: types.CallbackQuery):
        # Обработка команды /start
        choice_account = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(
                text=f"{i + 1}. Бот: {bot.api_id} ({bot.client.me.username})",
                callback_data=self.settings_callback.new(item_name="settings", bot=bot.api_id)
            )]
            for i, bot in enumerate(self.bot_list)
        ])
        await call.message.edit_text("Выберите бота:", reply_markup=choice_account)

    async def handle_restart_command(self, message: types.Message):
        # Обработка команды /restart
        await message.answer("Бот перезапускается...")
        if callable(self.restart):
            self.restart()

    async def bot_settings_menu(self, call: types.CallbackQuery):
        # Обработка выбора настроек бота
        bot_id = call.data.split(":")[2]
        choise_settings_type = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(
                text="Текст рассылки",
                callback_data=self.settings_callback.new(item_name="post_text", bot=bot_id)
            )],
            [types.InlineKeyboardButton(
                text="Текст ответа",
                callback_data=self.settings_callback.new(item_name="answer_text", bot=bot_id)
            )]
        ])
        await call.message.edit_text("Выберите настройки:", reply_markup=choise_settings_type)

    async def bot_settings_post_text(self, call: types.CallbackQuery):
        # Обработка выбора изменения текста рассылки
        bot_id = call.data.split(":")[2]
        bot = next((bot for bot in self.bot_list if str(bot.api_id) == bot_id), None)
        if bot:
            await call.message.edit_text(f"Сейчас сообщение рассылки:\n{bot.chat_text}\nВведите новое сообщение для рассылки")
            await call.answer()
            state = self.dp.current_state(user=call.from_user.id, chat=call.message.chat.id)
            await state.set_state("enter_post_text")
            self.bot_id = bot_id
            self.dp.register_message_handler(self.handle_enter_post_text, state="enter_post_text")
        else:
            await call.answer("Ошибка: Бот не найден.")

    async def bot_settings_answer_text(self, call: types.CallbackQuery):
        # Обработка выбора изменения текста ответа
        bot_id = call.data.split(":")[2]
        bot = next((bot for bot in self.bot_list if str(bot.api_id) == bot_id), None)
        if bot:
            await call.message.edit_text(f"Сейчас текст ответа:\n{', '.join(bot.answer_text)}\nВведите новый текст ответа(Через \)")
            await call.answer()
            state = self.dp.current_state(user=call.from_user.id, chat=call.message.chat.id)
            await state.set_state("enter_answer_text")
            self.bot_id = bot_id 
            self.dp.register_message_handler(self.handle_enter_answer_text, state="enter_answer_text")
        else:
            await call.answer("Ошибка: Бот не найден.")


    async def handle_enter_post_text(self, message: types.Message, state: FSMContext):
        await state.finish()
        await message.answer("Текст рассылки успешно обновлен. (Перезапустите бота для установки настроек)")

        # Обновление настроек в JSON-файле
        self.update_settings('chat_text', message.text, self.bot_id)

    async def handle_enter_answer_text(self, message: types.Message, state: FSMContext):
        if len(message.text.split("/")) < 2:
            await message.answer("Ой, что-то не так. Повторите еще раз!")
            return
        await state.finish()
        await message.answer("Текст ответа успешно обновлен.  (Перезапустите бота для установки настроек)")

        # Обновление настроек в JSON-файле
        self.update_settings('answer_text', message.text, self.bot_id)


    def update_settings(self, type, text, bot_id):
        # Обновление настроек в JSON-файле
        # Получение актуальных настроек
        settings = self.load_settings()

        # Обновление текста рассылки и текста ответа для каждого бота в списке
        for bot in settings["accounts"]:
            if str(bot["api_id"]) == bot_id:
                if type == "chat_text":
                    bot[type] = text
                else:
                    bot[type] = [answer for answer in text.split("/")]

        with open("settings.json", 'w', encoding="utf-8") as file:
            json.dump(settings, file, indent=4)

    def load_settings(self):
        return self.settings_dump

    async def set_default_commands(self):
        await self.dp.bot.set_my_commands([
            types.BotCommand("start", "Запустить бота"),
            types.BotCommand("restart", "Перезапуск бота"),
        ])

    async def __run(self, _):
        await self.set_default_commands()
        print("ChatBot is activated")

    def run(self):
        executor.start_polling(self.dp, skip_updates=True, on_startup=self.__run)
