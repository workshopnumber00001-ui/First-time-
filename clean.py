import os
import glob
from pathlib import Path
from pyrogram import Client, filters
from vars import ADMINS
from db import db
from datetime import datetime
from pyrogram.handlers import MessageHandler

def clean_downloads():
    """Clean everything in downloads directory"""
    try:
        os.makedirs("downloads", exist_ok=True)
        for file in glob.glob("downloads/*"):
            try:
                if os.path.isfile(file):
                    os.remove(file)
                    print(f"Removed from downloads: {file}")
            except Exception as e:
                print(f"Error removing {file}: {e}")
    except Exception as e:
        print(f"Error cleaning downloads: {e}")

def clean_media_files():
    """Clean images and videos except wm.png"""
    try:
        image_formats = ["*.jpg", "*.jpeg", "*.png"]
        video_formats = ["*.mp4", "*.mkv", "*.webm"]
        temp_formats = ["*.part", "*.ytdl"]
        formats_to_clean = image_formats + video_formats + temp_formats
        
        for format_pattern in formats_to_clean:
            for file in glob.glob(format_pattern):
                try:
                    if file == "wm.png":
                        continue
                    if os.path.isfile(file):
                        os.remove(file)
                        print(f"Removed from root: {file}")
                except Exception as e:
                    print(f"Error removing {file}: {e}")
    except Exception as e:
        print(f"Error cleaning media files: {e}")

def clean_thumb_cache():
    """Clean cached thumbnails"""
    try:
        for file in glob.glob("downloads/thumb_*.jpg"):
            try:
                os.remove(file)
                print(f"Removed cached thumbnail: {file}")
            except Exception as e:
                print(f"Error removing {file}: {e}")
    except Exception as e:
        print(f"Error cleaning thumb cache: {e}")

def clean_all():
    clean_downloads()
    clean_media_files()
    clean_thumb_cache()

async def clean_expired_users(client: Client):
    try:
        all_users = []
        for bot_username in db.list_bot_usernames():
            users = db.list_users(bot_username)
            all_users.extend([(user, bot_username) for user in users])
        
        removed_count = 0
        now = datetime.now()
        
        for user, bot_username in all_users:
            expiry = user['expiry_date']
            if isinstance(expiry, str):
                expiry = datetime.strptime(expiry, "%Y-%m-%d %H:%M:%S")
            if expiry <= now:
                try:
                    await client.send_message(
                        user['user_id'],
                        "**⚠️ Your subscription has expired**\n\n"
                        "Your access has been revoked. Contact admin to renew."
                    )
                except Exception as e:
                    print(f"Failed to notify user {user['user_id']}: {e}")
                if db.remove_user(user['user_id'], bot_username):
                    removed_count += 1
        return removed_count
    except Exception as e:
        print(f"Error cleaning expired users: {e}")
        return 0

async def handle_clean_command(client: Client, message):
    try:
        if message.from_user.id not in ADMINS:
            await message.reply_text("⚠️ You are not authorized to use this command.")
            return
        status_msg = await message.reply_text("🧹 Cleaning files and expired users...")
        clean_all()
        removed_users = await clean_expired_users(client)
        await status_msg.edit_text(
            "✅ Cleanup completed!\n"
            "- Cleaned downloads directory\n"
            "- Removed media files (except wm.png)\n"
            "- Removed .part and .ytdl files\n"
            f"- Removed {removed_users} expired users"
        )
    except Exception as e:
        await message.reply_text(f"❌ Error during cleanup: {str(e)}")

def register_clean_handler(bot: Client):
    bot.add_handler(MessageHandler(handle_clean_command, filters.command("clean") & filters.private))

clean_all()
