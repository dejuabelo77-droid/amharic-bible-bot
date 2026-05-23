import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==================== STUDENT PERMISSION LIST ====================
# ⚠️ Put the approved Telegram IDs inside these brackets, separated by commas!
APPROVED_STUDENTS = [] 
# ==================================================================

# Temporary memory to track registration steps for new users
USER_STEPS = {}
USER_DATA = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # If already approved, let them study instantly!
    if user_id in APPROVED_STUDENTS:
        await update.message.reply_text(
            "📚 <b>እንኳን ደህና መጣህ! ወደ ማጥኛ ቦቱ መግባት ትችላለህ። ጥያቄህን አሁን መጠየቅ ትችላለህ።</b>\n\n"
            "Welcome! You have full access to the study bot. You can start studying and ask your questions now! ✨",
            parse_mode="HTML"
        )
        return

    # Start the registration question flow
    USER_STEPS[user_id] = "WAITING_NAME"
    await update.message.reply_text("📋 **እንኳን ደህና መጡ! እባክዎን ሙሉ ስምዎን እዚህ ይጻፉልኝ:-**")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_text = update.message.text.strip()

    # If user is already approved, connect them straight to Gemini AI
    if user_id in APPROVED_STUDENTS:
        try:
            client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_text
            )
            await update.message.reply_text(response.text)
        except Exception as e:
            logging.error(f"Gemini Error: {e}")
            await update.message.reply_text("⚠️ Connection error. Please try again.")
        return

    # --- Registration Conversation Logic ---
    step = USER_STEPS.get(user_id)

    if step == "WAITING_NAME":
        USER_DATA[user_id] = {"name": user_text}
        USER_STEPS[user_id] = "WAITING_GENDER"
        await update.message.reply_text("ጾታዎ ምንድነው? ('ወንድ' ወይም 'ሴት')")
        return

    elif step == "WAITING_GENDER":
        if user_text not in ["ወንድ", "ሴት", "Male", "Female"]:
            await update.message.reply_text("❌ እባክዎ 'ወንድ' ወይም 'ሴት' ይበሉ!")
            return
        
        # Registration finished! Show the Bilingual Waiting Gate screen
        USER_STEPS[user_id] = "PENDING"
        await update.message.reply_text(
            f"📨 <b>ማመልከቻዎ ተልኳል! ነገር ግን መምህሩ ፈቃድ እስኪሰጥህ ድረስ መጠበቅ አለብህ።</b>\n"
            f"--------------------------------------------------\n"
            f"<b>Your application has been sent! Please wait until the teacher grants you access permission.</b>\n\n"
            f"እባክህ ይህንን መለያ ቁጥር (ID) ኮፒ አድርገህ ለመምህርህ ላክ:\n"
            f"Please copy and send this ID number to your teacher:\n"
            f"🆔 <code>{user_id}</code>",
            parse_mode="HTML"
        )
        return

    # If they try to text while status is still Pending
    elif USER_STEPS.get(user_id) == "PENDING":
        await update.message.reply_text(
            f"⏳ <b>ፈቃድ እየተጠባበቅክ ነው። እባክህ መምህሩ እስኪያጸድቅህ ድረስ ታገስ።</b>\n"
            f"Please wait for authorization. Your ID: <code>{user_id}</code>",
            parse_mode="HTML"
        )

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
