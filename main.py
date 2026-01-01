import os, telebot, requests, random, time, threading
from flask import Flask
from pymongo import MongoClient
from datetime import datetime
from telebot import types

# --- 1. CẤU HÌNH HỆ THỐNG ---
TOKEN = '8371917325:AAGLIPfishX6fCE6B3OdsEmUMtRAEG9eo6s' # Token mới nhất bạn cung cấp
MONGO_URI = 'mongodb+srv://buinek:XH1S550j3EzKpVFg@bottlee.qnaas3k.mongodb.net/?appName=bottlee'
API_KEY_PROXY = 'AvqAKLwQAuDDSNyWtVQUsv' # API Proxy
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

# --- 3. CỬA HÀNG DỊCH VỤ (GIAO DIỆN NÚT DÀI CHUẨN) ---
@bot.message_handler(func=lambda m: m.text == '🛒 Mua hàng')
def shop(message):
    markup = types.InlineKeyboardMarkup(row_width=1) # Ép nút hiển thị theo chiều dọc, dài và đẹp
    markup.add(
        types.InlineKeyboardButton("🌐 PROXY SIÊU TỐC (1.5k)", callback_data="proxy_menu"),
        types.InlineKeyboardButton("📲 THUÊ OTP GIÁ RẺ (2.5k)", callback_data="buy_otp_confirm"),
        types.InlineKeyboardButton("🔗 LINK VƯỢT GIÁ RẺ (10k)", callback_data="link_vuot_intro")
    ) # Tích hợp nút Link vượt
    
    shop_text = (
        "🛒 **CỬA HÀNG DỊCH VỤ**\n\n"
        "Vui lòng chọn loại dịch vụ bạn muốn trải nghiệm bên dưới:\n\n"
        "🔹 **Proxy**: Tốc độ cao, hỗ trợ Viettel, VNPT, FPT.\n"
        "🔹 **Thuê OTP**: Nhận mã nhanh, hoàn tiền tự động.\n"
        "🔹 **Link vượt**: Vượt app, lấy key không cần tải app."
    )
    bot.send_message(message.chat.id, shop_text, reply_markup=markup, parse_mode="Markdown")

# --- 4. LUỒNG LINK VƯỢT (GỬI THÔNG TIN CHO ADMIN) ---
@bot.callback_query_handler(func=lambda call: call.data == "link_vuot_intro")
def link_vuot_intro(call):
    text = (
        "🔗 **THÔNG TIN LINK VƯỢT**\n\n"
        "Link vượt là link vượt app\n"
        "Ko cần tải app\n"
        "Giá: **10.000 VNĐ / 1 lượt**\n\n"
        "📝 **Vui lòng ghi tên game cần vượt**\n"
        "VD: f168, fly88"
    ) # Nội dung bạn yêu cầu
    msg = bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_link_vuot_request)

def process_link_vuot_request(message):
    game_name = message.text
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    # Phản hồi cho khách
    bot.send_message(user_id, "⏳ Vui lòng đợi 1-2p để lấy link vượt...")
    
    # Gửi thông tin cho Admin xử lý
    admin_msg = (
        f"🚀 **YÊU CẦU LINK VƯỢT MỚI**\n"
        f"👤 Khách hàng: {user_name} (`{user_id}`)\n"
        f"🎮 Tên game: **{game_name}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👉 Trả lời link bằng cú pháp:\n`/sendlink {user_id} [Link_vượt]`"
    )
    bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")

@bot.message_handler(commands=['sendlink'])
def admin_send_link(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split(maxsplit=2)
        target_id = int(parts[1])
        link_content = parts[2]
        
        # Gửi link cho khách
        bot.send_message(target_id, f"✅ **Link vượt của bạn đã sẵn sàng:**\n\n`{link_content}`", parse_mode="Markdown")
        bot.send_message(ADMIN_ID, f"✅ Đã gửi link thành công cho khách `{target_id}`")
    except:
        bot.send_message(ADMIN_ID, "❌ Sai cú pháp. VD: `/sendlink 123456 https://link.com`", parse_mode="Markdown")

# --- 5. LUỒNG MUA PROXY (CHỌN MẠNG -> SỐ LƯỢNG -> ĐẨY HÀNG) ---
@bot.callback_query_handler(func=lambda call: call.data == "proxy_menu")
def proxy_carriers(call):
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("🌐 Viettel", callback_data="qty_Viettel"),
        types.InlineKeyboardButton("🌐 VNPT", callback_data="qty_VNPT"),
        types.InlineKeyboardButton("🌐 FPT", callback_data="qty_FPT")
    )
    bot.edit_message_text("✨ **CHỌN NHÀ MẠNG PROXY**\n\nVui lòng chọn nhà mạng muốn mua (Đồng giá 1.500đ):", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("qty_"))
def ask_quantity(call):
    carrier = call.data.replace("qty_", "")
    msg = bot.edit_message_text(
        f"🔢 **NHẬP SỐ LƯỢNG MUA**\n\n"
        f"🌐 Nhà mạng: **{carrier}**\n"
        f"👉 Vui lòng nhập số lượng muốn mua (từ **1** đến **50**):",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown"
    ) # Nhập số lượng 1-50
    bot.register_next_step_handler(msg, process_proxy_confirm, carrier)

def process_proxy_confirm(message, carrier):
    if not message.text.isdigit() or not (1 <= int(message.text) <= 50):
        bot.send_message(message.chat.id, "❌ Lỗi: Vui lòng nhập số lượng từ 1 đến 50.")
        return
    
    qty = int(message.text)
    total = qty * PROXY_PRICE
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Xác nhận thanh toán", callback_data=f"pay_proxy_{carrier}_{qty}"),
               types.InlineKeyboardButton("❌ Hủy", callback_data="proxy_menu"))

    confirm_text = (
        f"📝 **XÁC NHẬN ĐƠN HÀNG**\n\n"
        f"🔹 Dịch vụ: **Proxy {carrier}**\n"
        f"🔢 Số lượng: `{qty}`\n"
        f"💰 Tổng tiền: `{total:,} VNĐ`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👉 Nhấn xác nhận để thanh toán."
    )
    bot.send_message(message.chat.id, confirm_text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_proxy_"))
def finalize_proxy(call):
    _, _, carrier, qty = call.data.split('_')
    qty, total = int(qty), int(qty) * PROXY_PRICE
    u = users_col.find_one({"user_id": call.from_user.id})

    if not u or u.get('balance', 0) < total:
        bot.answer_callback_query(call.id, "❌ Số dư không đủ!", show_alert=True)
        return

    bot.edit_message_text(f"⏳ Đang khởi tạo `{qty}` Proxy {carrier}...", call.message.chat.id, call.message.message_id)
    
    # Gọi API Proxy.vn
    api_url = (f"https://proxy.vn/apiv2/muaproxy.php?"
               f"loaiproxy={carrier}&key={API_KEY_PROXY}&soluong={qty}&ngay=1&type=HTTP&user=random&password=random")
    
    try:
        res = requests.get(api_url, timeout=45).json()
        if res.get('status') == 'success':
            p_info = res.get('data') # Dữ liệu Proxy trả về
            users_col.update_one({"user_id": call.from_user.id}, {"$inc": {"balance": -total, "total_spent": total}})
            orders_col.insert_one({"user_id": call.from_user.id, "type": f"Proxy {carrier} x{qty}", "data": p_info, "date": datetime.now()})
            
            # Đẩy hàng trực tiếp cho khách
            bot.edit_message_text(f"✅ **MUA HÀNG THÀNH CÔNG!**\n\n🎁 **Thông tin Proxy của bạn:**\n`{p_info}`\n\n📌 Có thể xem lại tại mục '📋 Đơn hàng'.", 
                                  call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text(f"❌ Lỗi API: {res.get('message')}", call.message.chat.id, call.message.message_id)
    except:
        bot.edit_message_text("❌ Lỗi: Không thể kết nối tới server Proxy. Vui lòng thử lại!", call.message.chat.id, call.message.message_id)

# --- KHỞI CHẠY ---
if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8000)).start()
    bot.polling(none_stop=True)
