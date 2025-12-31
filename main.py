import os
import telebot
from flask import Flask
import threading
from telebot import types

# Cấu hình biến môi trường
TOKEN = os.getenv('TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID', '5519768222')

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def index(): return "Bot is Online"

# Hàm tạo Menu nút bấm
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("👤 Tài khoản"), types.KeyboardButton("🛒 Mua hàng"))
    markup.add(types.KeyboardButton("💳 Nạp tiền"), types.KeyboardButton("📝 Đơn hàng"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Chào Admin! Hệ thống đã sẵn sàng.", reply_markup=main_menu())

# XỬ LÝ KHI NHẤN NÚT (Sửa lỗi nút không dùng được)
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "👤 Tài khoản":
        bot.reply_to(message, "📌 Thông tin tài khoản của bạn đang được cập nhật...")
    elif message.text == "🛒 Mua hàng":
        bot.reply_to(message, "🛍 Lời chào mua hàng: Chào mừng bạn! Vui lòng chọn gói sản phẩm.")
    elif message.text == "💳 Nạp tiền":
        bot.reply_to(message, "💳 Vui lòng liên hệ Admin để nạp tiền.")
    elif message.text == "📝 Đơn hàng":
        bot.reply_to(message, "📝 Bạn chưa có đơn hàng nào.")

def run_flask():
    app.run(host='0.0.0.0', port=8000)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("Bot đang bắt đầu Polling...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)import os
import telebot
from flask import Flask
import threading
from pymongo import MongoClient
from telebot import types

# 1. Lấy thông tin cấu hình
TOKEN = os.getenv('TOKEN')
MONGO_URI = os.getenv('MONGO_URI')
ADMIN_ID = os.getenv('ADMIN_ID', '5519768222') #

# 2. Khởi tạo Bot và Database
bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI)
db = client['bottlee'] #

# 3. Cấu hình Flask để giữ server sống (Port 8000)
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running..."

# --- 4. LOGIC XỬ LÝ LỆNH /START VÀ HIỆN NÚT BẤM ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    
    # Tạo menu nút bấm (ReplyKeyboardMarkup)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("👤 Tài khoản")
    btn2 = types.KeyboardButton("🛒 Mua hàng")
    btn3 = types.KeyboardButton("💳 Nạp tiền")
    btn4 = types.KeyboardButton("📝 Đơn hàng")
    markup.add(btn1, btn2, btn3, btn4)

    if user_id == ADMIN_ID:
        bot.send_message(message.chat.id, "Chào Admin! Hệ thống đã sẵn sàng.", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Chào mừng bạn đến với shop! Vui lòng chọn chức năng bên dưới.", reply_markup=markup)

# --- 5. LOGIC XỬ LÝ KHI NGƯỜI DÙNG NHẤN NÚT ---

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    text = message.text
    
    if text == "👤 Tài khoản":
        # Ở đây bạn có thể code thêm phần lấy dữ liệu từ MongoDB
        bot.reply_to(message, "Thông tin tài khoản của bạn:\n- ID: " + str(message.from_user.id) + "\n- Số dư: 0đ")
        
    elif text == "🛒 Mua hàng":
        bot.reply_to(message, "🛍 Danh sách sản phẩm đang bán: \n1. Gói Proxy VIP\n2. Tài khoản Game\n(Vui lòng liên hệ Admin để mua)")
        
    elif text == "💳 Nạp tiền":
        bot.reply_to(message, "Hệ thống nạp tiền tự động đang bảo trì. Vui lòng chuyển khoản cho Admin: 5519768222")

    elif text == "📝 Đơn hàng":
        bot.reply_to(message, "Bạn chưa có đơn hàng nào gần đây.")

# --- 6. CẤU HÌNH CHẠY ĐA LUỒNG ---

def run_flask():
    app.run(host='0.0.0.0', port=8000)

if __name__ == "__main__":
    # Chạy Flask ở luồng phụ để Koyeb không báo lỗi Health Check
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    print("Bot Telegram đang bắt đầu Polling...")
    bot.infinity_polling()
