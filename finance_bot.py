import os
import json
import logging
from datetime import datetime, date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = "8880279666:AAGGb732K9jesymvXEI1QeNOTZrkm3Abq3E"
DATA_FILE = "finance_data.json"
# ================================

logging.basicConfig(level=logging.INFO)

# Состояния
(MAIN_MENU, INCOME_CAT, INCOME_CRYPTO_CAT, EXPENSE_CAT, EXPENSE_CRYPTO_CAT,
 ENTER_AMOUNT, ENTER_COMMENT, DEPOSIT_MENU, ENTER_DEPOSIT, STATS_MENU,
 ENTER_INITIAL_BALANCE) = range(11)

# ========== РАБОТА С ДАННЫМИ ==========
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "transactions": [],
        "deposit": {
            "initial": 0,
            "added": 0,
            "withdrawn": 0
        }
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_transaction(type_, category, subcategory, amount, comment=""):
    data = load_data()
    data["transactions"].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M"),
        "type": type_,
        "category": category,
        "subcategory": subcategory,
        "amount": amount,
        "comment": comment
    })
    save_data(data)

# ========== КЛАВИАТУРЫ ==========
def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Доход", callback_data="income"),
         InlineKeyboardButton("➖ Расход", callback_data="expense")],
        [InlineKeyboardButton("💼 Депозит", callback_data="deposit"),
         InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("📋 История", callback_data="history")]
    ])

def income_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💼 Зарплата", callback_data="inc_salary")],
        [InlineKeyboardButton("₿ Крипта", callback_data="inc_crypto")],
        [InlineKeyboardButton("📝 Другое", callback_data="inc_other")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_main")]
    ])

def income_crypto_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 Лонг", callback_data="inc_crypto_long"),
         InlineKeyboardButton("📉 Шорт", callback_data="inc_crypto_short")],
        [InlineKeyboardButton("💸 Фандинг", callback_data="inc_crypto_funding"),
         InlineKeyboardButton("↔️ Спред", callback_data="inc_crypto_spread")],
        [InlineKeyboardButton("📝 Другое", callback_data="inc_crypto_other")],
        [InlineKeyboardButton("◀️ Назад", callback_data="income")]
    ])

def expense_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Дом", callback_data="exp_home"),
         InlineKeyboardButton("🍕 Еда", callback_data="exp_food")],
        [InlineKeyboardButton("₿ Крипта", callback_data="exp_crypto"),
         InlineKeyboardButton("🛍 Прочее", callback_data="exp_other")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_main")]
    ])

def expense_crypto_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Пополнение депо", callback_data="exp_crypto_deposit")],
        [InlineKeyboardButton("🔒 Приватка/Сигналы", callback_data="exp_crypto_private")],
        [InlineKeyboardButton("🤖 Парсер/Бот", callback_data="exp_crypto_bot")],
        [InlineKeyboardButton("📱 Подписки", callback_data="exp_crypto_sub")],
        [InlineKeyboardButton("📝 Другое", callback_data="exp_crypto_other")],
        [InlineKeyboardButton("◀️ Назад", callback_data="expense")]
    ])

def deposit_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Пополнить депо", callback_data="dep_add")],
        [InlineKeyboardButton("📤 Вывести с депо", callback_data="dep_withdraw")],
        [InlineKeyboardButton("💰 Баланс депо", callback_data="dep_balance")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_main")]
    ])

def stats_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 За сегодня", callback_data="stats_today"),
         InlineKeyboardButton("📆 За месяц", callback_data="stats_month")],
        [InlineKeyboardButton("₿ Крипта", callback_data="stats_crypto"),
         InlineKeyboardButton("💼 Депозит", callback_data="stats_deposit")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_main")]
    ])

def back_keyboard(back_to="back_main"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data=back_to)]
    ])

# ========== СТАТИСТИКА ==========
def get_stats_today():
    data = load_data()
    today = date.today().strftime("%Y-%m-%d")
    txs = [t for t in data["transactions"] if t["date"] == today]

    income = sum(t["amount"] for t in txs if t["type"] == "income")
    expense = sum(t["amount"] for t in txs if t["type"] == "expense")

    income_details = {}
    expense_details = {}
    for t in txs:
        label = f"{t['category']}" + (f" → {t['subcategory']}" if t['subcategory'] else "")
        if t["type"] == "income":
            income_details[label] = income_details.get(label, 0) + t["amount"]
        else:
            expense_details[label] = expense_details.get(label, 0) + t["amount"]

    msg = f"📊 Статистика за сегодня ({date.today().strftime('%d.%m.%Y')})\n"
    msg += "━━━━━━━━━━━━━━━\n"
    msg += f"💰 Доходы: +{income:.2f} USDT\n"
    for k, v in income_details.items():
        msg += f"  └ {k}: {v:.2f}\n"
    msg += f"\n💸 Расходы: -{expense:.2f} USDT\n"
    for k, v in expense_details.items():
        msg += f"  └ {k}: {v:.2f}\n"
    msg += "━━━━━━━━━━━━━━━\n"
    balance = income - expense
    emoji = "✅" if balance >= 0 else "❌"
    msg += f"{emoji} Баланс за день: {'+' if balance >= 0 else ''}{balance:.2f} USDT"
    return msg

def get_stats_month():
    data = load_data()
    month = date.today().strftime("%Y-%m")
    txs = [t for t in data["transactions"] if t["date"].startswith(month)]

    income = sum(t["amount"] for t in txs if t["type"] == "income")
    expense = sum(t["amount"] for t in txs if t["type"] == "expense")

    income_details = {}
    expense_details = {}
    for t in txs:
        label = f"{t['category']}" + (f" → {t['subcategory']}" if t['subcategory'] else "")
        if t["type"] == "income":
            income_details[label] = income_details.get(label, 0) + t["amount"]
        else:
            expense_details[label] = expense_details.get(label, 0) + t["amount"]

    msg = f"📆 Статистика за {date.today().strftime('%B %Y')}\n"
    msg += "━━━━━━━━━━━━━━━\n"
    msg += f"💰 Доходы: +{income:.2f} USDT\n"
    for k, v in income_details.items():
        msg += f"  └ {k}: {v:.2f}\n"
    msg += f"\n💸 Расходы: -{expense:.2f} USDT\n"
    for k, v in expense_details.items():
        msg += f"  └ {k}: {v:.2f}\n"
    msg += "━━━━━━━━━━━━━━━\n"
    balance = income - expense
    emoji = "✅" if balance >= 0 else "❌"
    msg += f"{emoji} Баланс за месяц: {'+' if balance >= 0 else ''}{balance:.2f} USDT"
    return msg

def get_stats_crypto():
    data = load_data()
    month = date.today().strftime("%Y-%m")
    txs = [t for t in data["transactions"] if t["date"].startswith(month) and t["category"] == "Крипта"]

    income_by_sub = {}
    expense_by_sub = {}
    for t in txs:
        sub = t["subcategory"] or t["category"]
        if t["type"] == "income":
            income_by_sub[sub] = income_by_sub.get(sub, 0) + t["amount"]
        else:
            expense_by_sub[sub] = expense_by_sub.get(sub, 0) + t["amount"]

    total_income = sum(income_by_sub.values())
    total_expense = sum(expense_by_sub.values())

    msg = f"₿ Крипто-статистика {date.today().strftime('%B %Y')}\n"
    msg += "━━━━━━━━━━━━━━━\n"
    for k, v in income_by_sub.items():
        msg += f"  {k}: +{v:.2f} USDT\n"
    msg += f"\n💸 Расходы на крипту:\n"
    for k, v in expense_by_sub.items():
        msg += f"  └ {k}: -{v:.2f} USDT\n"
    msg += "━━━━━━━━━━━━━━━\n"
    net = total_income - total_expense
    emoji = "🏆" if net >= 0 else "❌"
    msg += f"{emoji} Чистый профит: {'+' if net >= 0 else ''}{net:.2f} USDT"
    return msg

def get_deposit_stats():
    data = load_data()
    dep = data["deposit"]
    initial = dep.get("initial", 0)
    added = dep.get("added", 0)
    withdrawn = dep.get("withdrawn", 0)

    month = date.today().strftime("%Y-%m")
    txs = [t for t in data["transactions"] if t["date"].startswith(month) and t["category"] == "Крипта" and t["type"] == "income"]
    crypto_profit = sum(t["amount"] for t in txs)

    total_invested = initial + added
    current = total_invested - withdrawn
    roi = (crypto_profit / total_invested * 100) if total_invested > 0 else 0

    msg = "💼 Крипто-депозит\n"
    msg += "━━━━━━━━━━━━━━━\n"
    msg += f"📥 Начальный баланс: {initial:.2f} USDT\n"
    msg += f"➕ Пополнено: {added:.2f} USDT\n"
    msg += f"➖ Выведено: {withdrawn:.2f} USDT\n"
    msg += f"💰 Сейчас в крипте: {current:.2f} USDT\n"
    msg += f"📈 Заработано за месяц: +{crypto_profit:.2f} USDT\n"
    msg += "━━━━━━━━━━━━━━━\n"
    msg += f"🏆 ROI за месяц: {roi:.2f}%"
    return msg

def get_history():
    data = load_data()
    txs = data["transactions"][-10:][::-1]
    if not txs:
        return "📋 История пуста"

    msg = "📋 Последние 10 операций\n━━━━━━━━━━━━━━━\n"
    for t in txs:
        emoji = "💰" if t["type"] == "income" else "💸"
        sign = "+" if t["type"] == "income" else "-"
        label = t["category"] + (f" → {t['subcategory']}" if t["subcategory"] else "")
        comment = f" ({t['comment']})" if t.get("comment") else ""
        msg += f"{emoji} {t['date']} {t['time']}\n"
        msg += f"  {label}{comment}: {sign}{t['amount']:.2f} USDT\n"
    return msg

# ========== ХЭНДЛЕРЫ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if data["deposit"]["initial"] == 0 and not data["transactions"]:
        await update.message.reply_text(
            "👋 Привет! Я твой личный финансовый бот.\n\n"
            "Для начала введи текущий баланс крипто-депозита (сколько у тебя сейчас в крипте):\n"
            "Просто напиши число, например: 800"
        )
        context.user_data["state"] = "initial_balance"
        return ENTER_INITIAL_BALANCE

    await update.message.reply_text(
        "💼 Главное меню",
        reply_markup=main_keyboard()
    )
    return MAIN_MENU

async def enter_initial_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.replace(",", "."))
        data = load_data()
        data["deposit"]["initial"] = amount
        save_data(data)
        await update.message.reply_text(
            f"✅ Начальный баланс установлен: {amount:.2f} USDT\n\n"
            "Теперь ты можешь пользоваться ботом!",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU
    except:
        await update.message.reply_text("Введи число, например: 800")
        return ENTER_INITIAL_BALANCE

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data_cb = query.data

    # ГЛАВНОЕ МЕНЮ
    if data_cb == "back_main":
        await query.edit_message_text("💼 Главное меню", reply_markup=main_keyboard())
        return MAIN_MENU

    # ДОХОДЫ
    elif data_cb == "income":
        await query.edit_message_text("➕ Выбери категорию дохода:", reply_markup=income_keyboard())
        return INCOME_CAT

    elif data_cb == "inc_salary":
        context.user_data.update({"type": "income", "category": "Зарплата", "subcategory": ""})
        await query.edit_message_text("💼 Введи сумму зарплаты:")
        return ENTER_AMOUNT

    elif data_cb == "inc_crypto":
        await query.edit_message_text("₿ Крипта — выбери тип:", reply_markup=income_crypto_keyboard())
        return INCOME_CRYPTO_CAT

    elif data_cb.startswith("inc_crypto_"):
        sub_map = {
            "inc_crypto_long": "📈 Лонг",
            "inc_crypto_short": "📉 Шорт",
            "inc_crypto_funding": "💸 Фандинг",
            "inc_crypto_spread": "↔️ Спред",
            "inc_crypto_other": "📝 Другое"
        }
        context.user_data.update({"type": "income", "category": "Крипта", "subcategory": sub_map.get(data_cb, "")})
        await query.edit_message_text(f"Введи сумму ({sub_map.get(data_cb, '')}):")
        return ENTER_AMOUNT

    elif data_cb == "inc_other":
        context.user_data.update({"type": "income", "category": "Другое", "subcategory": ""})
        await query.edit_message_text("📝 Введи сумму и комментарий через пробел\nНапример: 100 фриланс")
        return ENTER_COMMENT

    # РАСХОДЫ
    elif data_cb == "expense":
        await query.edit_message_text("➖ Выбери категорию расхода:", reply_markup=expense_keyboard())
        return EXPENSE_CAT

    elif data_cb == "exp_home":
        context.user_data.update({"type": "expense", "category": "🏠 Дом", "subcategory": ""})
        await query.edit_message_text("🏠 Введи сумму за дом:")
        return ENTER_AMOUNT

    elif data_cb == "exp_food":
        context.user_data.update({"type": "expense", "category": "🍕 Еда", "subcategory": ""})
        await query.edit_message_text("🍕 Введи сумму на еду:")
        return ENTER_AMOUNT

    elif data_cb == "exp_crypto":
        await query.edit_message_text("₿ Крипта — выбери тип расхода:", reply_markup=expense_crypto_keyboard())
        return EXPENSE_CRYPTO_CAT

    elif data_cb.startswith("exp_crypto_"):
        sub_map = {
            "exp_crypto_deposit": "💰 Пополнение депо",
            "exp_crypto_private": "🔒 Приватка/Сигналы",
            "exp_crypto_bot": "🤖 Парсер/Бот",
            "exp_crypto_sub": "📱 Подписки",
            "exp_crypto_other": "📝 Другое"
        }
        context.user_data.update({"type": "expense", "category": "Крипта", "subcategory": sub_map.get(data_cb, "")})
        await query.edit_message_text(f"Введи сумму ({sub_map.get(data_cb, '')}):")
        return ENTER_AMOUNT

    elif data_cb == "exp_other":
        context.user_data.update({"type": "expense", "category": "🛍 Прочее", "subcategory": ""})
        await query.edit_message_text("🛍 Введи сумму и комментарий через пробел\nНапример: 50 кофе")
        return ENTER_COMMENT

    # ДЕПОЗИТ
    elif data_cb == "deposit":
        await query.edit_message_text("💼 Депозит", reply_markup=deposit_keyboard())
        return DEPOSIT_MENU

    elif data_cb == "dep_add":
        context.user_data["dep_action"] = "add"
        await query.edit_message_text("📥 Введи сумму пополнения депозита:")
        return ENTER_DEPOSIT

    elif data_cb == "dep_withdraw":
        context.user_data["dep_action"] = "withdraw"
        await query.edit_message_text("📤 Введи сумму вывода с депозита:")
        return ENTER_DEPOSIT

    elif data_cb == "dep_balance":
        await query.edit_message_text(get_deposit_stats(), reply_markup=back_keyboard("deposit"))
        return DEPOSIT_MENU

    # СТАТИСТИКА
    elif data_cb == "stats":
        await query.edit_message_text("📊 Статистика", reply_markup=stats_keyboard())
        return STATS_MENU

    elif data_cb == "stats_today":
        await query.edit_message_text(get_stats_today(), reply_markup=back_keyboard("stats"))
        return STATS_MENU

    elif data_cb == "stats_month":
        await query.edit_message_text(get_stats_month(), reply_markup=back_keyboard("stats"))
        return STATS_MENU

    elif data_cb == "stats_crypto":
        await query.edit_message_text(get_stats_crypto(), reply_markup=back_keyboard("stats"))
        return STATS_MENU

    elif data_cb == "stats_deposit":
        await query.edit_message_text(get_deposit_stats(), reply_markup=back_keyboard("stats"))
        return STATS_MENU

    elif data_cb == "history":
        await query.edit_message_text(get_history(), reply_markup=back_keyboard("back_main"))
        return MAIN_MENU

    return MAIN_MENU

async def enter_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.replace(",", "."))
        ud = context.user_data
        add_transaction(ud["type"], ud["category"], ud["subcategory"], amount)

        sign = "+" if ud["type"] == "income" else "-"
        emoji = "✅" if ud["type"] == "income" else "💸"
        label = ud["category"] + (f" → {ud['subcategory']}" if ud["subcategory"] else "")

        await update.message.reply_text(
            f"{emoji} Записано!\n"
            f"{'💰' if ud['type'] == 'income' else '💸'} {label}: {sign}{amount:.2f} USDT\n"
            f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU
    except:
        await update.message.reply_text("Введи число, например: 150.5")
        return ENTER_AMOUNT

async def enter_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        parts = update.message.text.split(" ", 1)
        amount = float(parts[0].replace(",", "."))
        comment = parts[1] if len(parts) > 1 else ""
        ud = context.user_data
        add_transaction(ud["type"], ud["category"], ud["subcategory"], amount, comment)

        sign = "+" if ud["type"] == "income" else "-"
        emoji = "✅" if ud["type"] == "income" else "💸"

        await update.message.reply_text(
            f"{emoji} Записано!\n"
            f"{'💰' if ud['type'] == 'income' else '💸'} {ud['category']}{f' ({comment})' if comment else ''}: {sign}{amount:.2f} USDT\n"
            f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU
    except:
        await update.message.reply_text("Введи сумму и комментарий, например: 100 фриланс")
        return ENTER_COMMENT

async def enter_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.replace(",", "."))
        data = load_data()
        action = context.user_data.get("dep_action")

        if action == "add":
            data["deposit"]["added"] = data["deposit"].get("added", 0) + amount
            save_data(data)
            await update.message.reply_text(
                f"✅ Депозит пополнен на {amount:.2f} USDT",
                reply_markup=main_keyboard()
            )
        elif action == "withdraw":
            data["deposit"]["withdrawn"] = data["deposit"].get("withdrawn", 0) + amount
            save_data(data)
            await update.message.reply_text(
                f"✅ Вывод {amount:.2f} USDT зафиксирован",
                reply_markup=main_keyboard()
            )
        return MAIN_MENU
    except:
        await update.message.reply_text("Введи число, например: 500")
        return ENTER_DEPOSIT

# ========== ЗАПУСК ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ENTER_INITIAL_BALANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_initial_balance)],
            MAIN_MENU: [CallbackQueryHandler(button_handler)],
            INCOME_CAT: [CallbackQueryHandler(button_handler)],
            INCOME_CRYPTO_CAT: [CallbackQueryHandler(button_handler)],
            EXPENSE_CAT: [CallbackQueryHandler(button_handler)],
            EXPENSE_CRYPTO_CAT: [CallbackQueryHandler(button_handler)],
            DEPOSIT_MENU: [CallbackQueryHandler(button_handler)],
            STATS_MENU: [CallbackQueryHandler(button_handler)],
            ENTER_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_amount)],
            ENTER_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_comment)],
            ENTER_DEPOSIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_deposit)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    print("Финансовый бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
