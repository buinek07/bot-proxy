import telebot
from telebot import types
from pymongo import MongoClient
from flask import Flask
import threading
import os

# --- 1. KHỞI TẠO WEB SERVER (Để Koyeb không bị lỗi) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    app.run(host='0.0.0.0', port=8000)

# Chạy server ở một luồng riêng để không làm dừng Bot
threading.Thread(target=run_web).start()

# --- 2. CẤU HÌNH THÔNG TIN (Đã điền sẵn cho bạn) ---
TOKEN = '8371917325:AAE4ftu8HJkA5CyNd5On69r39WS10Osl1JQ'
MONGO_URI = 'mongodb+srv://buinek:XH1S550j3EzKpVFg@bottlee.qnaas3k.mongodb.net/?appName=bottlee'

# Cấu hình ngân hàng nạp tiền
BANK_ID = 'MB'           # Ngân hàng Quân Đội (Bạn có thể đổi sang VCB, ICB...)
STK = '123456789'        # <--- HÃY THAY SỐ TÀI KHOẢN THẬT CỦA BẠN VÀO ĐÂY

# Khởi tạo Bot và Database
bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI)
db = client.bot_proxy_db
users_col = db.users

# --- 3. GIAO DIỆN VÀ MENU ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('👤 Tài khoản', '🛒 Mua hàng', '💳 Nạp tiền', '📋 Đơn hàng', '📞 Admin')
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    # Kiểm tra và tạo tài khoản mới nếu chưa có trong Database
    if not users_col.find_one({"user_id": user_id}):
        users_col.insert_one({"user_id": user_id, "balance": 0})
    
    bot.send_message(
        message.chat.id, 
        "🤖 **Bot Proxy đã sẵn sàng!**\n\nChào mừng bạn đến với hệ thống cung cấp Proxy tự động.", 
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text == '💳 Nạp tiền')
def recharge(message):
    user_id = message.from_user.id
    # Tạo link ảnh QR từ VietQR
    qr_url = f"https://img.vietqr.io/image/{BANK_ID}-{STK}-compact2.jpg?amount=50000&addInfo=NAP{user_id}"
    
    caption = (f"🏦 **THÔNG TIN CHUYỂN KHOẢN**\n\n"
               f"🏧 Ngân hàng: **{BANK_ID}**\n"
               f"🔢 Số tài khoản: `{STK}`\n"
               f"📝 Nội dung: `NAP {user_id}`\n\n"
               f"⚠️ **Lưu ý:** Bạn phải ghi đúng nội dung để được cộng tiền tự động!")
    
    bot.send_photo(message.chat.id, qr_url, caption=caption, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == '🛒 Mua hàng')
def shop(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌐 Proxy Viettel (5k/24h)", callback_data="buy_vte"))
    bot.send_message(message.chat.id, "Vui lòng chọn loại Proxy muốn mua:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "buy_vte")
def confirm_purchase(call):
    text = "⚠️ **XÁC NHẬN THANH TOÁN**\n\n📦 Sản phẩm: Proxy Viettel\n💰 Giá: 5,000đ\n⏳ Thời hạn: 24 Giờ"
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Thanh toán", callback_data="pay_now"),
        types.InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel")
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel(call):
    bot.edit_message_text("❌ Giao dịch đã bị hủy.", call.message.chat.id, call.message.message_id)

# --- 4. CHẠY BOT ---
print("Bot is starting...")
bot.polling(none_stop=True)
