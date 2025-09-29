#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import random
from typing import List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# --- ЛОГИ ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- ХЕЛПЕРЫ ---
def parse_int(value: str, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default

def parse_choices(text: str) -> List[str]:
    # Разделители: ; , | или новая строка
    raw = [p.strip() for p in (
        text.replace("\n", "|").replace(";", "|").replace(",", "|").split("|")
    ) if p.strip()]
    # убрать возможные пустые
    return [r for r in raw if r]

# --- КОМАНДЫ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    kb = [
        [
            InlineKeyboardButton("🎲 /roll", callback_data="help_roll"),
            InlineKeyboardButton("🪙 /coin", callback_data="help_coin"),
        ],
        [
            InlineKeyboardButton("🎯 /choice", callback_data="help_choice"),
            InlineKeyboardButton("🎰 /dice", callback_data="help_dice"),
        ],
        [InlineKeyboardButton("📜 /help", callback_data="help_full")],
    ]
    await update.message.reply_text(
        "Привет! Я — рандомайзер‑бот. Нажми кнопку или используй команды.\n"
        "Быстрый старт: /roll 1 100",
        reply_markup=InlineKeyboardMarkup(kb),
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Команды:\n"
        "• /roll [min] [max] — случайное число (по умолчанию 1…100)\n"
        "• /coin — орёл/решка\n"
        "• /choice вариант1; вариант2; вариант3 — выберу один\n"
        "• /dice — кубик (телеграм‑анимация)\n"
        "\nПримеры:\n"
        "• /roll 1 6\n"
        "• /choice чай, кофе, сок\n"
    )

async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # /roll [min] [max]
    args = context.args
    if len(args) == 0:
        a, b = 1, 100
    elif len(args) == 1:
        a, b = 1, parse_int(args[0], 100)
    else:
        a, b = parse_int(args[0], 1), parse_int(args[1], 100)

    if a > b:
        a, b = b, a  # поменяем местами

    # ограничим диапазон чтобы не улететь
    span = b - a
    if span > 10_000_000:
        b = a + 10_000_000

    num = random.randint(a, b)
    await update.message.reply_text(f"🎲 Случайное число: *{num}* (из {a}…{b})", parse_mode="Markdown")

async def coin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    side = random.choice(["Орёл", "Решка"])
    await update.message.reply_text(f"🪙 {side}!")

async def choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = " ".join(context.args) if context.args else ""
    if not text and update.message and update.message.reply_to_message:
        # если команда использована как ответ на сообщение — берём текст оттуда
        text = update.message.reply_to_message.text or ""

    items = parse_choices(text)
    if len(items) < 2:
        await update.message.reply_text(
            "Нужно минимум *2 варианта*.\n"
            "Пример: `/choice чай; кофе; сок`",
            parse_mode="Markdown",
        )
        return

    pick = random.choice(items)
    await update.message.reply_text(f"🎯 Выбор: *{pick}*", parse_mode="Markdown")

async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_dice(chat_id=update.effective_chat.id, emoji='🎲')

# --- CALLBACKS ДЛЯ КНОПОК СТАРТА ---
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = update.callback_query.data
    await update.callback_query.answer()
    if data == "help_roll":
        await update.callback_query.edit_message_text("Используй: /roll [min] [max]\nПример: /roll 1 6")
    elif data == "help_coin":
        await update.callback_query.edit_message_text("Команда /coin — подбрасывает монетку: орёл или решка.")
    elif data == "help_choice":
        await update.callback_query.edit_message_text("Команда /choice — выберу один из вариантов.\nПример: /choice чай; кофе; сок")
    elif data == "help_dice":
        await update.callback_query.edit_message_text("Команда /dice — телеграм‑анимация кубика 🎲")
    else:
        await update.callback_query.edit_message_text(
            "📜 /help\n"
            "• /roll [min] [max]\n"
            "• /coin\n"
            "• /choice вариант1; вариант2; вариант3\n"
            "• /dice"
        )

# --- MAIN ---
def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise SystemExit("Нет переменной окружения BOT_TOKEN. Создайте .env или экспортируйте BOT_TOKEN.")

    app = Application.builder().token(token).build()

    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("roll", roll))
    app.add_handler(CommandHandler("rand", roll))
    app.add_handler(CommandHandler("coin", coin))
    app.add_handler(CommandHandler("choice", choice))
    app.add_handler(CommandHandler("dice", dice))

    # Кнопки из /start
    from telegram.ext import CallbackQueryHandler
    app.add_handler(CallbackQueryHandler(on_callback))

    logger.info("Bot started")
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    # Загрузим .env если есть
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass
    main()
