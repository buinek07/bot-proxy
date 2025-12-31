import os
import telebot
from flask import Flask
import threading
from pymongo import MongoClient

# Lấy các biến môi trường từ Koyeb
TOKEN = os.getenv('TOKEN')
MONGO_URI = os.getenv('MONGO_URI')
ADMIN_ID = os.getenv('ADMIN_ID', '5519768222') # Mặc định là ID của bạn

# Khởi tạo Bot và Database
bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI)
db = client['bottlee'] # Tên database từ URI của bạn

# Khởi tạo Flask để giữ server luôn sống
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot đang chạy trực tuyến!"

# --- PHẦN XỬ LÝ LỆNH BOT ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    if user_id == ADMIN_ID:
        bot.reply_to(message, "Chào Admin! Bot đã sẵn sàng nhận lệnh.")
    else:
        bot.reply_to(message, "Bạn không có quyền sử dụng bot này.")

@bot.message_handler(commands=['huydot'])
def huy_dot(message):
    # Thêm logic xử lý hủy đợt của bạn ở đây
    bot.reply_to(message, "Đã thực hiện lệnh hủy đợt.")

# --- CẤU HÌNH CHẠY ĐA LUỒNG (THREADING) ---

def run_flask():
    # Flask chạy trên port 8000 theo cấu hình Koyeb
    app.run(host='0.0.0.0', port=8000)

if __name__ == "__main__":
    # 1. Chạy Flask trong luồng phụ
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # 2. Chạy Bot trong luồng chính
    print("Bot Telegram đang bắt đầu Polling...")
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Lỗi Polling: {e}")
