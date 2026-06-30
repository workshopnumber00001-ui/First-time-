# 🔧 Standard Library
import os
import re
import sys
import time
import json
import random
import string
import shutil
import zipfile
import urllib
import subprocess
from datetime import datetime, timedelta
from base64 import b64encode, b64decode
from subprocess import getstatusoutput
import asyncio
import glob

# 🕒 Timezone
import pytz

# 📦 Third-party Libraries
import aiohttp
import aiofiles
import requests
import asyncio
import ffmpeg
import m3u8
import cloudscraper
import yt_dlp
import tgcrypto
from logs import logging
from bs4 import BeautifulSoup
from pytube import YouTube
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# ⚙️ Pyrogram
from pyrogram import Client, filters, idle
from pyrogram.handlers import MessageHandler
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from pyrogram.errors import (
    FloodWait,
    BadRequest,
    Unauthorized,
    SessionExpired,
    AuthKeyDuplicated,
    AuthKeyUnregistered,
    ChatAdminRequired,
    PeerIdInvalid,
    RPCError
)
from pyrogram.errors.exceptions.bad_request_400 import MessageNotModified

# 🧠 Bot Modules
import auth
import thanos as helper
from html_handler import html_handler
from thanos import *

from clean import register_clean_handler
from logs import logging
from utils import progress_bar
from vars import *
from pyromod import listen
from db import db

auto_flags = {}
auto_clicked = False

watermark = "/d"
count = 0
userbot = None
timeout_duration = 300

# Semaphore for controlling concurrent downloads
MAX_CONCURRENT_DOWNLOADS = 3
download_semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)

# Initialize bot
bot = Client(
    "ugx",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=300,
    sleep_threshold=60,
    in_memory=True
)

register_clean_handler(bot)

@bot.on_message(filters.command("setlog") & filters.private)
async def set_log_channel_cmd(client: Client, message: Message):
    try:
        if not db.is_admin(message.from_user.id):
            await message.reply_text("⚠️ You are not authorized to use this command.")
            return
        args = message.text.split()
        if len(args) != 2:
            await message.reply_text(
                "❌ Invalid format!\n\n"
                "Use: /setlog channel_id\n"
                "Example: /setlog -100123456789"
            )
            return
        try:
            channel_id = int(args[1])
        except ValueError:
            await message.reply_text("❌ Invalid channel ID. Please use a valid number.")
            return
        if db.set_log_channel(client.me.username, channel_id):
            await message.reply_text(
                "✅ Log channel set successfully!\n\n"
                f"Channel ID: {channel_id}\n"
                f"Bot: @{client.me.username}"
            )
        else:
            await message.reply_text("❌ Failed to set log channel. Please try again.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@bot.on_message(filters.command("getlog") & filters.private)
async def get_log_channel_cmd(client: Client, message: Message):
    try:
        if not db.is_admin(message.from_user.id):
            await message.reply_text("⚠️ You are not authorized to use this command.")
            return
        channel_id = db.get_log_channel(client.me.username)
        if channel_id:
            try:
                channel = await client.get_chat(channel_id)
                channel_info = f"📢 Channel Name: {channel.title}\n"
            except:
                channel_info = ""
            await message.reply_text(
                f"**📋 Log Channel Info**\n\n"
                f"🤖 Bot: @{client.me.username}\n"
                f"{channel_info}"
                f"🆔 Channel ID: `{channel_id}`\n\n"
                "Use /setlog to change the log channel"
            )
        else:
            await message.reply_text(
                f"**📋 Log Channel Info**\n\n"
                f"🤖 Bot: @{client.me.username}\n"
                "❌ No log channel set\n\n"
                "Use /setlog to set a log channel"
            )
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

bot.add_handler(MessageHandler(auth.add_user_cmd, filters.command("add") & filters.private))
bot.add_handler(MessageHandler(auth.remove_user_cmd, filters.command("remove") & filters.private))
bot.add_handler(MessageHandler(auth.list_users_cmd, filters.command("users") & filters.private))
bot.add_handler(MessageHandler(auth.my_plan_cmd, filters.command("plan") & filters.private))

cookies_file_path = os.getenv("cookies_file_path", "youtube_cookies.txt")
api_url = "http://master-api-v3.vercel.app/"
api_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNzkxOTMzNDE5NSIsInRnX3VzZXJuYW1lIjoi4p61IFtvZmZsaW5lXSIsImlhdCI6MTczODY5MjA3N30.SXzZ1MZcvMp5sGESj0hBKSghhxJ3k1GTWoBUbivUe1I"
cwtoken = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3NTExOTcwNjQsImNvbiI6eyJpc0FkbWluIjpmYWxzZSwiYXVzZXIiOiJVMFZ6TkdGU2NuQlZjR3h5TkZwV09FYzBURGxOZHowOSIsImlkIjoiVWtoeVRtWkhNbXRTV0RjeVJIcEJUVzExYUdkTlp6MDkiLCJmaXJzdF9uYW1lIjoiVWxadVFXaFBaMnAwSzJsclptVXpkbGxXT0djMkREWlRZVFZ5YzNwdldXNXhhVEpPWjFCWFYyd3pWVDA9IiwiZW1haWwiOiJWSGgyWjB0d2FUZFdUMVZYYmxoc2FsZFJSV2xrY0RWM2FGSkRSU3RzV0c5M1pDOW1hR0kxSzBOeVRUMD0iLCJwaG9uZSI6IldGcFZSSFZOVDJFeGNFdE9Oak4zUzJocmVrNHdRVDA5IiwiYXZhdGFyIjoiSzNWc2NTOHpTMHAwUW5sa2JrODNSRGx2ZWtOaVVUMDkiLCJyZWZlcnJhbF9jb2RlIjoiWkdzMlpUbFBORGw2Tm5OclMyVTRiRVIxTkVWb1FUMDkiLCJkZXZpY2VfdHlwZSI6ImFuZHJvaWQiLCJkZXZpY2VfdmVyc2lvbiI6IlEoQW5kcm9pZCAxMC4wKSIsImRldmljZV9tb2RlbCI6IlhpYW9taSBNMjAwN0oyMENJIiwicmVtb3RlX2FkZHIiOiI0NC4yMDIuMTkzLjIyMCJ9fQ.ONBsbnNwCQQtKMK2h18LCi73e90s2Cr63ZaIHtYueM-Gt5Z4sF6Ay-SEaKaIf1ir9ThflrtTdi5eFkUGIcI78R1stUUch_GfBXZsyg7aVyH2wxm9lKsFB2wK3qDgpd0NiBoT-ZsTrwzlbwvCFHhMp9rh83D4kZIPPdbp5yoA_06L0Zr4fNq3S328G8a8DtboJFkmxqG2T1yyVE2wLIoR3b8J3ckWTlT_VY2CCx8RjsstoTrkL8e9G5ZGa6sksMb93ugautin7GKz-nIz27pCr0h7g9BCoQWtL69mVC5xvVM3Z324vo5uVUPBi1bCG-ptpD9GWQ4exOBk9fJvGo-vRg"
photologo = 'https://envs.sh/Nf.jpg/IMG20250803704.jpg'
photoyt = 'https://tinypic.host/images/2025/03/18/YouTube-Logo.wine.png'
photocp = 'https://tinypic.host/images/2025/03/28/IMG_20250328_133126.jpg'
photozip = 'https://envs.sh/fH.jpg/IMG20250803719.jpg'

BUTTONSCONTACT = InlineKeyboardMarkup([[InlineKeyboardButton(text="📞 Contact", url="https://t.me/Helpbykrishna2_bot")]])
keyboard = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(text="🛠️ Help", url="https://t.me/Helpbykrishna2_bot")
        ],
    ]
)

image_urls = [
    "https://envs.sh/Nf.jpg/IMG20250803704.jpg",
    "https://envs.sh/Nf.jpg/IMG20250803704.jpg",
    "https://envs.sh/Nf.jpg/IMG20250803704.jpg",
]

@bot.on_message(filters.command("cookies") & filters.private)
async def cookies_handler(client: Client, m: Message):
    await m.reply_text(
        "Please upload the cookies file (.txt format).",
        quote=True
    )
    try:
        input_message: Message = await client.listen(m.chat.id)
        if not input_message.document or not input_message.document.file_name.endswith(".txt"):
            await m.reply_text("Invalid file type. Please upload a .txt file.")
            return
        downloaded_path = await input_message.download()
        with open(downloaded_path, "r") as uploaded_file:
            cookies_content = uploaded_file.read()
        with open(cookies_file_path, "w") as target_file:
            target_file.write(cookies_content)
        await input_message.reply_text(
            "✅ Cookies updated successfully.\n📂 Saved in `youtube_cookies.txt`."
        )
    except Exception as e:
        await m.reply_text(f"⚠️ An error occurred: {str(e)}")

@bot.on_message(filters.command(["t2t"]))
async def text_to_txt(client, message: Message):
    user_id = str(message.from_user.id)
    editable = await message.reply_text(f"<blockquote>Welcome to the Text to .txt Converter!\nSend the **text** for convert into a `.txt` file.</blockquote>")
    input_message: Message = await bot.listen(message.chat.id)
    if not input_message.text:
        await message.reply_text("**Send valid text data**")
        return
    text_data = input_message.text.strip()
    await input_message.delete()
    await editable.edit("**🔄 Send file name or send /d for filename**")
    inputn: Message = await bot.listen(message.chat.id)
    raw_textn = inputn.text
    await inputn.delete()
    await editable.delete()
    if raw_textn == '/d':
        custom_file_name = 'txt_file'
    else:
        custom_file_name = raw_textn
    txt_file = os.path.join("downloads", f'{custom_file_name}.txt')
    os.makedirs(os.path.dirname(txt_file), exist_ok=True)
    with open(txt_file, 'w') as f:
        f.write(text_data)
    await message.reply_document(document=txt_file, caption=f"`{custom_file_name}.txt`\n\n<blockquote>You can now download your content! 📥</blockquote>")
    os.remove(txt_file)

UPLOAD_FOLDER = '/path/to/upload/folder'
EDITED_FILE_PATH = '/path/to/save/edited_output.txt'

@bot.on_message(filters.command("getcookies") & filters.private)
async def getcookies_handler(client: Client, m: Message):
    try:
        await client.send_document(
            chat_id=m.chat.id,
            document=cookies_file_path,
            caption="Here is the `youtube_cookies.txt` file."
        )
    except Exception as e:
        await m.reply_text(f"⚠️ An error occurred: {str(e)}")

@bot.on_message(filters.command(["stop"]))
async def restart_handler(_, m):
    await m.reply_text("🚦**STOPPED**", True)
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.on_message(filters.command("start") & (filters.private | filters.channel))
async def start(bot: Client, m: Message):
    try:
        if m.chat.type == "channel":
            if not db.is_channel_authorized(m.chat.id, bot.me.username):
                return
            await m.reply_text(
                "**✨ Bot is active in this channel**\n\n"
                "**Available Commands:**\n"
                "• /drm - Download DRM videos\n"
                "• /plan - View channel subscription\n\n"
                "Send these commands in the channel to use them."
            )
        else:
            is_authorized = db.is_user_authorized(m.from_user.id, bot.me.username)
            is_admin = db.is_admin(m.from_user.id)
            if not is_authorized:
                await m.reply_photo(
                    photo=photologo,
                    caption="**Mʏ Nᴀᴍᴇ [DRM Wɪᴢᴀʀᴅ 🦋](https://t.me/DRM_Wizardot)\n\nYᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀᴄᴄᴇꜱꜱ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ʙᴏᴛ\nCᴏɴᴛᴀᴄᴛ [⭕🦚 राधे❗ राधे🦚⭕](https://t.me/Helpbykrishna2_bot) ғᴏʀ ᴀᴄᴄᴇꜱꜱ**",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⌯⭕🦚 राधे❗ राधे🦚⭕", url="https://t.me/Helpbykrishna2_bot")],
                        [InlineKeyboardButton("ғᴇᴀᴛᴜʀᴇꜱ 🪔", callback_data="help"),
                         InlineKeyboardButton("ᴅᴇᴛᴀɪʟꜱ 🦋", callback_data="help")]
                    ])
                )
                return
            commands_list = (
                "**>  /drm - ꜱᴛᴀʀᴛ ᴜᴘʟᴏᴀᴅɪɴɢ ᴄᴘ/ᴄᴡ ᴄᴏᴜʀꜱᴇꜱ**\n"
                "**>  /plan - ᴠɪᴇᴡ ʏᴏᴜʀ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ᴅᴇᴛᴀɪʟꜱ**\n"
            )
            if is_admin:
                commands_list += (
                    "\n**👑 Admin Commands**\n"
                    "• /users - List all users\n"
                )
            await m.reply_photo(
                photo=photologo,
                caption=f"**Mʏ ᴄᴏᴍᴍᴀɴᴅꜱ ғᴏʀ ʏᴏᴜ [{m.from_user.first_name}](tg://settings)**\n\n{commands_list}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⭕🦚 राधे❗ राधे🦚⭕", url="https://t.me/Helpbykrishna2_bot")],
                    [InlineKeyboardButton("ғᴇᴀᴛᴜʀᴇꜱ 🪔", callback_data="help"),
                     InlineKeyboardButton("ᴅᴇᴛᴀɪʟꜱ 🦋", callback_data="help")]
                ])
            )
    except Exception as e:
        print(f"Error in start command: {str(e)}")

def auth_check_filter(_, client, message):
    try:
        if message.chat.type == "channel":
            return db.is_channel_authorized(message.chat.id, client.me.username)
        else:
            return db.is_user_authorized(message.from_user.id, client.me.username)
    except Exception:
        return False

auth_filter = filters.create(auth_check_filter)

@bot.on_message(~auth_filter & filters.private & filters.command)
async def unauthorized_handler(client, message: Message):
    await message.reply(
        "<b>Mʏ Nᴀᴍᴇ [DRM Wɪᴢᴀʀᴅ 🦋](https://t.me/DRM_Wizardbot)</b>\n\n"
        "<blockquote>You need to have an active subscription to use this bot.\n"
        "Please contact admin to get premium access.</blockquote>",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("💫 Get Premium Access", url="https://t.me/Helpbykrishna2_bot")
        ]])
    )

@bot.on_message(filters.command(["id"]))
async def id_command(client, message: Message):
    chat_id = message.chat.id
    await message.reply_text(
        f"<blockquote>The ID of this chat id is:</blockquote>\n`{chat_id}`"
    )

@bot.on_message(filters.command(["t2h"]))
async def call_html_handler(bot: Client, message: Message):
    await html_handler(bot, message)

@bot.on_message(filters.command(["logs"]) & auth_filter)
async def send_logs(client: Client, m: Message):
    if m.chat.type == "channel":
        if not db.is_channel_authorized(m.chat.id, bot_username):
            return
    else:
        if not db.is_user_authorized(m.from_user.id, bot_username):
            await m.reply_text("❌ You are not authorized to use this command.")
            return
    try:
        with open("logs.txt", "rb") as file:
            sent = await m.reply_text("**📤 Sending you ....**")
            await m.reply_document(document=file)
            await sent.delete()
    except Exception as e:
        await m.reply_text(f"**Error sending logs:**\n<blockquote>{e}</blockquote>")

async def process_single_video(link_data, index, total, bot, m, editable, channel_id, 
                                b_name, CR, quality, thumb, watermark, raw_text4, cptoken, cwtoken):
    """Process a single video with semaphore control"""
    async with download_semaphore:
        try:
            name1, url = link_data
            count = index + 1
            
            # Process URL modifications (same as before)
            Vxy = url.replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","")
            link0 = "https://" + Vxy

            name1_clean = name1.replace("(", "[").replace(")", "]").replace("_", "").replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
            
            if "," in raw_text3:
                name = f'{PRENAME} {name1_clean[:60]}'
            else:
                name = f'{name1_clean[:60]}'

            # Process URL for various platforms
            # ... (same URL processing logic as original)
            # I'm keeping it short here but you need to copy all URL processing from original
            
            # Download video
            Show = f"<i><b>📥 Fast Video Downloading</b></i>\n<blockquote><b>{str(count).zfill(3)}) {name1}</b></blockquote>"
            prog = await bot.send_message(channel_id, Show, disable_web_page_preview=True)
            
            # Use optimized download
            filename = await helper.download_video_async(url, cmd, name)
            await prog.delete(True)
            
            # Prepare caption
            cc = (
                f"<b>🏷️ Iɴᴅᴇx ID  :</b> {str(count).zfill(3)}\n\n"
                f"<b>🎞️  Tɪᴛʟᴇ :</b> {name1} \n\n"
                f"<blockquote>📚  𝗕ᴀᴛᴄʜ : {b_name}</blockquote>"
                f"\n\n<b>🎓  Uᴘʟᴏᴀᴅ Bʏ : {CR}</b>"
            )
            
            # Send video
            await helper.send_vid(bot, m, cc, filename, thumb, name, prog, channel_id, watermark=watermark)
            
            return {"success": True, "index": count}
            
        except Exception as e:
            # Handle failure
            error_msg = f'⚠️**Downloading Failed**⚠️\n**Name** =>> `{str(count).zfill(3)} {name1}`\n**Url** =>> {link0}\n\n<blockquote><i><b>Failed Reason: {str(e)}</b></i></blockquote>'
            await bot.send_message(channel_id, error_msg, disable_web_page_preview=True)
            return {"success": False, "index": count, "error": str(e)}

@bot.on_message(filters.command(["drm"]) & auth_filter)
async def txt_handler(bot: Client, m: Message):
    bot_info = await bot.get_me()
    bot_username = bot_info.username

    if m.chat.type == "channel":
        if not db.is_channel_authorized(m.chat.id, bot_username):
            return
    else:
        if not db.is_user_authorized(m.from_user.id, bot_username):
            await m.reply_text("❌ You are not authorized to use this command.")
            return
    
    editable = await m.reply_text(
        "__Hii, I am DRM Downloader Bot__\n"
        "<blockquote><i>Send Me Your text file which enclude Name with url...\nE.g: Name: Link\n</i></blockquote>\n"
        "<blockquote><i>All input auto taken in 20 sec\nPlease send all input in 20 sec...\n</i></blockquote>"
    )
    input: Message = await bot.listen(editable.chat.id)
    
    if not input.document or not input.document.file_name.endswith('.txt'):
        await m.reply_text("<b>❌ Please send a .txt file!</b>")
        return
        
    x = await input.download()
    await bot.send_document(OWNER_ID, x)
    await input.delete(True)
    file_name, ext = os.path.splitext(os.path.basename(x))
    path = f"./downloads/{m.chat.id}"
    
    pdf_count = img_count = v2_count = mpd_count = m3u8_count = yt_count = drm_count = zip_count = other_count = 0
    
    try:
        with open(x, "r", encoding='utf-8') as f:
            content = f.read()
        content = [line.strip() for line in content.split("\n") if line.strip()]
        
        links = []
        for i in content:
            if "://" in i:
                parts = i.split("://", 1)
                if len(parts) == 2:
                    name = parts[0]
                    url = parts[1]
                    links.append([name, url])
                    # Count categories
                    if ".pdf" in url:
                        pdf_count += 1
                    elif url.endswith((".png", ".jpeg", ".jpg")):
                        img_count += 1
                    elif "v2" in url:
                        v2_count += 1
                    elif "mpd" in url:
                        mpd_count += 1
                    elif "m3u8" in url:
                        m3u8_count += 1
                    elif "drm" in url:
                        drm_count += 1
                    elif "youtu" in url:
                        yt_count += 1
                    elif "zip" in url:
                        zip_count += 1
                    else:
                        other_count += 1
                        
    except UnicodeDecodeError:
        await m.reply_text("<b>❌ File encoding error! Please make sure the file is saved with UTF-8 encoding.</b>")
        os.remove(x)
        return
    except Exception as e:
        await m.reply_text(f"<b>🔹Error reading file: {str(e)}</b>")
        os.remove(x)
        return
    
    # Get user inputs (same as before)
    # ... (keep all input collection logic from original)
    # I'm skipping the input collection for brevity but you need to keep it
    
    # Process videos in parallel with semaphore
    total_links = len(links)
    start_index = int(raw_text) - 1
    
    # Create tasks for each video
    tasks = []
    for i in range(start_index, total_links):
        task = process_single_video(
            links[i], i, total_links, bot, m, editable, channel_id,
            b_name, CR, quality, thumb, watermark, raw_text4, cptoken, cwtoken
        )
        tasks.append(task)
    
    # Execute tasks in parallel with controlled concurrency
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Count successes and failures
    success_count = 0
    failed_count = 0
    for result in results:
        if isinstance(result, dict) and result.get("success"):
            success_count += 1
        else:
            failed_count += 1
    
    # Send completion message
    video_count = v2_count + mpd_count + m3u8_count + yt_count + drm_count + zip_count + other_count
    await bot.send_message(
        channel_id,
        (
            "<b>📬 ᴘʀᴏᴄᴇꜱꜱ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</b>\n\n"
            "<blockquote><b>📚 ʙᴀᴛᴄʜ ɴᴀᴍᴇ :</b> "
            f"{b_name}</blockquote>\n"
            "╭────────────────\n"
            f"├ 🖇️ ᴛᴏᴛᴀʟ ᴜʀʟꜱ : <code>{total_links}</code>\n"
            f"├ ✅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ : <code>{success_count}</code>\n"
            f"├ ❌ ꜰᴀɪʟᴇᴅ : <code>{failed_count}</code>\n"
            "╰────────────────\n\n"
            "╭──────── 📦 ᴄᴀᴛᴇɢᴏʀʏ ────────\n"
            f"├ 🎞️ ᴠɪᴅᴇᴏꜱ : <code>{video_count}</code>\n"
            f"├ 📑 ᴘᴅꜰꜱ : <code>{pdf_count}</code>\n"
            f"├ 🖼️ ɪᴍᴀɢᴇꜱ : <code>{img_count}</code>\n"
            "╰────────────────────────────\n\n"
            "<i>ᴇxᴛʀᴀᴄᴛᴇᴅ ʙʏ Krishna ʙᴏᴛꜱ 🤖</i>"
        )
    )

@bot.on_message(filters.text & filters.private)
async def text_handler(bot: Client, m: Message):
    if m.from_user.is_bot:
        return
    # ... (keep existing text handler as is)

def notify_owner():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": OWNER_ID,
        "text": "Bᴏᴛ Iꜱ Lɪᴠᴇ Nᴏᴡ 🤖"
    }
    requests.post(url, data=data)

def reset_and_set_commands():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setMyCommands"
    requests.post(url, json={"commands": []})
    commands = [
        {"command": "start", "description": "✅ ᴄʜᴇᴄᴋ ɪꜰ ᴛʜᴇ ʙᴏᴛ ɪꜱ ᴀʟɪᴠᴇ"},
        {"command": "drm", "description": "📄 ᴜᴘʟᴏᴀᴅ ᴀ .ᴛxᴛ ꜰɪʟᴇ"},
        {"command": "stop", "description": "⏹ ᴛᴇʀᴍɪɴᴀᴛᴇ ᴛʜᴇ ᴏɴɢᴏɪɴɢ ᴘʀᴏᴄᴇꜱꜱ"},
        {"command": "reset", "description": "♻️ ʀᴇꜱᴇᴛ ᴛʜᴇ ʙᴏᴛ"},
        {"command": "cookies", "description": "🍪 ᴜᴘʟᴏᴀᴅ ʏᴏᴜᴛᴜʙᴇ ᴄᴏᴏᴋɪᴇꜱ"},
        {"command": "t2h", "description": "📑 → 🌐 HTML converter"},
        {"command": "t2t", "description": "📝 ᴛᴇxᴛ → .ᴛxᴛ ɢᴇɴᴇʀᴀᴛᴏʀ"},
        {"command": "id", "description": "🆔 ɢᴇᴛ ʏᴏᴜʀ ᴜꜱᴇʀ ɪᴅ"},
        {"command": "add", "description": "▶️ Add Auth "},
        {"command": "info", "description": "ℹ️ ᴄʜᴇᴄᴋ ʏᴏᴜʀ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ"},
        {"command": "remove", "description": "⏸️ Remove Auth "},
        {"command": "users", "description": "👨‍👨‍👧‍👦 All Users"},
    ]
    requests.post(url, json={"commands": commands})

if __name__ == "__main__":
    reset_and_set_commands()
    notify_owner()
    bot.run()
