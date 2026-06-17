import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

TOKEN = "8792479401:AAEhv0Frjs-Vl-P2UYy1yGCMpFclKDpoKjk"
ADMIN_ID = 8173198254

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
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    text TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS blocked (
    user_id INTEGER PRIMARY KEY
)
""")

conn.commit()


# ---------------- HELPERS ----------------
def is_blocked(user_id):
    cursor.execute("SELECT user_id FROM blocked WHERE user_id=?", (user_id,))
    return cursor.fetchone() is not None


def add_user(user):
    cursor.execute("""
    INSERT OR REPLACE INTO users (user_id, name, username)
    VALUES (?, ?, ?)
    """, (user.id, user.full_name, user.username))
    conn.commit()


def save_message(user_id, text):
    cursor.execute("INSERT INTO messages (user_id, text) VALUES (?, ?)", (user_id, text))
    conn.commit()


# ---------------- START ----------------
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    add_user(message.from_user)

    if message.from_user.id == ADMIN_ID:
        await message.answer("👑 پنل ادمین فعال شد")
    else:
        await message.answer("👋 سلام! پیام بده")


# ---------------- پیام کاربران ----------------
@dp.message_handler()
async def handle(message: types.Message):

    user = message.from_user

    if is_blocked(user.id):
        await message.answer("⛔ شما بلاک هستید")
        return

    add_user(user)
    save_message(user.id, message.text)

    text = (
        f"📩 پیام جدید\n\n"
        f"👤 {user.full_name}\n"
        f"🆔 {user.id}\n"
        f"💬 {message.text}"
    )

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton("👤 پروفایل", callback_data=f"profile_{user.id}"),
        types.InlineKeyboardButton("🚫 بلاک", callback_data=f"block_{user.id}")
    )

    await bot.send_message(ADMIN_ID, text, reply_markup=keyboard)
    await message.answer("✅ ارسال شد")


# ---------------- CALLBACKS ----------------
@dp.callback_query_handler()
async def cb(call: types.CallbackQuery):

    data = call.data

    # 👤 پروفایل
    if data.startswith("profile_"):
        user_id = int(data.split("_")[1])

        cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user = cursor.fetchone()

        if user:
            await call.message.answer(
                f"👤 پروفایل\n\n"
                f"🆔 {user[0]}\n"
                f"نام: {user[1]}\n"
                f"یوزرنیم: @{user[2]}"
            )

    # 🚫 بلاک
    elif data.startswith("block_"):
        user_id = int(data.split("_")[1])

        cursor.execute("INSERT OR IGNORE INTO blocked (user_id) VALUES (?)", (user_id,))
        conn.commit()

        await call.message.answer(f"⛔ کاربر {user_id} بلاک شد")

    await call.answer()


# ---------------- اجرا ----------------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)