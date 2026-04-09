import os, json, boto3, telebot, uuid
from telebot import types
from datetime import datetime

# הגדרות ענן
TOKEN = os.environ.get('TELEGRAM_TOKEN') 
SQS_URL = os.environ.get('SQS_URL')
REGION = "eu-west-1"
TABLE_NAME = "AidLogixInventory"

# חיבור ל-AWS
sqs = boto3.client('sqs', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

bot = telebot.TeleBot(TOKEN)

# --- תפריטים ---

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🆘 Request Aid", "📦 Donate Items", "📊 My Status", "ℹ️ About System")
    return markup

def categories_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🏥 Medical Support", "🍕 Food & Water", "😴 Sleeping Gear", "🔙 Back to Main")
    return markup

# --- ניהול הודעות ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 
        f"שלום {message.from_user.first_name}!\nברוך הבא למערכת AidLogix - ניהול לוגיסטי חכם בזמן אמת.",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda m: m.text in ["🆘 Request Aid", "📦 Donate Items"])
def select_category(message):
    action_type = "NEED" if "Request" in message.text else "DONATION"
    msg = bot.send_message(message.chat.id, "Select category:", reply_markup=categories_menu())
    bot.register_next_step_handler(msg, ask_details, action_type)

def ask_details(message, action_type):
    if message.text == "🔙 Back to Main":
        bot.send_message(message.chat.id, "Returning...", reply_markup=main_menu())
        return

    category = message.text
    msg = bot.send_message(
        message.chat.id, 
        f"Selected: {category}\nPlease enter item description and quantity (e.g., 20 units):",
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, final_process, action_type, category)

def final_process(message, action_type, category):
    item_content = message.text
    unique_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%H:%M:%S | %d/%m/%Y")
    
    try:
        # שמירה ב-DynamoDB עם קטגוריה
        table.put_item(
            Item={
                'uid': unique_id,
                'user': message.from_user.username or "Guest",
                'type': action_type,
                'category': category,
                'content': item_content,
                'timestamp': timestamp,
                'status': 'Open'
            }
        )
        
        # הודעת סיכום מעוצבת למשתמש
        response = (
            f"✅ **Entry Confirmed!**\n\n"
            f"🆔 **ID:** `{unique_id}`\n"
            f"📂 **Category:** {category}\n"
            f"📝 **Details:** {item_content}\n"
            f"🕒 **Time:** {timestamp}\n\n"
            f"Our logistics team has been notified via SQS."
        )
        
        bot.send_message(message.chat.id, response, parse_mode="Markdown", reply_markup=main_menu())
        
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Error connecting to AWS. Please check logs.", reply_markup=main_menu())

if __name__ == "__main__":
    bot.polling(none_stop=True)
