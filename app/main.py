import asyncio
import aiogram
import psycopg2
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from keyboards import settings_keyboard
from chek_database import get_database_activity, get_system_info, send_photo, restart_postgresql
import os
from dotenv import load_dotenv
load_dotenv()


# Инициализация
bot = Bot(token=os.environ.get("TOKEN"))
dp = Dispatcher(bot)
logging_middleware = LoggingMiddleware()
dp.middleware.setup(logging_middleware)


# проверка состояния базы данных
async def check_database_state():
    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            port=os.environ.get("DP_PORT"),
            database=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD")
        )
        cursor = conn.cursor()
        cursor.execute('SELECT 1')  
        cursor.close()
        conn.close()
        return True
    except psycopg2.OperationalError as e:
        return e

# отправка уведомлений об ошибке администратору
async def send_error_notification(status):
    admin_user_id = os.environ.get("ADMIN_ID") 
    await bot.send_message(admin_user_id, f"{status}")

# проверка состояния базы данных
async def database_monitoring():
    while True:
        status = await check_database_state()
        if status != True:
            await send_error_notification(status)
        await asyncio.sleep(15)  # Проверка каждые 15 секунд


#############################################
#              check_activity               #
#############################################

# Обработчик команды /check_activity
@dp.message_handler(commands=['check_activity'])
async def check_activity(message: types.Message):
    if str(message.from_user.id) == os.environ.get('ADMIN_ID'):
        activity_data = await get_database_activity()
        if activity_data:
            response = "Состояние базы данных:\n"
            # for row in activity_data:
            #     response += f"Процесс: {row[0]}, Query: {row[6]}\n"
            await message.answer(activity_data, parse_mode='html')
        else:
            await message.answer("Не удалось получить данные о состоянии базы данных.")


#############################################
#              check_info                   #
#############################################

@dp.message_handler(commands=['check_info'])
async def check_info(message: types.Message):
    if str(message.from_user.id) == os.environ.get('ADMIN_ID'):
        data = await get_system_info()
        if data:
            x_keys = list(data.keys())
            y = [data[key] for key in x_keys]
            await send_photo(message.chat.id, x_keys, y)
        else:
            await message.answer("Не удалось получить информацию о состоянии базы данных и системных параметрах.")



#############################################
#               settings                    #
#############################################

@dp.message_handler(commands=['settings'])
async def settings_command(message: types.Message):
    await message.answer("Выберите действие:", reply_markup=settings_keyboard)


@dp.message_handler(lambda message: message.text == "Перезагрузить PostgreSQL")
async def restart_postgres_handler(message: types.Message):
    result = await restart_postgresql()
    if result == True:
        await message.answer("PostgreSQL на удаленном сервере был успешно перезапущен.")
    elif result == False:
        await message.answer("Произошла ошибка при попытке перезапуска PostgreSQL на удаленном сервере.")
    else:
        await message.answer("Произошла ошибка при попытке подключения к удаленному серверу.")


@dp.message_handler(lambda message: message.text == "Отправить SQL запрос")
async def send_sql_handler(message: types.Message):
        await message.answer("Введите ваш SQL запрос:")

@dp.message_handler()
async def send_sql(message: types.Message):
    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            port=os.environ.get("DP_PORT"),
            database=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD")
        )

        cursor = conn.cursor()

        # Выполнение SQL запроса
        cursor.execute(message.text)
        result = cursor.fetchall()

        # Закрытие соединений
        cursor.close()
        conn.close()

        # Отправка результата пользователю
        if result:
            await message.answer("Результат выполнения SQL запроса:\n" + str(result))
        else:
            await message.answer("SQL запрос выполнен успешно.")
    except Exception as e:
        await message.answer("Произошла ошибка при выполнении SQL запроса.")



if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(database_monitoring())
    aiogram.executor.start_polling(dp, loop=loop)
