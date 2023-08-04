import logging

import telegram.constants as constants
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

from openai_helper import OpenAIHelper

# Chat-GPT3 Telegram Bot
class ChatGPT3TelegramBot:
    # GPT-3 CONFIGURATION
    def __init__(self, config: dict, openai: OpenAIHelper):
        self.config = config                # :param config: Словник з конфігурацією бота
        self.openai = openai                # :param openai: OpenAIHelper обʼєкт
        # self.disallowed_message = "Вибачте, але вам не дозволено користуватись цим ботом." #:param disallowed_message: Повідомлення про відсутність доступу

# HELP message
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text("/reset - Оновлює бесіду\n"
                                        "[Будь яке повідомлення] - Відправляє ваше повідомлення до AI\n"
                                        "/help - Меню помічника\n\n",
                                        disable_web_page_preview=True)

# RESET conversation
    async def reset(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_allowed(update):
            logging.warning(f'User {update.message.from_user.name} is not allowed to reset the conversation')
            await self.send_disallowed_message(update, context)
            return

        logging.info(f'Resetting the conversation for user {update.message.from_user.name}...')

        chat_id = update.effective_chat.id
        self.openai.reset_chat_history(chat_id=chat_id)
        await context.bot.send_message(chat_id=chat_id, text='Done!')

# PROMPT --React to incoming messages and respond accordingly.
    async def prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # if not await self.is_allowed(update):
        #    logging.warning(f'User {update.message.from_user.name} is not allowed to use the bot')
        #    await self.send_disallowed_message(update, context)
        #     return

        logging.info(f'New message received from user {update.message.from_user.name}')
        chat_id = update.effective_chat.id
        await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.TYPING)

        response = self.openai.get_chat_response(chat_id=chat_id, query=update.message.text)
        await context.bot.send_message(
            chat_id=chat_id,
            reply_to_message_id=update.message.message_id,
            parse_mode=constants.ParseMode.MARKDOWN,
            text=response
        )

# # MESSAGE -DISALLOWED
#     async def send_disallowed_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
#         await context.bot.send_message(
#             chat_id=update.effective_chat.id,
#             text=self.disallowed_message,
#             disable_web_page_preview=True
#         )
#
# # ERRORS
#     async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
#         logging.debug(f'Exception while handling an update: {context.error}')
#
# # ALLOWED USERS
#     async def is_allowed(self, update: Update) -> bool:
#         if self.config['allowed_user_ids'] == "*":
#             return True
#
#         allowed_user_ids = self.config['allowed_user_ids'].split(',')
#         if str(update.message.from_user.id) in allowed_user_ids:
#             return True
#         return False

# START BOT
    def run(self):
        application = ApplicationBuilder().token(self.config['token']).build()

        application.add_handler(CommandHandler('reset', self.reset))
        application.add_handler(CommandHandler('help', self.help))
        application.add_handler(CommandHandler('start', self.help))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.prompt))

        #application.add_error_handler(self.error_handler)

        application.run_polling()
