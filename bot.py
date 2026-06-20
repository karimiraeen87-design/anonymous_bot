import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# ---------------- TOKEN ----------------
TOKEN = "8792479401:AAGEATw7KV2yx5DMXVLew_m6jpy44ju2Ndc"

ADMINS = [8173198254, 8110699981]

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ---------------- DATABASE ----------------
conn = sqlite3.connect("bot.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    username TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS blocked (
    user_id INTEGER PRIMARY KEY
)
""")

conn.commit()

# ---------------- FUNCTIONS ----------------
def is_blocked(user_id):
    cursor.execute("SELECT 1 FROM blocked WHERE user_id=?", (user_id,))
    return cursor.fetchone() is not None


def add_user(user):
    cursor.execute("""
    INSERT OR REPLACE INTO users (user_id, name, username)
    VALUES (?, ?, ?)
    """, (user.id, user.full_name, user.username))
    conn.commit()


# ---------------- START ----------------
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    add_user(message.from_user)

    if message.from_user.id in ADMINS:
        await message.answer("👑 پنل ادمین فعال شد")
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("📩 ارسال پیام", callback_data="send_again")
        )
        await message.answer(
    f"""سلام {message.from_user.first_name} 👋

به صندوق پیام ناشناس خوش اومدی.

📩 پیام‌های تو بدون نمایش هویت مستقیم ارسال می‌شن.
🔒 اینجا همه چیز محرمانه و ناشناسه.

فقط پیامتو بنویس و ارسال کن.""",
    reply_markup=keyboard
)


# ---------------- USER MESSAGE ----------------
@dp.message_handler(lambda m: m.from_user.id not in ADMINS)
async def user_message(message: types.Message):

    if is_blocked(message.from_user.id):
        await message.answer("⛔ شما بلاک هستید")
        return

    add_user(message.from_user)

    text = (
        f"📩 پیام جدید\n\n"
        f"👤 {message.from_user.full_name}\n"
        f"🆔 {message.from_user.id}\n"
        f"💬 {message.text}"
    )

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("👤 پروفایل", callback_data=f"profile_{message.from_user.id}"),
        types.InlineKeyboardButton("🚫 بلاک", callback_data=f"block_{message.from_user.id}")
    )
    keyboard.add(
        types.InlineKeyboardButton("✅ آنبلاک", callback_data=f"unblock_{message.from_user.id}")
    )

    for admin in ADMINS:
        await bot.send_message(admin, text, reply_markup=keyboard)

    await message.answer("✅ ارسال شد")


# ---------------- ADMIN REPLY (REPLY METHOD) ----------------
@dp.message_handler(lambda m: m.from_user.id in ADMINS)
async def admin_reply(message: types.Message):

    if not message.reply_to_message:
        return

    text = message.reply_to_message.text

    if "🆔" not in text:
        return

    try:
        user_id = int(text.split("🆔 ")[1].split("\n")[0])

        await bot.send_message(
            user_id,
            f"📨 پاسخ ادمین:\n\n{message.text}",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("📩 ارسال پیام مجدد", callback_data="send_again")
            )
        )

        await message.reply("✅ ارسال شد")

    except:
        await message.reply("❌ خطا در ارسال")


# ---------------- CALLBACKS ----------------
@dp.callback_query_handler()
async def callback(call: types.CallbackQuery):

    data = call.data

    # profile
    if data.startswith("profile_"):
        user_id = int(data.split("_")[1])

        cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user = cursor.fetchone()

        if user:
            await call.message.answer(
                f"👤 پروفایل\n\n🆔 {user[0]}\nنام: {user[1]}\nیوزرنیم: @{user[2]}"
            )

    # block
    elif data.startswith("block_"):
        user_id = int(data.split("_")[1])

        cursor.execute("INSERT OR IGNORE INTO blocked VALUES (?)", (user_id,))
        conn.commit()

        await call.message.answer("⛔ بلاک شد")

    # unblock
    elif data.startswith("unblock_"):
        user_id = int(data.split("_")[1])

        cursor.execute("DELETE FROM blocked WHERE user_id=?", (user_id,))
        conn.commit()

        await call.message.answer("✅ آنبلاک شد")

    # send again
    elif data == "send_again":
        await call.message.answer("✍️ پیام جدیدت رو بنویس و ارسال کن")

    await call.answer()


# ---------------- RUN ----------------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
