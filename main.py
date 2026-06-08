"""
টেলিগ্রাম রোজ বট - Python
Bot Token: 8646107305:AAE-BAzeCvmT5-kZwlAwYgfL9xjwHIh61fc
Admin ID: 8709449192
Channel: https://t.me/+rVFJ134jGbEyOTRl
Channel ID: -1003512383446
"""

import logging
import json
import os
import re
import time
from datetime import datetime
from functools import wraps

from telegram import (
    Update,
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    filters,
    ContextTypes,
)
from telegram.error import TelegramError

# ─────────────────── CONFIG ────────────────────
BOT_TOKEN   = "8778653130:AAET-V8qti39v_pcAFsgQ7eqJMafyhzFWxs"
ADMIN_ID    = 8528931469
CHANNEL_ID  = -1003512383446
CHANNEL_URL = "https://t.me/+rVFJ134jGbEyOTRl"

DATA_FILE   = "bot_data.json"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─────────────────── DATA STORE ────────────────
def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "warns": {},       # chat_id -> {user_id: count}
        "notes": {},       # chat_id -> {name: text}
        "filters": {},     # chat_id -> {keyword: reply}
        "welcome": {},     # chat_id -> text
        "goodbye": {},     # chat_id -> text
        "locked": {},      # chat_id -> [lock_types]
        "muted": {},       # chat_id -> {user_id: until}
        "rules": {},       # chat_id -> text
        "blacklist": {},   # chat_id -> [words]
        "joined_users": [],# user_ids who joined channel
    }

def save_data(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

DATA = load_data()

# ─────────────────── HELPERS ───────────────────

async def is_channel_member(bot, user_id: int) -> bool:
    """Check if user is in the required channel."""
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ("member", "administrator", "creator")
    except TelegramError:
        return False

def require_channel(func):
    """Decorator: বট শুধু চেলেন মেম্বারদের কাজ করবে।"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if user is None:
            return
        if not await is_channel_member(context.bot, user.id):
            keyboard = [[InlineKeyboardButton("📢 চেলেনে জয়েন করুন", url=CHANNEL_URL)]]
            await update.effective_message.reply_text(
                "⚠️ বট ব্যবহার করতে আগে আমাদের চেলেনে জয়েন করুন!\n"
                f"👉 {CHANNEL_URL}\n\n"
                "জয়েন করার পরে আবার চেষ্টা করুন।",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return
        return await func(update, context)
    return wrapper

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int = None) -> bool:
    chat = update.effective_chat
    uid  = user_id or update.effective_user.id
    if chat.type == "private":
        return True
    try:
        member = await context.bot.get_chat_member(chat.id, uid)
        return member.status in ("administrator", "creator")
    except TelegramError:
        return False

def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await is_admin(update, context):
            await update.effective_message.reply_text("❌ শুধুমাত্র অ্যাডমিনরা এই কমান্ড ব্যবহার করতে পারবেন।")
            return
        return await func(update, context)
    return wrapper

def get_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reply বা args থেকে টার্গেট ইউজার বের করে।"""
    msg = update.effective_message
    if msg.reply_to_message:
        return msg.reply_to_message.from_user
    if context.args:
        try:
            return type("User", (), {"id": int(context.args[0]), "mention_html": lambda s: context.args[0]})()
        except (ValueError, IndexError):
            pass
    return None

def cid(chat_id) -> str:
    return str(chat_id)

def uid(user_id) -> str:
    return str(user_id)

# ─────────────────── /start ────────────────────
@require_channel
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"🌹 *হ্যালো {user.first_name}!*\n\n"
        "আমি একটি শক্তিশালী গ্রুপ ম্যানেজমেন্ট বট।\n"
        "রোজ বটের মতো সব ফিচার আমার কাছে আছে!\n\n"
        "📌 `/help` দিন সব কমান্ড দেখতে।"
    )
    keyboard = [
        [InlineKeyboardButton("📢 চেলেন", url=CHANNEL_URL),
         InlineKeyboardButton("❓ সাহায্য", callback_data="help_main")],
    ]
    await update.message.reply_text(text, parse_mode="Markdown",
                                    reply_markup=InlineKeyboardMarkup(keyboard))

# ─────────────────── /help ─────────────────────
HELP_TEXT = """
🌹 *রোজ বট — সকল কমান্ড*

━━━━━━━━━━━━━━━━━━
👮 *অ্যাডমিন কমান্ড*
━━━━━━━━━━━━━━━━━━
🔇 `/mute [reply/id] [সময়m/h/d]` — ইউজার মিউট
🔊 `/unmute [reply/id]` — মিউট তুলুন
🚫 `/ban [reply/id]` — ইউজার ব্যান
✅ `/unban [reply/id]` — ব্যান তুলুন
👢 `/kick [reply/id]` — ইউজার কিক
⚠️ `/warn [reply/id] [কারণ]` — সতর্কতা দিন
🗑️ `/unwarn [reply/id]` — সতর্কতা তুলুন
📋 `/warns [reply/id]` — সতর্কতা দেখুন
📌 `/pin` — মেসেজ পিন করুন
📌 `/unpin` — পিন তুলুন

━━━━━━━━━━━━━━━━━━
📝 *নোট ও ফিল্টার*
━━━━━━━━━━━━━━━━━━
📒 `/save [নাম] [টেক্সট]` — নোট সেভ
📖 `/get [নাম]` বা `#নাম` — নোট দেখুন
🗒️ `/notes` — সব নোট
🗑️ `/clear [নাম]` — নোট মুছুন
🔍 `/filter [শব্দ] [রিপ্লাই]` — ফিল্টার সেট
❌ `/stop [শব্দ]` — ফিল্টার বন্ধ
📋 `/filters` — সব ফিল্টার

━━━━━━━━━━━━━━━━━━
👋 *স্বাগত ও বিদায়*
━━━━━━━━━━━━━━━━━━
🙋 `/setwelcome [টেক্সট]` — স্বাগত বার্তা সেট
👋 `/setgoodbye [টেক্সট]` — বিদায় বার্তা সেট
🗑️ `/resetwelcome` — স্বাগত রিসেট
🗑️ `/resetgoodbye` — বিদায় রিসেট

━━━━━━━━━━━━━━━━━━
📜 *নিয়মকানুন*
━━━━━━━━━━━━━━━━━━
📜 `/setrules [টেক্সট]` — নিয়ম সেট করুন
📖 `/rules` — নিয়ম দেখুন
🗑️ `/clearrules` — নিয়ম মুছুন

━━━━━━━━━━━━━━━━━━
🚫 *ব্ল্যাকলিস্ট*
━━━━━━━━━━━━━━━━━━
➕ `/addblacklist [শব্দ]` — শব্দ ব্লক করুন
➖ `/rmblacklist [শব্দ]` — ব্লক তুলুন
📋 `/blacklist` — ব্লক শব্দ দেখুন

━━━━━━━━━━━━━━━━━━
ℹ️ *তথ্য*
━━━━━━━━━━━━━━━━━━
👤 `/id` — আইডি দেখুন
ℹ️ `/info [reply/id]` — ইউজার তথ্য
📊 `/chatinfo` — গ্রুপ তথ্য
🕐 `/time` — বর্তমান সময়

━━━━━━━━━━━━━━━━━━
🤖 *অন্যান্য*
━━━━━━━━━━━━━━━━━━
🏓 `/ping` — বট চলছে কিনা দেখুন
📢 `/broadcast [টেক্সট]` — (শুধু মালিক)
"""

@require_channel
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(HELP_TEXT, parse_mode="Markdown")

# ─────────────────── BAN / UNBAN / KICK ────────
@require_channel
@admin_only
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = get_target_user(update, context)
    if not target:
        await update.message.reply_text("❌ রিপ্লাই করুন অথবা ইউজার আইডি দিন।")
        return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(f"🚫 ইউজার ব্যান করা হয়েছে।\nID: `{target.id}`", parse_mode="Markdown")
    except TelegramError as e:
        await update.message.reply_text(f"❌ ব্যান করা যায়নি: {e}")

@require_channel
@admin_only
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = get_target_user(update, context)
    if not target:
        await update.message.reply_text("❌ রিপ্লাই করুন অথবা ইউজার আইডি দিন।")
        return
    try:
        await context.bot.unban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(f"✅ ইউজার আনব্যান হয়েছে।\nID: `{target.id}`", parse_mode="Markdown")
    except TelegramError as e:
        await update.message.reply_text(f"❌ আনব্যান করা যায়নি: {e}")

@require_channel
@admin_only
async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = get_target_user(update, context)
    if not target:
        await update.message.reply_text("❌ রিপ্লাই করুন।")
        return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await context.bot.unban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(f"👢 ইউজার কিক করা হয়েছে।\nID: `{target.id}`", parse_mode="Markdown")
    except TelegramError as e:
        await update.message.reply_text(f"❌ কিক করা যায়নি: {e}")

# ─────────────────── MUTE / UNMUTE ─────────────
def parse_duration(arg: str) -> int:
    """Returns seconds from e.g. 10m, 2h, 1d"""
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    match = re.match(r"(\d+)([smhd]?)", arg.lower())
    if match:
        val, unit = match.groups()
        return int(val) * units.get(unit, 60)
    return 0

@require_channel
@admin_only
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = get_target_user(update, context)
    if not target:
        await update.message.reply_text("❌ রিপ্লাই করুন।")
        return
    duration = 0
    if context.args:
        last = context.args[-1]
        duration = parse_duration(last)
    until = int(time.time()) + duration if duration else 0
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id, target.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until if until else None,
        )
        dur_text = f"{context.args[-1]}" if duration and context.args else "স্থায়ী"
        await update.message.reply_text(
            f"🔇 ইউজার মিউট হয়েছে।\nID: `{target.id}`\nসময়: {dur_text}", parse_mode="Markdown"
        )
    except TelegramError as e:
        await update.message.reply_text(f"❌ মিউট করা যায়নি: {e}")

@require_channel
@admin_only
async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = get_target_user(update, context)
    if not target:
        await update.message.reply_text("❌ রিপ্লাই করুন।")
        return
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id, target.id,
            permissions=ChatPermissions(
                can_send_messages=True, can_send_media_messages=True,
                can_send_other_messages=True, can_add_web_page_previews=True,
            ),
        )
        await update.message.reply_text(f"🔊 ইউজার আনমিউট হয়েছে।\nID: `{target.id}`", parse_mode="Markdown")
    except TelegramError as e:
        await update.message.reply_text(f"❌ আনমিউট করা যায়নি: {e}")

# ─────────────────── WARN ──────────────────────
MAX_WARNS = 3

@require_channel
@admin_only
async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = get_target_user(update, context)
    if not target:
        await update.message.reply_text("❌ রিপ্লাই করুন।")
        return
    chat_id = cid(update.effective_chat.id)
    user_id = uid(target.id)
    DATA["warns"].setdefault(chat_id, {})
    DATA["warns"][chat_id][user_id] = DATA["warns"][chat_id].get(user_id, 0) + 1
    count = DATA["warns"][chat_id][user_id]
    save_data(DATA)
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "কোনো কারণ নেই"
    if count >= MAX_WARNS:
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, target.id)
            DATA["warns"][chat_id][user_id] = 0
            save_data(DATA)
            await update.message.reply_text(
                f"⚠️ {MAX_WARNS}/{MAX_WARNS} সতর্কতা পূর্ণ!\n🚫 ইউজার ব্যান হয়েছে।", parse_mode="Markdown"
            )
        except TelegramError as e:
            await update.message.reply_text(f"❌ ব্যান ব্যর্থ: {e}")
    else:
        await update.message.reply_text(
            f"⚠️ সতর্কতা দেওয়া হয়েছে! ({count}/{MAX_WARNS})\nকারণ: {reason}", parse_mode="Markdown"
        )

@require_channel
@admin_only
async def unwarn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = get_target_user(update, context)
    if not target:
        await update.message.reply_text("❌ রিপ্লাই করুন।")
        return
    chat_id = cid(update.effective_chat.id)
    user_id = uid(target.id)
    warns = DATA["warns"].get(chat_id, {})
    if warns.get(user_id, 0) > 0:
        warns[user_id] -= 1
        DATA["warns"][chat_id] = warns
        save_data(DATA)
        await update.message.reply_text(f"✅ ১টি সতর্কতা কমানো হয়েছে।\nএখন: {warns[user_id]}/{MAX_WARNS}")
    else:
        await update.message.reply_text("ℹ️ কোনো সতর্কতা নেই।")

@require_channel
async def warns_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = get_target_user(update, context) or update.effective_user
    chat_id = cid(update.effective_chat.id)
    user_id = uid(target.id)
    count = DATA["warns"].get(chat_id, {}).get(user_id, 0)
    await update.message.reply_text(f"📋 সতর্কতা: {count}/{MAX_WARNS}\nID: `{target.id}`", parse_mode="Markdown")

# ─────────────────── NOTES ─────────────────────
@require_channel
@admin_only
async def save_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ ব্যবহার: `/save নাম টেক্সট`", parse_mode="Markdown")
        return
    chat_id = cid(update.effective_chat.id)
    name = context.args[0].lower()
    text = " ".join(context.args[1:])
    DATA["notes"].setdefault(chat_id, {})[name] = text
    save_data(DATA)
    await update.message.reply_text(f"📒 নোট `{name}` সেভ হয়েছে!", parse_mode="Markdown")

@require_channel
async def get_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ ব্যবহার: `/get নাম`", parse_mode="Markdown")
        return
    chat_id = cid(update.effective_chat.id)
    name = context.args[0].lower()
    note = DATA["notes"].get(chat_id, {}).get(name)
    if note:
        await update.message.reply_text(f"📖 *{name}*\n{note}", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ `{name}` নামে কোনো নোট নেই।", parse_mode="Markdown")

@require_channel
async def list_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = cid(update.effective_chat.id)
    notes = DATA["notes"].get(chat_id, {})
    if notes:
        text = "📒 *সব নোট:*\n" + "\n".join(f"• `{k}`" for k in notes)
    else:
        text = "❌ কোনো নোট নেই।"
    await update.message.reply_text(text, parse_mode="Markdown")

@require_channel
@admin_only
async def clear_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ ব্যবহার: `/clear নাম`", parse_mode="Markdown")
        return
    chat_id = cid(update.effective_chat.id)
    name = context.args[0].lower()
    if name in DATA["notes"].get(chat_id, {}):
        del DATA["notes"][chat_id][name]
        save_data(DATA)
        await update.message.reply_text(f"🗑️ নোট `{name}` মুছে গেছে।", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ নোট পাওয়া যায়নি।")

async def hashtag_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """#নাম দিলে নোট দেখাবে।"""
    msg = update.message
    if not msg or not msg.text:
        return
    chat_id = cid(update.effective_chat.id)
    for word in msg.text.split():
        if word.startswith("#"):
            name = word[1:].lower()
            note = DATA["notes"].get(chat_id, {}).get(name)
            if note:
                await msg.reply_text(f"📖 *{name}*\n{note}", parse_mode="Markdown")

# ─────────────────── FILTERS ───────────────────
@require_channel
@admin_only
async def add_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if len(context.args) < 2 and not msg.reply_to_message:
        await msg.reply_text("❌ ব্যবহার: `/filter শব্দ রিপ্লাই` অথবা রিপ্লাই করুন।", parse_mode="Markdown")
        return
    chat_id = cid(update.effective_chat.id)
    keyword = context.args[0].lower() if context.args else ""
    if msg.reply_to_message:
        reply_text = msg.reply_to_message.text or ""
    else:
        reply_text = " ".join(context.args[1:])
    if not keyword or not reply_text:
        await msg.reply_text("❌ কীওয়ার্ড ও রিপ্লাই দরকার।")
        return
    DATA["filters"].setdefault(chat_id, {})[keyword] = reply_text
    save_data(DATA)
    await msg.reply_text(f"🔍 ফিল্টার `{keyword}` সেট হয়েছে!", parse_mode="Markdown")

@require_channel
@admin_only
async def stop_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ ব্যবহার: `/stop শব্দ`", parse_mode="Markdown")
        return
    chat_id = cid(update.effective_chat.id)
    keyword = context.args[0].lower()
    if keyword in DATA["filters"].get(chat_id, {}):
        del DATA["filters"][chat_id][keyword]
        save_data(DATA)
        await update.message.reply_text(f"❌ ফিল্টার `{keyword}` বন্ধ হয়েছে।", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ ফিল্টার পাওয়া যায়নি।")

@require_channel
async def list_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = cid(update.effective_chat.id)
    filts = DATA["filters"].get(chat_id, {})
    if filts:
        text = "🔍 *সব ফিল্টার:*\n" + "\n".join(f"• `{k}`" for k in filts)
    else:
        text = "❌ কোনো ফিল্টার নেই।"
    await update.message.reply_text(text, parse_mode="Markdown")

async def check_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return
    chat_id = cid(update.effective_chat.id)
    text_lower = msg.text.lower()
    for keyword, reply in DATA["filters"].get(chat_id, {}).items():
        if keyword in text_lower:
            await msg.reply_text(reply)
            break

# ─────────────────── WELCOME / GOODBYE ─────────
@require_channel
@admin_only
async def set_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ ব্যবহার: `/setwelcome টেক্সট`\n\n"
            "ভেরিয়েবল: `{first}` `{last}` `{username}` `{id}` `{chatname}`",
            parse_mode="Markdown"
        )
        return
    chat_id = cid(update.effective_chat.id)
    text = " ".join(context.args)
    DATA["welcome"][chat_id] = text
    save_data(DATA)
    await update.message.reply_text("✅ স্বাগত বার্তা সেট হয়েছে!")

@require_channel
@admin_only
async def set_goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ ব্যবহার: `/setgoodbye টেক্সট`", parse_mode="Markdown")
        return
    chat_id = cid(update.effective_chat.id)
    text = " ".join(context.args)
    DATA["goodbye"][chat_id] = text
    save_data(DATA)
    await update.message.reply_text("✅ বিদায় বার্তা সেট হয়েছে!")

@require_channel
@admin_only
async def reset_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    DATA["welcome"].pop(cid(update.effective_chat.id), None)
    save_data(DATA)
    await update.message.reply_text("🗑️ স্বাগত বার্তা রিসেট হয়েছে।")

@require_channel
@admin_only
async def reset_goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    DATA["goodbye"].pop(cid(update.effective_chat.id), None)
    save_data(DATA)
    await update.message.reply_text("🗑️ বিদায় বার্তা রিসেট হয়েছে।")

def format_welcome(text: str, user, chat) -> str:
    return (
        text
        .replace("{first}", user.first_name or "")
        .replace("{last}", user.last_name or "")
        .replace("{username}", f"@{user.username}" if user.username else user.first_name)
        .replace("{id}", str(user.id))
        .replace("{chatname}", chat.title or "")
    )

async def member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    if not result:
        return
    chat   = result.chat
    member = result.new_chat_member
    old    = result.old_chat_member
    chat_id = cid(chat.id)

    # নতুন সদস্য
    if old.status in ("left", "kicked") and member.status == "member":
        user = member.user
        welcome_text = DATA["welcome"].get(chat_id)
        if welcome_text:
            text = format_welcome(welcome_text, user, chat)
        else:
            text = (
                f"👋 *স্বাগতম {user.first_name}!*\n"
                f"🌹 {chat.title} গ্রুপে আপনাকে স্বাগত জানাই!\n"
                f"📜 `/rules` দিয়ে নিয়ম পড়ুন।"
            )
        await context.bot.send_message(chat.id, text, parse_mode="Markdown")

    # চলে যাওয়া সদস্য
    elif member.status in ("left", "kicked") and old.status == "member":
        user = member.user
        goodbye_text = DATA["goodbye"].get(chat_id)
        if goodbye_text:
            text = format_welcome(goodbye_text, user, chat)
        else:
            text = f"👋 *{user.first_name}* চলে গেলেন। আবার আসবেন!"
        await context.bot.send_message(chat.id, text, parse_mode="Markdown")

# ─────────────────── RULES ─────────────────────
@require_channel
@admin_only
async def set_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ ব্যবহার: `/setrules টেক্সট`", parse_mode="Markdown")
        return
    chat_id = cid(update.effective_chat.id)
    DATA["rules"][chat_id] = " ".join(context.args)
    save_data(DATA)
    await update.message.reply_text("✅ নিয়ম সেট হয়েছে!")

@require_channel
async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = cid(update.effective_chat.id)
    r = DATA["rules"].get(chat_id)
    if r:
        await update.message.reply_text(f"📜 *গ্রুপের নিয়ম:*\n\n{r}", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ কোনো নিয়ম সেট করা হয়নি।")

@require_channel
@admin_only
async def clear_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    DATA["rules"].pop(cid(update.effective_chat.id), None)
    save_data(DATA)
    await update.message.reply_text("🗑️ নিয়ম মুছে গেছে।")

# ─────────────────── BLACKLIST ─────────────────
@require_channel
@admin_only
async def add_blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ ব্যবহার: `/addblacklist শব্দ`", parse_mode="Markdown")
        return
    chat_id = cid(update.effective_chat.id)
    word = " ".join(context.args).lower()
    DATA["blacklist"].setdefault(chat_id, [])
    if word not in DATA["blacklist"][chat_id]:
        DATA["blacklist"][chat_id].append(word)
        save_data(DATA)
        await update.message.reply_text(f"🚫 `{word}` ব্ল্যাকলিস্টে যোগ হয়েছে।", parse_mode="Markdown")
    else:
        await update.message.reply_text("ℹ️ শব্দটি ইতিমধ্যে তালিকায় আছে।")

@require_channel
@admin_only
async def rm_blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ ব্যবহার: `/rmblacklist শব্দ`", parse_mode="Markdown")
        return
    chat_id = cid(update.effective_chat.id)
    word = " ".join(context.args).lower()
    bl = DATA["blacklist"].get(chat_id, [])
    if word in bl:
        bl.remove(word)
        DATA["blacklist"][chat_id] = bl
        save_data(DATA)
        await update.message.reply_text(f"✅ `{word}` তালিকা থেকে সরানো হয়েছে।", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ শব্দটি তালিকায় নেই।")

@require_channel
async def show_blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = cid(update.effective_chat.id)
    bl = DATA["blacklist"].get(chat_id, [])
    if bl:
        text = "🚫 *ব্ল্যাকলিস্ট:*\n" + "\n".join(f"• `{w}`" for w in bl)
    else:
        text = "❌ কোনো ব্ল্যাকলিস্ট নেই।"
    await update.message.reply_text(text, parse_mode="Markdown")

async def check_blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return
    chat = update.effective_chat
    user = update.effective_user
    if await is_admin(update, context, user.id):
        return
    chat_id = cid(chat.id)
    text_lower = msg.text.lower()
    for word in DATA["blacklist"].get(chat_id, []):
        if word in text_lower:
            try:
                await msg.delete()
                await context.bot.send_message(
                    chat.id,
                    f"⚠️ {user.first_name}, ব্ল্যাকলিস্টেড শব্দ ব্যবহার করা যাবে না!"
                )
            except TelegramError:
                pass
            break

# ─────────────────── PIN ───────────────────────
@require_channel
@admin_only
async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg.reply_to_message:
        await msg.reply_text("❌ পিন করতে মেসেজে রিপ্লাই করুন।")
        return
    try:
        await context.bot.pin_chat_message(msg.chat.id, msg.reply_to_message.message_id)
        await msg.reply_text("📌 মেসেজ পিন করা হয়েছে!")
    except TelegramError as e:
        await msg.reply_text(f"❌ পিন করা যায়নি: {e}")

@require_channel
@admin_only
async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.unpin_chat_message(update.effective_chat.id)
        await update.message.reply_text("📌 পিন তোলা হয়েছে!")
    except TelegramError as e:
        await update.message.reply_text(f"❌ পিন তোলা যায়নি: {e}")

# ─────────────────── INFO COMMANDS ─────────────
@require_channel
async def user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if msg.reply_to_message:
        user = msg.reply_to_message.from_user
    else:
        user = update.effective_user
    await msg.reply_text(f"👤 *ইউজার আইডি:* `{user.id}`\n📛 নাম: {user.first_name}", parse_mode="Markdown")

@require_channel
async def user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if msg.reply_to_message:
        user = msg.reply_to_message.from_user
    else:
        user = update.effective_user
    chat_id = cid(update.effective_chat.id)
    warns_count = DATA["warns"].get(chat_id, {}).get(uid(user.id), 0)
    text = (
        f"ℹ️ *ইউজার তথ্য*\n\n"
        f"📛 নাম: {user.full_name}\n"
        f"🆔 আইডি: `{user.id}`\n"
        f"👤 ইউজারনেম: {'@' + user.username if user.username else 'নেই'}\n"
        f"⚠️ সতর্কতা: {warns_count}/{MAX_WARNS}\n"
        f"🤖 বট: {'হ্যাঁ' if user.is_bot else 'না'}"
    )
    await msg.reply_text(text, parse_mode="Markdown")

@require_channel
async def chat_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    try:
        count = await context.bot.get_chat_member_count(chat.id)
    except Exception:
        count = "?"
    text = (
        f"📊 *গ্রুপ তথ্য*\n\n"
        f"📛 নাম: {chat.title}\n"
        f"🆔 আইডি: `{chat.id}`\n"
        f"👥 সদস্য: {count}\n"
        f"📌 ধরন: {chat.type}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

@require_channel
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start = time.time()
    msg = await update.message.reply_text("🏓 পিং করছি...")
    elapsed = round((time.time() - start) * 1000)
    await msg.edit_text(f"🏓 পং! `{elapsed}ms`", parse_mode="Markdown")

@require_channel
async def time_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await update.message.reply_text(f"🕐 বর্তমান সময়: `{now}`", parse_mode="Markdown")

# ─────────────────── BROADCAST ─────────────────
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ শুধুমাত্র বট মালিক এই কমান্ড ব্যবহার করতে পারবেন।")
        return
    if not context.args:
        await update.message.reply_text("❌ ব্যবহার: `/broadcast বার্তা`", parse_mode="Markdown")
        return
    text = " ".join(context.args)
    await update.message.reply_text(f"📢 ব্রডকাস্ট পাঠানো হচ্ছে...\n\n{text}")

# ─────────────────── UNKNOWN ───────────────────
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ অজানা কমান্ড। `/help` দিন সব কমান্ড দেখতে।", parse_mode="Markdown"
    )

# ─────────────────── MAIN ──────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start",        start))
    app.add_handler(CommandHandler("help",         help_cmd))
    app.add_handler(CommandHandler("ban",          ban))
    app.add_handler(CommandHandler("unban",        unban))
    app.add_handler(CommandHandler("kick",         kick))
    app.add_handler(CommandHandler("mute",         mute))
    app.add_handler(CommandHandler("unmute",       unmute))
    app.add_handler(CommandHandler("warn",         warn))
    app.add_handler(CommandHandler("unwarn",       unwarn))
    app.add_handler(CommandHandler("warns",        warns_cmd))
    app.add_handler(CommandHandler("save",         save_note))
    app.add_handler(CommandHandler("get",          get_note))
    app.add_handler(CommandHandler("notes",        list_notes))
    app.add_handler(CommandHandler("clear",        clear_note))
    app.add_handler(CommandHandler("filter",       add_filter))
    app.add_handler(CommandHandler("stop",         stop_filter))
    app.add_handler(CommandHandler("filters",      list_filters))
    app.add_handler(CommandHandler("setwelcome",   set_welcome))
    app.add_handler(CommandHandler("setgoodbye",   set_goodbye))
    app.add_handler(CommandHandler("resetwelcome", reset_welcome))
    app.add_handler(CommandHandler("resetgoodbye", reset_goodbye))
    app.add_handler(CommandHandler("setrules",     set_rules))
    app.add_handler(CommandHandler("rules",        rules))
    app.add_handler(CommandHandler("clearrules",   clear_rules))
    app.add_handler(CommandHandler("addblacklist", add_blacklist))
    app.add_handler(CommandHandler("rmblacklist",  rm_blacklist))
    app.add_handler(CommandHandler("blacklist",    show_blacklist))
    app.add_handler(CommandHandler("pin",          pin))
    app.add_handler(CommandHandler("unpin",        unpin))
    app.add_handler(CommandHandler("id",           user_id))
    app.add_handler(CommandHandler("info",         user_info))
    app.add_handler(CommandHandler("chatinfo",     chat_info))
    app.add_handler(CommandHandler("ping",         ping))
    app.add_handler(CommandHandler("time",         time_cmd))
    app.add_handler(CommandHandler("broadcast",    broadcast))

    # Message handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_filters))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, hashtag_note))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_blacklist))

    # Member updates (welcome/goodbye)
    app.add_handler(ChatMemberHandler(member_update, ChatMemberHandler.CHAT_MEMBER))

    # Callback
    app.add_handler(CallbackQueryHandler(help_callback, pattern="^help_main$"))

    # Unknown
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    logger.info("🌹 রোজ বট চালু হয়েছে!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
