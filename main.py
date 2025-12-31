import os
import telebot
import requests
import random
import time
import threading
from flask import Flask
from pymongo import MongoClient
from datetime import datetime
from telebot import types

# --- 1. CẤU HÌNH HỆ THỐNG ---
TOKEN = os.getenv('TOKEN', '8371917325:AAE4ftu8HJkA5CyNd5On69r39WS10Osl1JQ')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://buinek:XH1S550j3EzKpVFg@bottlee.qnaas3k.mongodb.net/?appName=bottlee')
API_KEY_PROXY = 'AvqAKLwQAuDDSNyWtVQUsv'
API_KEY_SIM = 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJidWluZWsiLCJqdGkiOiI4MTI1NyIsImlhdCI6MTc2MjU0Mzc1MCwiZXhwIjoxODI0NzUxNzUwfQ.samlD0eFL1r0fx2JYsMX0qS6LK1zVCXXPPWHJHeHh9cWlbOWV3_WMfm64RTU2HIzQ0O6fyeog7TfDNlnmvcg2g'

ADMIN_ID = 5519768222 # [cite: 2025-12-30]
PROXY_PRICE = 1500
OTP_PRICE = 2500
SERVICE_ID_OTP = 49 

bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI)
db = client.bot_proxy_db
users_col = db.users
orders_col = db.orders

app = Flask('')
@app.route('/')
def home(): return "Bot is running!"

# --- 2. MENU CHÍNH ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('👤 Tài khoản', '🛒 Mua hàng', '💳 Nạp tiền', '📋 Đơn hàng', '📞 Admin')
    return markup

# --- 3. XỬ LÝ LỆNH START ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "None"
    now = datetime.now().strftime("%d/%m/%Y")
    # Cập nhật thông tin khách vào DB
    users_col.update_one(
        {"user_id": user_id},
        {"$set": {"username": username, "first_name": message.from_user.first_name}, 
         "$setOnInsert": {"join_date": now, "balance": 0, "total_deposit": 0, "total_spent": 0}},
        upsert=True
    )
    bot.send_message(message.chat.id, f"👋 Chào mừng {message.from_user.first_name}!\n⚡ Hệ thống Proxy & OTP tự động 24/7.", reply_markup=main_menu())

# --- 4. THÔNG TIN CÁ NHÂN ---
@bot.message_handler(func=lambda m: m.text == '👤 Tài khoản')
def account_info(message):
    u = users_col.find_one({"user_id": message.from_user.id})
    msg = (f"🌟 **THÔNG TIN CÁ NHÂN** 🌟\n\n"
           f"👤 Tên khách hàng: {u.get('username', 'None')}\n" #
           f"🆔 ID của bạn: `{message.from_user.id}`\n"
           f"📅 Ngày gia nhập: {u.get('join_date', 'None')}\n"
           f"--------------------------\n"
           f"💰 Số dư khả dụng: {u.get('balance', 0):,} VNĐ\n"
           f"📥 Tổng nạp: {u.get('total_deposit', 0):,} VNĐ\n"
           f"📤 Tổng đã chi tiêu: {u.get('total_spent', 0):,} VNĐ\n\n"
           f"🚀 Nạp thêm tiền để trải nghiệm dịch vụ tốt hơn!")
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

# --- 5. NẠP TIỀN TỰ ĐỘNG ---
@bot.message_handler(func=lambda m: m.text == '💳 Nạp tiền')
def recharge(message):
    user_id = message.from_user.id
    # Thông báo cho Admin
    try: bot.send_message(ADMIN_ID, f"🔔 **KHÁCH XEM NẠP TIỀN**\n👤: @{message.from_user.username}\n🆔: `{user_id}`")
    except: pass
    
    # Tạo nội dung ngẫu nhiên
    keys = ['tiencafe', 'tienbanhmysang', 'tiencoke', 'tienbunbo']
    memo = f"{random.choice(keys)}{user_id}" 
    qr_url = f"https://img.vietqr.io/image/MB-700122-compact2.jpg?amount=20000&addInfo={memo}"
    
    caption = (f"💳 **THÔNG TIN NẠP TIỀN TỰ ĐỘNG**\n\n" #
               f"🏦 Ngân hàng: MBBank\n"
               f"📝 STK: `700122`\n"
               f"👤 CTK: BUI DUC ANH\n\n"
               f"💰 Tối thiểu: 20,000 VND\n"
               f"📌 Nội dung: `{memo}`\n\n"
               f"📩 Hỗ trợ: @buinek")
    bot.send_photo(message.chat.id, qr_url, caption=caption, parse_mode="Markdown")

# --- 6. MUA HÀNG & PROXY (PROXY.VN) ---
@bot.message_handler(func=lambda m: m.text == '🛒 Mua hàng')
def shop(message):
    markup = types.InlineKeyboardMarkup()
    # Xóa giá tiền đằng sau theo yêu cầu
    markup.add(types.InlineKeyboardButton("🌐 PROXY", callback_data="proxy_menu"),
               types.InlineKeyboardButton("📲 NHẬN OTP", callback_data="buy_otp"))
    bot.send_message(message.chat.id, "🛒 Chọn loại dịch vụ bạn muốn trải nghiệm:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "proxy_menu")
def proxy_menu(call):
    markup = types.InlineKeyboardMarkup(row_width=3)
    # Menu chọn nhà mạng y hệt ảnh
    markup.add(types.InlineKeyboardButton("🌐 Viettel", callback_data="buy_proxy_Viettel"),
               types.InlineKeyboardButton("🌐 VNPT", callback_data="buy_proxy_VNPT"),
               types.InlineKeyboardButton("🌐 FPT", callback_data="buy_proxy_FPT"))
    bot.edit_message_text("✨ Vui lòng chọn nhà mạng (Đồng giá 1,500đ):", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_proxy_"))
def process_proxy_purchase(call):
    carrier = call.data.replace("buy_proxy_", "")
    user_id = call.from_user.id
    u = users_col.find_one({"user_id": user_id})

    if u['balance'] < PROXY_PRICE:
        bot.answer_callback_query(call.id, "❌ Số dư không đủ!", show_alert=True)
        return

    # Gọi API Proxy.vn
    api_url = f"https://proxy.vn/apiv2/muaproxy.php?loaiproxy={carrier}&key={API_KEY_PROXY}&soluong=1&ngay=1&type=HTTP&user=random&password=random"
    
    try:
        res = requests.get(api_url).json()
        if res.get('status') == 'success':
            proxy_data = res.get('data', 'Không xác định')
            # Trừ tiền và lưu đơn hàng
            users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -PROXY_PRICE, "total_spent": PROXY_PRICE}})
            orders_col.insert_one({"user_id": user_id, "type": f"Proxy {carrier}", "data": proxy_data, "date": datetime.now()})
            
            bot.edit_message_text(f"✅ **MUA PROXY THÀNH CÔNG!**\n\n🌐 Nhà mạng: {carrier}\n🔑 Thông tin: `{proxy_data}`", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, f"❌ Lỗi: {res.get('message', 'Kho hàng tạm hết')}", show_alert=True)
    except:
        bot.answer_callback_query(call.id, "❌ Lỗi kết nối máy chủ Proxy!", show_alert=True)

# --- 7. ĐƠN HÀNG (LỊCH SỬ) ---
@bot.message_handler(func=lambda m: m.text == '📋 Đơn hàng')
def order_history(message):
    user_id = message.from_user.id
    orders = list(orders_col.find({"user_id": user_id}).sort("date", -1).limit(5)) # Lấy 5 đơn gần nhất

    if not orders:
        bot.reply_to(message, "📝 Bạn chưa có đơn hàng nào.")
        return

    history_msg = "📋 **DANH SÁCH ĐƠN HÀNG GẦN ĐÂY**\n\n"
    for o in orders:
        date_str = o['date'].strftime("%H:%M %d/%m")
        history_msg += f"🔹 {o['type']} | {date_str}\n`{o['data']}`\n\n"
    
    bot.send_message(message.chat.id, history_msg, parse_mode="Markdown")

# --- 8. VẬN HÀNH (KHÔNG TREO KOYEB) ---
def run_web():
    app.run(host='0.0.0.0', port=8000)

if __name__ == "__main__":
    threading.Thread(target=run_web).start() #
    print("Bot đang khởi động với đầy đủ tính năng...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=40)
        except Exception as e:
            time.sleep(5)
