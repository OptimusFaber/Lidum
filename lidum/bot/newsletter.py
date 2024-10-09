from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


class Newsletter_Form(StatesGroup):
    newsletter_state = State()


class Newsletter:

    def __init__(self, bot: Bot):
        self.bot = bot

    async def create_newsletter(
        self,
        message: Message,
        state: FSMContext,
        preview_msg_markup: InlineKeyboardMarkup | None = None,
    ):

        self.message = message
        self.state = state
        self.user_msg_markup = message.reply_markup
        self.preview_msg_markup = preview_msg_markup

        data = await state.get_data()
        await state.clear()

        self.chat_id = data.get("chat_id")
        message_id = data.get("message_id")

        # Отправка предпросмотрового сообщения
        await self.send_preview_msg()

        # Удаление исходного сообщения пользователя
        await message.delete()
        await self.bot.delete_message(chat_id=self.chat_id, message_id=message_id)

    async def send_preview_msg(self):

        # Составление inline-кнопок для предпросмотрового сообщения
        user_msg_keyboard = self.user_msg_markup.inline_keyboard if self.user_msg_markup else []
        preview_msg_keyboard = self.preview_msg_markup.inline_keyboard if self.preview_msg_markup else []

        combined_keyboard = user_msg_keyboard + preview_msg_keyboard

        self.preview_msg_markup = InlineKeyboardMarkup(inline_keyboard=combined_keyboard)

        # Обработка входящего типа сообщения
        message = self.message

        if message.text:
            await self._text_state()

        elif message.photo:
            await self._photo_state()

        elif message.video:
            await self._video_state()

        elif message.audio:
            await self._audio_state()

        elif message.animation:
            await self._animation_state()

    async def delete_preview_msg(self):

        data = await self.state.get_data()
        preview_msg_id = data.get("preview_msg_id")

        await self.bot.delete_message(chat_id=self.chat_id, message_id=preview_msg_id)

    async def send_newsletter(self, users_ids):

        message = self.message

        data = await self.state.get_data()

        newsletter_text = data.get("newsletter_text")
        newsletter_photo = data.get("newsletter_photo")
        newsletter_caption = data.get("newsletter_caption")
        newsletter_video = data.get("newsletter_video")
        newsletter_audio = data.get("newsletter_audio")
        newsletter_animation = data.get("newsletter_audio")

        bot = self.bot

        for user_id in users_ids:

            try:
                if newsletter_text:
                    await bot.send_message(
                        chat_id=user_id,
                        text=newsletter_text,
                        entities=message.entities,
                        reply_markup=self.user_msg_markup,
                    )

                elif newsletter_photo:
                    await bot.send_photo(
                        chat_id=user_id,
                        photo=newsletter_photo,
                        caption=newsletter_caption,
                        caption_entities=message.caption_entities,
                        reply_markup=self.user_msg_markup,
                    )

                elif newsletter_video:
                    await bot.send_video(
                        chat_id=user_id,
                        video=newsletter_video,
                        caption=newsletter_caption,
                        caption_entities=message.caption_entities,
                        reply_markup=self.user_msg_markup,
                    )

                elif newsletter_audio:
                    await bot.send_audio(
                        chat_id=user_id,
                        audio=newsletter_audio,
                        caption=newsletter_caption,
                        caption_entities=message.caption_entities,
                        reply_markup=self.user_msg_markup,
                    )

                elif newsletter_animation:
                    await bot.send_animation(
                        chat_id=user_id,
                        animation=newsletter_animation,
                        caption=newsletter_caption,
                        caption_entities=message.caption_entities,
                        reply_markup=self.user_msg_markup,
                    )

            except Exception as e:
                print(f"Failed to send a message to the user {user_id}: {e}")

        await self.state.clear()

    async def _text_state(self):

        message = self.message
        chat_id = self.chat_id
        reply_markup = self.preview_msg_markup

        newsletter_text = message.text

        prv_message = await self.bot.send_message(
            text=newsletter_text,
            chat_id=chat_id,
            entities=message.entities,
            reply_markup=reply_markup,
        )

        await self.state.update_data(newsletter_text=newsletter_text, preview_msg_id=prv_message.message_id)

    async def _photo_state(self):

        message = self.message
        chat_id = self.chat_id
        reply_markup = self.preview_msg_markup

        newsletter_photo = message.photo[-1].file_id
        newsletter_caption = message.caption

        prv_message = await self.bot.send_photo(
            photo=newsletter_photo,
            caption=newsletter_caption,
            caption_entities=message.caption_entities,
            chat_id=chat_id,
            reply_markup=reply_markup,
        )

        await self.state.update_data(
            newsletter_photo=newsletter_photo,
            newsletter_caption=newsletter_caption,
            preview_msg_id=prv_message.message_id,
        )

    async def _video_state(self):

        message = self.message
        chat_id = self.chat_id
        reply_markup = self.preview_msg_markup

        newsletter_video = message.video.file_id
        newsletter_caption = message.caption

        prv_message = await self.bot.send_video(
            video=newsletter_video,
            caption=newsletter_caption,
            caption_entities=message.caption_entities,
            chat_id=chat_id,
            reply_markup=reply_markup,
        )

        await self.state.update_data(
            newsletter_video=newsletter_video,
            newsletter_caption=newsletter_caption,
            preview_msg_id=prv_message.message_id,
        )

    async def _audio_state(self):

        message = self.message
        chat_id = self.chat_id
        reply_markup = self.preview_msg_markup

        newsletter_audio = message.audio.file_id
        newsletter_caption = message.caption

        prv_message = await self.bot.send_audio(
            audio=newsletter_audio,
            caption=newsletter_caption,
            caption_entities=message.caption_entities,
            chat_id=chat_id,
            reply_markup=reply_markup,
        )

        await self.state.update_data(
            newsletter_audio=newsletter_audio,
            newsletter_caption=newsletter_caption,
            preview_msg_id=prv_message.message_id,
        )

    async def _animation_state(self):

        message = self.message
        chat_id = self.chat_id
        reply_markup = self.preview_msg_markup

        newsletter_animation = message.animation.file_id
        newsletter_caption = message.caption

        prv_message = await self.bot.send_animation(
            animation=newsletter_animation,
            caption=newsletter_caption,
            caption_entities=message.caption_entities,
            chat_id=chat_id,
            reply_markup=reply_markup,
        )

        await self.state.update_data(
            newsletter_animation=newsletter_animation,
            newsletter_caption=newsletter_caption,
            preview_msg_id=prv_message.message_id,
        )
