import asyncio
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus

# --- CONFIGURATION ---
API_ID = 37197223
API_HASH = "3a43ae287a696ee9a6a82fb79f605b75"
BOT_TOKEN = "8746166399:AAGwGDxHkEiVidNfXARhIsK4QHUGg6YCyVg"

app = Client(
    "tempest_ban_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Ban process track karne ke liye dictionary
ban_process_active = {}

# --- HELPER FUNCTIONS ---
async def is_power(client, chat_id, user_id):
    """Checks if the user is an admin or owner."""
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        return False

async def extract_target_user(client, message):
    """Extracts user information from reply or command arguments."""
    if message.reply_to_message:
        return message.reply_to_message.from_user
    if len(message.command) > 1:
        user_info = message.command[1]
        try:
            return await client.get_users(user_info)
        except Exception:
            return None
    return None

# --- COMMANDS ---

# 1. Single Ban Command
@app.on_message(filters.group & filters.command("ban"))
async def ban_user(client, message):
    if not await is_power(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    user = await extract_target_user(client, message)
    if not user:
        return await message.reply_text("⚠️ Usage: Reply to someone or use `/ban @username` / ID")

    try:
        target_member = await client.get_chat_member(message.chat.id, user.id)
        if target_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply_text("⚠️ Cannot perform action on admins.")
    except Exception:
        pass # User might not be in chat cache
    
    if user.id == message.from_user.id:
        return await message.reply_text("⚠️ You cannot ban yourself.")

    try:
        await client.ban_chat_member(message.chat.id, user.id)
        await message.reply_text(f"🚨 {user.mention} has been banned.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to ban: {e}")

# 2. Ban All Members Command
@app.on_message(filters.group & filters.command("banall"))
async def ban_all_members(client, message):
    chat_id = message.chat.id
    
    if not await is_power(client, chat_id, message.from_user.id):
        return await message.reply_text("❌ Only admin can use this command.")

    # Mark process as active for this chat
    ban_process_active[chat_id] = True
    sent_msg = await message.reply_text("🔄 **Ban All process shuru ho gaya hai...**\nStop karne ke liye `/stopall` likhein.")

    count = 0
    me = await client.get_me()

    async for member in client.get_chat_members(chat_id):
        # Stop signal check: Agar user ne /stopall daba diya ho
        if not ban_process_active.get(chat_id):
            await message.reply_text(f"🛑 **Process manually rok diya gaya!**\nAb tak `{count}` members ban kiye gaye.")
            return

        # Skip Admins, Owners and the Bot itself
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            continue
        if member.user.id == me.id:
            continue

        try:
            await client.ban_chat_member(chat_id, member.user.id)
            count += 1
            # Rate limiting delay (0.2s is safe for mid-sized groups)
            await asyncio.sleep(0.2) 
        except Exception:
            # Skip errors (like FloodWait or hidden members)
            continue

    ban_process_active[chat_id] = False
    await sent_msg.edit(f"✅ **Task Completed!**\n🚨 Total Banned: `{count}`")

# 3. Stop All Process Command
@app.on_message(filters.group & filters.command("stopall"))
async def stop_ban(client, message):
    chat_id = message.chat.id
    
    if not await is_power(client, chat_id, message.from_user.id):
        return await message.reply_text("❌ Only admin can stop this.")

    if ban_process_active.get(chat_id):
        ban_process_active[chat_id] = False
        await message.reply_text("⌛ Stopping the ban process... Please wait.")
    else:
        await message.reply_text("⚠️ Koi active process nahi chal raha hai.")

# Run the Bot
if __name__ == "__main__":
    print("Bot is starting...")
    app.run()
