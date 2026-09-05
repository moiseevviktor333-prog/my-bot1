import asyncio
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
# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__
name
__)
# Конфигурация бота
BOT
_
TOKEN = os.getenv("8919412947:AAG10ChkggPM5pM91fvasMh5Q6rnwvXx3eg")
PRODUCT
_
NAME = "100 фраз для первого сообщения"
PRODUCT
_
DESCRIPTION = (
"Готовые фразы для Tinder, VK, Instagram,"
"знакомства на улице и после лайка."
"Перестань думать, что написать — просто выбирай и отправляй"
)
PRICE
IN
_
_
STARS = 99 # Цена в Telegram Stars
PDF
FILE
_
_
PATH = Path(__
file
__).parent / "phrases.pdf" # Путь к PDF-файлу
# Инициализация бота и диспетчера
bot = Bot(token=BOT
_
TOKEN)
dp = Dispatcher()
# Хранилище пользователей, которые уже купили файл
# В production лучше использовать базу данных
purchased
_
users = set()
def get
_
buy_
keyboard() -> InlineKeyboardBuilder:
"""
Создает клавиатуру с кнопкой покупки.
Returns:
InlineKeyboardBuilder: Объект клавиатуры с кнопкой покупки
"""
keyboard = InlineKeyboardBuilder()
keyboard.button(
text=f"Купить за {PRICE
IN
_
_
callback
_
data="buy_product"
,
STARS} ⭐
"
,
)
return keyboard
@dp.message(CommandStart())
async def command
_
start(message: Message):
"""
Обработчик команды /start.
Отправляет приветственное сообщение с описанием продукта и кнопкой покупки.
Args:
message (Message): Входящее сообщение
"""
user
_
id = message.from
_
user.id
# Формируем текст приветствия
welcome
_
text = (
f"👋 Привет, {message.from
user.first
_
_
name}!\n\n"
f"📚 <b>{PRODUCT
_
NAME}</b>\n\n"
f"📝 {PRODUCT
_
DESCRIPTION}\n\n"
f"💰 Цена: {PRICE
IN
_
_
STARS} ⭐ (Telegram Stars)\n\n"
"👇 Нажмите на кнопку ниже, чтобы приобрести:"
)
# Если пользователь уже купил файл, добавляем соответствующее сообщение
if user
_
id in purchased
_
users:
welcome
_
text += "\n\n✅ Вы уже приобрели этот файл!"
await message.answer(
welcome
text,
_
parse
mode="HTML"
,
_
reply_
markup=get
_
buy_
keyboard().as
_
markup(),
)
@dp.callback
_query(F.data == "buy_product")
async def process
_
buy(callback: CallbackQuery):
"""
Обработчик нажатия на кнопку покупки.
Проверяет, не купил ли пользователь уже файл, и отправляет счёт.
Args:
callback (CallbackQuery): Объект callback-запроса
"""
user
id = callback.from
_
_
user.id
# Проверяем, не купил ли пользователь уже файл
if user
_
id in purchased
_
users:
# Если купил, отправляем файл бесплатно
await send
_pdf(callback.message.chat.id, user
_
id)
await callback.answer("✅ Файл уже был куплен ранее, отправляю снова!")
return
# Создаём счёт на оплату через Telegram Stars
prices = [
LabeledPrice(
label=PRODUCT
NAME,
_
amount=PRICE
IN
_
_
STARS, # Сумма в Telegram Stars
)
]
try:
# Отправляем счёт пользователю
await bot.send
_
invoice(
chat
_
id=callback.message.chat.id,
title=PRODUCT
NAME,
_
description=PRODUCT
_
DESCRIPTION,
prices=prices,
provider
token=""
_
, # Для Telegram Stars не нужен
payload="phrases
_pdf
_payment"
, # Уникальный идентификатор платежа
currency="XTR"
, # Валюта Telegram Stars
)
await callback.answer("Счёт отправлен! 💫")
except Exception as e:
logger.error(f"Ошибка при отправке счёта: {e}")
await callback.answer("Произошла ошибка при создании счёта"
, show
_
alert=True)
@dp.pre
checkout
_
_query()
async def process
_pre
_
checkout(pre
checkout
_
_query: PreCheckoutQuery):
"""
Обработчик pre-checkout запроса.
Подтверждает готовность принять платёж.
Args:
pre
checkout
_
_query (PreCheckoutQuery): Объект pre-checkout запроса
"""
# Подтверждаем платёж (обязательно для продолжения оплаты)
await bot.answer
_pre
checkout
_
_query(
pre
checkout
_
_query.id,
ok=True,
)
@dp.message(F.successful
_payment)
async def process
successful
_
_payment(message: Message):
"""
Обработчик успешной оплаты.
Отправляет PDF-файл пользователю после получения оплаты.
Args:
message (Message): Сообщение с информацией об успешной оплате
"""
user
_
id = message.from
_
user.id
# Добавляем пользователя в список купивших
purchased
_
users.add(user
_
id)
# Отправляем PDF-файл
await send
_pdf(message.chat.id, user
_
id)
# Отправляем благодарность
await message.answer(
"🎉 <b>Спасибо за покупку!</b>\n\n"
"Надеюсь, эти фразы помогут вам начать интересные разговоры!\n"
"Если будут вопросы — пишите!"
,
parse
mode="HTML"
,
_
)
async def send
_pdf(chat
id: int, user
_
_
id: int):
"""
Отправляет PDF-файл пользователю.
Args:
chat
_
id (int): ID чата
user
_
id (int): ID пользователя
"""
try:
# Проверяем существование файла
if not PDF
FILE
_
_
PATH.exists():
logger.error(f"Файл {PDF
FILE
_
_
await bot.send
_
message(
PATH} не найден!")
chat
id,
_
"❌ К сожалению, файл временно недоступен. Пожалуйста, свяжитесь с
"
администратором.
,
)
return
# Отправляем файл
file = FSInputFile(PDF
FILE
_
_
await bot.send
_
document(
chat
id=chat
id,
PATH)
_
_
document=file,
caption=(
f"📄 <b>{PRODUCT
_
NAME}</b>\n"
"Сохраните файл, чтобы не потерять! 📥"
),
parse
mode="HTML"
_
,
)
logger.info(f"Файл отправлен пользователю {user
_
id}")
except Exception as e:
logger.error(f"Ошибка при отправке файла пользователю {user
_
id}: {e}")
await bot.send
_
message(
chat
id,
_
"❌ Произошла ошибка при отправке файла. Пожалуйста, попробуйте позже
"
или свяжитесь с администратором.
,
)
async def main():
"""
Главная функция запуска бота.
"""
logger.info("Запуск бота...
")
# Проверяем наличие PDF-файла при запуске
if not PDF
FILE
_
_
PATH.exists():
logger.warning(f"ВНИМАНИЕ: Файл {PDF
FILE
_
_
PATH} не найден!")
else:
logger.info(f"PDF-файл найден: {PDF
FILE
_
_
PATH}")
# Запускаем polling
await dp.start
_polling(bot)
if
name
__
__
== "
main
":
__
__
asyncio.run(main()