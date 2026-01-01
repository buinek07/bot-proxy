import os, telebot, requests, random, time, threading
from flask import Flask
from pymongo import MongoClient
from datetime import datetime
from telebot import types

# --- 1. CẤU HÌNH HỆ THỐNG (Lấy từ Koyeb) ---
TOKEN = os.getenv('BOT_TOKEN') # Lấy Token từ biến môi trường trên Koyeb
MONGO_URI = os.getenv('MONGO_URI') # Lấy Mongo từ biến môi trường trên Koyeb
API_KEY_PROXY = 'AvqAKLwQAuDDSNyWtVQUsv' # API Proxy của bạn
ADMIN_ID = 5519768222 # ID Admin của bạn [cite: 2025-12-30]
PROXY_PRICE = 1500

bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI)
db = client.bot_proxy_db
users_col, orders_col = db.users, db.orders

app = Flask('')
@app.route('/')
def home(): return "Bot is Healthy!"

# --- 2. MENU CHÍNH ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('👤 Tài khoản', '🛒 Mua hàng', '💳 Nạp tiền', '📋 Đơn hàng', '📞 Admin')
    return markup

# --- 3. CỬA HÀNG DỊCH VỤ (NÚT DÀI DỌC) ---
@bot.message_handler(func=lambda m: m.text == '🛒 Mua hàng')
def shop(message):
    # Ép row_width=1 để các nút nằm dọc và dài ra
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🌐 PROXY SIÊU TỐC (1.5k)", callback_data="proxy_menu"),
        types.InlineKeyboardButton("📲 THUÊ OTP GIÁ RẺ (2.5k)", callback_data="buy_otp_confirm"),
        types.InlineKeyboardButton("🔗 LINK VƯỢT GIÁ RẺ (10k)", callback_data="link_vuot_intro")
    ) # Đã thêm nút Link vượt
    
    shop_text = (
        "🛒 **CỬA HÀNG DỊCH VỤ**\n\n"
        "Vui lòng chọn loại dịch vụ bạn muốn trải nghiệm bên dưới:\n\n"
        "🔹 **Proxy**: Tốc độ cao, hỗ trợ đa mạng.\n"
        "🔹 **Thuê OTP**: Nhận mã nhanh, tự động.\n"
        "🔹 **Link vượt**: Vượt app, lấy key nhanh chóng."
    )
    bot.send_message(message.chat.id, shop_text, reply_markup=markup, parse_mode="Markdown")

# --- 4. LUỒNG LINK VƯỢT ---
@bot.callback_query_handler(func=lambda call: call.data == "link_vuot_intro")
def link_vuot_intro(call):
    text = (
        "🔗 **THÔNG TIN LINK VƯỢT**\n\n"
        "Link vượt app, lấy key không cần tải app.\n"
        "Giá: **10.000 VNĐ / 1 lượt**\n\n"
        "📝 **Vui lòng ghi tên game cần vượt**\n"
        "VD: f168, fly88"
    )
    msg = bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_link_vuot_request)

def process_link_vuot_request(message):
    game_name = message.text
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    bot.send_message(user_id, "⏳ Vui lòng đợi 1-2p để Admin lấy link vượt cho bạn...")
    
    # Gửi yêu cầu về cho Admin [cite: 2025-12-30]
    admin_msg = (
        f"🚀 **YÊU CẦU LINK VƯỢT MỚI**\n"
        f"👤 Khách hàng: {user_name} (`{user_id}`)\n"
        f"🎮 Game: **{game_name}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👉 Trả lời bằng: `/sendlink {user_id} [Link]`"
    )
    bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")

@bot.message_handler(commands=['sendlink'])
def admin_send_link(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split(maxsplit=2)
        target_id = int(parts[1])
        link_content = parts[2]
        bot.send_message(target_id, f"✅ **Link vượt của bạn đây:**\n\n`{link_content}`", parse_mode="Markdown")
        bot.send_message(ADMIN_ID, f"✅ Đã gửi link cho `{target_id}`")
    except:
        bot.send_message(ADMIN_ID, "❌ Sai cú pháp: `/sendlink [ID] [Link]`")

# --- 5. LUỒNG PROXY (GIỮ NGUYÊN) ---
@bot.callback_query_handler(func=lambda call: call.data == "proxy_menu")
def proxy_carriers(call):
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("🌐 Viettel", callback_data="qty_Viettel"),
        types.InlineKeyboardButton("🌐 VNPT", callback_data="qty_VNPT"),
        types.InlineKeyboardButton("🌐 FPT", callback_data="qty_FPT")
    )
    bot.edit_message_text("✨ **CHỌN NHÀ MẠNG PROXY**", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

# (Các hàm xử lý Proxy khác giữ nguyên như cũ...)

# --- KHỞI CHẠY ---
if __name__ == "__main__":
    # Chạy Flask để Koyeb báo Healthy
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8000)).start()
    bot.polling(none_stop=True)
