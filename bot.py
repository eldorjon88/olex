from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from redis import Redis
from requests import post
from decouple import config
import json


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Salom! Saytga kirish uchun maxsus havola orqali keling.")
        return

    redis = Redis(host='localhost', port=6379, db=0)
    start_param = context.args[0]
    redis_data = redis.get(start_param)

    if not redis_data:
        await update.message.reply_text("Havola muddati tugagan yoki noto'g'ri!")
        return

    user = update.effective_user

    photos = await context.bot.get_user_profile_photos(user.id)
    photo_url = None

    if photos.total_count > 0:
        file_id = photos.photos[0][-1].file_id
        file = await context.bot.get_file(file_id)
        photo_url = f"https://api.telegram.org/file/bot{context.bot.token}/{file.file_path}"

    data = {
        "telegram_id": user.id,
        "username": user.username if user.username else f"id{user.id}",
        "first_name": user.first_name,
        "last_name": user.last_name if user.last_name else "",
        "photo_url": photo_url,
    }

    redis.set(start_param, json.dumps(data), ex=900)

    response = post("http://localhost:8000/api/auth/verify-tg/", json={"unicID": start_param})

    if response.status_code == 201:
        await update.message.reply_text("✅ Muvaffaqiyatli! Saytga qaytishingiz mumkin.")
    else:
        await update.message.reply_text(f"❌ Xato: {response.status_code}")

    redis.close()


if __name__ == "__main__":
    app = ApplicationBuilder().token(config("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    print("Bot ishga tushdi...")
    app.run_polling()