import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

load_dotenv()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #update - полная иформация о том что произошло
    #update.effective_user - иформация о человеке
    #update.effective_chat - инормация о чате
    #update.effective_message - информация о сообщении
    # context - контекст, в котором мы можем использовать бота
    await context.bot.send_message(
        chat_id=update.effective_user.id, text=f'Привет, {update.effective_user.first_name}'
    )
    # чтобы перезапустить бота ctrl + C


if __name__ == "__main__":
    application = ApplicationBuilder().token(os.getenv('TOKEN')).build()
    # handler - обработчик, который будет обрабатывать 

    application.add_handler(CommandHandler("start", start))

    application.run_polling()