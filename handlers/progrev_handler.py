from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ContextTypes,
)
from config.states import FIRST_MESSAGE, GET_NAME, GET_PHONE, INLINE_BUTTON
from utils.escape_sym import escape_sym
from handlers.jobs import send_job_message
from datetime import timedelta
from db.users_crud import create_user, get_user, update_user
from logs.logger import logger
from db.user_tags_crud import create_user_tag
from config.config import ADMIN_ID
from handlers.admins_handlers import admin_start


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # update - полная иформация о том что произошло
    # update.effective_user - иформация о человеке
    # update.effective_chat - инормация о чате
    # update.effective_message - информация о сообщении
    # context - контекст, в котором мы можем использовать бота
    if update.effective_user.id == int(ADMIN_ID):
        return await admin_start(update, context)

    """отвечаем на кнопку InlineKeyboardButton"""
    query = update.callback_query
    if query:
        await query.answer()
        await query.delete_message()
    else:
        if not await get_user(update.effective_user.id):
            await create_user(update.effective_user.id)
            logger.info(f"Пользователь {update.effective_user.id} создан 👻")
            await create_user_tag(update.effective_user.id, "Горячий")
            logger.info(f"Пользователь {update.effective_user.id} добавлен в таблицу tags 👻")

    keyboard = [["Да", "Нет"], ["Ещё не знаю"]]
    markup = ReplyKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=escape_sym(
            f"Привет, {update.effective_user.first_name}.\n *Хочешь гайд?*"
        ),
        reply_markup=markup,
        parse_mode="MarkdownV2",
    )
    job = context.job_queue.run_once(
        send_job_message,
        when=timedelta(seconds=30),
        data={"message": "Привет"},
        name=f"send_job_message_{update.effective_user.id}",
        chat_id=update.effective_user.id,
    )
    context.user_data["job_name"] = job.name
    return FIRST_MESSAGE


async def get_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Отменяем запланированное сообщение, если пользователь ответил
    if "job_name" in context.user_data:
        for jobs in context.job_queue.get_jobs_by_name(context.user_data["job_name"]):
            jobs.schedule_removal()
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
        context.job_queue.run_once(
            send_job_message,
            when=timedelta(seconds=30),
            data={"message": "Привет"},
            name="send_job_message",
            chat_id=update.effective_user.id,
        )
        return INLINE_BUTTON


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # lst = context.job_queue.get_jobs_by_name("send_job_message")
    # if lst:
    # for job in lst:
    # job.schedule_removal()
    name = update.effective_message.text
    await update_user(update.effective_user.id, name=name)
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
    await update_user(update.effective_user.id, phone=phone)
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=f"Спасибо, {context.user_data['name']}! Ваш номер телефона: {context.user_data['phone']}.",
    )


async def get_inline_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # "Спасибо за ответ!", show_alert=True чтобы показать всплывающее окно
    if query.data == "yes":
        await query.edit_message_text(text="Спасибо за ответ!")


    # чтобы перезапустить бота ctrl + C
