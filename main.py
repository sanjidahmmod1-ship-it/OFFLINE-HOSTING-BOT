import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot, BotCommand
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, ContextTypes, filters
)
from telegram.error import TelegramError
from config import BOT_TOKEN, ADMIN_ID
from database import (
    init_db, save_user, add_bot, get_bots, get_bot,
    stats, is_banned, set_ban, all_users
)
from security import encrypt_token, decrypt_token

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("offline-host-bot")

WAIT_TOKEN, WAIT_EDIT = range(2)

def home_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add New Bot", callback_data="add")],
        [InlineKeyboardButton("🤖 My Bots", callback_data="mybots"),
         InlineKeyboardButton("📖 Help", callback_data="help")]
    ])

def cancel_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="home")]])

async def allowed(update: Update) -> bool:
    user = update.effective_user
    if not user:
        return False
    save_user(user.id)
    if is_banned(user.id):
        if update.effective_message:
            await update.effective_message.reply_text("⛔ আপনার অ্যাকাউন্টটি নিষিদ্ধ করা হয়েছে।")
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await allowed(update):
        return
    await update.effective_message.reply_text(
        "🤖 স্বাগতম OFFLINE HOST BOT-এ!\n\n"
        "এখান থেকে আপনার Telegram Bot যুক্ত করে সেটিংস পরিচালনা করতে পারবেন।\n"
        "নতুন Bot তৈরি করতে আগে @BotFather থেকে Token নিন।",
        reply_markup=home_keyboard()
    )

async def newbot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await allowed(update):
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Open Official BotFather", url="https://t.me/BotFather")],
        [InlineKeyboardButton("➕ I Have a Token", callback_data="add")]
    ])
    await update.effective_message.reply_text(
        "📝 নতুন Telegram Bot তৈরির নিয়ম:\n"
        "১. @BotFather খুলুন\n"
        "২. /newbot পাঠান\n"
        "৩. Bot Name ও Username দিন\n"
        "৪. পাওয়া Token কপি করুন\n"
        "৫. নিচের I Have a Token চাপুন\n\n"
        "⚠️ Token কাউকে দেবেন না।",
        reply_markup=kb
    )

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if is_banned(query.from_user.id):
        await query.message.reply_text("⛔ আপনার অ্যাকাউন্ট নিষিদ্ধ।")
        return ConversationHandler.END
    await query.message.reply_text(
        "🔐 আপনার Bot Token পাঠান।\n\n"
        "Token যাচাই করে আপনার অ্যাকাউন্টে যুক্ত করা হবে।\n"
        "বাতিল করতে /cancel লিখুন।"
    )
    return WAIT_TOKEN

async def receive_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await allowed(update):
        return ConversationHandler.END
    token = (update.message.text or "").strip()
    if len(token) > 200 or ":" not in token:
        await update.message.reply_text("❌ Token format সঠিক মনে হচ্ছে না। আবার পাঠান অথবা /cancel দিন।")
        return WAIT_TOKEN
    try:
        async with Bot(token=token) as managed_bot:
            info = await managed_bot.get_me()
        encrypted = encrypt_token(token)
        added = add_bot(
            owner_id=update.effective_user.id,
            telegram_id=info.id,
            username=info.username or "",
            first_name=info.first_name or "",
            encrypted_token=encrypted
        )
        if not added:
            await update.message.reply_text(
                "⚠️ এই Bot ইতিমধ্যে আমাদের সিস্টেমে যুক্ত আছে।\n"
                "একটি Bot একবারই যুক্ত করা যাবে।",
                reply_markup=home_keyboard()
            )
            return ConversationHandler.END
        await update.message.reply_text(
            "✅ Bot সফলভাবে যুক্ত হয়েছে!\n\n"
            f"Name: {info.first_name}\n"
            f"Username: @{info.username}\n"
            f"Bot ID: {info.id}\n\n"
            "এখন My Bots থেকে সেটিংস পরিবর্তন করুন।",
            reply_markup=home_keyboard()
        )
    except TelegramError:
        logger.warning("Token validation failed for user %s", update.effective_user.id)
        await update.message.reply_text("❌ Token যাচাই করা যায়নি। Token ঠিক আছে কি না দেখুন। আবার পাঠান অথবা /cancel দিন।")
        return WAIT_TOKEN
    except Exception:
        logger.exception("Unexpected add-bot error")
        await update.message.reply_text("❌ একটি সমস্যা হয়েছে। পরে আবার চেষ্টা করুন।")
        return WAIT_TOKEN
    return ConversationHandler.END

async def mybots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if is_banned(query.from_user.id):
        return
    rows = get_bots(query.from_user.id)
    if not rows:
        await query.message.reply_text("আপনার কোনো Bot যুক্ত করা নেই। ➕ Add New Bot চাপুন।", reply_markup=home_keyboard())
        return
    buttons = [
        [InlineKeyboardButton(f"🤖 {name} (@{username})", callback_data=f"bot:{row_id}")]
        for row_id, username, name in rows
    ]
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="home")])
    await query.message.reply_text("📂 আপনার যুক্ত করা Bot:", reply_markup=InlineKeyboardMarkup(buttons))

async def bot_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        row_id = int(query.data.split(":")[1])
    except (ValueError, IndexError):
        return
    row = get_bot(row_id, query.from_user.id)
    if not row:
        await query.message.reply_text("❌ Bot পাওয়া যায়নি।")
        return
    _, telegram_id, username, name, _ = row
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Change Name", callback_data=f"edit:name:{row_id}")],
        [InlineKeyboardButton("📝 Change Description", callback_data=f"edit:description:{row_id}")],
        [InlineKeyboardButton("📖 Change About", callback_data=f"edit:about:{row_id}")],
        [InlineKeyboardButton("⚙️ Set Commands", callback_data=f"edit:commands:{row_id}")],
        [InlineKeyboardButton("ℹ️ Bot Information", callback_data=f"info:{row_id}")],
        [InlineKeyboardButton("🗑 Remove from this manager", callback_data=f"remove:{row_id}")],
        [InlineKeyboardButton("⬅️ My Bots", callback_data="mybots")]
    ])
    await query.message.reply_text(
        f"🤖 BOT SETTINGS\n\nName: {name}\nUsername: @{username}\nID: {telegram_id}",
        reply_markup=kb
    )

async def edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        _, action, row_id_text = query.data.split(":")
        row_id = int(row_id_text)
    except ValueError:
        return ConversationHandler.END
    if not get_bot(row_id, query.from_user.id):
        await query.message.reply_text("❌ Bot পাওয়া যায়নি।")
        return ConversationHandler.END
    context.user_data["edit_bot_id"] = row_id
    context.user_data["edit_action"] = action
    prompts = {
        "name": "নতুন Bot Name পাঠান (সর্বোচ্চ ৬৪ অক্ষর):",
        "description": "নতুন Description পাঠান (সর্বোচ্চ ৫১২ অক্ষর):",
        "about": "নতুন About Text পাঠান (সর্বোচ্চ ১২০ অক্ষর):",
        "commands": "প্রতি লাইনে একটি Command দিন। উদাহরণ:\nstart - Start the bot\nhelp - Show help"
    }
    await query.message.reply_text(prompts[action] + "\n\nবাতিল করতে /cancel দিন।")
    return WAIT_EDIT

async def save_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await allowed(update):
        return ConversationHandler.END
    row_id = context.user_data.get("edit_bot_id")
    action = context.user_data.get("edit_action")
    row = get_bot(row_id, update.effective_user.id) if row_id else None
    if not row:
        await update.message.reply_text("❌ Bot পাওয়া যায়নি।")
        return ConversationHandler.END
    value = (update.message.text or "").strip()
    limits = {"name": 64, "description": 512, "about": 120}
    if action in limits and len(value) > limits[action]:
        await update.message.reply_text(f"❌ Text সর্বোচ্চ {limits[action]} অক্ষর হতে পারবে। আবার পাঠান।")
        return WAIT_EDIT
    try:
        token = decrypt_token(row[4])
        async with Bot(token=token) as managed_bot:
            if action == "name":
                await managed_bot.set_my_name(name=value)
            elif action == "description":
                await managed_bot.set_my_description(description=value)
            elif action == "about":
                await managed_bot.set_my_short_description(short_description=value)
            elif action == "commands":
                commands = []
                for line in value.splitlines():
                    if " - " not in line:
                        continue
                    command, description = line.split(" - ", 1)
                    command = command.strip().lstrip("/")
                    description = description.strip()
                    if command and description and len(command) <= 32 and len(description) <= 256:
                        commands.append(BotCommand(command, description))
                if not commands:
                    await update.message.reply_text("❌ সঠিক Command পাওয়া যায়নি। উদাহরণ অনুযায়ী আবার পাঠান।")
                    return WAIT_EDIT
                await managed_bot.set_my_commands(commands)
        await update.message.reply_text("✅ Bot settings সফলভাবে আপডেট হয়েছে।", reply_markup=home_keyboard())
    except TelegramError:
        logger.exception("Telegram settings update failed")
        await update.message.reply_text("❌ Telegram API আপডেট গ্রহণ করেনি। ইনপুট যাচাই করে আবার চেষ্টা করুন।")
    except Exception:
        logger.exception("Settings update failed")
        await update.message.reply_text("❌ আপডেট করা যায়নি।")
    context.user_data.pop("edit_bot_id", None)
    context.user_data.pop("edit_action", None)
    return ConversationHandler.END

async def bot_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        row_id = int(query.data.split(":")[1])
    except (ValueError, IndexError):
        return
    row = get_bot(row_id, query.from_user.id)
    if not row:
        await query.message.reply_text("❌ Bot পাওয়া যায়নি।")
        return
    try:
        async with Bot(token=decrypt_token(row[4])) as managed_bot:
            info = await managed_bot.get_me()
            webhook = await managed_bot.get_webhook_info()
        await query.message.reply_text(
            f"ℹ️ BOT INFORMATION\n\nName: {info.first_name}\n"
            f"Username: @{info.username}\nID: {info.id}\n"
            f"Can Join Groups: {info.can_join_groups}\n"
            f"Webhook Active: {'Yes' if webhook.url else 'No'}"
        )
    except Exception:
        logger.exception("Bot info failed")
        await query.message.reply_text("❌ Bot information পাওয়া যায়নি।")

async def remove_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        row_id = int(query.data.split(":")[1])
    except (ValueError, IndexError):
        return
    from database import delete_bot
    if delete_bot(row_id, query.from_user.id):
        await query.message.reply_text("✅ Bot শুধু OFFLINE HOST BOT-এর তালিকা থেকে সরানো হয়েছে। আসল Telegram Bot ডিলিট হয়নি।", reply_markup=home_keyboard())
    else:
        await query.message.reply_text("❌ Bot সরানো যায়নি।")

async def home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🏠 Main Menu", reply_markup=home_keyboard())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "📖 Help\n\n/newbot - নতুন Bot তৈরির নির্দেশনা\n"
        "/start - Main Menu\n/cancel - চলমান কাজ বাতিল\n\n"
        "Token নিতে @BotFather ব্যবহার করুন।",
        reply_markup=home_keyboard()
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("edit_bot_id", None)
    context.user_data.pop("edit_action", None)
    await update.effective_message.reply_text("❌ কাজ বাতিল হয়েছে।", reply_markup=home_keyboard())
    return ConversationHandler.END

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    users, bots = stats()
    await update.message.reply_text(
        f"👑 OFFLINE HOST BOT ADMIN\n\nTotal Users: {users}\nTotal Bots: {bots}\n\n"
        "/ban USER_ID\n/unban USER_ID\n/broadcast আপনার মেসেজ"
    )

async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("ব্যবহার: /ban USER_ID")
        return
    set_ban(int(context.args[0]), True)
    await update.message.reply_text("✅ User banned.")

async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("ব্যবহার: /unban USER_ID")
        return
    set_ban(int(context.args[0]), False)
    await update.message.reply_text("✅ User unbanned.")

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("ব্যবহার: /broadcast MESSAGE")
        return
    message = " ".join(context.args)
    sent = 0
    for uid in all_users():
        try:
            await context.bot.send_message(uid, message)
            sent += 1
        except TelegramError:
            logger.info("Broadcast could not reach user %s", uid)
    await update.message.reply_text(f"📢 Broadcast শেষ। পাঠানো হয়েছে: {sent}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Unhandled exception: %s", context.error)

def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conversation = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_start, pattern=r"^add$"),
            CallbackQueryHandler(edit_start, pattern=r"^edit:(name|description|about|commands):\d+$")
        ],
        states={
            WAIT_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_token)],
            WAIT_EDIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_edit)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newbot", newbot_command))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(conversation)
    app.add_handler(CallbackQueryHandler(mybots, pattern=r"^mybots$"))
    app.add_handler(CallbackQueryHandler(bot_details, pattern=r"^bot:\d+$"))
    app.add_handler(CallbackQueryHandler(bot_info, pattern=r"^info:\d+$"))
    app.add_handler(CallbackQueryHandler(remove_bot, pattern=r"^remove:\d+$"))
    app.add_handler(CallbackQueryHandler(help_cmd, pattern=r"^help$"))
    app.add_handler(CallbackQueryHandler(home, pattern=r"^home$"))
    app.add_error_handler(error_handler)

    logger.info("OFFLINE HOST BOT is starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
