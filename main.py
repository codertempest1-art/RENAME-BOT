import os, re, asyncio, requests, time, math
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from pyromod import listen
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
API_ID = 37197223
API_HASH = "3a43ae287a696ee9a6a82fb79f605b75"
BOT_TOKEN = "8416317246:AAF7M6ampaP5u0yOcjD-lWiXyMWsbTohpB4"
ADMINS = [7426624114]
START_PIC = "https://graph.org/file/43b04771f3720fe8dd566-5d7f961ab3c8e3b362.jpg"

# Memory Storage
db_config = {"channel": None, "caption": None}

# Web Server for 24/7 (Render/Koyeb)
app = Flask(__name__)
@app.route('/')
def home(): return "Raphael Master System is Online!"
def run_flask(): app.run(host="0.0.0.0", port=8080)

bot = Client("RaphaelMaster", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- PROGRESS BAR ---
async def progress_bar(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        progress = "[{0}{1}]".format(
            ''.join(["▰" for i in range(math.floor(percentage / 10))]),
            ''.join(["▱" for i in range(10 - math.floor(percentage / 10))])
        )
        tmp = f"**{ud_type} Mode**\n{progress} {round(percentage, 2)}%\n🚀 Speed: {round(speed / 1024, 2)} KB/s"
        try: await message.edit(text=tmp)
        except: pass

# --- UI COMPONENTS ---
START_BUTTONS = InlineKeyboardMarkup([
    [InlineKeyboardButton("ℹ️ About Me", callback_data="about_btn")],
    [InlineKeyboardButton("💸 Donate", callback_data="donate_btn"),
     InlineKeyboardButton("📚 Commands", callback_data="cmds_btn")],
    [InlineKeyboardButton("🏢 Support", url="https://t.me/tempest_support"),
     InlineKeyboardButton("📡 Updates", url="https://t.me/tempest_updates")],
    [InlineKeyboardButton("➕ Add Raphael to Groups", url="https://t.me/share/url?url=CheckOutThisBot")]
])
BACK_BUTTON = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_start")]])

# --- HANDLERS ---
@bot.on_message(filters.command("start") & filters.private)
async def start(c, m):
    caption = f"Hello There, My name's Raphael 🦋\n\nI am an AI Integrated Anime themed Advanced Renamer Bot."
    await m.reply_photo(photo=START_PIC, caption=caption, reply_markup=START_BUTTONS)

@bot.on_callback_query()
async def cb_handler(c, cb):
    if cb.data == "about_btn":
        await cb.message.edit_caption(caption="**🦋 About Raphael:**\n\n• Developer: Daughter of Tempest\n• Version: 3.0\n• Purpose: Batch Renaming & Thumbnails.", reply_markup=BACK_BUTTON)
    elif cb.data == "cmds_btn":
        await cb.message.edit_caption(caption="**📚 Commands:**\n• `/setchnl` - Set Channel\n• `/setcap` - Custom Caption\n• Forward files to start Batch!", reply_markup=BACK_BUTTON)
    elif cb.data == "back_start":
        await cb.message.edit_caption(caption="Hello There, My name's Raphael 🦋", reply_markup=START_BUTTONS)
    elif "type_" in cb.data:
        f_type = "video" if "type_v_" in cb.data else "manga"
        msg_id = int(cb.data.split("_")[-1])
        await cb.message.edit_text(f"📝 Bhejiye: **{f_type.upper()} Name**")
        name_reply = await c.listen(cb.message.chat.id)
        m = await c.get_messages(cb.message.chat.id, msg_id)
        await process_file(c, m, f_type, name_reply.text.strip().upper())

@bot.on_message(filters.private & (filters.video | filters.document))
async def batch_init(c, m):
    if not db_config["channel"]: return await m.reply_text("❌ Pehle `/setchnl` karein.")
    btns = [[InlineKeyboardButton("🎬 VIDEO", callback_data=f"type_v_{m.id}"),
             InlineKeyboardButton("📚 MANGA", callback_data=f"type_m_{m.id}")]]
    await m.reply_text("⚡ Select type and give name:", reply_markup=InlineKeyboardMarkup(btns))

async def process_file(c, m, f_type, base_name):
    file = m.video or m.document
    file_size_mb = file.file_size / (1024 * 1024)
    orig_name = file.file_name
    match = re.search(r'(\d+)', orig_name)
    num = match.group(1) if match else "01"
    ext = os.path.splitext(orig_name)[1]
    new_name = f"{base_name} S01 EP{num}{ext}" if f_type == "video" else f"{base_name} CH - {num}{ext}"

    sts = await m.reply_text("📥 **Processing...**")
    start_time = time.time()
    try:
        path = await m.download(file_name=new_name, progress=progress_bar, progress_args=("Downloading", sts, start_time))
        thumb_path = "thumb.jpg"
        if not os.path.exists(thumb_path):
            with open(thumb_path, 'wb') as f: f.write(requests.get(START_PIC).content)

        cap = db_config["caption"] or f"**{base_name} - {num}**\n@TEMPEST_MAIN"
        await sts.edit("📤 **Uploading...**")
        if f_type == "video":
            await c.send_video(db_config["channel"], video=path, thumb=thumb_path, caption=cap, file_name=new_name, progress=progress_bar, progress_args=("Uploading", sts, start_time))
        else:
            await c.send_document(db_config["channel"], document=path, thumb=thumb_path, caption=cap, file_name=new_name, progress=progress_bar, progress_args=("Uploading", sts, start_time))
        
        if os.path.exists(path): os.remove(path)
        delay = 5 if file_size_mb < 500 else (12 if file_size_mb > 1000 else 8)
        await sts.edit(f"✅ Success! Wait `{delay}s`...")
        await asyncio.sleep(delay)
        await sts.delete()
    except Exception as e: await m.reply_text(f"❌ Error: {e}")

@bot.on_message(filters.command("setchnl") & filters.user(ADMINS))
async def set_chnl(c, m):
    try:
        db_config["channel"] = int(m.command[1])
        await m.reply_text(f"✅ Target Channel Set!")
    except: await m.reply_text("Usage: `/setchnl -100xxxx`")

@bot.on_message(filters.command("setcap") & filters.user(ADMINS))
async def set_cap(c, m):
    await m.reply_text("📝 Bhejiye naya caption:")
    r = await c.listen(m.chat.id)
    db_config["caption"] = r.text
    await m.reply_text("✅ Caption Saved!")

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    bot.start()
    print("Raphael Master System Ready!")
    bot.loop.run_forever()
