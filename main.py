import telebot
from telebot import types
from pymongo import MongoClient
from flask import Flask
import threading
from datetime import datetime
import requests

# --- CẤU HÌNH ---
TOKEN = '8371917325:AAE4ftu8HJkA5CyNd5On69r39WS10Osl1JQ'
MONGO_URI = 'mongodb+srv://buinek:XH1S550j3EzKpVFg@bottlee.qnaas3k.mongodb.net/?appName=bottlee'
API_KEY_PROXY = 'AvqAKLwQAuDDSNyWtVQUsv'

# THAY DÃY SỐ ID CỦA BẠN VÀO ĐÂY (Lấy từ @userinfobot)
ADMIN_ID = 5698547214 
BANK_ID = 'MB'
STK = '700122' 

# GIÁ PROXY (1,500đ)
PROXY_PRICE = 1500

bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI)
db = client.bot_proxy_db
users_col = db.users
orders_col = db.orders

# Web server giữ mạng cho Koyeb
app = Flask('')
@app.route('/')
def home(): return "Bot is running!"
def run_web(): app.run(host='0.0.0.0', port=8000)
threading.Thread(target=run_web).start()

def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('👤 Tài khoản', '🛒 Mua hàng', '💳 Nạp tiền', '📋 Đơn hàng', '📞 Admin')
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not users_col.find_one({"user_id": user_id}):
        users_col.insert_one({
            "user_id": user_id, "first_name": message.from_user.first_name,
            "join_date": datetime.now().strftime("%d/%m/%Y"),
            "balance": 0, "total_deposit": 0, "total_spent": 0
        })
    bot.send_message(message.chat.id, "🤖 **Bot Proxy đã sẵn sàng!**", reply_markup=main_menu(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == '👤 Tài khoản')
def account_info(message):
    u = users_col.find_one({"user_id": message.from_user.id})
    if u:
        msg = (f"👤 **Thông tin tài khoản**\n\n👤 Tên: **{u['first_name']}**\n🆔 ID: `{u['user_id']}`\n"
               f"📅 Ngày tham gia: {u['join_date']}\n\n💰 Số dư: {u['balance']:,} VND\n"
               f"📊 Tổng nạp: {u['total_deposit']:,} VND\n💸 Tổng chi: {u['total_spent']:,} VND")
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == '🛒 Mua hàng')
def shop(message):
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🌐 Viettel", callback_data="buy_Viettel"),
        types.InlineKeyboardButton("🌐 VNPT", callback_data="buy_VNPT"),
        types.InlineKeyboardButton("🌐 FPT", callback_data="buy_FPT")
    )
    bot.send_message(message.chat.id, f"✨ **Vui lòng chọn nhà mạng (Đồng giá {PROXY_PRICE:,}đ):**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def confirm_purchase(call):
    isp = call.data.split("_")[1]
    text = f"⚠️ **XÁC NHẬN THANH TOÁN**\n\n📦 Sản phẩm: Proxy {isp}\n💰 Giá: {PROXY_PRICE:,} VND\n⏳ Thời hạn: 24 Giờ"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Thanh toán", callback_data=f"pay_{isp}"),
               types.InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def process_payment(call):
    user_id = call.from_user.id
    isp = call.data.split("_")[1]
    user_data = users_col.find_one({"user_id": user_id})

    if user_data['balance'] < PROXY_PRICE:
        bot.answer_callback_query(call.id, "❌ Số dư không đủ! Vui lòng nạp thêm.", show_alert=True)
        return

    # Gọi API Proxy.vn
    api_url = f"https://proxy.vn/apiv2/muaproxy.php?loaiproxy={isp}&key={API_KEY_PROXY}&soluong=1&ngay=1&type=HTTP&user=random&password=random"
    
    try:
        response = requests.get(api_url).text
        if "error" in response.lower() or "không đủ" in response.lower():
            bot.send_message(user_id, "❌ Lỗi: Kho hàng hết hoặc hệ thống Proxy bảo trì. Vui lòng thử lại sau!")
            return
        
        # Trừ tiền và lưu đơn hàng
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -PROXY_PRICE, "total_spent": PROXY_PRICE}})
        orders_col.insert_one({"user_id": user_id, "isp": isp, "data": response, "date": datetime.now()})
        
        msg = f"✅ **THANH TOÁN THÀNH CÔNG!**\n\n📦 Loại: Proxy {isp}\n🌐 Thông tin: `{response}`\n💰 Trừ phí: -{PROXY_PRICE:,} VND"
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        
        # Thông báo Admin
        bot.send_message(ADMIN_ID, f"💰 Khách {user_id} vừa mua {isp} ({PROXY_PRICE:,}đ)")
    except:
        bot.send_message(user_id, "❌ Có lỗi kết nối API.")

@bot.message_handler(func=lambda m: m.text == '💳 Nạp tiền')
def recharge(message):
    user_id = message.from_user.id
    qr_url = f"https://img.vietqr.io/image/{BANK_ID}-{STK}-compact2.jpg?amount=50000&addInfo=NAP{user_id}"
    bot.send_photo(message.chat.id, qr_url, caption=f"🏦 **STK:** `{STK}`\n📝 **Nội dung:** `NAP {user_id}`", parse_mode="Markdown")

@bot.message_handler(commands=['plus'])
def plus_money(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, amt = message.text.split()
        users_col.update_one({"user_id": int(tid)}, {"$inc": {"balance": int(amt), "total_deposit": int(amt)}})
        bot.send_message(ADMIN_ID, f"✅ Đã cộng {int(amt):,} VND cho `{tid}`")
        bot.send_message(int(tid), f"✅ Bạn đã được cộng {int(amt):,} VND vào tài khoản!")
    except: bot.send_message(ADMIN_ID, "❌ Lỗi. Cú pháp: `/plus ID TIEN`")

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel_action(call):
    bot.edit_message_text("❌ Giao dịch đã bị hủy.", call.message.chat.id, call.message.message_id)

bot.polling(none_stop=True)
