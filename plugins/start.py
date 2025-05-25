# Copyright (c) 2025 devgagan : https://github.com/devgaganin.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.

from shared_client import app
from pyrogram import filters
from pyrogram.errors import UserNotParticipant
from pyrogram.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from config import LOG_GROUP, OWNER_ID, FORCE_SUB

async def subscribe(app, message):
    if FORCE_SUB:
        try:
          user = await app.get_chat_member(FORCE_SUB, message.from_user.id)
          if str(user.status) == "ChatMemberStatus.BANNED":
              await message.reply_text("Bạn đã bị chặn. Vui lòng liên hệ Team SKY")
              return 1
        except UserNotParticipant:
            link = await app.export_chat_invite_link(FORCE_SUB)
            caption = f"Vui lòng tham gia kênh của chúng tôi để sử dụng bot."
            await message.reply_photo(photo="https://graph.org/file/d44f024a08ded19452152.jpg",caption=caption, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Tham gia ngay...", url=f"{link}")]]))
            return 1
        except Exception as ggn:
            await message.reply_text(f"Đã xảy ra lỗi. Vui lòng liên hệ quản trị viên !!!{ggn}")
            return 1 
     
@app.on_message(filters.command("set"))
async def set(_, message):
    if message.from_user.id not in OWNER_ID:
        await message.reply("Bạn không có quyền sử dụng lệnh này.")
        return
     
    await app.set_bot_commands([
        BotCommand("start", "🚀 Khởi động bot"),
        BotCommand("batch", "🫠 Trích xuất hàng loạt"),
        BotCommand("login", "🔑 Đăng nhập bot"),
        BotCommand("setbot", "🧸 Thêm bot để xử lý tệp"),
        BotCommand("logout", "🚪 Đăng xuất khỏi bot"),
        BotCommand("adl", "👻 Tải xuống âm thanh từ 30+ trang web"),
        BotCommand("dl", "💀 Tải video từ 30+ trang web"),
        BotCommand("status", "⟳ Làm mới trạng thái "),
        BotCommand("transfer", "💘 Tặng gói cao cấp cho người khác"),
        BotCommand("add", "➕ Thêm người dùng vào gói cao cấp"),
        BotCommand("rem", "➖ Xóa khỏi gói cao cấp"),
        BotCommand("rembot", "🤨 Xóa bot tùy chỉnh của bạn"),
        BotCommand("settings", "⚙️ Cài đặt bot"),
        BotCommand("plan", "🗓️ Xem thông tin gói"),
        BotCommand("terms", "🥺 Điều khoản và điều kiện"),
        BotCommand("help", "❓ Hướng dẫn sử dụng"),
        BotCommand("cancel", "🚫 Hủy quá trình đăng nhập/batch/cài đặt"),
        BotCommand("stop", "🚫 Hủy quá trình batch")
 
    await message.reply("✅ Cài Đặt Lệnh Thành Công!")
 
# Danh sách trang hướng dẫn sử dụng bot
    (
        "📝 **Tổng quan lệnh bot (1/2)**:\n\n"
        "1. **/add userID**\n"
        "> Thêm người dùng vào premium (chỉ chủ sở hữu)\n\n"
        "2. **/rem userID**\n"
        "> Xóa người dùng khỏi premium (chỉ chủ sở hữu)\n\n"
        "3. **/transfer userID**\n"
        "> Chuyển premium cho người khác (chỉ premium)\n\n"
        "4. **/get**\n"
        "> Lấy danh sách ID người dùng (chỉ chủ sở hữu)\n\n"
        "5. **/lock**\n"
        "> Khóa kênh không cho trích xuất (chỉ chủ sở hữu)\n\n"
        "6. **/dl link**\n"
        "> Tải video (không khả dụng ở v3)\n\n"
        "7. **/adl link**\n"
        "> Tải âm thanh (không khả dụng ở v3)\n\n"
        "8. **/login**\n"
        "> Đăng nhập để truy cập kênh riêng tư\n\n"
        "9. **/batch**\n"
        "> Trích xuất hàng loạt (sau khi đăng nhập)\n\n"
    ),
    (
        "📝 **Tổng quan lệnh bot (2/2)**:\n\n"
        "10. **/logout**\n"
        "> Đăng xuất khỏi bot\n\n"
        "11. **/stats**\n"
        "> Thống kê hoạt động bot\n\n"
        "12. **/plan**\n"
        "> Kiểm tra gói premium\n\n"
        "13. **/speedtest**\n"
        "> Kiểm tra tốc độ máy chủ (không khả dụng ở v3)\n\n"
        "14. **/terms**\n"
        "> Điều khoản và điều kiện\n\n"
        "15. **/cancel**\n"
        "> Hủy tiến trình đang chạy\n\n"
        "16. **/myplan**\n"
        "> Xem chi tiết gói của bạn\n\n"
        "17. **/session**\n"
        "> Tạo phiên Pyrogram V2\n\n"
        "18. **/settings**\n"
        "> 1. SETCHATID: Đăng tải trực tiếp vào kênh, nhóm hoặc DM người dùng (dùng -100[chatID])\n"
        "> 2. SETRENAME: Thêm tag tùy chỉnh hoặc tên kênh\n"
        "> 3. CAPTION: Thêm chú thích tùy chỉnh\n"
        "> 4. REPLACEWORDS: Thay thế từ khóa đã bị xóa\n"
        "> 5. RESET: Đặt lại tất cả về mặc định\n\n"
        "> Bạn có thể thiết lập ảnh đại diện, watermark PDF/video, đăng nhập bằng session, v.v. trong mục settings\n\n"
        "**__Tài Trợ Bởi TEAM SKY__**"
    )
]
 
 # Hàm gửi nội dung trợ giúp hoặc chuyển trang trợ giúp
async def send_or_edit_help_page(_, message, page_number):
    if page_number < 0 or page_number >= len(help_pages):
        return
 
     
    prev_button = InlineKeyboardButton("◀️ Quay lại", callback_data=f"help_prev_{page_number}")
    next_button = InlineKeyboardButton("Tiếp theo ▶️", callback_data=f"help_next_{page_number}")
 
     
    buttons = []
    if page_number > 0:
        buttons.append(prev_button)
    if page_number < len(help_pages) - 1:
        buttons.append(next_button)
 
     
    keyboard = InlineKeyboardMarkup([buttons])
 
     
    await message.delete()
 
     
    await message.reply(
        help_pages[page_number],
        reply_markup=keyboard
    )
 
 
@app.on_message(filters.command("help"))
async def help(client, message):
    join = await subscribe(client, message)
    if join == 1:
        return
     
    await send_or_edit_help_page(client, message, 0)
 
 
@app.on_callback_query(filters.regex(r"help_(prev|next)_(\d+)"))
async def on_help_navigation(client, callback_query):
    action, page_number = callback_query.data.split("_")[1], int(callback_query.data.split("_")[2])
 
    if action == "prev":
        page_number -= 1
    elif action == "next":
        page_number += 1

    await send_or_edit_help_page(client, callback_query.message, page_number)
     
    await callback_query.answer()

 
@app.on_message(filters.command("terms") & filters.private)
async def terms(client, message):
     terms_text = (
        "> 📜 **Điều khoản và điều kiện** 📜\n\n"
        "✨ Chúng tôi không chịu trách nhiệm cho hành vi người dùng và không khuyến khích nội dung vi phạm bản quyền. Người dùng chịu trách nhiệm hoàn toàn.\n"
        "✨ Khi mua, chúng tôi không đảm bảo thời gian hoạt động hoặc hiệu lực gói. __Việc cấp quyền hay chặn người dùng hoàn toàn do chúng tôi quyết định.__\n"
        "✨ Thanh toán **__không đảm bảo__** sẽ được cấp quyền dùng lệnh /batch. Việc cấp quyền phụ thuộc vào quyết định và tâm trạng của chúng tôi.\n"
    )
     
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📋 Xem gói cao cấp", callback_data="see_plan")],
            [InlineKeyboardButton("💬 Liên hệ ngay", url="https://t.me/NAME_APEX")],
        ]
    )
    await message.reply_text(terms_text, reply_markup=buttons)
 
 
@app.on_message(filters.command("plan") & filters.private)
async def plan(client, message):
     plan_text = (
        "> 💰 **Giá Premium**:\n\n Gói mặc định VIP_1 300.000VND và VIP_2 500.000VND sử dụng trong 30 ngày. Cập nhật thông tin thanh toán vui lòng liên hệ admin **__@Name_Apex__** .\n"
        "📥 **Giới hạn tải**: VIP_1 20 bài viết + VIP_2 50 bài viết bằng một lệnh /batch tùy chỉnh số lượng tải.\n"
        "🛑 **Batch**: Có hai chế độ /bulk và /batch.\n"
        "   - Bạn nên chờ quá trình tự hủy trước khi tiếp tục tải hoặc đăng.\n\n"
        "📜 **Điều khoản**: Xem chi tiết bằng cách gửi lệnh /terms.\n"
    )
     
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📜 Xem Điều Khoản", callback_data="see_terms")],
            [InlineKeyboardButton("💬 Liên Hệ Ngay", url="https://t.me/Name_Apex")],
        ]
    )
    await message.reply_text(plan_text, reply_markup=buttons)
 
 
@app.on_callback_query(filters.regex("see_plan"))
async def see_plan(client, callback_query):
    plan_text = (
        "> 💰**Giá Premium**:\n\n Gói mặc định VIP_1 300.000VND và VIP_2 500.000VND sử dụng trong 30 ngày. Cập nhật thông tin thanh toán vui lòng liên hệ admin **__@Name_Apex__** .\n"
        "📥 **Giới hạn tải**: VIP_1 20 bài viết + VIP_2 50 bài viết bằng một lệnh /batch tùy chỉnh số lượng tải.\n"
        "🛑 **Batch**: Có hai chế độ /bulk và /batch.\n"
        "   - Bạn nên chờ quá trình tự hủy trước khi tiếp tục tải hoặc đăng.\n\n"
        "📜 **Điều khoản**: Xem chi tiết bằng cách gửi lệnh /terms 👇.\n"
    )
     
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📜 Xem Điều Khoản", callback_data="see_terms")],
            [InlineKeyboardButton("💬 Liên Hệ Ngay", url="https://t.me/Name_Apex")],
        ]
    )
    await callback_query.message.edit_text(plan_text, reply_markup=buttons)
 
 
@app.on_callback_query(filters.regex("see_terms"))
async def see_terms(client, callback_query):
    terms_text = (
          "> 📜 **Điều khoản và điều kiện** 📜\n\n"
        "✨ Chúng tôi không chịu trách nhiệm cho hành vi người dùng và không khuyến khích nội dung vi phạm bản quyền. Người dùng chịu trách nhiệm hoàn toàn.\n"
        "✨ Khi mua, chúng tôi không đảm bảo thời gian hoạt động hoặc hiệu lực gói. __Việc cấp quyền hay chặn người dùng hoàn toàn do chúng tôi quyết định.__\n"
        "✨ Thanh toán **__không đảm bảo__** sẽ được cấp quyền dùng lệnh /batch. Việc cấp quyền phụ thuộc vào quyết định và tâm trạng của chúng tôi.\n"
    )
     
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📋 Xem Điều Khoản", callback_data="see_plan")],
            [InlineKeyboardButton("💬 Liên Hệ Ngay", url="https://t.me/Name_Apex")],
        ]
    )
    await callback_query.message.edit_text(terms_text, reply_markup=buttons)
 
 
