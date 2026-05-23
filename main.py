import logging
import time
import requests
import os
import threading
import random
from flask import Flask
from google import genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, PollAnswerHandler, MessageHandler, filters, CallbackQueryHandler

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- CONFIGURATION KEYS ---
TELEGRAM_TOKEN = "6727548522:AAEcmfi23n8YQFksAC5msuTL36raJXFZEd8"
ADMIN_ID = 6840024600  
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"  

# --- TOTAL CHAPTERS IN ACTS ---
TOTAL_ACTS_CHAPTERS = 28

# --- COMPLETE DATA BANK FOR ACTS 1 (30 MCQs + 5 BLANKS) ---
QUIZ_BANK = {
    "የሐዋርያት ሥራ 1": {
        "mcq": [
            # 1-10 (Original Questions)
            {"question": "የሐዋርያት ሥራ መጽሐፍ የተጻፈው ለማን ነው?", "options": ["ለቴዎፍሎስ", "ለጢሞቴዎስ", "ለቲቶ", "ለታዴዎስ"], "correct": 0},
            {"question": "ኢየሱስ ከተሰቃየ በኋላ ለሐዋርያት ለስንት ቀናት ታያቸው?", "options": ["7 ቀናት", "12 ቀናት", "30 ቀናት", "40 ቀናት"], "correct": 3},
            {"question": "ኢየሱስ ሐዋርያትን ከየት ከተማ እንዳይወጡ አዟቸዋል?", "options": ["ከገሊላ", "ከኢየሩሳሌም", "ከሰማርያ", "ከናዝሬት"], "correct": 1},
            {"question": "ዮሐንስ በውኃ አጠመቀ፥ እናንተ ግን በምን ትጠመቃላችሁ ተባለ?", "options": ["በእሳት", "በዘይት", "በመንፈስ ቅዱስ", "በወይን"], "correct": 2},
            {"question": "ኢየሱስ ወደ ሰማይ ያረገው ከየትኛው ተራራ ነው?", "options": ["ከደብረ ዘይት ተራራ", "ከሲና ተራራ", "ከናባው ተራራ", "ከታቦር ተራራ"], "correct": 0},
            {"question": "በቁጥር 15 ላይ በአንድነት በአምልኮ የተሰበሰቡት ሰዎች ቁጥር ስንት ነበር?", "options": ["በግምት 12", "በግምት 50", "በግምት 120", "በግምት 500"], "correct": 2},
            {"question": "ይሁዳ በካደበት ገንዘብ የተገዛውና 'የደም መሬት' የተባለው እርሻ ስም ማን ይባላል?", "options": ["ጎልጎታ", "አኬልዳማ", "ጌተሰማኒ", "ሰሊሆም"], "correct": 1},
            {"question": "በይሁዳ ምትክ እንዲመረጡ የቀረቡት ሁለት ሰዎች እነማን ነበሩ?", "options": ["በርናባስና ሳውል", "ዮሴፍ በርሳባስና ማትያስ", "እስጢภาኖስና ፊልጶስ", "ሲላስና ጢሞቴዎስ"], "correct": 1},
            {"question": "ሐዋርያት በሁለቱ ሰዎች መካከል ለመምረጥ ምን አደረጉ?", "options": ["ተመራረጡ", "ዕጣ ተጣጣሉ", "ማርያምን ጠየቁ", "ምልክት ጠበቁ"], "correct": 1},
            {"question": "በመጨረሻም ከዐሥራ አንዱ ሐዋርያት ጋር የተቆጠረው ማን ነው?", "options": ["ማትያስ", "ዮሴፍ ኢዮስጦስ", "ጳውሎስ", "ማርቆስ"], "correct": 0},
            
            # 11-20 (New Balanced Context Questions)
            {"question": "ኢየሱስ ከመሰቃየቱ በፊት የመረጣቸውን ሐዋርያት በምን አዟቸው ነበር?", "options": ["በሕግ", "በመንፈስ ቅዱስ", "በመልአክ", "በራዕይ"], "correct": 1},
            {"question": "ደቀ መዛሙርቱ ኢየሱስን 'ጌታ ሆይ፥ በዚህ ወራት ለእስራኤል መንግሥትን ______?' ብለው ጠየቁት።", "options": ["ትሰጣለህን", "ትመልሳለህን", "ታጠፋለህን", "ትቀይራለህን"], "correct": 1},
            {"question": "ኢየሱስ አብ በገዛ ሥልጣኑ ያደረገውን ምንን ማወቅ ለእናንተ አልተሰጣችሁም አላቸው?", "options": ["ምስጢራትን", "ሰማያትን", "ዘመናትንና ወራትን", "የሞት ቀንን"], "correct": 2},
            {"question": "መንፈስ ቅዱስ በወረደ ጊዜ እስከ የትኛው የምድር ዳርቻ ድረስ ምስክሮቼ ትሆናላችሁ አላቸው?", "options": ["እስከ አፍሪካ", "እስከ ሮሜ", "እስከ ምድር ዳርቻ", "እስከ ይሁዳ ብቻ"], "correct": 2},
            {"question": "ኢየሱስ ይህንን ከተናገረ በኋላ ወደ ላይ ሲያርግ ምን ከዓይናቸው ሰውረችው?", "options": ["ደመና", "እሳት", "ብርሃን", "ጭጋግ"], "correct": 0},
            {"question": "ኢየሱስ ወደ ሰማይ ሲሄድ ደቀ መዛሙርቱ ወደ የት ትኩር ብለው ይመለከቱ ነበር?", "options": ["ወደ ምድር", "ወደ ሰማይ", "ወደ ተራራው", "ወደ ኢየሩሳሌም"], "correct": 1},
            {"question": "ደቀ መዛሙርቱ ወደ ሰማይ ሲያዩ በአጠገባቸው የቆሙት ሁለት ሰዎች ምን ለብሰው ነበር?", "options": ["ጥቁር ልብስ", "ቀይ ልብስ", "ነጭ ልብስ", "የሐር ልብስ"], "correct": 2},
            {"question": "ነጭ ልብስ የለበሱት ሰዎች ደቀ መዛሙርቱን ማን ብለው ጠሯቸው?", "options": ["የኢየሩሳሌም ሰዎች", "የገሊላ ሰዎች", "የይሁዳ ሰዎች", "የሰማርያ ሰዎች"], "correct": 1},
            {"question": "ከደብረ ዘይት ተራራ እስከ ኢየሩሳሌም ያለው ርቀት በሰንበት ቀን ጉዞ ምን ያህል ነው?", "options": ["የአንድ ሰዓት መንገድ", "የቅርብ መንገድ", "የሦስት ቀን መንገድ", "የቀን መንገድ"], "correct": 1},
            {"question": "ደቀ መዛሙርቱ ወደ ኢየሩሳሌም በተመለሱ ጊዜ ወደ የትኛው ክፍል ወጡ?", "options": ["ወደ ቤተ መቅደስ", "ወደ ምኩራብ", "ወደ ማረፊያቸው ሰገነት", "ወደ ገበያ"], "correct": 2},

            # 21-30 (Final Set to reach 30 MCQs)
            {"question": "በሰገነቱ ላይ አብረው ከነበሩት መካከል የያዕቆብ ልጅ ማን ይገኝበታል?", "options": ["ይሁዳ", "ቶማስ", "ማቴዎስ", "በርተሎሜዎስ"], "correct": 0},
            {"question": "በጸሎት ክፍል ውስጥ ከሐዋርያት ጋር በአንድነት የሚተጉት እነማን ነበሩ?", "options": ["ሴቶችና የኢየሱስ እናት ማርያም", "ፈሪሳውያን", "የሮሜ ወታደሮች", "ሌሎች ሕዝቦች"], "correct": 0},
            {"question": "በወንድሞች መካከል ተነሥቶ ንግግር ያደረገው መሪ ሐዋርያ ማን ነው?", "options": ["ዮሐንስ", "ጰጥሮስ", "ያዕቆብ", "እንድርያስ"], "correct": 1},
            {"question": "ጰጥሮስ ስለ ይሁዳ ክህደት አስቀድሞ በመንፈስ ቅዱስ የተነገረው የማን መጽሐፍ መፈጸም ነበረበት አለ?", "options": ["የኢሳይያስ", "የዳዊት (መዝሙር)", "የኤርምያስ", "የሙሴ"], "correct": 1},
            {"question": "ይሁዳ ኢየሱስን ለያዙት ሰዎች ምን ሆነላቸው ተብሎ ተጽፏል?", "options": ["ጠላት", "መሪ", "ዳኛ", "ምስክር"], "correct": 1},
            {"question": "ይሁዳ ከእኛ ጋር ተቆጥሮ የትኛውን አገልግሎት አግኝቶ ነበር?", "options": ["የመቅደስ አገልግሎት", "ይህንን አገልግሎት (ዕጣ)", "የንጉሥነት ክብር", "የምኩራብ አለቅነት"], "correct": 1},
            {"question": "በመዝሙር መጽሐፍ 'መኖሪያው ምድረ በዳ ትሁን' የሚለው ኃይለ ቃል ስለ ማን የተጻፈ ነው?", "options": ["ስለ ይሁዳ", "ስለ ጰጥሮስ", "ስለ ሄሮድስ", "ስለ ጲላጦስ"], "correct": 0},
            {"question": "በመዝሙር ላይ 'ሹመቱን ሌላ ይውሰዳት' ተብሎ የተጻፈውን ለመፈጸም የተፈለገው መመዘኛ ምን ነበር?", "options": ["ሀብታም መሆን", "ከዮሐንስ ጥምቀት ጀምሮ እስከ እርገቱ አብሮ መሆን", "የነገደ ይሁዳ መሆን", "በእድሜ ትልቅ መሆን"], "correct": 1},
            {"question": "ዮሴፍ በርሳባስ ሌላ ስም ምን ተብሎ ይጠራ ነበር?", "options": ["ኢዮስጦስ", "ማትያስ", "ማርቆስ", "ሉቃስ"], "correct": 0},
            {"question": "ሐዋርያት ዕጣ ከመጣጣላቸው በፊት ወደ ማን ጸለዩ?", "options": ["ወደ መላእክት", "ሁሉን ወደሚያውቅ ወደ ጌታ", "ወደ ሕዝቡ", "ወደ ሊቀ ካህናቱ"], "correct": 1}
        ],
        "blank": [
            {"question": "ኢየሱስ ሐዋርያትን 'መንፈስ ቅዱስ በእናንተ ላይ በወረደ ጊዜ _________ ትቀበላላችሁ' አላቸው።", "answer": "ኃይል"},
            {"question": "በይሁዳ ምትክ በዕጣ የተመረጠው አዲሱ ሐዋርያ ስም _________ ይባላል።", "answer": "ማትያስ"},
            {"question": "የይሁዳ መሬት የሆነው አኬልዳማ ትርጉሙ _________ ማለት ነው።", "answer": "የደም መሬት"},
            {"question": "ኢየሱስ ወደ ሰማይ ካረገ በኋላ ሁለት ሰዎች ነጭ _________ ለብሰው በአጠገባቸው ቆሙ።", "answer": "ልብስ"},
            {"question": "ደቀ መዛሙርቱ ወደ ኢየሩሳሌም ከተመለሱ በኋላ በአንድነት ሆነው በ_________ ይተጉ ነበር።", "answer": "ጸሎት"}
        ]
    }
}

SUMMARY_BANK = {
    "የሐዋርያት ሥራ 1": "🌟 **የየሐዋርያት ሥራ ምዕራፍ 1 ዋና ትምህርቶችና ማጠቃለያ ተጠናቋል።**"
}

db = {"users": {}, "held_results": {}}
user_sessions = {}
poll_to_user = {}

flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Bot Core Framework Running Seamlessly!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE" else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in db["users"]:
        db["users"][user_id] = {
            "name": "", "gender": "", "registered": False, "approved": False, 
            "step": "AWAITING_NAME", "fail_count": 0, "passed_chapters": []
        }
        await update.message.reply_text("📋 **እንኳን ደህና መጡ! እባክዎ ሙሉ ስምዎን እዚህ ይጻፉልኝ፦**")
        return
    user = db["users"][user_id]
    if not user.get("approved", False):
        await update.message.reply_text("⏳ **ምዝገባዎ በአስተማሪው ዘንድ ገና አልተፈቀደም።**")
        return
    
    completed = len(user.get("passed_chapters", []))
    status_msg = f"👋 ሰላም {user['name']}!\n📊 የእርሶ የጥናት ስኬት: {completed}/{TOTAL_ACTS_CHAPTERS} ምዕራፎች ተጠናቀዋል።\n\n"
    if completed >= TOTAL_ACTS_CHAPTERS:
        status_msg += "🎉 ማሳሰቢያ፦ ሁሉንም ምዕራፎች ጨርሰዋል! ታላቁን የ 50 ጥያቄዎች ማጠቃለያ ፈተና ለመጀመር 👉 `/finalexam` ይጻፉ።"
    else:
        status_msg += "🔹 ንባብ ለመጀመር 👉 `/study` ይጻፉ\n🔹 ጥያቄ ለመጠየቅ ዝም ብለው መልዕክት ይጻፉ።"
        
    await update.message.reply_text(status_msg)

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()
    
    if user_id in db["users"] and not db["users"][user_id].get("registered", False):
        session = db["users"][user_id]
        if session["step"] == "AWAITING_NAME":
            session["name"] = text
            session["step"] = "AWAITING_GENDER"
            await update.message.reply_text(f"ጾታዎ ምንድነው? ('ወንድ' ወይም 'ሴት')")
            return
        elif session["step"] == "AWAITING_GENDER":
            if text not in ["ወንድ", "ሴት"]:
                await update.message.reply_text("❌ እባክዎ 'ወንድ' ወይም 'ሴት' ይበሉ!")
                return
            session["gender"] = text
            session["registered"] = True
            session["step"] = ""
            await update.message.reply_text("📨 ማመልከቻዎ ተልኳል! አስተማሪው እስኪያጸድቅ ይጠብቁ።")
            
            keyboard = [[InlineKeyboardButton("✅ ፍቀድ (Approve)", callback_data=f"approve_{user_id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            try:
                await context.bot.send_message(chat_id=ADMIN_ID, text=f"🔔 **አዲስ ተማሪ!**\n👤 ስም: {session['name']}\n🚻 ጾታ: {session['gender']}", reply_markup=reply_markup)
            except Exception: pass
            return

    if user_id in user_sessions and user_sessions[user_id]["type"] == "FINAL_BLANK":
        session = user_sessions[user_id]
        q_data = session["final_questions"][session["current_idx"]]
        correct_answer = q_data["answer"].strip().lower()
        
        if text.lower() == correct_answer:
            session["score"] += 1
            await update.message.reply_text("✅ ትክክል!")
        else:
            await update.message.reply_text(f"❌ ስህተት! ትክክለኛው መልስ: **{q_data['answer']}** ነበር።")
            
        session["current_idx"] += 1
        await send_next_final_question(context, user_id)
        return

    if user_id in user_sessions and user_sessions[user_id]["type"] == "BLANK":
        session = user_sessions[user_id]
        blank_questions = QUIZ_BANK[session["chapter"]]["blank"]
        current_blank_idx = session["current_blank_q"]
        
        correct_answer = blank_questions[current_blank_idx]["answer"].strip().lower()
        if text.lower() == correct_answer:
            session["score"] += 1
            await update.message.reply_text("✅ ትክክል!")
        else:
            await update.message.reply_text(f"❌ ስህተት! ትክክለኛው መልስ: **{blank_questions[current_blank_idx]['answer']}** ነበር።")
            
        session["current_blank_q"] += 1
        await send_next_question(context, user_id)
        return

    if user_id in db["users"] and db["users"][user_id].get("approved", False):
        if user_id in user_sessions: return
        if not ai_client:
            await update.message.reply_text("⚠️ AI በአሁኑ ጊዜ አልተገናኘም።")
            return
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        try:
            prompt = f"You are a professional Christian Bible Teacher. Answer this question accurately based on the 66 books of the Bible in Amharic: {text}"
            response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            await update.message.reply_text(response.text)
        except Exception:
            await update.message.reply_text("🤔 እባክዎ እንደገና ይሞክሩ።")

async def handle_approval_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if str(update.effective_user.id) != str(ADMIN_ID): return
    if query.data.startswith("approve_"):
        target = query.data.split("_")[1]
        if target in db["users"]:
            db["users"][target]["approved"] = True
            await query.edit_message_text(text="✅ ተማሪው ተፈቅዶለታል!")
            try:
                await context.bot.send_message(chat_id=int(target), text="🎉 ተፈቅዶልዎታል! ለመማር `/study` ይጻፉ።")
            except Exception: pass

async def study(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in db["users"] or not db["users"][user_id].get("approved", False):
        await update.message.reply_text("⚠️ ፍቃድ አልተሰጥዎትም።")
        return
    chapter_request = "የሐዋርያት ሥራ 1" if not context.args else " ".join(context.args).strip()
    if chapter_request not in QUIZ_BANK:
        await update.message.reply_text("❌ ምዕራፉ አልተዘጋጀም።")
        return
        
    await update.message.reply_text("📖 ንባቡን በማምጣት ላይ...")
    url = "https://raw.githubusercontent.com/霖/amharic-bible/master/acts/1.txt"
    try:
        response = requests.get(url)
        bible_text = response.text.strip() if response.status_code == 200 else "መጽሐፍ ቅዱስዎ ላይ ያንብቡ።"
        max_len = 3900
        if len(bible_text) > max_len:
            for i in range(0, len(bible_text), max_len):
                await update.message.reply_text(bible_text[i:i+max_len])
        else:
            await update.message.reply_text(bible_text)
            
        user_info = db["users"][user_id]
        fails = user_info.get("fail_count", 0)
        
        if fails == 0:
            required_seconds = 600  
        elif fails == 1:
            required_seconds = 900  
        else:
            required_seconds = 900 + ((fails - 1) * 300) 

        user_sessions[user_id] = {
            "chapter": chapter_request, "start_time": time.time(), "required_time": required_seconds,
            "type": "MCQ", "current_mcq_q": 0, "current_blank_q": 0, "score": 0
        }
        
        minutes_display = int(required_seconds // 60)
        await update.message.reply_text(f"⏱️ **የንባብ ሰዓት ተጀምሯል!**\n\n⚠️ ይህንን ምዕራፍ ለ **{minutes_display} ደቂቃ** በትኩረት ማንበብ አለብዎት። ካነበቡ በኋላ `/quiz` ይጻፉ።")
    except Exception:
        await update.message.reply_text("ስህተት አጋጥሟል።")

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in user_sessions:
        await update.message.reply_text("መጀመሪያ ንባብ ለመጀመር `/study` ይጻፉ!")
        return
        
    session = user_sessions[user_id]
    if "final" in session.get("type", "").lower(): return
    
    elapsed_time = time.time() - session["start_time"]
    remaining_seconds = session["required_time"] - elapsed_time
    
    if remaining_seconds > 0:
        minutes = int(remaining_seconds // 60)
        seconds = int(remaining_seconds % 60)
        await update.message.reply_text(f"🛑 **የማንበቢያ ጊዜዎ አልተጠናቀቀም!**\n\nእባክዎ ሌላ **{minutes} ደቂቃ ከ {seconds} ሰከንድ** ያንብቡ።")
        return
        
    await update.message.reply_text("🧠 **የምዕራፍ መፈተኛው ተከፍቷል!** መጀመሪያ የ MCQ ጥያቄዎች ይቀርባሉ...")
    await send_next_question(context, user_id)

async def send_next_question(context, user_id):
    session = user_sessions[user_id]
    chapter_data = QUIZ_BANK[session["chapter"]]
    
    if session["type"] == "MCQ":
        idx = session["current_mcq_q"]
        if idx < len(chapter_data["mcq"]):
            q_data = chapter_data["mcq"][idx]
            msg = await context.bot.send_quiz(
                chat_id=int(user_id),
                question=f"[MCQ] ጥያቄ {idx+1}/{len(chapter_data['mcq'])}:\n{q_data['question']}",
                options=q_data['options'], correct_option_id=q_data['correct'], is_anonymous=False
            )
            poll_to_user[msg.poll.id] = user_id
            return
        else:
            session["type"] = "BLANK"
            await context.bot.send_message(chat_id=int(user_id), text="📝 **አሁን ደግሞ የባዶ ቦታ መሙያ ጥያቄዎች ይጀምራሉ!**")
            
    if session["type"] == "BLANK":
        idx = session["current_blank_q"]
        if idx < len(chapter_data["blank"]):
            q_data = chapter_data["blank"][idx]
            await context.bot.send_message(chat_id=int(user_id), text=f"[ባዶ ቦታ] ጥያቄ {idx+1}/{len(chapter_data['blank'])}:\n\n{q_data['question']}")
            return
        else:
            await evaluate_and_route_results(context, user_id)

async def start_final_exam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_info = db["users"].get(user_id)
    
    if not user_info or len(user_info.get("passed_chapters", [])) < TOTAL_ACTS_CHAPTERS:
        await update.message.reply_text(f"🛑 **የማጠናቀቂያ ፈተናው አልተፈቀደም!**\n\nታላቁን ፈተና ለመውሰድ መጀመሪያ ሁሉንም {TOTAL_ACTS_CHAPTERS} ምዕራፎች ማለፍ አለብዎት።")
        return

    await update.message.reply_text("🎲 **ታላቁ የ 50 ጥያቄዎች ማጠቃለያ ፈተና በመዘጋጀት ላይ ነው...**")
    
    all_mcqs = []
    all_blanks = []
    for ch, data in QUIZ_BANK.items():
        all_mcqs.extend(data.get("mcq", []))
        all_blanks.extend(data.get("blank", []))
        
    random.shuffle(all_mcqs)
    random.shuffle(all_blanks)
    
    selected_mcqs = all_mcqs[:40]
    selected_blanks = all_blanks[:10]
    
    final_pool = []
    for q in selected_mcqs:
        item = q.copy()
        item["final_type"] = "MCQ"
        final_pool.append(item)
    for q in selected_blanks:
        item = q.copy()
        item["final_type"] = "BLANK"
        final_pool.append(item)
        
    user_sessions[user_id] = {
        "type": "FINAL_MCQ", "final_questions": final_pool, "current_idx": 0, "score": 0
    }
    
    await update.message.reply_text("🚀 ፈተናው ተጀምሯል። ለማለፍ ቢያንስ **70%** ማግኘት አለብዎት! መልካም ዕድል!")
    await send_next_final_question(context, user_id)

async def send_next_final_question(context, user_id):
    session = user_sessions[user_id]
    pool = session["final_questions"]
    idx = session["current_idx"]
    
    if idx >= len(pool):
        await evaluate_final_exam_performance(context, user_id)
        return
        
    q_data = pool[idx]
    if q_data["final_type"] == "MCQ":
        session["type"] = "FINAL_MCQ"
        msg = await context.bot.send_quiz(
            chat_id=int(user_id),
            question=f"[FINAL MCQ] ጥያቄ {idx+1}/50:\n{q_data['question']}",
            options=q_data['options'], correct_option_id=q_data['correct'], is_anonymous=False
        )
        poll_to_user[msg.poll.id] = user_id
    else:
        session["type"] = "FINAL_BLANK"
        await context.bot.send_message(chat_id=int(user_id), text=f"[FINAL ባዶ ቦታ] ጥያቄ {idx+1}/50:\n\n{q_data['question']}")

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer
    if answer.poll_id not in poll_to_user: return
    user_id = poll_to_user[answer.poll_id]
    session = user_sessions[user_id]
    
    if "final" in session["type"].lower():
        q_data = session["final_questions"][session["current_idx"]]
        if answer.option_ids[0] == q_data["correct"]:
            session["score"] += 1
        session["current_idx"] += 1
        del poll_to_user[answer.poll_id]
        await send_next_final_question(context, user_id)
    else:
        q_data = QUIZ_BANK[session["chapter"]]["mcq"][session["current_mcq_q"]]
        if answer.option_ids[0] == q_data["correct"]:
            session["score"] += 1
        session["current_mcq_q"] += 1
        del poll_to_user[answer.poll_id]
        await send_next_question(context, user_id)

async def evaluate_and_route_results(context, user_id):
    session = user_sessions[user_id]
    user_info = db["users"][user_id]
    total_q = len(QUIZ_BANK[session["chapter"]]["mcq"]) + len(QUIZ_BANK[session["chapter"]]["blank"])
    score = session["score"]
    percentage = (score / total_q) * 100
    
    if percentage >= 60.0:
        user_info["fail_count"] = 0
        if session["chapter"] not in user_info["passed_chapters"]:
            user_info["passed_chapters"].append(session["chapter"])
            
        db["held_results"][user_id] = {
            "name": user_info["name"], "gender": user_info["gender"],
            "score": score, "total": total_q, "chapter": session["chapter"]
        }
        await context.bot.send_message(chat_id=int(user_id), text=f"🎉 **እንኳን ደስ አሰኞት! አልፈዋል!** (ውጤት: {score}/{total_q} - {int(percentage)}%)\n\nውጤትዎ ተቆልፏል። አስተማሪው ሲለቀው ማጠቃለያው ይላክልዎታል።")
    else:
        user_info["fail_count"] = user_info.get("fail_count", 0) + 1
        current_fails = user_info["fail_count"]
        next_lock_minutes = 15 if current_fails == 1 else 15 + ((current_fails - 1) * 5)
        await context.bot.send_message(
            chat_id=int(user_id), 
            text=f"❌ **ውጤትዎ ከ 60% በታች ነው! አልለፉም።** ({int(percentage)}%)\n\n"
                 f"⏱️ የሚቀጥለው የፈተና መቆለፊያ ጊዜዎ ወደ **{next_lock_minutes} ደቂቃ** አድጓል። እንደገና ለመሞከር `/study` ይጻፉ።"
        )
    del user_sessions[user_id]

async def evaluate_final_exam_performance(context, user_id):
    session = user_sessions[user_id]
    user_info = db["users"][user_id]
    score = session["score"]
    percentage = (score / 50) * 100
    
    if percentage >= 70.0:
        await context.bot.send_message(
            chat_id=int(user_id),
            text=f"🎓 **ታላቅ የምስራች! የሐዋርያት ሥራ መጽሐፍ ማጠናቀቂያ ፈተናን በ {int(percentage)}% ውጤት በብቃት አጠናቀዋል!**\n\n"
                 f"🏆 ማዕረግዎ ተመዝግቧል። አስተማሪው በይፋ ሲያጸድቅ **የምስክር ወረቀት (Certificate)** ይሰጥዎታል።"
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"🎓 **ሚዛን ያለፈ ተመራቂ!**\n👤 ስም: {user_info['name']}\n🎯 የማጠቃለያ ፈተና ውጤት: {score}/50 ({int(percentage)}%)")
        except Exception: pass
    else:
        await context.bot.send_message(
            chat_id=int(user_id),
            text=f"❌ **የማጠናቀቂያ ፈተናውን አላለፉም!** (ውጤት: {score}/50 - {int(percentage)}%)\n\n"
                 f"⚠️ ለማለፍ ቢያንስ **70%** ያስፈልግዎታል። የጥያቄዎቹ ቅደም ተከተልና ምርጫዎች በሙሉ ተቀይረዋል፤ እባክዎ በድጋሚ ለመፈተን በጥንቃቄ ተዘጋጅተው `/finalexam` ይጻፉ።"
        )
    del user_sessions[user_id]

async def release_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID: return
    if not db["held_results"]:
        await update.message.reply_text("📋 የተቆለፈ ውጤት የለም።")
        return
    for student_id, data in list(db["held_results"].items()):
        try:
            await context.bot.send_message(chat_id=int(student_id), text=f"🔔 **የፈተና ውጤትዎ፦** {data['score']}/{data['total']}")
            await context.bot.send_message(chat_id=int(student_id), text=SUMMARY_BANK.get(data["chapter"], "መልካም ጥናት!"))
        except Exception: pass
    db["held_results"].clear()
    await update.message.reply_text("✅ ውጤቶች በሙሉ ተለቀቁ!")

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("study", study))
    app.add_handler(CommandHandler("quiz", start_quiz))
    app.add_handler(CommandHandler("finalexam", start_final_exam))
    app.add_handler(CommandHandler("release", release_results))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    app.add_handler(CallbackQueryHandler(handle_approval_buttons))
    app.add_handler(PollAnswerHandler(handle_answer))
    app.run_polling()

if __name__ == '__main__':
    main()
