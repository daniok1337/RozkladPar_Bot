import asyncio
import pytz
import logging
import sys
import os
from aiogram.types import BotCommand
from datetime import datetime
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.handlers import router, load_json, get_week_type, SCHEDULE_FILE, USERS_FILE, TIMEZONE, DAYS_UKR
from aiohttp import web


async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command="/today", description="Розклад на сьогодні"),
        BotCommand(command="/week", description="Розклад на тиждень"),
        BotCommand(command="/reminders_on", description="Увімкнути нагадування"),
        BotCommand(command="/reminders_off", description="Вимкнути нагадування"),
        BotCommand(command="/start", description="Перезапустити бота"),
    ]
    await bot.set_my_commands(main_menu_commands)

async def health_check(request):
    return web.Response(text="Бот працює")

async def start_dummy_server():
    app = web.Application()
    app.add_routes([web.get('/', health_check)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Фейковий сервер запущено на порту {port}")


async def check_reminders(bot: Bot):
    try:
        schedule = load_json(SCHEDULE_FILE)
        users = load_json(USERS_FILE)
        tz = pytz.timezone(TIMEZONE)
        now = datetime.now(tz)
        
        if now.weekday() > 4: return

        weekdays_list = list(DAYS_UKR.keys())
        today_key = weekdays_list[now.weekday()]
        current_week = get_week_type()
        lessons = schedule.get(today_key, [])
        for lesson in lessons:
            if lesson['week_type'] != 'both' and lesson['week_type'] != current_week:
                continue

            try:
                time_str = lesson['time'].split('-')[0].strip()
                l_h, l_m = map(int, time_str.split(':'))
                lesson_time = now.replace(hour=l_h, minute=l_m, second=0, microsecond=0)
                
                diff = (lesson_time - now).total_seconds()
                
                if 240 <= diff <= 300:
                    zoom_link = lesson.get('zoom', '')
                    link_text = f"\n<a href='{zoom_link}'>Приєднатися до Zoom</a>" if len(zoom_link) > 5 else ""
                    
                    text = (f"<b>НАГАДУВАННЯ!</b>\n"
                            f"Через 5 хвилин пара:\n"
                            f"<b>{lesson['subject']}</b>"
                            f"{link_text}")
                    
                    print(f"Нагадування: {lesson['subject']}")
                    
                    for user_id, user_data in users.items():
                        if user_data.get("reminders", True):
                            try:
                                await bot.send_message(user_id, text, parse_mode="HTML")
                            except Exception:
                                pass
            except ValueError:
                continue

    except Exception as e:
        print(f"Помилка Scheduler: {e}")



async def main():
    bot = Bot(token ="8272347586:AAF1bwld_Mv7oBP_0T3P2OhESnNb0kOu0DM")
    dp =  Dispatcher()
    dp.include_router(router)
    await start_dummy_server()
    await set_main_menu(bot)
    scheduler = AsyncIOScheduler(timezone=pytz.timezone(TIMEZONE))
    scheduler.add_job(check_reminders, 'interval', seconds=60, kwargs={'bot': bot})
    scheduler.start()
    print("Ботa запущено")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот не працює")