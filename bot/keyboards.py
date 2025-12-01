from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📂 Выбрать доску")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_mode_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💡 Идеи", callback_data="mode_ideas"),
            InlineKeyboardButton(text="🔨 Разбить на задачи", callback_data="mode_breakdown")
        ],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
    ])

def get_review_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принять и сохранить", callback_data="review_accept")],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="review_back"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")
        ]
    ])