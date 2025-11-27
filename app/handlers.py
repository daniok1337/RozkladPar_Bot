from aiogram import F, Router
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message, CallbackQuery
from datetime import datetime
import app.keyboards as kb
import json
import os
import pytz
router = Router()


SCHEDULE_FILE = "schedule.json"
USERS_FILE = "users.json"
TIMEZONE = "Europe/Kiev"

def load_json(path):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf=8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_week_type():
    tz = pytz.timezone(TIMEZONE)
    iso_week = datetime.now(tz).isocalendar()[1]
    return "odd" if iso_week % 2 == 0 else "even"

def get_link_text(url):
    if "zoom" in url: return "Zoom"
    if "google" in url or "meet" in url: return "Google Meet"
    return "пари"

DAYS_UKR = {
    "Monday": "Понеділок", "Tuesday": "Вівторок", "Wednesday": "Середа",
    "Thursday": "Четвер", "Friday": "П'ятниця", "Saturday": "Субота", "Sunday": "Неділя"
}
DAYS_LIST = list(DAYS_UKR.keys())

@router.message(CommandStart())
async def cmd_start(message: Message):
    users = load_json(USERS_FILE)
    chat_id = str(message.from_user.id)
    if chat_id not in users:
        users[chat_id] = {"active": True, "reminders": True}
        save_json(USERS_FILE, users)
    current_week = "Чисельник" if get_week_type() == "odd" else "Знаменник"
    await message.answer(f"Привіт! Я бот розкладу, який вкиноє різні функції.\nЗараз тиждень: <b>{current_week}</b>\n"
        "Можна тиснути кнопки або писати команди:\n"
        "/today — Розклад на сьогодні\n"
        "/week — Весь тиждень\n"
        "/reminders_on — Ввімкнути нагадування\n"
        "/reminders_off — Вимкнути нагадування", 
        reply_markup=kb.main,
        parse_mode="HTML"
    )
    
@router.message(Command("today"))
async def cmd_today(message: Message):
    await show_today_schedule(message)

async def show_today_schedule(message: Message):
    tz = pytz.timezone(TIMEZONE)
    today_idx = datetime.now(tz).weekday()
    if today_idx > 4:
        await message.answer("Сьогодні вихідний!")
        return
    
    today_eng = DAYS_LIST[today_idx]
    schedule = load_json(SCHEDULE_FILE)
    lessons = schedule.get(today_eng, [])
    current_week = get_week_type()
    week_name = "Чисельник" if current_week == "odd" else "Знаменник"
    day_name = DAYS_UKR.get(today_eng, today_eng)
    
    text = f"<b>Сьогодні {day_name} ({week_name}):</b>\n\n"
    found = False
    for l in lessons:
        if l['week_type'] != 'both' and l['week_type'] != current_week: continue
        found = True
        text += f"<b>{l['time']}</b> — {l['subject']}\n"
        link = l.get('link') or l.get('zoom')

        if link and len(link) > 5:
            service_name = get_link_text(link)
            text += f"<a href='{link}'>Приєднатися до {service_name}</a>\n"
        else:
            text += "<i>(Офлайн)</i>\n"
        text += "\n"
    if not found: text += "Пар немає!"
    await message.answer(text, parse_mode="HTML")

@router.message(Command("week"))
@router.message(F.text.contains("Весь тиждень"))
async def show_week(message: Message):
    schedule = load_json(SCHEDULE_FILE)
    current_week = get_week_type()
    week_name = "Чисельник" if current_week == "odd" else "Знаменник"
    
    text = f" <b>Весь тиждень ({week_name}):</b>\n\n"
    
    for eng, ukr in DAYS_UKR.items():
        lessons = schedule.get(eng, [])
        active_lessons = [l for l in lessons if l['week_type'] == 'both' or l['week_type'] == current_week]
        if active_lessons:
            text += f" <b>{ukr}</b>:\n"
            for l in active_lessons:
                text += f" {l['time']} — {l['subject']}\n"
            text += "\n"   
    await message.answer(text, parse_mode="HTML")


@router.message(Command("reminders_on"))
async def turn_on(message: Message):
    await set_reminder_status(message, True)

@router.message(Command("reminders_off"))
async def turn_off(message: Message):
    await set_reminder_status(message, False)

@router.message(Command("reminders"))
async def cmd_reminders_info(message: Message):
    await message.answer(
        "<b>Керування нагадуваннями:</b>\n\n"
        "Натисни: /reminders_on (Увімкнути)\n"
        "Натисни: /reminders_off (Вимкнути)",
        parse_mode="HTML"
    )

async def set_reminder_status(message: Message, status: bool):
    users = load_json(USERS_FILE)
    chat_id = str(message.chat.id)

    if chat_id not in users:
        users[chat_id] = {"active": True, "reminders": status}
    else:
        users[chat_id]["reminders"] = status
    save_json(USERS_FILE, users)

    text = "<b>Нагадування УВІМКНЕНО!</b>" if status else "<b>Нагадування ВИМКНЕНО.</b>"
    await message.answer(text, parse_mode="HTML")



@router.message(F.text == "Обрати день")
async def show_days(message: Message):
    try:
        await message.delete()
    except:
        pass
    user_id = message.from_user.id
    await message.answer("Оберіть день тижня", reply_markup=kb.get_days_inline(user_id))


@router.callback_query(F.data.in_(DAYS_UKR.keys()))
async def process_day(callback: CallbackQuery):
    day_key = callback.data
    
    schedule = load_json(SCHEDULE_FILE)
    lessons = schedule.get(day_key, [])
    current_week = get_week_type()
    week_name = "Чисельник" if current_week == "odd" else "Знаменник"
    day_name = DAYS_UKR.get(day_key, day_key)
    text = f"<b>{day_name} ({week_name}):</b>\n\n"
    found_lessons = False
    
    for l in lessons:
        if l['week_type'] != 'both' and l['week_type'] != current_week:
            continue
        
        found_lessons = True
        text += f" <b>{l['time']}</b> — {l['subject']}\n"
        link = l.get('link') or l.get('zoom')

        if link and len(link) > 5:
            service_name = get_link_text(link)
            text += f"<a href='{link}'>Приєднатися до {service_name}</a>\n"
        else:
            text += "<i>(Офлайн / немає посилання)</i>\n"

    if not found_lessons:
        text += "Пар немає! Відпочиваємо."
    await callback.message.edit_text(text, reply_markup=callback.message.reply_markup, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("close_"))
async def close_menu(callback: CallbackQuery):
    owmer_id = int(callback.data.split("_")[1])
    clicker_id = callback.from_user.id
    if clicker_id == owmer_id:   
        await callback.message.delete()
        await callback.answer()
    else:
        await callback.answer()
