from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Создаем клавиатуру с двумя кнопками
settings_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("Перезагрузить PostgreSQL")],
        [KeyboardButton("Отправить SQL запрос")],
    ],
    resize_keyboard=True  # Разрешаем клавиатуре изменять размер
)