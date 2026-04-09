import os, json, boto3, telebot, uuid
from telebot import types
from datetime import datetime
from boto3.dynamodb.conditions import Attr

# Configuration
TOKEN = os.environ.get('TELEGRAM_TOKEN') 
SQS_URL = os.environ.get('SQS_URL')
REGION = "eu-west-1"
TABLE_NAME = "AidLogixInventory"

# AWS Initialization
sqs = boto3.client('sqs', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

bot = telebot.TeleBot(TOKEN)

# --- UI Menus ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🆘 Request Aid", "📦 Donate Items", "📊 My Status", "ℹ️ About System")
    return markup

def categories_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🏥 Medical Support", "🍕 Food & Water", "😴 Sleeping Gear", "🔙 Back to Main")
    return markup

# --- Handlers ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 
        f"Hello {message.from_user.first_name}!\nWelcome to AidLogix - Cloud Logistics System.",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda m: m.text == "ℹ️ About System")
def about_system(message):
    about_text = (
        "🤖 **AidLogix Platform**\n\n"
        "A smart management platform designed to organize equipment distribution and aid in emergencies.\n"
        "The system replaces manual logging with a centralized cloud system, ensuring aid reaches its destination in real-time."
    )
    bot.send_message(message.chat.id, about_text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📊 My Status")
def my_status(message):
    username = message.from_user.username or "Guest"
    bot.send_message(message.chat.id, "🔍 Fetching your data from the cloud...")
    
    try:
        response = table.scan(FilterExpression=Attr('user').eq(username))
        items = response.get('Items', [])
        
        if not items:
            bot.send_message(message.chat.id, "No records found for your user.")
            return

        requests = [i for i in items if i['type'] == "NEED"]
        donations = [i for i in items if i['type'] == "DONATION"]

        report = f"📊 **Activity Report for {username}:**\n\n"
        
        report += "🆘 **Aid Requests (Needs):**\n"
        if not requests: report += "_No open requests_\n"
        for req in requests:
            report += f"• {req['content']} ({req.get('category', 'General')})\n"
            
        report += "\n📦 **Donations Registered:**\n"
        if not donations: report += "_No donations registered_\n"
        for don in donations:
            report += f"• {don['content']} ({don.get('category', 'General')})\n"

        bot.send_message(message.chat.id, report, parse_mode="Markdown")
            
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Error connecting to the database.")

# --- Data Entry Flow ---
@bot.message_handler(func=lambda m: m.text in ["🆘 Request Aid", "📦 Donate Items"])
def select_category(message):
    action_type = "NEED" if "Request" in message.text else "DONATION"
    msg = bot.send_message(message.chat.id, "Select Category:", reply_markup=categories_menu())
    bot.register_next_step_handler(msg, ask_details, action_type)

def ask_details(message, action_type):
    if message.text == "🔙 Back to Main":
        bot.send_message(message.chat.id, "Returning...", reply_markup=main_menu())
        return

    category = message.text
    msg = bot.send_message(message.chat.id, f"Selected: {category}\nPlease describe items and quantity:")
    bot.register_next_step_handler(msg, final_process, action_type, category)

def final_process(message, action_type, category):
    item_content = message.text
    unique_id = str(uuid.uuid4())[:8]
    
    try:
        # Save to DynamoDB
        table.put_item(
            Item={
                'uid': unique_id,
                'user': message.from_user.username or "Guest",
                'type': action_type,
                'category': category,
                'content': item_content,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'status': 'Open'
            }
        )
        
        # Send to SQS
        payload = {"id": unique_id, "type": action_type, "content": item_content}
        sqs.send_message(QueueUrl=SQS_URL, MessageBody=json.dumps(payload))

        bot.send_message(
            message.chat.id, 
            f"✅ Successfully registered!\n🆔 Entry ID: `{unique_id}`", 
            parse_mode="Markdown", 
            reply_markup=main_menu()
        )
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Error saving data to the cloud.")

if __name__ == "__main__":
    bot.polling(none_stop=True)
