# ---------------------------------------------------
# Tên File: ytdl.py (mã thuần)
# Mô tả: Một bot Pyrogram để tải video từ YouTube và các trang web khác từ các kênh hoặc nhóm Telegram
#        và tải lại chúng lên Telegram.
# Tác giả: Gagan
# GitHub: https://github.com/devgaganin/
# Telegram: https://t.me/ultimatesmmnews
# YouTube: https://youtube.com/@dev_gagan
# Ngày tạo: 2025-01-11
# Lần sửa cuối: 2025-01-11
# Phiên bản: 2.0.5
# Giấy phép: Giấy phép MIT
# ---------------------------------------------------

import yt_dlp
import os
import tempfile
import time
import asyncio
import random
import string
import requests
import logging
import time
import math
from shared_client import client, app
from telethon import events
from telethon.sync import TelegramClient
from telethon.tl.types import DocumentAttributeVideo
from utils.func import get_video_metadata, screenshot
from telethon.tl.functions.messages import EditMessageRequest
from devgagantools import fast_upload
from concurrent.futures import ThreadPoolExecutor
import aiohttp 
import logging
import aiofiles
from config import YT_COOKIES, INSTA_COOKIES
from mutagen.id3 import ID3, TIT2, TPE1, COMM, APIC
from mutagen.mp3 import MP3
 
logger = logging.getLogger(__name__)
 
 
thread_pool = ThreadPoolExecutor()
ongoing_downloads = {}  # Từ điển lưu trữ các lượt tải đang diễn ra
 
def d_thumbnail(thumbnail_url, save_path):
    """Tải hình ảnh thu nhỏ từ URL và lưu vào đường dẫn được chỉ định."""
    try:
        response = requests.get(thumbnail_url, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return save_path
    except requests.exceptions.RequestException as e:
        logger.error(f"Không thể tải hình ảnh thu nhỏ: {e}")
        return None
 
 
async def download_thumbnail_async(url, path):
    """Tải hình ảnh thu nhỏ bất đồng bộ."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                with open(path, 'wb') as f:
                    f.write(await response.read())
 
 
async def extract_audio_async(ydl_opts, url):
    """Trích xuất âm thanh từ URL bất đồng bộ."""
    def sync_extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=True)
    return await asyncio.get_event_loop().run_in_executor(thread_pool, sync_extract)
 
 
def get_random_string(length=7):
    """Tạo chuỗi ngẫu nhiên với độ dài được chỉ định."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length)) 
 
 
async def process_audio(client, event, url, cookies_env_var=None):
    """Xử lý và tải âm thanh từ URL."""
    cookies = None
    if cookies_env_var:
        cookies = cookies_env_var
 
    temp_cookie_path = None
    if cookies:
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt') as temp_cookie_file:
            temp_cookie_file.write(cookies)
            temp_cookie_path = temp_cookie_file.name
 
    start_time = time.time()
    random_filename = f"@ultimatesmmnews__{event.sender_id}"
    download_path = f"{random_filename}.mp3"
 
    ydl_opts = {
        'format': 'bestaudio/best',  # Chọn định dạng âm thanh tốt nhất
        'outtmpl': f"{random_filename}.%(ext)s",  # Tên file đầu ra
        'cookiefile': temp_cookie_path,  # File cookie tạm thời
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],  # Chuyển đổi sang mp3
        'quiet': False,
        'noplaylist': True,  # Không tải danh sách phát
    }
    prog = None
 
    progress_message = await event.reply("**__Đang bắt đầu trích xuất âm thanh...__**")
 
    try:
         
        info_dict = await extract_audio_async(ydl_opts, url)
        title = info_dict.get('title', 'Âm thanh đã trích xuất')
 
        await progress_message.edit("**__Đang chỉnh sửa siêu dữ liệu...__**")
 
         
        if os.path.exists(download_path):
            def edit_metadata():
                audio_file = MP3(download_path, ID3=ID3)
                try:
                    audio_file.add_tags()
                except Exception:
                    pass
                audio_file.tags["TIT2"] = TIT2(encoding=3, text=title)  # Tiêu đề bài hát
                audio_file.tags["TPE1"] = TPE1(encoding=3, text="TEAM Name_Apex")  # Tên nghệ sĩ
                audio_file.tags["COMM"] = COMM(encoding=3, lang="eng", desc="Bình luận", text="Hỗ trợ bởi TEAM Name_Apex")  # Bình luận
 
                thumbnail_url = info_dict.get('thumbnail')
                if thumbnail_url:
                    thumbnail_path = os.path.join(tempfile.gettempdir(), "thumb.jpg")
                    asyncio.run(download_thumbnail_async(thumbnail_url, thumbnail_path))
                    with open(thumbnail_path, 'rb') as img:
                        audio_file.tags["APIC"] = APIC(
                            encoding=3, mime='image/jpeg', type=3, desc='Bìa', data=img.read()
                        )  # Hình ảnh bìa
                    os.remove(thumbnail_path)
                audio_file.save()
 
            await asyncio.to_thread(edit_metadata)
 
         
 
         
        chat_id = event.chat_id
        if os.path.exists(download_path):
            await progress_message.delete()
            prog = await client.send_message(chat_id, "**__Đang bắt đầu tải lên...__**")
            uploaded = await fast_upload(
                client, download_path, 
                reply=prog, 
                name=None,
                progress_bar_function=lambda done, total: progress_callback(done, total, chat_id)
            )
            await client.send_file(chat_id, uploaded, caption=f"**{title}**\n\n**__Hỗ trợ bởi TEAM Name_Apex__**")
            if prog:
                await prog.delete()
        else:
            await event.reply("**__Không tìm thấy file âm thanh sau khi trích xuất!__**")
 
    except Exception as e:
        logger.exception("Lỗi trong quá trình trích xuất hoặc tải lên âm thanh")
        await event.reply(f"**__Đã xảy ra lỗi: {e}__**")
    finally:
        if os.path.exists(download_path):
            os.remove(download_path)
        if temp_cookie_path and os.path.exists(temp_cookie_path):
            os.remove(temp_cookie_path)
 
@client.on(events.NewMessage(pattern="/adl"))
async def handler(event):
    """Xử lý lệnh /adl để tải âm thanh."""
    user_id = event.sender_id
    if user_id in ongoing_downloads:
        await event.reply("**Bạn đang có một lượt tải đang diễn ra. Vui lòng đợi cho đến khi hoàn tất!**")
        return
 
    if len(event.message.text.split()) < 2:
        await event.reply("**Cách dùng:** `/adl <liên-kết-video>`\n\nVui lòng cung cấp một liên kết video hợp lệ!")
        return    
 
    url = event.message.text.split()[1]
    ongoing_downloads[user_id] = True
 
    try:
        if "instagram.com" in url:
            await process_audio(client, event, url, cookies_env_var=INSTA_COOKIES)
        elif "youtube.com" in url or "youtu.be" in url:
            await process_audio(client, event, url, cookies_env_var=YT_COOKIES)
        else:
            await process_audio(client, event, url)
    except Exception as e:
        await event.reply(f"**Đã xảy ra lỗi:** `{e}`")
    finally:
        ongoing_downloads.pop(user_id, None)
 
 
async def fetch_video_info(url, ydl_opts, progress_message, check_duration_and_size):
    """Lấy thông tin video từ URL."""
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
 
        if check_duration_and_size:
             
            duration = info_dict.get('duration', 0)
            if duration and duration > 3 * 3600:   
                await progress_message.edit("**❌ __Video dài hơn 3 giờ. Hủy tải xuống...__**")
                return None
 
             
            estimated_size = info_dict.get('filesize_approx', 0)
            if estimated_size and estimated_size > 2 * 1024 * 1024 * 1024:   
                await progress_message.edit("**🤞 __Kích thước video lớn hơn 2GB. Hủy tải xuống.__**")
                return None
 
        return info_dict
 
def download_video(url, ydl_opts):
    """Tải video từ URL."""
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
 
 
@client.on(events.NewMessage(pattern="/dl"))
async def handler(event):
    """Xử lý lệnh /dl để tải video."""
    user_id = event.sender_id
 
     
    if user_id in ongoing_downloads:
        await event.reply("**Bạn đang có một lượt tải ytdlp đang diễn ra. Vui lòng đợi cho đến khi hoàn tất!**")
        return
 
    if len(event.message.text.split()) < 2:
        await event.reply("**Cách dùng:** `/dl <liên-kết-video>`\n\nVui lòng cung cấp một liên kết video hợp lệ!")
        return    
 
    url = event.message.text.split()[1]
 
     
    try:
        if "instagram.com" in url:
            await process_video(client, event, url, INSTA_COOKIES, check_duration_and_size=False)
        elif "youtube.com" in url or "youtu.be" in url:
            await process_video(client, event, url, YT_COOKIES, check_duration_and_size=True)
        else:
            await process_video(client, event, url, None, check_duration_and_size=False)
 
    except Exception as e:
        await event.reply(f"**Đã xảy ra lỗi:** `{e}`")
    finally:
         
        ongoing_downloads.pop(user_id, None)
 
 
 
 
user_progress = {}
 
def progress_callback(done, total, user_id):
    """Cập nhật thanh tiến trình cho quá trình tải lên."""
     
    if user_id not in user_progress:
        user_progress[user_id] = {
            'previous_done': 0,
            'previous_time': time.time()
        }
 
     
    user_data = user_progress[user_id]
 
     
    percent = (done / total) * 100
 
     
    completed_blocks = int(percent // 10)
    remaining_blocks = 10 - completed_blocks
    progress_bar = "♦" * completed_blocks + "◇" * remaining_blocks
 
     
    done_mb = done / (1024 * 1024)   
    total_mb = total / (1024 * 1024)
 
     
    speed = done - user_data['previous_done']
    elapsed_time = time.time() - user_data['previous_time']
 
    if elapsed_time > 0:
        speed_bps = speed / elapsed_time   
        speed_mbps = (speed_bps * 8) / (1024 * 1024)   
    else:
        speed_mbps = 0
 
     
    if speed_bps > 0:
        remaining_time = (total - done) / speed_bps
    else:
        remaining_time = 0
 
     
    remaining_time_min = remaining_time / 60
 
     
    final = (
        f"╭──────────────────╮\n"
        f"│        **__Đang tải lên...__**       \n"
        f"├──────────\n"
        f"│ {progress_bar}\n\n"
        f"│ **__Tiến độ:__** {percent:.2f}%\n"
        f"│ **__Đã tải:__** {done_mb:.2f} MB / {total_mb:.2f} MB\n"
        f"│ **__Tốc độ:__** {speed_mbps:.2f} Mbps\n"
        f"│ **__Thời gian còn lại:__** {remaining_time_min:.2f} phút\n"
        f"╰──────────────────╯\n\n"
        f"**__Hỗ trợ bởi TEAM Name_Apex__**"
    )
 
     
    user_data['previous_done'] = done
    user_data['previous_time'] = time.time()
 
    return final
 
async def process_video(client, event, url, cookies_env_var, check_duration_and_size=False):
    """Xử lý và tải video từ URL."""
    start_time = time.time()
    logger.info(f"Nhận được liên kết: {url}")
     
    cookies = None
    if cookies_env_var:
        cookies = cookies_env_var
 
     
    random_filename = get_random_string() + ".mp4"
    download_path = os.path.abspath(random_filename)
    logger.info(f"Đã tạo đường dẫn tải xuống ngẫu nhiên: {download_path}")
 
     
    temp_cookie_path = None
    if cookies:
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt') as temp_cookie_file:
            temp_cookie_file.write(cookies)
            temp_cookie_path = temp_cookie_file.name
        logger.info(f"Đã tạo file cookie tạm thời tại: {temp_cookie_path}")
 
     
    thumbnail_file = None
    metadata = {'width': None, 'height': None, 'duration': None, 'thumbnail': None}
 
     
    ydl_opts = {
        'outtmpl': download_path,
        'format': 'best',  # Chọn định dạng video tốt nhất
        'cookiefile': temp_cookie_path if temp_cookie_path else None,
        'writethumbnail': True,  # Lưu hình ảnh thu nhỏ
        'verbose': True,
    }
    prog = None
    progress_message = await event.reply("**__Đang bắt đầu tải xuống...__**")
    logger.info("Bắt đầu quá trình tải xuống...")
    try:
        info_dict = await fetch_video_info(url, ydl_opts, progress_message, check_duration_and_size)
        if not info_dict:
            return
         
        await asyncio.to_thread(download_video, url, ydl_opts)
        title = info_dict.get('title', 'Hỗ trợ bởi TEAM Name_Apex')
        k = await get_video_metadata(download_path)      
        W = k['width']
        H = k['height']
        D = k['duration']
        metadata['width'] = info_dict.get('width') or W
        metadata['height'] = info_dict.get('height') or H
        metadata['duration'] = int(info_dict.get('duration') or 0) or D
        thumbnail_url = info_dict.get('thumbnail', None)
        THUMB = None
 
         
        if thumbnail_url:
            thumbnail_file = os.path.join(tempfile.gettempdir(), get_random_string() + ".jpg")
            downloaded_thumb = d_thumbnail(thumbnail_url, thumbnail_file)
            if downloaded_thumb:
                logger.info(f"Hình ảnh thu nhỏ đã được lưu tại: {downloaded_thumb}")
 
        if thumbnail_file:
            THUMB = thumbnail_file
        else:
            THUMB = await screenshot(download_path, metadata['duration'], event.sender_id)

        chat_id = event.chat_id
        SIZE = 2 * 1024 * 1024
        caption = f"{title}"
     
        if os.path.exists(download_path) and os.path.getsize(download_path) > SIZE:
            prog = await client.send_message(chat_id, "**__Đang bắt đầu tải lên...__**")
            await split_and_upload_file(app, chat_id, download_path, caption)
            await prog.delete()
         
        if os.path.exists(download_path):
            await progress_message.delete()
            prog = await client.send_message(chat_id, "**__Đang bắt đầu tải lên...__**")
            uploaded = await fast_upload(
                client, download_path,
                reply=prog,
                progress_bar_function=lambda done, total: progress_callback(done, total, chat_id)
            )
            await client.send_file(
                event.chat_id,
                uploaded,
                caption=f"**{title}**",
                attributes=[
                    DocumentAttributeVideo(
                        duration=metadata['duration'],
                        w=metadata['width'],
                        h=metadata['height'],
                        supports_streaming=True
                    )
                ],
                thumb=THUMB if THUMB else None
            )
            if prog:
                await prog.delete()
        else:
            await event.reply("**__Không tìm thấy file sau khi tải xuống. Có lỗi xảy ra!__**")
    except Exception as e:
        logger.exception("Đã xảy ra lỗi trong quá trình tải xuống hoặc tải lên.")
        await event.reply(f"**__Đã xảy ra lỗi: {e}__**")
    finally:
         
        if os.path.exists(download_path):
            os.remove(download_path)
        if temp_cookie_path and os.path.exists(temp_cookie_path):
            os.remove(temp_cookie_path)
        if thumbnail_file and os.path.exists(thumbnail_file):
            os.remove(thumbnail_file)
 

async def split_and_upload_file(app, sender, file_path, caption):
    """Chia nhỏ và tải lên file lớn."""
    if not os.path.exists(file_path):
        await app.send_message(sender, "❌ Không tìm thấy file!")
        return

    file_size = os.path.getsize(file_path)
    start = await app.send_message(sender, f"ℹ️ Kích thước file: {file_size / (1024 * 1024):.2f} MB")
    PART_SIZE =  1.9 * 1024 * 1024 * 1024  # Kích thước mỗi phần

    part_number = 0
    async with aiofiles.open(file_path, mode="rb") as f:
        while True:
            chunk = await f.read(PART_SIZE)
            if not chunk:
                break

            # Tạo tên file cho phần
            base_name, file_ext = os.path.splitext(file_path)
            part_file = f"{base_name}.part{str(part_number).zfill(3)}{file_ext}"

            # Ghi phần vào file
            async with aiofiles.open(part_file, mode="wb") as part_f:
                await part_f.write(chunk)

            # Tải lên phần
            edit = await app.send_message(sender, f"⬆️ Đang tải lên phần {part_number + 1}...")
            part_caption = f"{caption} \n\n**Phần: {part_number + 1}**"
            await app.send_document(sender, document=part_file, caption=part_caption,
                progress=progress_bar,
                progress_args=("╭─────────────────────╮\n│      **__Tải lên bởi Pyro__**\n├─────────────────────", edit, time.time())
            )
            await edit.delete()
            os.remove(part_file)

            part_number += 1

    await start.delete()
    os.remove(file_path)


PROGRESS_BAR = """
│ **__Hoàn tất:__** {1}/{2}
│ **__Byte:__** {0}%
│ **__Tốc độ:__** {3}/s
│ **__Thời gian còn lại:__** {4}
╰─────────────────────╯
"""

async def get_seconds(time_string: str) -> int:
    """
    Chuyển đổi chuỗi thời gian (ví dụ: '5min', '2hour') thành giây.
    """
    def extract_value_and_unit(ts: str):
        value = ''.join(filter(str.isdigit, ts))
        unit = ts[len(value):].strip()
        return int(value) if value else 0, unit
    
    value, unit = extract_value_and_unit(time_string)
    time_units = {
        's': 1,
        'min': 60,
        'hour': 3600,
        'day': 86400,
        'month': 86400 * 30,
        'year': 86400 * 365
    }
    
    return value * time_units.get(unit, 0)

async def progress_bar(current: int, total: int, ud_type: str, message, start: float):
    """
    Cập nhật thanh tiến trình cho quá trình đang diễn ra.
    """
    now = time.time()
    diff = now - start
    
    if round(diff % 10) == 0 or current == total:
        percentage = (current * 100) / total
        speed = current / diff if diff else 0
        elapsed_time = round(diff * 1000)
        time_to_completion = round((total - current) / speed) * 1000 if speed else 0
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time_str = TimeFormatter(elapsed_time)
        estimated_total_time_str = TimeFormatter(estimated_total_time)

        progress = "".join(["♦" for _ in range(math.floor(percentage / 10))]) + \
                   "".join(["◇" for _ in range(10 - math.floor(percentage / 10))])
        
        progress_text = progress + PROGRESS_BAR.format(
            round(percentage, 2),
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            estimated_total_time_str if estimated_total_time_str else "0 s"
        )
        try:
            await message.edit(text=f"{ud_type}\n│ {progress_text}")
        except:
            pass

def humanbytes(size: int) -> str:
    """
    Chuyển đổi byte thành định dạng dễ đọc cho con người.
    """
    if not size:
        return ""
    
    power = 2**10
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    n = 0
    while size > power and n < len(units) - 1:
        size /= power
        n += 1
    
    return f"{round(size, 2)} {units[n]}"

def TimeFormatter(milliseconds: int) -> str:
    """
    Định dạng mili giây thành khoảng thời gian dễ đọc.
    """
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    
    parts = []
    if days: parts.append(f"{days} ngày")
    if hours: parts.append(f"{hours} giờ")
    if minutes: parts.append(f"{minutes} phút")
    if seconds: parts.append(f"{seconds} giây")
    if milliseconds: parts.append(f"{milliseconds} mili giây")
    
    return ', '.join(parts)

def convert(seconds: int) -> str:
    """
    Chuyển đổi giây thành định dạng HH:MM:SS.
    """
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}"
