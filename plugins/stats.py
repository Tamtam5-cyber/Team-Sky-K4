# Bản quyền (c) 2025 devgagan : https://github.com/devgaganin.  
# Được cấp phép theo giấy phép GNU General Public License v3.0.  
# Xem tệp LICENSE trong thư mục gốc của repo để biết toàn bộ văn bản giấy phép.

from datetime import timedelta, datetime
from shared_client import client as bot_client
from telethon import events
from utils.func import (
    get_premium_details,        # Lấy thông tin Premium của người dùng
    is_private_chat,           # Kiểm tra xem có phải trò chuyện riêng không
    get_display_name,          # Lấy tên hiển thị người dùng
    get_user_data,             # Lấy thông tin người dùng
    premium_users_collection,  # Truy cập cơ sở dữ liệu người dùng Premium
    is_premium_user            # Kiểm tra xem người dùng có Premium không
)
from config import OWNER_ID    # ID của admin (chủ bot)

# Cấu hình ghi log
import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('teamspy')

# Xử lý lệnh /status - kiểm tra trạng thái tài khoản
@bot_client.on(events.NewMessage(pattern='/status'))
async def status_handler(event):
    if not await is_private_chat(event):
        await event.respond("Lệnh này chỉ dùng được trong tin nhắn riêng vì lý do bảo mật.")
        return

    user_id = event.sender_id
    user_data = await get_user_data(user_id)

    # Kiểm tra trạng thái đăng nhập & bot riêng
    session_active = "session_string" in user_data if user_data else False
    bot_active = "bot_token" in user_data if user_data else False

    # Kiểm tra trạng thái premium
    premium_status = "❌ Không phải thành viên premium"
    premium_details = await get_premium_details(user_id)
    if premium_details:
        expiry_utc = premium_details["subscription_end"]
        expiry_ist = expiry_utc + timedelta(hours=5, minutes=30)
        formatted_expiry = expiry_ist.strftime("%d-%b-%Y %I:%M:%S %p")
        premium_status = f"✅ Premium đến {formatted_expiry} (IST)"

    await event.respond(
        "**Trạng thái tài khoản của bạn:**\n\n"
        f"**Đăng nhập:** {'✅ Đã đăng nhập' if session_active else '❌ Chưa đăng nhập'}\n"
        f"**Premium:** {premium_status}"
    )

# Xử lý lệnh /transfer - chuyển quyền premium sang người khác
@bot_client.on(events.NewMessage(pattern='/transfer'))
async def transfer_premium_handler(event):
    if not await is_private_chat(event):
        await event.respond("Lệnh này chỉ dùng trong tin nhắn riêng.")
        return

    user_id = event.sender_id
    sender = await event.get_sender()
    sender_name = get_display_name(sender)

    # Kiểm tra xem người gửi có phải premium không
    if not await is_premium_user(user_id):
        await event.respond("❌ Bạn không có Premium để chuyển.")
        return

    args = event.text.split()
    if len(args) != 2:
        await event.respond("Cách dùng: /transfer user_id\nVí dụ: /transfer 123456789")
        return

    try:
        target_user_id = int(args[1])
    except ValueError:
        await event.respond("❌ user_id không hợp lệ. Hãy nhập số nguyên hợp lệ.")
        return

    if target_user_id == user_id:
        await event.respond("❌ Bạn không thể chuyển Premium cho chính mình.")
        return

    if await is_premium_user(target_user_id):
        await event.respond("❌ Người nhận đã có Premium.")
        return

    try:
        premium_details = await get_premium_details(user_id)
        if not premium_details:
            await event.respond("❌ Không lấy được thông tin Premium.")
            return

        target_name = 'Không rõ'
        try:
            target_entity = await bot_client.get_entity(target_user_id)
            target_name = get_display_name(target_entity)
        except Exception as e:
            logger.warning(f"Không lấy được tên người nhận: {e}")

        now = datetime.now()
        expiry_date = premium_details['subscription_end']

        # Cập nhật dữ liệu premium cho người nhận
        await premium_users_collection.update_one(
            {'user_id': target_user_id},
            {'$set': {
                'user_id': target_user_id,
                'subscription_start': now,
                'subscription_end': expiry_date,
                'expireAt': expiry_date,
                'transferred_from': user_id,
                'transferred_from_name': sender_name
            }},
            upsert=True
        )

        # Xoá premium khỏi người gửi
        await premium_users_collection.delete_one({'user_id': user_id})

        expiry_ist = expiry_date + timedelta(hours=5, minutes=30)
        formatted_expiry = expiry_ist.strftime("%d-%b-%Y %I:%M:%S %p")

        await event.respond(
            f"✅ Đã chuyển Premium thành công cho {target_name} ({target_user_id}). Premium của bạn đã bị gỡ bỏ."
        )

        try:
            await bot_client.send_message(
                target_user_id,
                f"🎁 Bạn đã nhận được Premium từ {sender_name} ({user_id}). Premium có hiệu lực đến {formatted_expiry} (IST)."
            )
        except Exception as e:
            logger.error(f"Không thể gửi tin nhắn cho {target_user_id}: {e}")

        try:
            # Gửi thông báo cho admin
            owner_id = (
                int(OWNER_ID) if isinstance(OWNER_ID, str)
                else OWNER_ID[0] if isinstance(OWNER_ID, list)
                else OWNER_ID
            )
            await bot_client.send_message(
                owner_id,
                f"♻️ Chuyển Premium: {sender_name} ({user_id}) đã chuyển Premium cho {target_name} ({target_user_id}). Hạn: {formatted_expiry}"
            )
        except Exception as e:
            logger.error(f"Không thể thông báo admin: {e}")
    except Exception as e:
        logger.error(f"Lỗi chuyển premium: {e}")
        await event.respond(f"❌ Lỗi khi chuyển Premium: {str(e)}")

# Xử lý lệnh /rem - chỉ admin có thể gỡ premium của người khác
@bot_client.on(events.NewMessage(pattern='/rem'))
async def remove_premium_handler(event):
    user_id = event.sender_id

    if not await is_private_chat(event):
        return

    if user_id not in OWNER_ID:
        return

    args = event.text.split()
    if len(args) != 2:
        await event.respond("Cách dùng: /rem user_id\nVí dụ: /rem 123456789")
        return

    try:
        target_user_id = int(args[1])
    except ValueError:
        await event.respond("❌ user_id không hợp lệ. Nhập số nguyên.")
        return

    if not await is_premium_user(target_user_id):
        await event.respond(f"❌ Người dùng {target_user_id} không có Premium.")
        return

    try:
        target_name = 'Không rõ'
        try:
            target_entity = await bot_client.get_entity(target_user_id)
            target_name = get_display_name(target_entity)
        except Exception as e:
            logger.warning(f"Không lấy được tên người dùng: {e}")

        result = await premium_users_collection.delete_one({'user_id': target_user_id})
        if result.deleted_count > 0:
            await event.respond(
                f"✅ Đã gỡ Premium khỏi {target_name} ({target_user_id})."
            )
            try:
                await bot_client.send_message(
                    target_user_id,
                    "⚠️ Premium của bạn đã bị quản trị viên gỡ bỏ."
                )
            except Exception as e:
                logger.error(f"Không thể gửi tin nhắn đến {target_user_id}: {e}")
        else:
            await event.respond(f"❌ Không thể gỡ Premium khỏi {target_user_id}.")
    except Exception as e:
        logger.error(f"Lỗi khi gỡ Premium: {e}")
        await event.respond(f"❌ Lỗi khi gỡ Premium: {str(e)}")
