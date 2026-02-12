import os
import re
import asyncio
import logging
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pyromod import listen

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
@app.route('/')
def home(): return "Manual Interactive Bot is Live!"

def run_flask(): app.run(host='0.0.0.0', port=8080)

# Credentials
API_ID = 37197223
API_HASH = "3a43ae287a696ee9a6a82fb79f605b75"
BOT_TOKEN = "8416317246:AAF7M6ampaP5u0yOcjD-lWiXyMWsbTohpB4"
DB_CHANNEL = -1003702250649

bot = Client("RenameBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start") & filters.private)
async def start(c, m):
    await m.reply_text(f"Swagat hai Rimiru! 👋\n\nAb main har file ke liye aapse details poochunga. Files forward kijiye.")

@bot.on_message(filters.private & (filters.video | filters.document))
async def manual_handler(c, m):
    file = m.video or m.document
    original_name = file.file_name or "Unknown File"
    
    # 1. Prompt for every single file
    prompt = await m.reply_text(
        f"📂 **File Detected:** `{original_name}`\n\n"
        "Kripya details bhejiye (Order maintain karne ke liye):\n"
        "Format: `Name | Season | Episode | Quality | Audio`"
    )
    
    try:
        # User reply ka wait (Bot yahan ruk jayega)
        user_reply = await c.listen(m.chat.id)
        
        if "|" not in user_reply.text:
            await m.reply_text("❌ Galat format! Dubara file bhejein aur `|` ka use karein.")
            return

        parts = user_reply.text.split('|')
        
        # User data mapping
        name = parts[0].strip().upper()
        season = parts[1].strip() if len(parts) > 1 else "01"
        episode = parts[2].strip() if len(parts) > 2 else "01"
        quality = parts[3].strip() if len(parts) > 3 else "480p"
        audio = parts[4].strip() if len(parts) > 4 else "Hindi"
        
        # 2. Final Caption Taiyar Karna
        caption = f"""
{name} (S - {season}) 
╭──────────────────
├ 🗂Episodes - {episode}
├ 🔊Audio - {audio} #𝖮𝖿𝖿𝗂𝖼𝗂𝖺𝗅 
├ 🎼Quality - {quality}
├──────────────────
  MAIN CHANNEL : [ @TEMPEST_MAIN ]
"""

        # 3. DB Channel mein bhejna
        sent = await c.copy_message(
            chat_id=DB_CHANNEL,
            from_chat_id=m.chat.id,
            message_id=m.id,
            caption=caption
        )
        
        db_id = str(DB_CHANNEL).replace("-100", "")
        link = f"https://t.me/c/{db_id}/{sent.id}"
        
        await m.reply_text(f"✅ Kaam ho gaya!\n🔗 **Link:** {link}", disable_web_page_preview=True)
        
        # Messages delete karna taaki chat saaf rahe
        await prompt.delete()
        await user_reply.delete()

    except Exception as e:
        await m.reply_text(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    t = Thread(target=run_flask, daemon=True)
    t.start()
    bot.run()
