import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import FSInputFile
from aiogram.filters import Command
from aiogram.utils import markdown
from aiogram.fsm.storage.memory import MemoryStorage

# 🔹 Ваш API-токен
API_TOKEN = "7735427380:AAGQgL3Arrl4evlhf0vg7X4Pu1iGLS03DjU"

# 🔹 Данные админа
ADMIN_ID = 770819003  # Проверь, что это твой настоящий ID

# 🔹 Включаем логирование
logging.basicConfig(level=logging.INFO)

# 🔹 Создаем бота и диспетчер с памятью
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
        "phone": message.from_user.phone_number if hasattr(message.from_user, 'phone_number') else "❌ Номер не надано"
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

# 🔹 Запуск бота
async def main():
    """Функция запуска бота."""
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
