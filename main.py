import logging
import os
from dotenv import load_dotenv
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

load_dotenv()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

FIRST_MESSAGE, GET_NAME, GET_PHONE, INLINE_BUTTON = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # update - полная иформация о том что произошло
    # update.effective_user - иформация о человеке
    # update.effective_chat - инормация о чате
    # update.effective_message - информация о сообщении
    # context - контекст, в котором мы можем использовать бота

    """отвечаем на кнопку InlineKeyboardButton"""
    query = update.callback_query
    if query:
        await query.answer()
        await query.delete_message()

    keyboard = [["Да", "Нет"], ["Ещё не знаю"]]
    markup = ReplyKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=f"Привет, {update.effective_user.first_name} Хочешь гайд?",
        reply_markup=markup,
    )
    return FIRST_MESSAGE


async def get_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.effective_message.text
    keyboard = [[update.effective_user.first_name]]
    markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Напишите своё имя или нажмите на него",
    )
    context.user_data["answer"] = answer
    if answer == "Да":
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="Чтобы забрать гайд, напиши своё имя.",
            reply_markup=markup,
        )
        return GET_NAME
    else:
        keyboard = [
            [
                InlineKeyboardButton("Да", callback_data="yes"),
                InlineKeyboardButton("Нет", callback_data="no"),
            ]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="Тогда всё!",
            reply_markup=markup,
        )
        return INLINE_BUTTON


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_message.text
    keyboard = [[KeyboardButton("Отправить номер телефона", request_contact=True)]]
    markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Нажмите кнопку чтобы отправить номер телефона",
    )
    context.user_data["name"] = name
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=f"Спасибо, {name}! Напиши свой номер телефона.",
        reply_markup=markup,
    )
    return GET_PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.effective_message.contact.phone_number
    context.user_data["phone"] = phone
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=f"Спасибо, {context.user_data['name']}! Ваш номер телефона: {context.user_data['phone']}.",
    )


async def get_inline_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await (
        query.answer()
    )  # "Спасибо за ответ!", show_alert=True чтобы показать всплывающее окно
    if query.data == "yes":
        await query.edit_message_text(text="Спасибо за ответ!")

    # чтобы перезапустить бота ctrl + C


if __name__ == "__main__":
    application = ApplicationBuilder().token(os.getenv("TOKEN")).build()
    # handler - обработчик, который будет обрабатывать
    # ComandHandler - обработчик, который будет обрабатывать команды
    # MesageHandler - обработчик, который будет обрабатывать сообщения
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            FIRST_MESSAGE: [
                MessageHandler(
                    filters=filters.TEXT & ~filters.COMMAND, callback=get_answer
                )
            ],
            GET_NAME: [
                MessageHandler(
                    filters=filters.TEXT & ~filters.COMMAND, callback=get_name
                )
            ],
            GET_PHONE: [
                MessageHandler(
                    filters=filters.CONTACT | filters.TEXT & ~filters.COMMAND,
                    callback=get_phone,
                    # | filters.Regex('^\d{11}$') можно так проверять номер телефона
                )
            ],
            INLINE_BUTTON: [
                CallbackQueryHandler(callback=get_inline_button, pattern="yes"),
                CallbackQueryHandler(callback=start, pattern="no"),
            ],
        },
        fallbacks=[],
    )

    application.add_handler(conv_handler)

    application.run_polling()
