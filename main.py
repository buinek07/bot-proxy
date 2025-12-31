import os
import telebot
from flask import Flask
import threading
from telebot import types

# 1. Cấu hình biến môi trường
TOKEN = os.getenv('TOKEN')
# ID của bạn để bot nhận diện Admin
ADMIN_ID = os.getenv('ADMIN_ID', '5519768222') 

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def index(): 
    return "Bot is Online and Healthy!"

# 2. Hàm tạo Menu nút bấm (Khắc phục lỗi nút không dùng được)
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("👤 Tài khoản")
    btn2 = types.KeyboardButton("🛒 Mua hàng")
    btn3 = types.KeyboardButton("💳 Nạp tiền")
    btn4 = types.KeyboardButton("📝 Đơn hàng")
    markup.add(btn1, btn2, btn3, btn4)
    return markup

# 3. Xử lý lệnh /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    if user_id == ADMIN_ID:
        bot.send_message(message.chat.id, "Chào Admin! Hệ thống đã sẵn sàng nhận lệnh.", reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, "Chào mừng bạn đến với Shop! Chọn chức năng bên dưới:", reply_markup=main_menu())

# 4. Xử lý các câu chào mua hàng và nội dung nút bấm
@bot.message_handler(func=lambda message: True)
def handle_text_buttons(message):
    text = message.text
    
    if text == "👤 Tài khoản":
        bot.reply_to(message, f"📌 Thông tin của bạn:\n- ID: {message.from_user.id}\n- Số dư: 0đ")
        
    elif text == "🛒 Mua hàng":
        # Đây là nơi bạn để lời chào mua hàng của mình
        response = (
            "🛍 **Chào mừng bạn đến với khu vực mua sắm!**\n\n"
            "Hiện tại chúng tôi cung cấp các gói sau:\n"
            "1. Proxy cá nhân - 50k/tháng\n"
            "2. Proxy xoay - 100k/tháng\n"
            "Vui lòng liên hệ Admin để thanh toán."
        )
        bot.send_message(message.chat.id, response, parse_mode="Markdown")
        
    elif text == "💳 Nạp tiền":
        bot.reply_to(message, "💳 Để nạp tiền, vui lòng chuyển khoản theo cú pháp: NAP [ID_CUA_BAN]")

    elif text == "📝 Đơn hàng":
        bot.reply_to(message, "📝 Bạn chưa có lịch sử đơn hàng nào.")

# 5. Cấu hình đa luồng để chạy trên Koyeb
def run_flask():
    # Chạy trên port 8000 để vượt qua Health Check của Koyeb
    app.run(host='0.0.0.0', port=8000)

if __name__ == "__main__":
    # Chạy Flask ở luồng riêng để không chặn Bot
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    print("Bot Telegram đang bắt đầu Polling...")
    # Thiết lập polling ổn định
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
