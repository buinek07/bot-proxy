import os, telebot, requests, random, time, threading
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
users_col, orders_col = db.users, db.orders

app = Flask('')
@app.route('/')
def home(): return "Bot is Healthy!"

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
           f"📤 Tổng đã chi tiêu: {u.get('total_spent', 0):,} VNĐ")
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

# --- 4. NẠP TIỀN & XÁC NHẬN ---
@bot.message_handler(func=lambda m: m.text == '💳 Nạp tiền')
def recharge(message):
    user_id = message.from_user.id
    keys = ['tiencafe', 'tienbanhmysang', 'tiencoke']
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
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "⏳ Giao dịch đang xử lý. Vui lòng đợi..")
    bot.send_message(ADMIN_ID, f"🚀 **YÊU CẦU DUYỆT NẠP**\n🆔: `{call.from_user.id}`\n📌 Nội dung: `{call.data}`\n👉 `/plus {call.from_user.id} [Số tiền]`")

@bot.message_handler(commands=['plus'])
def plus_money(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, amt = message.text.split()
        amt_int = int(amt)
        users_col.update_one({"user_id": int(tid)}, {"$inc": {"balance": amt_int, "total_deposit": amt_int}})
        bot.send_message(int(tid), f"🎉 **NẠP TIỀN THÀNH CÔNG!**\n💰 Số tiền nạp: `{amt_int:,} VND`\n🙏 Cảm ơn bạn đã tin tưởng dịch vụ!", parse_mode="Markdown")
        bot.send_message(ADMIN_ID, f"✅ Đã cộng {amt_int:,}đ cho {tid}")
    except: bot.send_message(ADMIN_ID, "❌ Lỗi. Cú pháp: /plus [ID] [Số tiền]")

# --- 5. CỬA HÀNG DỊCH VỤ ---
@bot.message_handler(func=lambda m: m.text == '🛒 Mua hàng')
def shop(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🌐 PROXY SIÊU TỐC", callback_data="proxy_menu"),
        types.InlineKeyboardButton("📲 THUÊ OTP GIÁ RẺ", callback_data="buy_otp_confirm")
    ) #
    
    shop_text = (
        "🛒 **CỬA HÀNG DỊCH VỤ**\n\n"
        "Vui lòng chọn loại dịch vụ bạn muốn trải nghiệm bên dưới:\n\n"
        "🔹 **Proxy**: Proxy tĩnh tốc độ cao, ổn định.\n"
        "🔹 **Thuê OTP**: Nhận mã nhanh chóng, hoàn tiền nếu lỗi."
    ) #
    bot.send_message(message.chat.id, shop_text, reply_markup=markup, parse_mode="Markdown")

# --- 6. LOGIC PROXY (PROXY.VN) ---
@bot.callback_query_handler(func=lambda call: call.data == "proxy_menu")
def proxy_menu(call):
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(types.InlineKeyboardButton("Viettel", callback_data="ask_Viettel"),
               types.InlineKeyboardButton("VNPT", callback_data="ask_VNPT"),
               types.InlineKeyboardButton("FPT", callback_data="ask_FPT"))
    bot.edit_message_text("✨ Vui lòng chọn nhà mạng (Đồng giá 1,500đ):", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ask_"))
def ask_proxy(call):
    carrier = call.data.replace("ask_", "")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Mua ngay", callback_data=f"pay_proxy_{carrier}"),
               types.InlineKeyboardButton("❌ Hủy", callback_data="proxy_menu"))
    bot.edit_message_text(f"❓ Xác nhận mua **Proxy {carrier}** giá 1,500đ?", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_proxy_"))
def pay_proxy(call):
    carrier = call.data.replace("pay_proxy_", "")
    user_id = call.from_user.id
    u = users_col.find_one({"user_id": user_id})
    if u.get('balance', 0) < PROXY_PRICE:
        bot.answer_callback_query(call.id, "❌ Số dư không đủ!", show_alert=True)
        return
    
    bot.edit_message_text(f"⏳ Đang lấy Proxy {carrier} từ hệ thống...", call.message.chat.id, call.message.message_id)
    api_url = f"https://proxy.vn/apiv2/muaproxy.php?loaiproxy={carrier}&key={API_KEY_PROXY}&soluong=1&ngay=1&type=HTTP&user=random&password=random"
    
    try:
        res = requests.get(api_url, timeout=30).json()
        if res.get('status') == 'success':
            p_data = res.get('data') #
            users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -PROXY_PRICE, "total_spent": PROXY_PRICE}})
            orders_col.insert_one({"user_id": user_id, "type": f"Proxy {carrier}", "data": p_data, "date": datetime.now()})
            bot.edit_message_text(f"✅ **MUA THÀNH CÔNG!**\n🔑 Thông tin: `{p_data}`", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        else: bot.edit_message_text(f"❌ Lỗi: {res.get('message')}", call.message.chat.id, call.message.message_id)
    except: bot.edit_message_text("❌ Lỗi kết nối API Proxy.vn!", call.message.chat.id, call.message.message_id)

# --- 7. LOGIC OTP (CODESIM.NET) ---
@bot.callback_query_handler(func=lambda call: call.data == "buy_otp_confirm")
def otp_ask(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Xác nhận (2.5k)", callback_data="pay_otp_now"),
               types.InlineKeyboardButton("❌ Hủy", callback_data="proxy_menu"))
    bot.edit_message_text("❓ Bạn muốn thuê OTP (Dịch vụ ID: 49)?", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "pay_otp_now")
def otp_pay(call):
    user_id = call.from_user.id
    u = users_col.find_one({"user_id": user_id})
    if u.get('balance', 0) < OTP_PRICE:
        bot.answer_callback_query(call.id, "❌ Không đủ tiền!", show_alert=True)
        return
    
    users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -OTP_PRICE, "total_spent": OTP_PRICE}})
    try:
        res = requests.get(f"https://apisim.codesim.net/sim/get_sim?service_id={SERVICE_ID_OTP}&api_key={API_KEY_SIM}").json()
        if res.get('success'):
            data = res['data']
            sim_id, phone = data['id'], data['phone_number']
            bot.edit_message_text(f"📲 Số: `{phone}`\n⏳ Đang đợi mã OTP...", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            threading.Thread(target=otp_worker, args=(user_id, sim_id, phone, call.message.message_id)).start()
        else: raise Exception(res.get('message', 'Hết số'))
    except Exception as e:
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": OTP_PRICE, "total_spent": -OTP_PRICE}})
        bot.edit_message_text(f"❌ Lỗi: {str(e)}. Đã hoàn tiền!", call.message.chat.id, call.message.message_id)

def otp_worker(user_id, sim_id, phone, msg_id):
    timeout = time.time() + 120
    while time.time() < timeout:
        try:
            res = requests.get(f"https://apisim.codesim.net/otp/get_otp_by_phone_api_key?otp_id={sim_id}&api_key={API_KEY_SIM}").json()
            if res.get('success') and res.get('data'):
                otp = res['data']['sms_content']
                bot.edit_message_text(f"✅ **MÃ OTP: `{otp}`**\n📞 Số: `{phone}`", user_id, msg_id, parse_mode="Markdown")
                orders_col.insert_one({"user_id": user_id, "type": "OTP", "data": f"{phone}|{otp}", "date": datetime.now()})
                return
        except: pass
        time.sleep(5)
    requests.get(f"https://apisim.codesim.net/sim/cancel_api_key/{sim_id}?api_key={API_KEY_SIM}")
    users_col.update_one({"user_id": user_id}, {"$inc": {"balance": OTP_PRICE, "total_spent": -OTP_PRICE}})
    bot.send_message(user_id, f"🔄 **HOÀN TIỀN:** Không nhận được mã cho `{phone}`.")

# --- 8. ĐƠN HÀNG ---
@bot.message_handler(func=lambda m: m.text == '📋 Đơn hàng')
def order_history(message):
    orders = list(orders_col.find({"user_id": message.from_user.id}).sort("date", -1).limit(10))
    if not orders:
        bot.send_message(message.chat.id, "📦 **Đơn hàng**\n\nBạn chưa có đơn hàng nào.", parse_mode="Markdown")
        return
    msg = "📋 **DANH SÁCH ĐƠN HÀNG**\n\n"
    for o in orders:
        msg += f"🔹 {o['type']} | {o['date'].strftime('%H:%M %d/%m')}\n`{o['data']}`\n\n"
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

# --- 9. VẬN HÀNH ---
def run_web(): app.run(host='0.0.0.0', port=8000)
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    while True:
        try: bot.polling(none_stop=True, interval=0, timeout=40)
        except: time.sleep(5)
