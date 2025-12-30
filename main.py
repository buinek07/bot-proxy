import telebot
from telebot import types
from pymongo import MongoClient
from flask import Flask
import threading
from datetime import datetime
import requests
import random
import time

# --- CẤU HÌNH HỆ THỐNG ---
TOKEN = '8371917325:AAE4ftu8HJkA5CyNd5On69r39WS10Osl1JQ'
MONGO_URI = 'mongodb+srv://buinek:XH1S550j3EzKpVFg@bottlee.qnaas3k.mongodb.net/?appName=bottlee'
API_KEY_PROXY = 'AvqAKLwQAuDDSNyWtVQUsv'
# API KEY bạn cung cấp
API_KEY_SIM = 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJidWluZWsiLCJqdGkiOiI4MTI1NyIsImlhdCI6MTc2MjU0Mzc1MCwiZXhwIjoxODI0NzUxNzUwfQ.samlD0eFL1r0fx2JYsMX0qS6LK1zVCXXPPWHJHeHh9cWlbOWV3_WMfm64RTU2HIzQ0O6fyeog7TfDNlnmvcg2g'

ADMIN_ID = 5519768222 # ID Admin của bạn
PROXY_PRICE = 1500    # Giá Proxy
OTP_PRICE = 2500      # Giá dịch vụ OTP
SERVICE_ID_OTP = 49   # ID dịch vụ Nhận OTP bạn đã xác nhận

bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI)
db = client.bot_proxy_db
users_col = db.users
orders_col = db.orders

app = Flask('')
@app.route('/')
def home(): return "Bot is running!"
def run_web(): app.run(host='0.0.0.0', port=8000)
threading.Thread(target=run_web).start()

# --- XỬ LÝ LẤY SỐ THEO API BẠN GỬI ---
@bot.callback_query_handler(func=lambda call: call.data == "pay_OTP")
def process_otp_payment(call):
    user_id = call.from_user.id
    u = users_col.find_one({"user_id": user_id})

    if u.get('balance', 0) < OTP_PRICE:
        bot.answer_callback_query(call.id, "❌ Tài khoản không đủ số dư!", show_alert=True)
        return

    # Trừ tiền trước khi lấy số
    users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -OTP_PRICE, "total_spent": OTP_PRICE}})

    # URL lấy số theo mục 4 trong API bạn gửi
    api_get_sim = f"https://apisim.codesim.net/sim/get_sim?service_id={SERVICE_ID_OTP}&api_key={API_KEY_SIM}"
    
    try:
        res = requests.get(api_get_sim).json()
        if res.get('success'):
            sim_data = res.get('data')
            sim_id = sim_data.get('id')
            phone = sim_data.get('phone_number')
            
            bot.edit_message_text(f"📲 **LẤY SỐ THÀNH CÔNG**\n\n📞 Số điện thoại: `{phone}`\n⏳ Trạng thái: **Đang chờ mã OTP...**", 
                                  call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            
            # Chạy luồng kiểm tra mã OTP
            threading.Thread(target=check_otp_logic, args=(user_id, sim_id, phone, call.message.message_id)).start()
        else:
            raise Exception(res.get('message', 'Hết số'))
    except Exception as e:
        # Hoàn tiền nếu lỗi lấy số
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": OTP_PRICE, "total_spent": -OTP_PRICE}})
        bot.edit_message_text(f"❌ Lỗi: {str(e)}. Đã hoàn tiền!", call.message.chat.id, call.message.message_id)

# --- KIỂM TRA OTP THEO MỤC 5 CỦA API ---
def check_otp_logic(user_id, sim_id, phone, msg_id):
    timeout = time.time() + 120 # Đợi 2 phút
    while time.time() < timeout:
        try:
            # URL kiểm tra mã theo mục 5 trong API bạn gửi
            check_url = f"https://apisim.codesim.net/otp/get_otp_by_phone_api_key?otp_id={sim_id}&api_key={API_KEY_SIM}"
            res = requests.get(check_url).json()
            if res.get('success') and res.get('data'):
                otp_code = res.get('data').get('sms_content')
                bot.edit_message_text(f"✅ **NHẬN MÃ THÀNH CÔNG**\n\n📞 Số: `{phone}`\n📩 Mã OTP: `{otp_code}`", user_id, msg_id, parse_mode="Markdown")
                orders_col.insert_one({"user_id": user_id, "type": "OTP", "data": f"{phone}|{otp_code}", "date": datetime.now()})
                return
        except: pass
        time.sleep(5)
    
    # Hủy số và hoàn tiền nếu hết thời gian theo mục 6
    requests.get(f"https://apisim.codesim.net/sim/cancel_api_key/{sim_id}?api_key={API_KEY_SIM}")
    users_col.update_one({"user_id": user_id}, {"$inc": {"balance": OTP_PRICE, "total_spent": -OTP_PRICE}})
    bot.send_message(user_id, f"🔄 **HOÀN TIỀN:** Không nhận được mã cho số `{phone}`.")

# --- LỆNH CỘNG TIỀN VÀ CẢM ƠN ---
@bot.message_handler(commands=['plus'])
def plus_money(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, amt = message.text.split()
        users_col.update_one({"user_id": int(tid)}, {"$inc": {"balance": int(amt), "total_deposit": int(amt)}})
        bot.send_message(ADMIN_ID, f"✅ Đã cộng {amt} cho {tid}")
        # Mẫu cảm ơn bạn yêu cầu
        bot.send_message(int(tid), f"🎉 **NẠP TIỀN THÀNH CÔNG!**\n💰 Bạn được cộng: `{int(amt):,} VND`\n🙏 Cảm ơn bạn đã tin tưởng sử dụng dịch vụ!")
    except: pass

# --- VÒNG LẶP CHỐNG XUNG ĐỘT (CONFLICT 409) ---
def run_bot():
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
