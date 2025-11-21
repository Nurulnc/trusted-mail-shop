import telebot
from telebot import types

# === তোমার তথ্য ===
TOKEN = "8483604629:AAFNpyosW51VqNiwz6lJs-3CNhnXXZKc53o"
ADMIN_ID = 1651695602

# প্রতি ক্যাটাগরির দাম (টাকায়)
PRICES = {
    "edu": 3,
    "outlook": 3,    # তুমি যা চাও
    "hotmail": 3     # তুমি যা চাও
}

PAYMENT_INFO = """💳 Payment Methods:
🔴 bKash: 01815243007
🟢 Nagad: 01815243007
🔵 Binance Pay: 38017799
**Total Amount: {total} Taka** ({quantity} × {price} Tk per account)
📤 Send **screenshot** after payment."""

user_data = {}  # {user_id: {'category': 'edu/outlook/hotmail', 'quantity':.., 'total':.., 'state':.., 'admin_msg_id':..}}

bot = telebot.TeleBot(TOKEN)

# ===================== START =====================
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_edu = types.InlineKeyboardButton("🟢 Buy .EDU Email (3 Tk)", callback_data="cat_edu")
    btn_outlook = types.InlineKeyboardButton("🔵 Buy Outlook Account (3 Tk)", callback_data="cat_outlook")
    btn_hotmail = types.InlineKeyboardButton("🟡 Buy Hotmail Account (3 Tk)", callback_data="cat_hotmail")
    markup.add(btn_edu, btn_outlook, btn_hotmail)

    bot.send_message(message.chat.id,
                     "🌟 **Account Seller Bot** 🌟\n\n"
                     "নিচের অপশন থেকে যেটা কিনতে চাও সেটা বেছে নাও 👇",
                     parse_mode="Markdown", reply_markup=markup)

# ===================== ক্যাটাগরি সিলেক্ট =====================
@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def category_selected(call):
    category = call.data.split("_")[1]  # edu / outlook / hotmail
    name = {"edu": ".EDU Email", "outlook": "Outlook Account", "hotmail": "Hotmail Account"}[category]

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=f"📋 Order {name}")

    user_data[call.from_user.id] = {
        "category": category,
        "state": "waiting_quantity"
    }

    bot.send_message(call.message.chat.id,
                     f"📦 **কতগুলো {name} কিনবেন?**\n\n"
                     "শুধু সংখ্যা লিখুন (যেমন: ১০)",
                     parse_mode="Markdown")

# ===================== কোয়ান্টিটি =====================
@bot.message_handler(func=lambda m: m.from_user.id in user_data and user_data[m.from_user.id]["state"] == "waiting_quantity")
def handle_quantity(message):
    user_id = message.from_user.id
    try:
        quantity = int(message.text.strip())
        if quantity < 1:
            raise ValueError
    except:
        bot.send_message(user_id, "❌ শুধু পজিটিভ সংখ্যা লিখুন (যেমন: 5)")
        return

    category = user_data[user_id]["category"]
    price_per = PRICES[category]
    total = quantity * price_per

    user_data[user_id].update({
        "quantity": quantity,
        "total": total,
        "price_per": price_per,
        "state": "waiting_screenshot"
    })

    bot.send_message(user_id, PAYMENT_INFO.format(
        total=total, quantity=quantity, price=price_per
    ), parse_mode="Markdown")

    bot.send_message(user_id, "📤 এখন **পেমেন্ট স্ক্রিনশট** পাঠান।", parse_mode="Markdown")

# ===================== স্ক্রিনশট =====================
@bot.message_handler(content_types=['photo'],
                     func=lambda m: m.from_user.id in user_data and user_data[m.from_user.id]["state"] == "waiting_screenshot")
def handle_photo(message):
    user_id = message.from_user.id
    data = user_data[user_id]
    cat = data["category"]
    name = {"edu": ".EDU Email", "outlook": "Outlook", "hotmail": "Hotmail"}[cat]

    # ফরওয়ার্ড স্ক্রিনশট
    forwarded = bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)

    username = message.from_user.username or "No username"
    full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()

    admin_text = (f"🟢 **NEW ORDER [{name.upper()}]** 🟢\n\n"
                  f"👤 **User**: {full_name}\n"
                  f"🆔 **ID**: <code>{user_id}</code>\n"
                  f"✏️ **Username**: @{username}\n"
                  f"📦 **Quantity**: {data['quantity']} pc(s)\n"
                  f"💰 **Total**: {data['total']} Taka\n\n"
                  f"📸 Screenshot received. Waiting for **Transaction ID**...")

    sent = bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML", reply_to_message_id=forwarded.message_id)

    bot.send_message(user_id, "✅ স্ক্রিনশট পাওয়া গেছে!\n\n🔤 এখন **Transaction ID** লিখুন।", parse_mode="Markdown")

    user_data[user_id].update({
        "state": "waiting_txnid",
        "admin_msg_id": sent.message_id
    })

# ===================== ট্রানজেকশন আইডি =====================
@bot.message_handler(func=lambda m: m.from_user.id in user_data and user_data[m.from_user.id]["state"] == "waiting_txnid")
def handle_txnid(message):
    user_id = message.from_user.id
    txn_id = message.text.strip()
    data = user_data[user_id]
    cat_name = {"edu": ".EDU Email", "outlook": "Outlook", "hotmail": "Hotmail"}[data["category"]]

    bot.send_message(ADMIN_ID,
                     f"🔤 **Transaction ID**: <code>{txn_id}</code>",
                     parse_mode="HTML",
                     reply_to_message_id=data["admin_msg_id"])

    bot.send_message(user_id,
                     f"🎯 **অর্ডার গৃহীত!**\n\n"
                     f"⏳ এডমিন পেমেন্ট চেক করছেন...\n"
                     f"📦 {data['quantity']}টা {cat_name} ৫-১০ মিনিটে পাবেন।\n"
                     "ধন্যবাদ ❤️",
                     parse_mode="Markdown")

    user_data.pop(user_id, None)

# ===================== ADMIN APPROVE =====================
@bot.message_handler(commands=['approve'])
def approve_order(message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        parts = message.text.split()
        if len(parts) < 4:
            raise ValueError

        target_id = int(parts[1])
        qty_wanted = int(parts[2])
        category = parts[3].lower()          # edu / outlook / hotmail
        accounts = parts[4:]                 # mail:pass বা শুধু mail

        if category not in ["edu", "outlook", "hotmail"]:
            bot.send_message(ADMIN_ID, "❌ ক্যাটাগরি শুধু: edu, outlook, hotmail")
            return

        if len(accounts) != qty_wanted:
            bot.send_message(ADMIN_ID, f"❌ ভুল! চেয়েছে {qty_wanted}টা, দিয়েছো {len(accounts)}টা।")
            return

        name = {"edu": ".EDU Email", "outlook": "Outlook Account", "hotmail": "Hotmail Account"}[category]
        acc_text = "\n".join([f"📧 <code>{acc}</code>" for acc in accounts])

        bot.send_message(target_id,
                         f"🎉 **পেমেন্ট ভেরিফাইড!**\n\n"
                         f"✅ আপনার {name} গুলো:\n\n"
                         f"{acc_text}\n\n"
                         "🔐 তৎক্ষণাৎ পাসওয়ার্ড চেঞ্জ করুন!\n"
                         "❤️ ধন্যবাদ!",
                         parse_mode="HTML")

        bot.send_message(ADMIN_ID, f"✅ {qty_wanted}টা {name} পাঠানো হয়েছে → {target_id}")

    except Exception as e:
        bot.send_message(ADMIN_ID,
                         "❌ **ভুল ফরম্যাট!**\n\n"
                         "ব্যবহার:\n"
                         "<code>/approve user_id qty category mail1:pass1 mail2:pass2 ...</code>\n"
                         "ক্যাটাগরি: edu / outlook / hotmail",
                         parse_mode="HTML")

# ===================== Fallback =====================
@bot.message_handler(func=lambda m: True)
def fallback(message):
    if message.from_user.id not in user_data:
        bot.send_message(message.chat.id, "👋 /start চেপে অর্ডার দিন।")

bot.infinity_polling()