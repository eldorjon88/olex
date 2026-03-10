from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from redis import Redis
from decouple import config
import requests
import json

user_tokens = {}
BACKEND_URL = "http://127.0.0.1:8000/api/v1/"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Salom! Saytga kirish uchun maxsus havola orqali keling.")
        return

    redis = Redis(host='localhost', port=6379, db=0)
    start_param = context.args[0]
    redis_data = redis.get(start_param)

    if not redis_data:
        await update.message.reply_text("Havola muddati tugagan yoki noto'g'ri!")
        redis.close()
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
    response = requests.post(f"{BACKEND_URL}auth/verify-tg/", json={"unicID": start_param})

    if response.status_code in [200, 201]:
        await update.message.reply_text("✅ Muvaffaqiyatli! Saytga qaytishingiz mumkin.")
    else:
        await update.message.reply_text("❌ Xatolik yuz berdi")

    redis.close()


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resp = requests.post(
        f"{BACKEND_URL}auth/get-tg/",
        json={"telegram_id": update.effective_user.id}
    )
    if resp.status_code == 200:
        token = resp.json().get("tokens", {}).get("access")
        user_tokens[update.effective_user.id] = token
        await update.message.reply_text("✅ Login muvaffaqiyatli")
    else:
        await update.message.reply_text("❌ Avval /start orqali ro'yxatdan o'ting")


async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = user_tokens.get(update.effective_user.id)
    if not token:
        await update.message.reply_text("Avval /login qiling")
        return
    try:
        title, description, price, category = context.args[:4]
    except:
        await update.message.reply_text("Format: /add_product title description price category_id")
        return

    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BACKEND_URL}products/", headers=headers,
                         json={"title": title, "description": description,
                               "price": price, "category": category,
                               "region": "Toshkent", "district": "Yunusobod"})
    if resp.status_code in [200, 201]:
        await update.message.reply_text("✅ Mahsulot qo'shildi")
    else:
        await update.message.reply_text(f"❌ Xato: {resp.text}")


async def add_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = user_tokens.get(update.effective_user.id)
    if not token:
        await update.message.reply_text("Avval /login qiling")
        return
    try:
        product_id = context.args[0]
    except:
        await update.message.reply_text("Format: /favorite product_id")
        return

    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BACKEND_URL}favorites/", headers=headers, json={"product": product_id})
    if resp.status_code in [200, 201]:
        await update.message.reply_text("✅ Favorite qo'shildi")
    else:
        await update.message.reply_text(f"❌ Xato: {resp.text}")


async def add_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = user_tokens.get(update.effective_user.id)
    if not token:
        await update.message.reply_text("Avval /login qiling")
        return
    try:
        product_id = context.args[0]
    except:
        await update.message.reply_text("Format: /order product_id")
        return

    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BACKEND_URL}orders/", headers=headers, json={"product": product_id})
    if resp.status_code in [200, 201]:
        await update.message.reply_text("✅ Buyurtma yaratildi")
    else:
        await update.message.reply_text(f"❌ Xato: {resp.text}")


async def add_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = user_tokens.get(update.effective_user.id)
    if not token:
        await update.message.reply_text("Avval /login qiling")
        return
    try:
        order_id = context.args[0]
        rating = context.args[1]
        comment = " ".join(context.args[2:])
    except:
        await update.message.reply_text("Format: /review order_id rating comment")
        return

    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BACKEND_URL}reviews/", headers=headers,
                         json={"order": order_id, "rating": rating, "comment": comment})
    if resp.status_code in [200, 201]:
        await update.message.reply_text("✅ Review qo'shildi")
    else:
        await update.message.reply_text(f"❌ Xato: {resp.text}")


if __name__ == "__main__":
    app = ApplicationBuilder().token(config("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("login", login))
    app.add_handler(CommandHandler("add_product", add_product))
    app.add_handler(CommandHandler("favorite", add_favorite))
    app.add_handler(CommandHandler("order", add_order))
    app.add_handler(CommandHandler("review", add_review))
    print("Bot ishga tushdi...")
    app.run_polling()