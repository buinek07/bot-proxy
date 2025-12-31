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

ADMIN_ID = 5519768222 
PROXY_PRICE = 1500
OTP_PRICE = 2500

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

# --- 3. LỆNH START & TÀI KHOẢN ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "None"
    now = datetime.now().strftime("%d/%m/%Y")
    users_col.update_one(
        {"user_id": user_id},
        {"$set": {"username": username, "first_name": message.from_user.first_name}, 
         "$setOnInsert": {"join_date": now, "balance": 0, "total_deposit": 0, "total_spent": 0}},
        upsert=True
    )
    bot.send_message(message.chat.id, f"👋 Chào mừng {message.from_user.first_name}!\n⚡ Hệ thống Proxy & OTP tự động 24/7.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == '👤 Tài khoản')
def account_info(message):
    u = users_col.find_one({"user_id": message.from_user.id})
    msg = (f"🌟 **THÔNG TIN CÁ NHÂN** 🌟\n\n"
           f"👤 Tên khách hàng: {u.get('username', 'None')}\n"
           f"🆔 ID của bạn: `{message.from_user.id}`\n"
           f"📅 Ngày gia nhập: {u.get('join_date', 'None')}\n"
           f"--------------------------\n"
           f"💰 Số dư khả dụng: {u.get('balance', 0):,} VNĐ\n"
           f"📥 Tổng nạp: {u.get('total_deposit', 0):,} VNĐ\n"
           f"📤 Tổng đã chi tiêu: {u.get('total_spent', 0):,} VNĐ\n\n"
           f"🚀 Nạp thêm tiền để trải nghiệm dịch vụ tốt hơn!")
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

# --- 4. NẠP TIỀN & XÁC NHẬN ---
@bot.message_handler(func=lambda m: m.text == '💳 Nạp tiền')
def recharge(message):
    user_id = message.from_user.id
    keys = ['tiencafe', 'tienbanhmysang', 'tiencoke', 'tienbunbo']
    memo = f"{random.choice(keys)}{user_id}"
    qr_url = f"https://img.vietqr.io/image/MB-700122-compact2.jpg?amount=20000&addInfo={memo}"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Xác nhận đã nạp", callback_data=f"confirm_{memo}"))
    
    caption = (f"💳 **THÔNG TIN NẠP TIỀN TỰ ĐỘNG**\n\n"
               f"🏦 Ngân hàng: MBBank\n📝 STK: `700122`\n👤 CTK: BUI DUC ANH\n\n"
               f"💰 Tối thiểu: 20,000 VND\n📌 Nội dung: `{memo}`\n\n📩 Hỗ trợ: @buinek")
    bot.send_photo(message.chat.id, qr_url, caption=caption, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def handle_confirm(call):
    memo = call.data.replace("confirm_", "")
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "⏳ Giao dịch đang xử lý. Vui lòng đợi..")
    bot.send_message(ADMIN_ID, f"🚀 **YÊU CẦU DUYỆT NẠP**\n👤: @{call.from_user.username}\n🆔: `{call.from_user.id}`\n📌 Nội dung: `{memo}`\n👉 `/plus {call.from_user.id} [Số tiền]`")

# --- 5. LỆNH ADMIN NẠP TIỀN ---
@bot.message_handler(commands=['plus'])
def plus_money(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, amt = message.text.split()
        amt_int = int(amt)
        users_col.update_one({"user_id": int(tid)}, {"$inc": {"balance": amt_int, "total_deposit": amt_int}})
        bot.send_message(ADMIN_ID, f"✅ Đã cộng {amt_int:,}đ cho {tid}")
        # Nhắn tin thành công cho khách
        thanks_msg = (f"🎉 **NẠP TIỀN THÀNH CÔNG!**\n"
                      f"💰 Số tiền nạp: `{amt_int:,} VND`\n"
                      f"🙏 Cảm ơn bạn đã tin tưởng sử dụng dịch vụ!")
        bot.send_message(int(tid), thanks_msg, parse_mode="Markdown")
    except: bot.send_message(ADMIN_ID, "❌ Lỗi. Cú pháp: /plus [ID] [Số tiền]")

# --- 6. MUA HÀNG & PROXY & ĐƠN HÀNG ---
@bot.message_handler(func=lambda m: m.text == '🛒 Mua hàng')
def shop(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌐 PROXY", callback_data="proxy_menu"),
               types.InlineKeyboardButton("📲 NHẬN OTP", callback_data="buy_otp"))
    bot.send_message(message.chat.id, "🛒 Chọn loại dịch vụ:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "proxy_menu")
def proxy_menu(call):
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(types.InlineKeyboardButton("🌐 Viettel", callback_data="buy_proxy_Viettel"),
               types.InlineKeyboardButton("🌐 VNPT", callback_data="buy_proxy_VNPT"),
               types.InlineKeyboardButton("🌐 FPT", callback_data="buy_proxy_FPT"))
    bot.edit_message_text("✨ Vui lòng chọn nhà mạng (Đồng giá 1,500đ):", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_proxy_"))
def process_proxy(call):
    carrier = call.data.replace("buy_proxy_", "")
    u = users_col.find_one({"user_id": call.from_user.id})
    if u['balance'] < PROXY_PRICE:
        bot.answer_callback_query(call.id, "❌ Số dư không đủ!", show_alert=True)
        return
    api_url = f"https://proxy.vn/apiv2/muaproxy.php?loaiproxy={carrier}&key={API_KEY_PROXY}&soluong=1&ngay=1&type=HTTP&user=random&password=random"
    try:
        res = requests.get(api_url).json()
        if res.get('status') == 'success':
            p_data = res.get('data')
            users_col.update_one({"user_id": call.from_user.id}, {"$inc": {"balance": -PROXY_PRICE, "total_spent": PROXY_PRICE}})
            orders_col.insert_one({"user_id": call.from_user.id, "type": f"Proxy {carrier}", "data": p_data, "date": datetime.now()})
            bot.edit_message_text(f"✅ **MUA THÀNH CÔNG!**\n\n🌐 {carrier}\n🔑 Thông tin: `{p_data}`", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        else: bot.answer_callback_query(call.id, f"❌ Lỗi: {res.get('message')}", show_alert=True)
    except: bot.answer_callback_query(call.id, "❌ Lỗi kết nối API!", show_alert=True)

@bot.message_handler(func=lambda m: m.text == '📋 Đơn hàng')
def order_history(message):
    orders = list(orders_col.find({"user_id": message.from_user.id}).sort("date", -1).limit(5))
    if not orders:
        bot.reply_to(message, "📝 Bạn chưa có đơn hàng nào.")
        return
    msg = "📋 **ĐƠN HÀNG GẦN ĐÂY**\n\n"
    for o in orders:
        msg += f"🔹 {o['type']} | {o['date'].strftime('%H:%M %d/%m')}\n`{o['data']}`\n\n"
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

# --- 7. VẬN HÀNH ---
def run_web(): app.run(host='0.0.0.0', port=8000)
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    while True:
        try: bot.polling(none_stop=True, interval=0, timeout=40)
        except: time.sleep(5)
