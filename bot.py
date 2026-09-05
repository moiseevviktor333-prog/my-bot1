import asyncio
import json
import logging
import os
from pathlib import Path
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    PreCheckoutQuery,
    LabeledPrice,
    FSInputFile,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
PRODUCT_NAME = "100 фраз для первого сообщения"
PRODUCT_DESCRIPTION = (
    "Готовые фразы для Tinder, VK, Instagram, "
    "знакомства на улице и после лайка. "
    "Перестань думать, что написать — просто выбирай и отправляй."
)
PRICE_IN_STARS = 99  # Цена в Telegram Stars
BASE_DIR = Path(__file__).parent
PDF_FILE_PATH = BASE_DIR / "phrases.pdf"
DB_FILE_PATH = BASE_DIR / "purchased_users.json"

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализация простого файлового хранилища для продакшена
def load_purchased_users() -> set:
    if DB_FILE_PATH.exists():
        try:
            with open(DB_FILE_PATH, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception as e:
            logger.error(f"Ошибка чтения БД: {e}")
    return set()

def save_user_purchase(user_id: int):
    purchased_users.add(user_id)
    try:
        with open(DB_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(list(purchased_users), f)
    except Exception as e:
        logger.error(f"Ошибка записи в БД: {e}")

purchased_users = load_purchased_users()

def get_buy_keyboard() -> InlineKeyboardBuilder:
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text=f"Купить за {PRICE_IN_STARS} ⭐",
        callback_data="buy_product"
    )
    return keyboard

@dp.message(CommandStart())
async def command_start(message: Message):
    user_id = message.from_user.id
    welcome_text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"📚 <b>{PRODUCT_NAME}</b>\n\n"
        f"📝 {PRODUCT_DESCRIPTION}\n\n"
        f"💰 Цена: {PRICE_IN_STARS} ⭐ (Telegram Stars)\n\n"
        "👇 Нажмите на кнопку ниже, чтобы приобрести:"
    )
    
    if user_id in purchased_users:
        welcome_text += "\n\n✅ Вы уже приобрели этот файл!"

    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=get_buy_keyboard().as_markup(),
    )

@dp.callback_query(F.data == "buy_product")
async def process_buy(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id in purchased_users:
        await send_pdf(callback.message.chat.id, user_id)
        await callback.answer("✅ Файл уже был куплен ранее, отправляю снова!")
        return

    prices = [LabeledPrice(label=PRODUCT_NAME, amount=PRICE_IN_STARS)]
    
    try:
        await bot.send_invoice(
            chat_id=callback.message.chat.id,
            title=PRODUCT_NAME,
            description=PRODUCT_DESCRIPTION,
            prices=prices,
            provider_token="",  # Для Telegram Stars оставляем пустым
            payload="phrases_pdf_payment",
            currency="XTR",
        )
        await callback.answer("Счёт отправлен! 💫")
    except Exception as e:
        logger.error(f"Ошибка при отправке счёта: {e}")
        await callback.answer("Произошла ошибка при создании счёта", show_alert=True)

@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def process_successful_payment(message: Message):
    user_id = message.from_user.id
    save_user_purchase(user_id)  # Сохраняем в JSON
    
    await send_pdf(message.chat.id, user_id)
    await message.answer(
        "🎉 <b>Спасибо за покупку!</b>\n\n"
        "Надеюсь, эти фразы помогут вам начать интересные разговоры!\n"
        "Если будут вопросы — пишите!",
        parse_mode="HTML",
    )

async def send_pdf(chat_id: int, user_id: int):
    try:
        if not PDF_FILE_PATH.exists():
            logger.error(f"Файл {PDF_FILE_PATH} не найден!")
            await bot.send_message(
                chat_id,
                "❌ К сожалению, файл временно недоступен. Пожалуйста, свяжитесь с администратором."
            )
            return

        file = FSInputFile(PDF_FILE_PATH)
        await bot.send_document(
            chat_id=chat_id,
            document=file,
            caption=f"📄 <b>{PRODUCT_NAME}</b>\nСохраните файл, чтобы не потерять! 📥",
            parse_mode="HTML",
        )
        logger.info(f"Файл отправлен пользователю {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке файла пользователю {user_id}: {e}")
        await bot.send_message(
            chat_id,
            "❌ Произошла ошибка при отправке файла. Пожалуйста, попробуйте позже или свяжитесь с администратором."
        )

async def main():
    logger.info("Запуск бота...")
    if not PDF_FILE_PATH.exists():
        logger.warning(f"ВНИМАНИЕ: Файл {PDF_FILE_PATH} не найден!")
    else:
        logger.info(f"PDF-файл найден: {PDF_FILE_PATH}")
        
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()  # Корректное закрытие сессии сетей

if __name__ == "__main__":
    asyncio.run(main())