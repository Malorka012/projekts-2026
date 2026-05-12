# Pozitīvais tests Nr.1

# Nosaukums: Eksamens
# Datums: 2026-05-20 14:00
# Rezultāts: Pasakums veiksmigi pievienots


# Pozitīvais tests Nr.2

# Nosaukums: Koncerts
# Datums: 2026-12-01 18:30
# Rezultāts: Pasakums veiksmigi pievienots


# Negatīvais tests Nr.1

# Nosaukums: Volejbola turnīrs
# Datums: 2026/05/20 14:00
# Rezultāts: Nepareizs datuma formats!


# Negatīvais tests Nr.2

# Nosaukums: Minecraft turnīrs
# Datums: 2026-15-99 77:88
# Rezultāts: Nepareizs datuma formats!





from datetime import datetime
import json
import calendar

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

TOKEN = "8721016961:AAFowBRU5rt7CQrXupLRv41lQmmwdPVwFQM"

app = ApplicationBuilder().token(TOKEN).build()

events = []
user_modes = {}

# ielādē pasākumus no faila
try:
    with open("events.json", "r", encoding="utf-8") as file:
        events = json.load(file)
except Exception:
    events = []


# saglabā pasākumus failā
def save_events():
    with open("events.json", "w", encoding="utf-8") as file:
        json.dump(events, file, ensure_ascii=False, indent=4)


# aprēķina atlikušo laiku
def time_left(date_string):
    event_time = datetime.strptime(date_string, "%Y-%m-%d %H:%M")
    seconds = int((event_time - datetime.now()).total_seconds())

    if seconds <= 0:
        return "beidzies"

    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    return f"{days}d {hours}h {minutes}m {secs}s"


# galvenā izvēlne
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Saraksts", callback_data="list")],
        [InlineKeyboardButton("Kalendars", callback_data="calendar")],
        [InlineKeyboardButton("Pievienot", callback_data="add")],
        [InlineKeyboardButton("Dzest", callback_data="delete")]
    ])


# izveido kalendāru
def create_calendar(year, month):
    keyboard = [
        [InlineKeyboardButton(f"{month}/{year}", callback_data="ignore")]
    ]

    for week in calendar.monthcalendar(year, month):
        row = []

        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="ignore"))
            else:
                text = str(day)

                for event in events:
                    event_date = datetime.strptime(
                        event["date"],
                        "%Y-%m-%d %H:%M"
                    )

                    if (
                        event_date.year == year and
                        event_date.month == month and
                        event_date.day == day
                    ):
                        text += "*"

                row.append(
                    InlineKeyboardButton(
                        text,
                        callback_data=f"day_{year}_{month}_{day}"
                    )
                )

        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton("<", callback_data=f"prev_{year}_{month}"),
        InlineKeyboardButton(">", callback_data=f"next_{year}_{month}")
    ])

    keyboard.append([
        InlineKeyboardButton("Atpakal", callback_data="back")
    ])

    return InlineKeyboardMarkup(keyboard)


# /start komanda
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Izvelies:",
        reply_markup=main_menu()
    )


# pogu apstrāde
async def handle_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id

    # SARAKSTS
    if data == "list":

        if not events:
            await query.edit_message_text(
                "Nav pasakumu",
                reply_markup=main_menu()
            )
            return

        text_output = ""

        for event in events:
            text_output += (
                f"{event['name']} - "
                f"{time_left(event['date'])}\n"
            )

        await query.edit_message_text(
            text_output,
            reply_markup=main_menu()
        )

    # KALENDĀRS
    elif data == "calendar":
        now = datetime.now()

        await query.edit_message_text(
            "Kalendars:",
            reply_markup=create_calendar(now.year, now.month)
        )

    # IEPRIEKŠĒJAIS/NĀKAMAIS MĒNESIS
    elif data.startswith("prev_") or data.startswith("next_"):

        _, year, month = data.split("_")

        year = int(year)
        month = int(month)

        if data.startswith("prev"):
            month -= 1
        else:
            month += 1

        if month == 0:
            month = 12
            year -= 1

        if month == 13:
            month = 1
            year += 1

        await query.edit_message_text(
            "Kalendars:",
            reply_markup=create_calendar(year, month)
        )

    # KONKRĒTA DIENA
    elif data.startswith("day_"):

        _, year, month, day = data.split("_")

        year = int(year)
        month = int(month)
        day = int(day)

        text_output = f"{day}.{month}.{year}\n\n"

        found = False

        for event in events:

            event_date = datetime.strptime(
                event["date"],
                "%Y-%m-%d %H:%M"
            )

            if (
                event_date.year == year and
                event_date.month == month and
                event_date.day == day
            ):
                text_output += (
                    f"{event['name']} - "
                    f"{time_left(event['date'])}\n"
                )

                found = True

        if not found:
            text_output += "Nav pasakumu"

        await query.edit_message_text(
            text_output,
            reply_markup=create_calendar(year, month)
        )

    # PIEVIENOT PASĀKUMU
    elif data == "add":

        user_modes[user_id] = {
            "step": "name"
        }

        await query.edit_message_text("Ievadi pasakuma nosaukumu:")

    # DZĒST PASĀKUMU
    elif data == "delete":

        if not events:
            await query.edit_message_text(
                "Nav ko dzest",
                reply_markup=main_menu()
            )
            return

        keyboard = []

        for i, event in enumerate(events):
            keyboard.append([
                InlineKeyboardButton(
                    event["name"],
                    callback_data=f"remove_{i}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton("Atpakal", callback_data="back")
        ])

        await query.edit_message_text(
            "Izvelies ko dzest:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # DZĒŠANAS APSTIPRINĀŠANA
    elif data.startswith("remove_"):

        index = int(data.split("_")[1])

        if index < len(events):
            events.pop(index)
            save_events()

        await query.edit_message_text(
            "Pasakums dzests",
            reply_markup=main_menu()
        )

    # ATPAKAĻ
    elif data == "back":

        await query.edit_message_text(
            "Izvelies:",
            reply_markup=main_menu()
        )


# teksta ievade
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in user_modes:
        return

    user_data = user_modes[user_id]

    # ievada nosaukumu
    if user_data["step"] == "name":

        user_modes[user_id] = {
            "step": "date",
            "name": update.message.text
        }

        await update.message.reply_text(
            "Ievadi datumu formātā:\nYYYY-MM-DD HH:MM"
        )

    # ievada datumu
    elif user_data["step"] == "date":

        try:
            datetime.strptime(
                update.message.text,
                "%Y-%m-%d %H:%M"
            )

            events.append({
                "name": user_data["name"],
                "date": update.message.text
            })

            save_events()

            del user_modes[user_id]

            await update.message.reply_text(
                "Pasakums veiksmigi pievienots!",
                reply_markup=main_menu()
            )

        except Exception:
            await update.message.reply_text(
                "Nepareizs datuma formats!\n"
                "Pareizs: YYYY-MM-DD HH:MM"
            )



app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_click))
app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_text
    )
)

print("Bots palaists...")

app.run_polling()
