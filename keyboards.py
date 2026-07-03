from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def admin_keyboard(user_id: int):

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Одобрить",
                    callback_data=f"approve:{user_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"reject:{user_id}",
                ),
            ]
        ]
    )
