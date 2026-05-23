import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# Enable logging to track errors on Render
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==================== STUDENT PERMISSION LIST ====================
# ⚠️ Add authorized student Telegram IDs inside this list, separated by commas.
# Example: APPROVED_STUDENTS = [558493022, 994827364]
APPROVED_STUDENTS = [] 
# ==================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # Check if the student is already approved
    if user_id in APPROVED_STUDENTS:
        await update.message.reply_text(
            "📚 <b>እንኳን ደህና መጣህ! ወደ ማጥኛ ቦቱ መግባት ትችላለህ። ጥያቄህን አሁን መጠየቅ ትችላለህ።</b>\n\n"
            "Welcome! You have full access to the study bot. You can start studying and ask your questions now! ✨",
            parse_mode="HTML"
        )
        return

    # If the student is new/not approved, show the bilingual waiting message
    await update.message.reply_text(
        f"⏳ <b>ተመዝግበሃል! ነገር ግን መምህሩ ፈቃድ እስኪሰጥህ ድረስ መጠበቅ አለብህ።</b>\n"
        f"--------------------------------------------------\n"
        f"<b>You have registered! Please wait until the teacher grants you access permission.</b>\n\n"
        f"እባክህ ይህንን መለያ ቁጥር (ID) ኮፒ አድርገህ ለመምህርህ ላክ:\n"
        f"Please copy and send this ID number to your teacher:\n"
        f"🆔 <code>{user_id}</code>",
        parse_mode="HTML"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # Gatekeeper: If they are not approved, remind them to wait in both languages
    if user_id not in APPROVED_STUDENTS:
        await update.message.reply_text(
            f"❌ <b>ይቅርታ! ይህንን ቦት ለመጠቀም መጀመሪያ ከመምህሩ ፈቃድ ማግኘት አለብህ።</b>\n"
            f"--------------------------------------------------\n"
            f"<b>Access Denied. You must get permission from the teacher first to use this bot.</b>\n\n"
            f"Your ID: <code>{user_id}</code>",
            parse_mode="HTML"
        )
        return

    # Your finished Gemini AI study feature
    user_text = update.message.text
    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_text
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"Gemini API Error: {e}")
        await update.message.reply_text("⚠️ Connection error. Please try again.")

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return
        
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
