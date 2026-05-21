import os
import json
import logging
import requests
from datetime import datetime, date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = "8880279666:AAGGb732K9jesymvXEI1QeNOTZrkm3Abq3E"
OWNER_ID = 1780854025
DATA_FILE = "finance_data.json"
# ================================

logging.basicConfig(level=logging.INFO)

# Состояния
(MAIN_MENU, INCOME_CAT, INCOME_CRYPTO_CAT, EXPENSE_CAT, EXPENSE_CRYPTO_CAT,
 ENTER_AMOUNT, ENTER_COMMENT, DEPOSIT_MENU, ENTER_DEPOSIT, STATS_MENU,
 ENTER_INITIAL_BALANCE, NOTES_MENU, ENTER_NOTE, EDIT_MENU, EDIT_SELECT,
 EDIT_AMOUNT, DELETE_SELECT) = range(17)

def is_owner(update: Update) -> bool:
    user_id = update.effective_user.id if update.effective_user else None
    return user_id == OWNER_ID

# ========== КУРС ВАЛЮТ ==========
def get_czk_to_usdt():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=czk", timeout=5)
        data = r.json()
        czk_per_usdt = data["tether"]["czk"]
        return czk_per_usdt
    except:
        return 23.5  # fallback курс

def czk_to_usdt(czk):
    rate = get_czk_to_usdt()
    return czk / rate

def usdt_to_czk(usdt):
    rate = get_czk_to_usdt()
    return usdt * rate

# ========== РАБОТА С ДАННЫМИ ==========
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "transactions": [],
        "notes": [],
        "deposit": {"initial": 0, "added": 0, "withdrawn": 0}
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_transaction(type_, category, subcategory, amount, currency, comment=""):
    data = load_data()
    data["transactions"].append({
        "id": len(data["transactions"]) + 1,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M"),
        "type": type_,
        "category": category,
        "subcategory": subcategory,
        "amount": amount,
        "currency": currency,
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
        [InlineKeyboardButton("📋 История", callback_data="history"),
         InlineKeyboardButton("💬 Заметки", callback_data="notes")],
        [InlineKeyboardButton("✏️ Редактировать", callback_data="edit"),
         InlineKeyboardButton("🗑 Удалить", callback_data="delete")]
    ])

def income_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💼 Зарплата (CZK)", callback_data="inc_salary")],
        [InlineKeyboardButton("₿ Крипта (USDT)", callback_data="inc_crypto")],
        [InlineKeyboardButton("📝 Другое (CZK)", callback_data="inc_other")],
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
        [InlineKeyboardButton("🏠 Дом (CZK)", callback_data="exp_home"),
         InlineKeyboardButton("🍕 Еда (CZK)", callback_data="exp_food")],
        [InlineKeyboardButton("₿ Крипта (USDT)", callback_data="exp_crypto"),
         InlineKeyboardButton("🛍 Прочее (CZK)", callback_data="exp_other")],
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
        [InlineKeyboardButton("💱 Курс CZK/USDT", callback_data="stats_rate")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_main")]
    ])

def notes_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить заметку", callback_data="note_add")],
        [InlineKeyboardButton("📋 Мои заметки", callback_data="note_list")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_main")]
    ])

def back_keyboard(back_to="back_main"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data=back_to)]
    ])

# ========== ФОРМАТИРОВАНИЕ ==========
def fmt(amount, currency):
    if currency == "CZK":
        return f"{amount:,.0f} CZK"
    return f"{amount:.2f} USDT"

# ========== СТАТИСТИКА ==========
def get_stats_today():
    data = load_data()
    today = date.today().strftime("%Y-%m-%d")
    txs = [t for t in data["transactions"] if t["date"] == today]
    rate = get_czk_to_usdt()

    czk_income = sum(t["amount"] for t in txs if t["type"] == "income" and t.get("currency") == "CZK")
    czk_expense = sum(t["amount"] for t in txs if t["type"] == "expense" and t.get("currency") == "CZK")
    usdt_income = sum(t["amount"] for t in txs if t["type"] == "income" and t.get("currency") == "USDT")
    usdt_expense = sum(t["amount"] for t in txs if t["type"] == "expense" and t.get("currency") == "USDT")

    msg = f"📊 Сегодня ({date.today().strftime('%d.%m.%Y')})\n"
    msg += "━━━━━━━━━━━━━━━\n"
    msg += f"🏠 Жизнь (CZK):\n"
    msg += f"  💰 Доходы: +{czk_income:,.0f} CZK\n"
    msg += f"  💸 Расходы: -{czk_expense:,.0f} CZK\n"
    msg += f"  💵 Баланс: {czk_income - czk_expense:+,.0f} CZK\n"
    msg += "━━━━━━━━━━━━━━━\n"
    msg += f"₿ Крипта (USDT):\n"
    msg += f"  💰 Доходы: +{usdt_income:.2f} USDT\n"
    msg += f"  💸 Расходы: -{usdt_expense:.2f} USDT\n"
    msg += f"  💵 Баланс: {usdt_income - usdt_expense:+.2f} USDT\n"
    msg += "━━━━━━━━━━━━━━━\n"
    msg += f"💱 Курс: 1 USDT = {rate:.1f} CZK"
    return msg

def get_stats_month():
    data = load_data()
    month = date.today().strftime("%Y-%m")
    txs = [t for t in data["transactions"] if t["date"].startswith(month)]
    rate = get_czk_to_usdt()

    czk_income_details = {}
    czk_expense_details = {}
    usdt_income_details = {}
    usdt_expense_details = {}

    for t in txs:
        label = t["category"] + (f" → {t['subcategory']}" if t.get("subcategory") else "")
        if t.get("currency") == "CZK":
            if t["type"] == "income":
                czk_income_details[label] = czk_income_details.get(label, 0) + t["amount"]
            else:
                czk_expense_details[label] = czk_expense_details.get(label, 0) + t["amount"]
        else:
            if t["type"] == "income":
                usdt_income_details[label] = usdt_income_details.get(label, 0) + t["amount"]
            else:
                usdt_expense_details[label] = usdt_expense_details.get(label, 0) + t["amount"]

    czk_in = sum(czk_income_details.values())
    czk_ex = sum(czk_expense_details.values())
    usdt_in = sum(usdt_income_details.values())
    usdt_ex = sum(usdt_expense_details.values())

    msg = f"📆 {date.today().strftime('%B %Y')}\n"
    msg += "━━━━━━━━━━━━━━━\n"
    msg += "🏠 Жизнь (CZK):\n"
    for k, v in czk_income_details.items():
        msg += f"  ✅ {k}: +{v:,.0f}\n"
    for k, v in czk_expense_details.items():
        msg += f"  ❌ {k}: -{v:,.0f}\n"
    msg += f"  💵 Итого: {czk_in - czk_ex:+,.0f} CZK\n"
    msg += "━━━━━━━━━━━━━━━\n"
    msg += "₿ Крипта (USDT):\n"
    for k, v in usdt_income_details.items():
        msg += f"  ✅ {k}: +{v:.2f}\n"
    for k, v in usdt_expense_details.items():
        msg += f"  ❌ {k}: -{v:.2f}\n"
    msg += f"  💵 Итого: {usdt_in - usdt_ex:+.2f} USDT\n"
    msg += "━━━━━━━━━━━━━━━\n"
    msg += f"💱 Курс: 1 USDT = {rate:.1f} CZK"
    return msg

def get_stats_crypto():
    data = load_data()
    month = date.today().strftime("%Y-%m")
    txs = [t for t in data["transactions"] if t["date"].startswith(month) and t.get("currency") == "USDT"]

    income_by_sub = {}
    expense_by_sub = {}
    for t in txs:
        sub = t.get("subcategory") or t["category"]
        if t["type"] == "income":
            income_by_sub[sub] = income_by_sub.get(sub, 0) + t["amount"]
        else:
            expense_by_sub[sub] = expense_by_sub.get(sub, 0) + t["amount"]

    total_income = sum(income_by_sub.values())
    total_expense = sum(expense_by_sub.values())
    net = total_income - total_expense

    msg = f"₿ Крипто-статистика {date.today().strftime('%B %Y')}\n"
    msg += "━━━━━━━━━━━━━━━\n"
    msg += "💰 Доходы:\n"
    for k, v in income_by_sub.items():
        msg += f"  {k}: +{v:.2f} USDT\n"
    msg += "\n💸 Расходы:\n"
    for k, v in expense_by_sub.items():
        msg += f"  {k}: -{v:.2f} USDT\n"
    msg += "━━━━━━━━━━━━━━━\n"
    emoji = "🏆" if net >= 0 else "❌"
    msg += f"{emoji} Чистый профит: {net:+.2f} USDT"
    return msg

def get_deposit_stats():
    data = load_data()
    dep = data["deposit"]
    initial = dep.get("initial", 0)
    added = dep.get("added", 0)
    withdrawn = dep.get("withdrawn", 0)
    rate = get_czk_to_usdt()

    month = date.today().strftime("%Y-%m")
    txs = [t for t in data["transactions"] if t["date"].startswith(month) and t.get("currency") == "USDT" and t["type"] == "income"]
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
    msg += f"   ≈ {current * rate:,.0f} CZK\n"
    msg += f"📈 Заработано за месяц: +{crypto_profit:.2f} USDT\n"
    msg += "━━━━━━━━━━━━━━━\n"
    msg += f"🏆 ROI за месяц: {roi:.2f}%\n"
    msg += f"💱 Курс: 1 USDT = {rate:.1f} CZK"
    return msg

def get_rate_info():
    rate = get_czk_to_usdt()
    msg = "💱 Текущий курс\n"
    msg += "━━━━━━━━━━━━━━━\n"
    msg += f"1 USDT = {rate:.2f} CZK\n"
    msg += f"1 CZK = {1/rate:.4f} USDT\n"
    msg += "━━━━━━━━━━━━━━━\n"
    msg += f"100 USDT = {100*rate:,.0f} CZK\n"
    msg += f"1000 CZK = {1000/rate:.2f} USDT\n"
    msg += f"10000 CZK = {10000/rate:.2f} USDT"
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
        label = t["category"] + (f" → {t['subcategory']}" if t.get("subcategory") else "")
        comment = f" ({t['comment']})" if t.get("comment") else ""
        currency = t.get("currency", "USDT")
        amount_str = f"{t['amount']:,.0f} {currency}" if currency == "CZK" else f"{t['amount']:.2f} {currency}"
        msg += f"#{t.get('id','?')} {emoji} {t['date']}\n"
        msg += f"  {label}{comment}: {sign}{amount_str}\n"
    return msg

def get_edit_list():
    data = load_data()
    txs = data["transactions"][-10:][::-1]
    if not txs:
        return None, "История пуста"

    msg = "✏️ Выбери запись для редактирования:\n━━━━━━━━━━━━━━━\n"
    buttons = []
    for t in txs:
        currency = t.get("currency", "USDT")
        amount_str = f"{t['amount']:,.0f}" if currency == "CZK" else f"{t['amount']:.2f}"
        label = f"#{t.get('id','?')} {t['category']} {amount_str} {currency}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"edit_id_{t.get('id')}")])
    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(buttons), msg

def get_delete_list():
    data = load_data()
    txs = data["transactions"][-10:][::-1]
    if not txs:
        return None, "История пуста"

    msg = "🗑 Выбери запись для удаления:\n━━━━━━━━━━━━━━━\n"
    buttons = []
    for t in txs:
        currency = t.get("currency", "USDT")
        amount_str = f"{t['amount']:,.0f}" if currency == "CZK" else f"{t['amount']:.2f}"
        label = f"#{t.get('id','?')} {t['category']} {amount_str} {currency}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"delete_id_{t.get('id')}")])
    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(buttons), msg

def get_notes_list():
    data = load_data()
    notes = data.get("notes", [])
    if not notes:
        return "💬 Заметок пока нет"
    msg = "💬 Мои заметки\n━━━━━━━━━━━━━━━\n"
    for n in notes[-10:][::-1]:
        msg += f"📌 {n['date']}\n{n['text']}\n\n"
    return msg

# ========== ХЭНДЛЕРЫ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("⛔ Доступ запрещён.")
        return ConversationHandler.END

    data = load_data()
    if data["deposit"]["initial"] == 0 and not data["transactions"]:
        await update.message.reply_text(
            "👋 Привет! Я твой личный финансовый бот.\n\n"
            "Введи текущий баланс крипто-депозита в USDT:"
        )
        return ENTER_INITIAL_BALANCE

    await update.message.reply_text("💼 Главное меню", reply_markup=main_keyboard())
    return MAIN_MENU

async def enter_initial_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.replace(",", "."))
        data = load_data()
        data["deposit"]["initial"] = amount
        save_data(data)
        await update.message.reply_text(
            f"✅ Начальный баланс: {amount:.2f} USDT",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU
    except:
        await update.message.reply_text("Введи число, например: 800")
        return ENTER_INITIAL_BALANCE

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_owner(update):
        await query.edit_message_text("⛔ Доступ запрещён.")
        return ConversationHandler.END
    cb = query.data

    if cb == "back_main":
        await query.edit_message_text("💼 Главное меню", reply_markup=main_keyboard())
        return MAIN_MENU

    # ДОХОДЫ
    elif cb == "income":
        await query.edit_message_text("➕ Категория дохода:", reply_markup=income_keyboard())
        return INCOME_CAT

    elif cb == "inc_salary":
        context.user_data.update({"type": "income", "category": "💼 Зарплата", "subcategory": "", "currency": "CZK"})
        await query.edit_message_text("💼 Введи сумму зарплаты в CZK:")
        return ENTER_AMOUNT

    elif cb == "inc_crypto":
        await query.edit_message_text("₿ Крипта — тип дохода:", reply_markup=income_crypto_keyboard())
        return INCOME_CRYPTO_CAT

    elif cb.startswith("inc_crypto_"):
        sub_map = {
            "inc_crypto_long": "📈 Лонг", "inc_crypto_short": "📉 Шорт",
            "inc_crypto_funding": "💸 Фандинг", "inc_crypto_spread": "↔️ Спред",
            "inc_crypto_other": "📝 Другое"
        }
        sub = sub_map.get(cb, "")
        context.user_data.update({"type": "income", "category": "Крипта", "subcategory": sub, "currency": "USDT"})
        await query.edit_message_text(f"Введи сумму в USDT ({sub}):")
        return ENTER_AMOUNT

    elif cb == "inc_other":
        context.user_data.update({"type": "income", "category": "Другое", "subcategory": "", "currency": "CZK"})
        await query.edit_message_text("📝 Введи сумму в CZK и комментарий\nНапример: 5000 фриланс")
        return ENTER_COMMENT

    # РАСХОДЫ
    elif cb == "expense":
        await query.edit_message_text("➖ Категория расхода:", reply_markup=expense_keyboard())
        return EXPENSE_CAT

    elif cb == "exp_home":
        context.user_data.update({"type": "expense", "category": "🏠 Дом", "subcategory": "", "currency": "CZK"})
        await query.edit_message_text("🏠 Введи сумму в CZK:")
        return ENTER_AMOUNT

    elif cb == "exp_food":
        context.user_data.update({"type": "expense", "category": "🍕 Еда", "subcategory": "", "currency": "CZK"})
        await query.edit_message_text("🍕 Введи сумму в CZK:")
        return ENTER_AMOUNT

    elif cb == "exp_crypto":
        await query.edit_message_text("₿ Крипта — тип расхода:", reply_markup=expense_crypto_keyboard())
        return EXPENSE_CRYPTO_CAT

    elif cb.startswith("exp_crypto_"):
        sub_map = {
            "exp_crypto_deposit": "💰 Пополнение депо",
            "exp_crypto_private": "🔒 Приватка/Сигналы",
            "exp_crypto_bot": "🤖 Парсер/Бот",
            "exp_crypto_sub": "📱 Подписки",
            "exp_crypto_other": "📝 Другое"
        }
        sub = sub_map.get(cb, "")
        context.user_data.update({"type": "expense", "category": "Крипта", "subcategory": sub, "currency": "USDT"})
        await query.edit_message_text(f"Введи сумму в USDT ({sub}):")
        return ENTER_AMOUNT

    elif cb == "exp_other":
        context.user_data.update({"type": "expense", "category": "🛍 Прочее", "subcategory": "", "currency": "CZK"})
        await query.edit_message_text("🛍 Введи сумму в CZK и комментарий\nНапример: 500 одежда")
        return ENTER_COMMENT

    # ДЕПОЗИТ
    elif cb == "deposit":
        await query.edit_message_text("💼 Депозит", reply_markup=deposit_keyboard())
        return DEPOSIT_MENU

    elif cb == "dep_add":
        context.user_data["dep_action"] = "add"
        await query.edit_message_text("📥 Введи сумму пополнения в USDT:")
        return ENTER_DEPOSIT

    elif cb == "dep_withdraw":
        context.user_data["dep_action"] = "withdraw"
        await query.edit_message_text("📤 Введи сумму вывода в USDT:")
        return ENTER_DEPOSIT

    elif cb == "dep_balance":
        await query.edit_message_text(get_deposit_stats(), reply_markup=back_keyboard("deposit"))
        return DEPOSIT_MENU

    # СТАТИСТИКА
    elif cb == "stats":
        await query.edit_message_text("📊 Статистика", reply_markup=stats_keyboard())
        return STATS_MENU

    elif cb == "stats_today":
        await query.edit_message_text(get_stats_today(), reply_markup=back_keyboard("stats"))
        return STATS_MENU

    elif cb == "stats_month":
        await query.edit_message_text(get_stats_month(), reply_markup=back_keyboard("stats"))
        return STATS_MENU

    elif cb == "stats_crypto":
        await query.edit_message_text(get_stats_crypto(), reply_markup=back_keyboard("stats"))
        return STATS_MENU

    elif cb == "stats_deposit":
        await query.edit_message_text(get_deposit_stats(), reply_markup=back_keyboard("stats"))
        return STATS_MENU

    elif cb == "stats_rate":
        await query.edit_message_text(get_rate_info(), reply_markup=back_keyboard("stats"))
        return STATS_MENU

    # ИСТОРИЯ
    elif cb == "history":
        await query.edit_message_text(get_history(), reply_markup=back_keyboard("back_main"))
        return MAIN_MENU

    # ЗАМЕТКИ
    elif cb == "notes":
        await query.edit_message_text("💬 Заметки", reply_markup=notes_keyboard())
        return NOTES_MENU

    elif cb == "note_add":
        await query.edit_message_text("💬 Введи текст заметки:")
        return ENTER_NOTE

    elif cb == "note_list":
        await query.edit_message_text(get_notes_list(), reply_markup=back_keyboard("notes"))
        return NOTES_MENU

    # РЕДАКТИРОВАНИЕ
    elif cb == "edit":
        kb, msg = get_edit_list()
        if kb:
            await query.edit_message_text(msg, reply_markup=kb)
        else:
            await query.edit_message_text(msg, reply_markup=back_keyboard("back_main"))
        return EDIT_SELECT

    elif cb.startswith("edit_id_"):
        tx_id = int(cb.replace("edit_id_", ""))
        context.user_data["edit_id"] = tx_id
        data = load_data()
        tx = next((t for t in data["transactions"] if t.get("id") == tx_id), None)
        if tx:
            currency = tx.get("currency", "USDT")
            await query.edit_message_text(
                f"✏️ Редактирование записи #{tx_id}\n"
                f"Категория: {tx['category']}\n"
                f"Сумма: {tx['amount']} {currency}\n\n"
                f"Введи новую сумму в {currency}:",
                reply_markup=back_keyboard("edit")
            )
            return EDIT_AMOUNT
        return EDIT_SELECT

    # УДАЛЕНИЕ
    elif cb == "delete":
        kb, msg = get_delete_list()
        if kb:
            await query.edit_message_text(msg, reply_markup=kb)
        else:
            await query.edit_message_text(msg, reply_markup=back_keyboard("back_main"))
        return DELETE_SELECT

    elif cb.startswith("delete_id_"):
        tx_id = int(cb.replace("delete_id_", ""))
        data = load_data()
        data["transactions"] = [t for t in data["transactions"] if t.get("id") != tx_id]
        save_data(data)
        await query.edit_message_text(f"🗑 Запись #{tx_id} удалена!", reply_markup=main_keyboard())
        return MAIN_MENU

    return MAIN_MENU

async def enter_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.replace(",", ".").replace(" ", ""))
        ud = context.user_data
        add_transaction(ud["type"], ud["category"], ud.get("subcategory", ""), amount, ud.get("currency", "USDT"))

        sign = "+" if ud["type"] == "income" else "-"
        emoji = "✅" if ud["type"] == "income" else "💸"
        label = ud["category"] + (f" → {ud['subcategory']}" if ud.get("subcategory") else "")
        currency = ud.get("currency", "USDT")
        amount_str = f"{amount:,.0f} {currency}" if currency == "CZK" else f"{amount:.2f} {currency}"

        await update.message.reply_text(
            f"{emoji} Записано!\n{label}: {sign}{amount_str}\n📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU
    except:
        await update.message.reply_text("Введи число, например: 5000")
        return ENTER_AMOUNT

async def enter_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        parts = update.message.text.split(" ", 1)
        amount = float(parts[0].replace(",", ".").replace(" ", ""))
        comment = parts[1] if len(parts) > 1 else ""
        ud = context.user_data
        currency = ud.get("currency", "CZK")
        add_transaction(ud["type"], ud["category"], ud.get("subcategory", ""), amount, currency, comment)

        sign = "+" if ud["type"] == "income" else "-"
        emoji = "✅" if ud["type"] == "income" else "💸"
        amount_str = f"{amount:,.0f} {currency}" if currency == "CZK" else f"{amount:.2f} {currency}"

        await update.message.reply_text(
            f"{emoji} Записано!\n{ud['category']}{f' ({comment})' if comment else ''}: {sign}{amount_str}\n📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU
    except:
        await update.message.reply_text("Введи сумму и комментарий, например: 5000 аренда")
        return ENTER_COMMENT

async def enter_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.replace(",", "."))
        data = load_data()
        action = context.user_data.get("dep_action")
        if action == "add":
            data["deposit"]["added"] = data["deposit"].get("added", 0) + amount
            save_data(data)
            await update.message.reply_text(f"✅ Депозит пополнен на {amount:.2f} USDT", reply_markup=main_keyboard())
        elif action == "withdraw":
            data["deposit"]["withdrawn"] = data["deposit"].get("withdrawn", 0) + amount
            save_data(data)
            await update.message.reply_text(f"✅ Вывод {amount:.2f} USDT зафиксирован", reply_markup=main_keyboard())
        return MAIN_MENU
    except:
        await update.message.reply_text("Введи число, например: 500")
        return ENTER_DEPOSIT

async def enter_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    data = load_data()
    if "notes" not in data:
        data["notes"] = []
    data["notes"].append({"date": datetime.now().strftime("%d.%m.%Y %H:%M"), "text": text})
    save_data(data)
    await update.message.reply_text("💬 Заметка сохранена!", reply_markup=main_keyboard())
    return MAIN_MENU

async def enter_edit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.replace(",", ".").replace(" ", ""))
        tx_id = context.user_data.get("edit_id")
        data = load_data()
        for t in data["transactions"]:
            if t.get("id") == tx_id:
                t["amount"] = amount
                break
        save_data(data)
        await update.message.reply_text(f"✅ Запись #{tx_id} обновлена! Новая сумма: {amount}", reply_markup=main_keyboard())
        return MAIN_MENU
    except:
        await update.message.reply_text("Введи число")
        return EDIT_AMOUNT

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
            NOTES_MENU: [CallbackQueryHandler(button_handler)],
            EDIT_SELECT: [CallbackQueryHandler(button_handler)],
            DELETE_SELECT: [CallbackQueryHandler(button_handler)],
            ENTER_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_amount)],
            ENTER_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_comment)],
            ENTER_DEPOSIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_deposit)],
            ENTER_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_note)],
            EDIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_edit_amount)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    print("Финансовый бот v2 запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
