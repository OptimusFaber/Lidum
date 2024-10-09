from datetime import datetime, timezone

from aiogram import types
from aiogram.types import BotCommand, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .. import get_app, create_bot, get_session
from ..config import APP_NAME, ADMIN_IDS, BOT_USERNAME
from ..utils.db import Telegram_User, tg_users, event_by_id
from ..utils.db import tg_user_by_id, event_ids_by_tg_id
from ..utils.db import add_database_entries
from .newsletter import Newsletter, Newsletter_Form
from ..utils.crypto import encrypt

app = get_app()
Session = get_session(app)[1]
bot, dp, router = create_bot(app)

newsletter = Newsletter(bot)


@router.callback_query(lambda c: c.data == "events_handler")
async def events_handler(callback: CallbackQuery):

    user_id = callback.message.chat.id

    session = Session()
    tg_user = tg_user_by_id(telegram_id=user_id, session=session)

    markup = InlineKeyboardBuilder()

    if tg_user is None:
        markup.button(text="Back", callback_data="back_to_start")
        await callback.message.edit_text(text="You do not have any created events", reply_markup=markup.as_markup())

    else:
        event_ids = event_ids_by_tg_id(telegram_id=user_id, session=session)

        for id in event_ids:
            event = event_by_id(event_id=id, session=session)

            markup.button(text=event.event_name, url=f"https://t.me/{BOT_USERNAME}/{APP_NAME}?startapp=minter-{encrypt(id)}")

        markup.button(text="Back", callback_data="back_to_start")
        markup.adjust(1)

        await callback.message.edit_text(text="Select an event:", reply_markup=markup.as_markup())

    session.close()


@router.callback_query(lambda c: c.data == "cancel_newsletter")
async def cancel_newsletter(callback: CallbackQuery):
    await newsletter.delete_preview_msg()


@router.callback_query(lambda c: c.data == "send_newsletter")
async def send_newslwetter(callback: CallbackQuery):

    session = Session()
    tg_users_ids = [user.id for user in tg_users(session)]
    session.close()

    await newsletter.send_newsletter(tg_users_ids)

    await callback.message.delete()
    await callback.message.answer(text="The newsletter has been sent.")


@router.message(Newsletter_Form.newsletter_state)
async def set_newsletter_data(message: types.Message, state: FSMContext):

    markup = InlineKeyboardBuilder()

    markup.button(text="Send", callback_data="send_newsletter")
    markup.button(text="Cancel", callback_data="cancel_newsletter")

    markup.adjust(1)

    await newsletter.create_newsletter(message=message, state=state, preview_msg_markup=markup.as_markup())


@router.callback_query(lambda c: c.data and c.data.startswith("newsletter:"))
async def newsletter_handler(callback: CallbackQuery, state: FSMContext):

    markup = InlineKeyboardBuilder()
    command = callback.data.split(":")[1]

    match command:

        case "create":

            markup.button(text="Cancel", callback_data="back_to_admin")

            await callback.message.edit_text(
                text="Send a message that should be forwarded to everyone:",
                reply_markup=markup.as_markup(),
            )

            await state.update_data(message_id=callback.message.message_id, chat_id=callback.message.chat.id)

            await state.set_state(Newsletter_Form.newsletter_state)


async def admin_message(message: types.Message, edit: bool = False):

    answer_message = "You do not have access rights to this panel."
    reply_markup = None

    if str(message.chat.id) in ADMIN_IDS:

        markup = InlineKeyboardBuilder()

        markup.button(text="Create a newsletter", callback_data="newsletter:create")

        markup.adjust(1)

        answer_message = "Welcome to the admin panel!"
        reply_markup = markup.as_markup()

    if edit:
        await message.edit_text(answer_message, reply_markup=reply_markup)

    else:
        await message.answer(answer_message, reply_markup=reply_markup)


async def start_message(message: types.Message, edit: bool = False):

    session = Session()

    user_id = message.chat.id
    user = tg_user_by_id(telegram_id=user_id, session=session)

    # Запись id пользователя в БД
    if user is None:

        new_tg_user = Telegram_User(
            id=user_id,
            username=message.from_user.username,
        )

        add_database_entries(entries=new_tg_user, session=session)

    else:
        if user.username is None:
            user.username = message.from_user.username

        user.last_enter = datetime.now(timezone.utc)
        session.commit()

    session.close()

    markup = InlineKeyboardBuilder()

    markup.button(text="Mini-app", url=f"https://t.me/{BOT_USERNAME}?startapp")
    markup.button(text="My events", callback_data="events_handler")
    markup.button(text="Subscribe", url="https://t.me/lidumapp")
    markup.button(text="TechSupport", url="https://t.me/LidumSupport")

    markup.adjust(1, 1, 2)

    if edit:
        await message.edit_text(text="Welcome to LidumBot!", reply_markup=markup.as_markup())

    else:
        await message.answer(text="Welcome to LidumBot!", reply_markup=markup.as_markup())


@router.callback_query(lambda c: c.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery, state: FSMContext):
    await admin_message(callback.message, edit=True)
    await state.clear()


@router.callback_query(lambda c: c.data == "back_to_start")
async def back_to_start(callback: CallbackQuery):
    await start_message(callback.message, edit=True)


@router.message(Command("admin"))
async def admin(message: types.Message):
    await admin_message(message)


@router.message(Command("start"))
async def start(message: types.Message):
    await start_message(message)


async def set_commands():
    commands = [
        BotCommand(command="start", description="Launching the bot"),
    ]

    await bot.set_my_commands(commands)


if __name__ == "__main__":
    dp.startup.register(set_commands)
    dp.run_polling(bot)
