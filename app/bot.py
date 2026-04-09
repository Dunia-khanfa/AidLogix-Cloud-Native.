import os, json, boto3, telebot, uuid
from telebot import types
from datetime import datetime
from boto3.dynamodb.conditions import Attr

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

# --- פונקציות עזר לתפריטים ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🆘 Request Aid", "📦 Donate Items", "📊 My Status", "ℹ️ About System")
    return markup

def categories_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🏥 Medical Support", "🍕 Food & Water", "😴 Sleeping Gear", "🔙 Back to Main")
    return markup

# --- ניהול פקודות בסיסיות ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 
        f"שלום {message.from_user.first_name}!\nברוך הבא למערכת AidLogix - ניהול לוגיסטי חכם.",
        reply_markup=main_menu()
    )

# --- לוגיקה לכפתור "About System" ---
@bot.message_handler(func=lambda m: m.text == "ℹ️ About System")
def about_system(message):
    about_text = (
        "🤖 **AidLogix v2.0**\n\n"
        "מערכת זו מבוססת ענן (AWS) ונועדה לנהל מלאי לוגיסטי בזמן חירום.\n"
        "• **IaC:** Terraform\n"
        "• **Database:** DynamoDB\n"
        "• **Messaging:** SQS\n\n"
        "כל בקשה נרשמת בתור מאובטח ומעובדת ע\"י צוות הלוגיסטיקה."
    )
    bot.send_message(message.chat.id, about_text, parse_mode="Markdown")

# --- לוגיקה לכפתור "My Status" (שליפת נתונים מהענן!) ---
@bot.message_handler(func=lambda m: m.text == "📊 My Status")
def my_status(message):
    username = message.from_user.username or "Guest"
    bot.send_message(message.chat.id, "🔍 Searching the cloud database...")
    
    try:
        # שליפת כל הפריטים של המשתמש הספציפי מה-DynamoDB
        response = table.scan(
            FilterExpression=Attr('user').eq(username)
        )
        items = response.get('Items', [])
        
        if not items:
            bot.send_message(message.chat.id, "No active requests found for your user.")
        else:
            report = f"📋 **Your Active Requests ({len(items)}):**\n\n"
            for item in items[:5]: # מציג את 5 האחרונים
                report += f"🔹 {item['content']} ({item['category']})\n   Status: `{item['status']}`\n\n"
            bot.send_message(message.chat.id, report, parse_mode="Markdown")
            
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Error fetching data from AWS.")

# --- זרימת בקשות ותרומות ---
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
    msg = bot.send_message(message.chat.id, f"Selected: {category}\nPlease enter quantity and item name:")
    bot.register_next_step_handler(msg, final_process, action_type, category)

def final_process(message, action_type, category):
    item_content = message.text
    unique_id = str(uuid.uuid4())[:8]
    
    try:
        table.put_item(
            Item={
                'uid': unique_id,
                'user': message.from_user.username or "Guest",
                'type': action_type,
                'category': category,
                'content': item_content,
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'status': 'Open'
            }
        )
        bot.send_message(message.chat.id, f"✅ Registered! ID: `{unique_id}`", parse_mode="Markdown", reply_markup=main_menu())
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Connection Error.")

if __name__ == "__main__":
    bot.polling(none_stop=True)
