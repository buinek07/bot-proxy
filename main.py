import telebot
from telebot import types
from pymongo import MongoClient
import requests

# --- CẤU HÌNH THÔNG TIN (THAY ĐỔI TẠI ĐÂY) ---
TOKEN = '8371917325:AAE4ftu8HJkA5CyNd5On69r39WS10Osl1JQ'
MONGO_URI = 'mongodb+srv://buinek:<17/12/07Bui>@bottlee.qnaas3k.mongodb.net/?appName=bottlee' # Ví dụ: mongodb+srv://admin:password@cluster...
BANK_ID = 'MB'        # Mã ngân hàng nhận tiền (VD: MB, VCB, ICB)
STK = 'SỐ_TK_CỦA_BẠN'  # Số tài khoản ngân hàng của bạn

# Thông tin PayOS (Để xử lý nạp tiền tự động sau này)
PAYOS_CLIENT_ID = '0f29346e-d60e-4ba4-b575-ede0dcb019e1'
PAYOS_API_KEY = '2a6c7ca4-cbf1-4f6a-bb58-e8fffcfd265b'
PAYOS_CHECKSUM = '420b12b52bfb319c0b4621375f98816672f02f5541c0995a2528533d353d5adf'

# Khởi tạo Bot và Database
bot = telebot.TeleBot(TOKEN)
try:
    client = MongoClient(MONGO_URI)
    db = client.bot_proxy_db
    users_col = db.users
except Exception as e:
    print(f"Lỗi kết nối Database: {e}")

# --- MENU CHÍNH ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('👤 Tài khoản', '🛒 Mua hàng', '💳 Nạp tiền', '📋 Đơn hàng', '📞 Admin')
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    # Kiểm tra/Tạo tài khoản mới trong database
    if not users_col.find_one({"user_id": user_id}):
        users_col.insert_one({"user_id": user_id, "balance": 0, "total_recharge": 0})
    
    bot.send_message(message.chat.id, "🤖 Chào mừng bạn đến với Hệ thống Proxy Tự động!", reply_markup=main_menu())

# --- XỬ LÝ TÀI KHOẢN ---
@bot.message_handler(func=lambda m: m.text == '👤 Tài khoản')
def account_info(message):
    user = users_col.find_one({"user_id": message.from_user.id})
    balance = user['balance'] if user else 0
    text = (f"👤 **THÔNG TIN TÀI KHOẢN**\n\n"
            f"🆔 ID: `{message.from_user.id}`\n"
            f"💰 Số dư: `{balance:,}` VNĐ\n"
            f"🛠 Loại khách: Thành viên")
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# --- XỬ LÝ NẠP TIỀN (GỬI ẢNH QR TRỰC TIẾP) ---
@bot.message_handler(func=lambda m: m.text == '💳 Nạp tiền')
def recharge(message):
    user_id = message.from_user.id
    amount = 50000  # Mức nạp mặc định
    
    # Tạo link QR từ VietQR API
    qr_url = f"https://img.vietqr.io/image/{BANK_ID}-{STK}-compact2.jpg?amount={amount}&addInfo=NAP{user_id}"
    
    caption = (f"🏦 **HỆ THỐNG NẠP TIỀN TỰ ĐỘNG**\n\n"
               f"💵 Số tiền: `{amount:,}` VNĐ\n"
               f"📝 Nội dung chuyển khoản: `NAP {user_id}`\n\n"
               f"⚠️ **Lưu ý:** Bạn phải chuyển đúng nội dung để hệ thống tự động cộng tiền!")
    
    bot.send_photo(message.chat.id, qr_url, caption=caption, parse_mode="Markdown")

# --- XỬ LÝ MUA HÀNG & XÁC NHẬN ---
@bot.message_handler(func=lambda m: m.text == '🛒 Mua hàng')
def shop(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌐 Proxy Tĩnh Viettel (5.000đ/24h)", callback_data="conf_vte"))
    bot.send_message(message.chat.id, "Vui lòng chọn loại Proxy cần mua:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "conf_vte")
def confirm_purchase(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("✅ Xác nhận thanh toán", callback_data="buy_vte"),
               types.InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel_action"))
    
    text = ("⚠️ **XÁC NHẬN GIAO DỊCH**\n\n"
            "📦 Sản phẩm: Proxy Tĩnh Viettel\n"
            "💰 Giá: 5,000 VNĐ\n"
            "⏳ Thời hạn
