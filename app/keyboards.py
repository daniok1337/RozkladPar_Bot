from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
InlineKeyboardMarkup, InlineKeyboardButton)


main = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text = "Обрати день" ),
                                      KeyboardButton(text = "Весь тиждень")]
                                      ], resize_keyboard=True)

def get_days_inline(user_id): 
    return InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text = "Понеділок", callback_data='Monday'), 
    InlineKeyboardButton(text = "Вівторок",callback_data='Tuesday')],
    [InlineKeyboardButton(text = "Середа",callback_data='Wednesday'), 
    InlineKeyboardButton(text = "Четвер",callback_data='Thursday')],
    [InlineKeyboardButton(text = "П'ятниця",callback_data='Friday')],
    [InlineKeyboardButton(text = "Закрити меню",callback_data=f"close_{user_id}")]
    ])