import asyncio
import logging
import os
import shutil
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    FSInputFile,
)

from config import (
    BOT_TOKEN,
    ADMIN_ID,
    PASSPORTS_DIR,
    RECEIPTS_DIR,
    INSTRUCTION_IMAGE,
)

from storage import (
    get_user,
    update_user,
)

from keyboards import admin_keyboard
from states import CheckIn


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()

forwarded_messages = {}


# -----------------------------
# /start
# -----------------------------

@dp.message(CommandStart())
async def start(
    message: Message,
    state: FSMContext,
):

    await state.clear()

    get_user(message.from_user.id)

    await state.set_state(CheckIn.waiting_passport)

    text = (
        "🌲 <b>Добро пожаловать в наш лесной дом!</b>\n\n"
        "Спасибо, что выбрали нас для своего отдыха.\n\n"
        "Для завершения дистанционного заселения, "
        "пожалуйста, отправьте:\n\n"
        "📄 фотографию паспорта\n\n"
        "💳 чек об оплате страхового депозита "
        "<b>5000 ₽</b>\n\n"
        "После проверки документов мы сразу "
        "направим Вам инструкцию по заселению."
    )

    await message.answer(text)


# -----------------------------
# Получение паспорта
# -----------------------------

@dp.message(
    CheckIn.waiting_passport,
    F.photo,
)
async def passport_received(
    message: Message,
    state: FSMContext,
):

    user_id = message.from_user.id
    photo = message.photo[-1]

    update_user(
        user_id,
        passport=photo.file_id,
    )

    await state.set_state(CheckIn.waiting_receipt)

    await message.answer(
        "✅ Паспорт получен.\n\n"
        "Теперь отправьте фотографию чека о переводе страхового депозита."
    )


# -----------------------------
# Получение чека
# -----------------------------

@dp.message(
    CheckIn.waiting_receipt,
    F.photo,
)
async def receipt_received(
    message: Message,
    state: FSMContext,
):

    user_id = message.from_user.id
    photo = message.photo[-1]

    update_user(
        user_id,
        receipt=photo.file_id,
        approved=False,
    )

    await state.clear()

    await message.answer(
        "✅ Спасибо!\n\n"
        "Мы приняли Ваши документы на проверку.\n\n"
        "Сразу после окончания проверки Вам будут направлены инструкции по заселению."
    )

    passport_file_id = get_user(user_id)["passport"]
    receipt_file_id = get_user(user_id)["receipt"]

    guest_name = message.from_user.full_name

    username = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else "не указан"
    )

    text = (
        "🏡 <b>Новое заселение</b>\n\n"
        f"👤 <b>Имя:</b> {guest_name}\n"
        f"📱 <b>Username:</b> {username}\n"
        f"🆔 <b>ID:</b> {user_id}"
    )

    await bot.send_message(
        ADMIN_ID,
        text,
    )

    await bot.send_photo(
        ADMIN_ID,
        photo=passport_file_id,
        caption="📄 Паспорт",
    )

    await bot.send_photo(
        ADMIN_ID,
        photo=receipt_file_id,
        caption="💳 Чек",
        reply_markup=admin_keyboard(user_id),
    )


# -----------------------------
# Если вместо чека
# -----------------------------

@dp.message(CheckIn.waiting_receipt)
async def wrong_receipt(
    message: Message,
):

    await message.answer(
        "Пожалуйста, отправьте фотографию чека."
    )


# -----------------------------
# Одобрение документов
# -----------------------------

@dp.callback_query(F.data.startswith("approve:"))
async def approve_user(callback: CallbackQuery):

    user_id = int(callback.data.split(":")[1])

    update_user(
        user_id,
        approved=True,
    )

    print("INSTRUCTION_IMAGE =", INSTRUCTION_IMAGE)
    print("exists =", INSTRUCTION_IMAGE.exists())

    photo = FSInputFile(str(INSTRUCTION_IMAGE))

    await bot.send_photo(
        chat_id=user_id,
        photo=photo,
        caption=(
            "✅ <b>Документы успешно проверены.</b>\n\n"
            "Добро пожаловать в наш лесной дом!\n\n"
            "Желаем Вам приятного отдыха ❤️"
        ),
        parse_mode="HTML",
    )

    await callback.message.edit_reply_markup()

    await callback.answer("Гость одобрен ✅")


# -----------------------------
# Отклонение документов
# -----------------------------

@dp.callback_query(F.data.startswith("reject:"))
async def reject_user(callback: CallbackQuery, state: FSMContext):

    user_id = int(callback.data.split(":")[1])

    update_user(
        user_id,
        passport=None,
        receipt=None,
        approved=False,
    )

    await state.clear()

    await bot.send_message(
        user_id,
        "❌ Документы отклонены.\n\n"
        "Пожалуйста, отправьте /start заново."
    )

    await callback.message.edit_reply_markup()
    await callback.answer("Отклонено")


# -----------------------------
# Сообщения после заселения
# -----------------------------

@dp.message()
async def guest_messages(message: Message):

    if message.from_user.id == ADMIN_ID:
        return

    user = get_user(message.from_user.id)

    if not user["approved"]:
        return

    username = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else "не указан"
    )

    text = (
        "💬 <b>Новое сообщение от гостя</b>\n\n"
        f"👤 {message.from_user.full_name}\n"
        f"📱 {username}\n"
        f"🆔 {message.from_user.id}\n\n"
        f"{message.text}"
    )

    sent = await bot.send_message(
        ADMIN_ID,
        text,
    )

    forwarded_messages[sent.message_id] = message.from_user.id


# -----------------------------
# Ответ администратора гостю
# -----------------------------

@dp.message(F.reply_to_message)
async def admin_reply(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    replied = message.reply_to_message.message_id

    if replied not in forwarded_messages:
        return

    guest_id = forwarded_messages[replied]

    await bot.send_message(
        guest_id,
        f"💬 {message.text}"
    )


# -----------------------------
# Запуск
# -----------------------------

async def main():

    print("=================================")
    print("🏡 Forest House Bot запущен")
    print("=================================")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
