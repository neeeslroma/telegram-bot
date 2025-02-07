import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import FSInputFile
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

# 🔹 Логирование
logging.basicConfig(level=logging.INFO)

# 🔹 API-токен бота из переменных среды
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise ValueError("Не найден BOT_TOKEN! Установите переменную окружения.")

# 🔹 Данные админа (из переменной среды, если есть)
ADMIN_ID = int(os.getenv("ADMIN_ID", 770819003))

# 🔹 Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# 🔹 Словарь для хранения данных пользователей
user_data = {}

@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Отправляет первое сообщение с фото, а через 7 секунд — второе сообщение."""
    photo_path = "photo_olga.jpg"

    try:
        photo = FSInputFile(photo_path)
        await message.answer_photo(
            photo=photo,
            caption="Вітаю!\nДякую за підписку та увагу до моєї сторінки!\n"
                    "Мене звуть Ольга і я практикуючий таролог, який допоможе вам отримати відповіді на ваши запитання.",
            reply_markup=types.ReplyKeyboardRemove()
        )
    except FileNotFoundError:
        await message.answer("⚠️ Виникла помилка: не знайдено фото для привітання.")
        logging.error(f"Ошибка: файл {photo_path} не найден.")
        return

    user_data[message.from_user.id] = {
        "stage": 1,
        "answers": [],
        "phone": "❌ Номер не надано"
    }

    await asyncio.sleep(7)
    await send_second_message(message)

async def send_second_message(message: types.Message):
    """Отправляет второе сообщение через 7 секунд после первого."""
    await message.answer(
        text="Напишіть будь ласка ваше ім'я, дату народження, номер телефону та ваше питання. "
             "Також буду вдячна за стислий опис ситуації, щодо вашого питання.\n\n"
             "Якщо ваше запитання про стосунки, то напишіть будь ласка ще й ім'я вашого партнера."
    )
    user_data[message.from_user.id]["stage"] = 2

@dp.message(F.text)
async def third_message(message: types.Message):
    """Обработчик текстового ответа пользователя — отправляет третье сообщение."""
    if message.from_user.id not in user_data or user_data[message.from_user.id]["stage"] != 2:
        return

    user_data[message.from_user.id]["answers"].append(message.text)

    await message.answer(
        text="Очікуйте відповідь на ваше питання впродовж 48 годин, дякую за розуміння!"
    )

    user_data[message.from_user.id]["stage"] = 3

    logging.info(f"Ожидание 10 секунд перед отправкой уведомления админу ({ADMIN_ID})...")
    await asyncio.sleep(10)
    await send_admin_notification(message.from_user.id, message.from_user.username)

async def send_admin_notification(user_id, username):
    """Формирует и отправляет админу уведомление о новом пользователе."""
    if user_id not in user_data or user_data[user_id].get("stage") != 3:
        logging.warning(f"❌ Не удалось отправить уведомление админу: user_id {user_id} не завершил диалог")
        return

    phone_number = user_data[user_id].get("phone", "❌ Номер не надано")
    answers = user_data[user_id].get("answers", [])

    if not answers:
        answers_text = "❌ Користувач не надав відповіді."
    else:
        answers_text = "\n\n".join([f"❓ {i + 1}) {ans}" for i, ans in enumerate(answers)])

    admin_message = (
        f"🔔 Новий користувач скористався ботом!\n\n"
        f"👤 Username: @{username or 'Немає'}\n"
        f"📞 Телефон: {phone_number}\n\n"
        f"📩 Його відповіді:\n{answers_text}"
    )

    try:
        logging.info(f"📨 Відправка повідомлення адміну ({ADMIN_ID})...")
        await bot.send_message(ADMIN_ID, admin_message)
        logging.info(f"✅ Повідомлення адміну надіслано ({ADMIN_ID})!")
    except Exception as e:
        logging.error(f"❌ Помилка при відправці повідомлення адміну: {e}")

# 🔹 Фейковый веб-сервер для Render
async def handle(request):
    return web.Response(text="Bot is running!")

async def run_server():
    app = web.Application()
    app.router.add_get("/", handle)
    
    port = int(os.getenv("PORT", 8080))  # Render требует порт
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# 🔹 Запуск бота и сервера одновременно
async def main():
    await asyncio.gather(dp.start_polling(bot), run_server())

if __name__ == "__main__":
    asyncio.run(main())
