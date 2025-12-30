import telebot
from telebot import types
from pymongo import MongoClient
from flask import Flask
import threading
import os

# --- WEB SERVER CHO KOYEB (Để báo trạng thái Healthy) ---
app = Flask('')
@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    app.run(host='0.0.0.0', port=8000)

threading.Thread(target=run_web).start()

# --- CẤU HÌNH THÔNG TIN CỦA BẠN ---
TOKEN = '8371917325:AAE4ftu8HJkA5CyNd5On69r39WS10Osl1JQ'
# Chuỗi kết nối MongoDB chuẩn của bạn
MONGO_URI = 'mongodb+srv://buinek:XH1S550j3EzKpVFg@bottlee.qnaas3k.mongodb.net/?appName=bottlee'

# THAY SỐ TÀI KHOẢN CỦA BẠN VÀO ĐÂY
BANK_ID = 'MB'           # Mã ngân hàng (MB, VCB, ICB...)
STK = '123456789'        # <--- THAY SỐ TÀI KHOẢN THẬT CỦA BẠN VÀO ĐÂY

bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI)
db = client.bot_proxy_db
users_col = db.users

# --- GIAO DIỆN MENU ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('👤 Tài khoản', '🛒 Mua hàng', '💳 Nạp tiền', '📋 Đơn hàng', '📞 Admin')
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not users_col.find_one({"user_id": user_id}):
        users_col.insert_one({"user_id": user_id, "balance": 0})
    bot.send_message(message.chat.id, "🤖 Bot Proxy đã sẵn sàng phục vụ!", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == '💳 Nạp tiền')
def recharge(message):
    user_id = message.from_user.id
    # Tự động tạo mã QR VietQR với nội dung nạp tiền kèm ID người dùng
    qr_url = f"https://img.vietqr.io/image/{BANK_ID}-{STK}-compact2.jpg?amount=50000&addInfo=NAP{user_id}"
    
    caption = (f"🏦 **HỆ THỐNG NẠP TIỀN TỰ ĐỘNG**\n\n"
               f"🏧 Ngân hàng: **{BANK_ID}**\n"
               f"🔢 Số tài khoản: `{STK}`\n"
               f"💰 Số tiền: `50,000đ`\n"
               f"📝 Nội dung chuyển khoản: `NAP {user_id}`\n\n"
               f"⚠️ **Lưu ý:** Bạn phải chuyển đúng nội dung để hệ thống tự động cộng tiền!")
    
    bot.send_photo(message.chat.id, qr_url, caption=caption, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == '🛒 Mua hàng')
def shop(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌐 Proxy Viettel (5k/24h)", callback_data="buy_vte"))
    bot.send_message(message.chat.id, "Vui lòng chọn loại Proxy:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "buy_vte")
def confirm(call):
    text = "⚠️ **XÁC NHẬN THANH TOÁN**\n\n📦 Sản phẩm: Proxy Viettel\n💰 Giá: 5,000đ\n⏳ Thời hạn: 24 Giờ"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Xác nhận", callback_data="final"),
               types.InlineKeyboardButton("❌ Hủy", callback_data="cancel"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel_buy(call):
    bot.edit_message_text("❌ Giao dịch đã bị hủy.", call.message.chat.id, call.message.message_id)

bot.polling(none_stop=True)
