# Bản quyền (c) 2025 devgagan: https://github.com/devgaganin.
# Được cấp phép theo GNU General Public License v3.0.
# Xem tệp LICENSE trong thư mục gốc của repository để biết chi tiết bản quyền.

from telethon import events, Button
import re
import os
import asyncio
import string
import random
from shared_client import client as gf
from config import OWNER_ID
from utils.func import get_user_data_key, save_user_data, users_collection

# Các phần mở rộng video được hỗ trợ
VIDEO_EXTENSIONS = {
    'mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm',
    'mpeg', 'mpg', '3gp'
}
SET_PIC = 'settings.jpg'
MESS = 'Tùy chỉnh thiết lập cho tập tin của bạn...'

# Danh sách các cuộc hội thoại đang hoạt động
active_conversations = {}

# Lệnh /settings để hiển thị menu thiết lập
@gf.on(events.NewMessage(incoming=True, pattern='/settings'))
async def settings_command(event):
    user_id = event.sender_id
    await send_settings_message(event.chat_id, user_id)

# Gửi menu thiết lập tới người dùng
async def send_settings_message(chat_id, user_id):
    buttons = [
        [
            Button.inline('📝 Thiết lập Chat ID', b'setchat'),
            Button.inline('🏷️ Thiết lập Rename Tag', b'setrename')
        ],
        [
            Button.inline('📋 Thiết lập Caption', b'setcaption'),
            Button.inline('🔄 Thay thế từ', b'setreplacement')
        ],
        [
            Button.inline('🗑️ Xóa từ', b'delete'),
            Button.inline('🔄 Đặt lại thiết lập', b'reset')
        ],
        [
            Button.inline('🔑 Đăng nhập phiên', b'addsession'),
            Button.inline('🚪 Đăng xuất', b'logout')
        ],
        [
            Button.inline('🖼️ Thiết lập ảnh đại diện', b'setthumb'),
            Button.inline('❌ Xóa ảnh đại diện', b'remthumb')
        ],
        [
            Button.url('🆘 Báo lỗi', 'https://t.me/team_spy_pro')
        ]
    ]
    await gf.send_message(chat_id, MESS, buttons=buttons)

# Xử lý các sự kiện callback từ nút inline
@gf.on(events.CallbackQuery)
async def callback_query_handler(event):
    user_id = event.sender_id
    
    callback_actions = {
        b'setchat': {
            'type': 'setchat',
            'message': """Gửi ID của nhóm (có tiền tố -100): 
__👉 **Lưu ý:** nếu bạn dùng bot riêng, bot đó cần là admin nhóm. Nếu không thì bot này phải là admin.__
👉 __Nếu muốn đăng lên nhóm có chủ đề, dùng định dạng **-100IDNHOM/IDCHUDE** ví dụ: **-1004783898/12**__"""
        },
        b'setrename': {
            'type': 'setrename',
            'message': 'Gửi thẻ đổi tên:'
        },
        b'setcaption': {
            'type': 'setcaption',
            'message': 'Gửi chú thích (caption):'
        },
        b'setreplacement': {
            'type': 'setreplacement',
            'message': "Gửi từ cần thay và từ thay thế theo định dạng: 'TỪ' 'TUTHAYTHE'"
        },
        b'addsession': {
            'type': 'addsession',
            'message': 'Gửi chuỗi phiên Pyrogram V2:'
        },
        b'delete': {
            'type': 'deleteword',
            'message': 'Gửi các từ (cách nhau bởi dấu cách) để xóa khỏi tên/chú thích...'
        },
        b'setthumb': {
            'type': 'setthumb',
            'message': 'Gửi ảnh bạn muốn đặt làm thumbnail.'
        }
    }

    if event.data in callback_actions:
        action = callback_actions[event.data]
        await start_conversation(event, user_id, action['type'], action['message'])
    elif event.data == b'logout':
        result = await users_collection.update_one(
            {'user_id': user_id},
            {'$unset': {'session_string': ''}}
        )
        if result.modified_count > 0:
            await event.respond('✅ Đã đăng xuất và xóa phiên thành công.')
        else:
            await event.respond('❌ Bạn chưa đăng nhập.')
    elif event.data == b'reset':
        try:
            await users_collection.update_one(
                {'user_id': user_id},
                {'$unset': {
                    'delete_words': '',
                    'replacement_words': '',
                    'rename_tag': '',
                    'caption': '',
                    'chat_id': ''
                }}
            )
            thumbnail_path = f'{user_id}.jpg'
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
            await event.respond('✅ Đã đặt lại tất cả cài đặt. Gõ /logout để đăng xuất nếu muốn.')
        except Exception as e:
            await event.respond(f'❌ Lỗi khi đặt lại: {e}')
    elif event.data == b'remthumb':
        try:
            os.remove(f'{user_id}.jpg')
            await event.respond('✅ Đã xóa ảnh đại diện!')
        except FileNotFoundError:
            await event.respond('❌ Không tìm thấy ảnh đại diện để xóa.')

# Bắt đầu cuộc hội thoại với người dùng để nhận dữ liệu
async def start_conversation(event, user_id, conv_type, prompt_message):
    if user_id in active_conversations:
        await event.respond('⛔ Cuộc hội thoại trước bị hủy. Bắt đầu mới.')

    msg = await event.respond(f'{prompt_message}\n\n(Gõ /cancel để hủy thao tác này)')
    active_conversations[user_id] = {'type': conv_type, 'message_id': msg.id}

# Hủy thao tác hiện tại
@gf.on(events.NewMessage(pattern='/cancel'))
async def cancel_conversation(event):
    user_id = event.sender_id
    if user_id in active_conversations:
        await event.respond('✅ Đã hủy thao tác.')
        del active_conversations[user_id]

# Xử lý đầu vào từ người dùng trong cuộc hội thoại
@gf.on(events.NewMessage())
async def handle_conversation_input(event):
    user_id = event.sender_id
    if user_id not in active_conversations or event.message.text.startswith('/'):
        return

    conv_type = active_conversations[user_id]['type']

    handlers = {
        'setchat': handle_setchat,
        'setrename': handle_setrename,
        'setcaption': handle_setcaption,
        'setreplacement': handle_setreplacement,
        'addsession': handle_addsession,
        'deleteword': handle_deleteword,
        'setthumb': handle_setthumb
    }

    if conv_type in handlers:
        await handlers[conv_type](event, user_id)

    if user_id in active_conversations:
        del active_conversations[user_id]

# Xử lý từng loại dữ liệu
async def handle_setchat(event, user_id):
    try:
        chat_id = event.text.strip()
        await save_user_data(user_id, 'chat_id', chat_id)
        await event.respond('✅ Đã lưu Chat ID thành công!')
    except Exception as e:
        await event.respond(f'❌ Lỗi: {e}')

async def handle_setrename(event, user_id):
    rename_tag = event.text.strip()
    await save_user_data(user_id, 'rename_tag', rename_tag)
    await event.respond(f'✅ Đã thiết lập thẻ đổi tên: {rename_tag}')

async def handle_setcaption(event, user_id):
    caption = event.text
    await save_user_data(user_id, 'caption', caption)
    await event.respond('✅ Đã thiết lập caption thành công!')

async def handle_setreplacement(event, user_id):
    match = re.match("'(.+)' '(.+)'", event.text)
    if not match:
        await event.respond("❌ Sai định dạng. Ví dụ đúng: 'TỪ' 'TUTHAYTHE'")
    else:
        word, replace_word = match.groups()
        delete_words = await get_user_data_key(user_id, 'delete_words', [])
        if word in delete_words:
            await event.respond(f"❌ Từ '{word}' đã nằm trong danh sách xóa.")
        else:
            replacements = await get_user_data_key(user_id, 'replacement_words', {})
            replacements[word] = replace_word
            await save_user_data(user_id, 'replacement_words', replacements)
            await event.respond(f"✅ Đã thay thế: '{word}' ➜ '{replace_word}'")

async def handle_addsession(event, user_id):
    session_string = event.text.strip()
    await save_user_data(user_id, 'session_string', session_string)
    await event.respond('✅ Đã lưu chuỗi phiên thành công!')

async def handle_deleteword(event, user_id):
    words_to_delete = event.message.text.split()
    delete_words = await get_user_data_key(user_id, 'delete_words', [])
    delete_words = list(set(delete_words + words_to_delete))
    await save_user_data(user_id, 'delete_words', delete_words)
    await event.respond(f"✅ Đã thêm vào danh sách xóa: {', '.join(words_to_delete)}")

async def handle_setthumb(event, user_id):
    if event.photo:
        temp_path = await event.download_media()
        try:
            thumb_path = f'{user_id}.jpg'
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
            os.rename(temp_path, thumb_path)
            await event.respond('✅ Đã lưu ảnh đại diện!')
        except Exception as e:
            await event.respond(f'❌ Lỗi khi lưu ảnh đại diện: {e}')
    else:
        await event.respond('❌ Vui lòng gửi ảnh. Đã hủy thao tác.')

# Tạo tên ngẫu nhiên (không sử dụng trong đoạn này nhưng có thể dùng trong rename)
def generate_random_name(length=7):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# Đổi tên tập tin theo quy tắc người dùng đặt
async def rename_file(file, sender, edit):
    try:
        delete_words = await get_user_data_key(sender, 'delete_words', [])
        custom_rename_tag = await get_user_data_key(sender, 'rename_tag', '')
        replacements = await get_user_data_key(sender, 'replacement_words', {})

        last_dot_index = str(file).rfind('.')
        if last_dot_index != -1 and last_dot_index != 0:
            ggn_ext = str(file)[last_dot_index + 1:]
            if ggn_ext.isalpha() and len(ggn_ext) <= 9:
                if ggn_ext.lower() in VIDEO_EXTENSIONS:
                    original_file_name = str(file)[:last_dot_index]
                    file_extension = 'mp4'
                else:
                    original_file_name = str(file)[:last_dot_index]
                    file_extension = ggn_ext
            else:
                original_file_name = str(file)[:last_dot_index]
                file_extension = 'mp4'
        else:
            original_file_name = str(file)
            file_extension = 'mp4'

        for word in delete_words:
            original_file_name = original_file_name.replace(word, '')

        for word, replace_word in replacements.items():
            original_file_name = original_file_name.replace(word, replace_word)

        new_file_name = f'{original_file_name} {custom_rename_tag}.{file_extension}'

        os.rename(file, new_file_name)
        return new_file_name
    except Exception as e:
        print(f"Lỗi đổi tên: {e}")
        return file
