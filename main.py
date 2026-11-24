import os, json, asyncio
from threading import Thread
from flask import Flask
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ChatType

# RZ - Rwanda online business zizewe - @Hyunda100bot
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "RZ V7 LIVE - Rwanda online business zizewe"
def run_web():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
Thread(target=run_web, daemon=True).start()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN = int(os.getenv("ADMIN_ID", "0"))
DATA="bot_data.json"; SCHED="schedule.json"

# ===== TABLE YA OWNER - IZA HASI HOSE =====
OWNER_TABLE = (
    "\n\n"
    "┌────────────────────────┐\n"
    "│  📩 CONTACT OWNER      │\n"
    "├────────────────────────┤\n"
    "│  Telegram: @Onlinebu12 │\n"
    "│  WhatsApp: 0727172400  │\n"
    "└────────────────────────┘\n"
    "🇷🇼 Rwanda online business zizewe - RZ"
)

def contact_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 Andikira Owner Telegram", url="https://t.me/Onlinebu12")],
        [InlineKeyboardButton("💬 WhatsApp 0727172400", url="https://wa.me/250727172400")],
    ])

def load_data():
    try:
        with open(DATA) as f: d=json.load(f)
        return d.get("groups",{}),d.get("pending",{}),d.get("keywords",{}),d.get("settings",{"welcome":True,"anti_link":True})
    except: return {},{},{},{"welcome":True,"anti_link":True}
def save_data():
    with open(DATA,"w") as f: json.dump({"groups":groups,"pending":pending,"keywords":keywords,"settings":settings},f,indent=2)
def load_sched():
    try:
        with open(SCHED) as f: return json.load(f)
    except: return []
def save_sched():
    with open(SCHED,"w") as f: json.dump(jobs,f,indent=2)

groups,pending,keywords,settings=load_data(); jobs=load_sched()

async def is_admin(u): return u.effective_user.id==ADMIN

# ===== SCHEDULE - MESSAGE + TABLE HASI =====
async def loop_job(app):
    while True:
        try:
            now=datetime.now()
            for job in jobs[:]:
                if now>=datetime.fromisoformat(job["next_run"]):
                    full_text = job["text"] + OWNER_TABLE
                    for gid in list(groups.keys()):
                        try: await app.bot.send_message(chat_id=int(gid),text=full_text); await asyncio.sleep(0.3)
                        except: pass
                    job["next_run"]=(now+timedelta(minutes=job["interval_minutes"])).isoformat(); save_sched()
        except: pass
        await asyncio.sleep(30)

def panel_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📢 BROADCAST ALL {len(groups)}",callback_data="broadcast_all")],
        [InlineKeyboardButton(f"👥 G:{len(groups)}",callback_data="list_groups"),InlineKeyboardButton(f"⏳ P:{len(pending)}",callback_data="list_pending")],
        [InlineKeyboardButton("⏰ JOBS",callback_data="sched_list"),InlineKeyboardButton("📊 STATS",callback_data="stats")],
        [InlineKeyboardButton("⚙️ SET",callback_data="set"),InlineKeyboardButton("🔑 KEYWORDS",callback_data="keys")],
        [InlineKeyboardButton("📩 Owner Telegram", url="https://t.me/Onlinebu12")],
        [InlineKeyboardButton("💬 WhatsApp 0727172400", url="https://wa.me/250727172400")],
    ])

async def start(update,context):
    chat=update.effective_chat; gid=str(chat.id)
    if chat.type in [ChatType.GROUP,ChatType.SUPERGROUP]:
        if gid not in groups:
            groups[gid]={"title":chat.title,"added_at":datetime.now().isoformat()}; save_data()
        await update.message.reply_text(f"🇷🇼 RZ BOT V7\n{chat.title}\nEMEWE ✅ - Ndi muri group, nzatangira kohereza" + OWNER_TABLE)
        return
    if not await is_admin(update):
        await update.message.reply_text("Muraho! 👋\n🇷🇼 Rwanda online business zizewe - RZ\n@Hyunda100bot" + OWNER_TABLE, reply_markup=contact_kb()); return
    await update.message.reply_text(f"👑 RZ PANEL 👑\n\nRwanda online business zizewe 🇷🇼\n@Hyunda100bot\n\nG:{len(groups)} | P:{len(pending)} | J:{len(jobs)}\nLIVE 🟢" + OWNER_TABLE,reply_markup=panel_kb())

async def addkey(update,context):
    if not await is_admin(update): return
    txt=" ".join(context.args)
    if "|" not in txt: await update.message.reply_text("Koresha: /addkey hello | Muraho neza, uri muri RZ"); return
    k,v=txt.split("|",1); keywords[k.strip().lower()]=v.strip(); save_data()
    await update.message.reply_text(f"✅ Keyword '{k.strip()}' yongewe - RZ")

async def delkey(update,context):
    if not await is_admin(update): return
    k=" ".join(context.args).lower()
    if k in keywords: del keywords[k]; save_data(); await update.message.reply_text("✅ Deleted")
    else: await update.message.reply_text("Nta keyword")

async def schedule(update,context):
    if not await is_admin(update): return
    txt=" ".join(context.args)
    if "|" not in txt:
        await update.message.reply_text("Koresha:\n/schedule 30 | Message yawe hano\n\nUrugero:\n/schedule 30 | Twabazaniye offers nshya!"); return
    mins,msg=txt.split("|",1); mins=int(mins.strip())
    jobs.append({"id":len(jobs)+1,"interval_minutes":mins,"text":msg.strip(),"next_run":(datetime.now()+timedelta(minutes=mins)).isoformat()}); save_sched()
    await update.message.reply_text(f"✅ Schedule yashyizweho!\n\nBuri {mins} min izohereza:\n\"{msg.strip()}\"" + OWNER_TABLE)

async def groups_cmd(update,context):
    if not await is_admin(update): return
    t="\n".join([f"{v.get('title')} | {k}" for k,v in groups.items()]) or "Nta group"
    await update.message.reply_text(t[:3000])

async def handle_msg(update,context):
    chat=update.effective_chat; text=update.message.text or ""
    if context.user_data.get("broad") and await is_admin(update) and chat.type==ChatType.PRIVATE:
        if text=="/cancel": context.user_data["broad"]=False; await update.message.reply_text("❌ Stopped"); return
        c=0
        for gid in list(groups.keys()):
            try:
                if update.message.text:
                    await context.bot.send_message(chat_id=int(gid),text=text + OWNER_TABLE)
                else:
                    await context.bot.copy_message(chat_id=int(gid),from_chat_id=chat.id,message_id=update.message.message_id)
                    await context.bot.send_message(chat_id=int(gid),text=OWNER_TABLE.strip())
                c+=1; await asyncio.sleep(0.3)
            except: pass
        context.user_data["broad"]=False; await update.message.reply_text(f"✅ RZ Sent {c}/{len(groups)}" + OWNER_TABLE); return
    if chat.type in [ChatType.GROUP,ChatType.SUPERGROUP]:
        gid=str(chat.id)
        if gid in groups:
            if settings.get("anti_link") and ("http" in text.lower() or "t.me/" in text.lower()):
                if update.effective_user.id!=ADMIN:
                    try: await update.message.delete(); await update.message.reply_text("🚫 Link ntizemewe hano muri RZ. Vugana na Admin." + OWNER_TABLE); return
                    except: pass
            low=text.lower()
            for k,v in keywords.items():
                if k in low: await update.message.reply_text(v + OWNER_TABLE); break

async def new_mem(update,context):
    chat=update.effective_chat; gid=str(chat.id)
    for m in update.message.new_chat_members:
        if m.id==context.bot.id:
            if gid not in groups:
                groups[gid]={"title":chat.title,"added_at":datetime.now().isoformat()}; save_data()
            await update.message.reply_text("✅ RZ V7 Yinjiye! 🇷🇼\nRwanda online business zizewe\nNzatangira kohereza messages hano, nta Admin bikenewe." + OWNER_TABLE, reply_markup=contact_kb())
        else:
            if gid in groups and settings.get("welcome"):
                await update.message.reply_text(
                    f"👋 Muraho {m.first_name}! Murakaza neza muri {chat.title} 🎉\n"
                    f"🇷🇼 Rwanda online business zizewe - RZ\n"
                    f"Soma rules, tubane neza!" + OWNER_TABLE,
                    reply_markup=contact_kb()
                )

async def btn(update,context):
    q=update.callback_query; await q.answer(); d=q.data
    if not await is_admin(update): return
    if d=="list_groups":
        t="\n".join([f"{v.get('title')} | {k}" for k,v in groups.items()]) or "Nta group"
        await q.edit_message_text(t[:3000],reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back",callback_data="back")]]))
    elif d=="list_pending":
        if not pending: await q.edit_message_text("Nta pending",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back",callback_data="back")]])); return
        kb=[]
        for gid,info in list(pending.items())[:10]: kb.append([InlineKeyboardButton(f"✅ {info.get('title','G')[:15]}",callback_data=f"ap_{gid}"),InlineKeyboardButton("❌",callback_data=f"rj_{gid}")])
        kb.append([InlineKeyboardButton("⬅️ Back",callback_data="back")]); await q.edit_message_text(f"⏳ P:{len(pending)}",reply_markup=InlineKeyboardMarkup(kb))
    elif d.startswith("ap_"):
        gid=d.split("ap_")[1]
        if gid in pending: groups[gid]=pending.pop(gid); save_data(); await q.edit_message_text("✅ RZ Approved")
    elif d.startswith("rj_"):
        gid=d.split("rj_")[1]
        if gid in pending: pending.pop(gid); save_data(); await q.edit_message_text("❌ Rejected")
    elif d=="broadcast_all": await q.edit_message_text("✍️ Ohereza msg ya RZ / /cancel" + OWNER_TABLE); context.user_data["broad"]=True
    elif d=="stats": await q.edit_message_text(f"📊 RZ STATS\n🇷🇼 Rwanda online business zizewe\nG:{len(groups)}\nP:{len(pending)}\nJ:{len(jobs)}\nK:{len(keywords)}" + OWNER_TABLE,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back",callback_data="back")]]))
    elif d=="sched_list":
        t="\n".join([f"{j['id']} {j['interval_minutes']}m: {j['text'][:25]}" for j in jobs]) or "Nta job"
        await q.edit_message_text(t,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🗑️ Clear",callback_data="clear_jobs")],[InlineKeyboardButton("⬅️ Back",callback_data="back")]]))
    elif d=="clear_jobs": jobs.clear(); save_sched(); await q.edit_message_text("✅ Cleared")
    elif d=="set":
        kb=[[InlineKeyboardButton(f"Welcome:{settings.get('welcome')}",callback_data="tw")],[InlineKeyboardButton(f"AntiLink:{settings.get('anti_link')}",callback_data="tl")],[InlineKeyboardButton("⬅️ Back",callback_data="back")]]
        await q.edit_message_text("⚙️ RZ Settings",reply_markup=InlineKeyboardMarkup(kb))
    elif d=="tw": settings["welcome"]=not settings.get("welcome",True); save_data(); await q.edit_message_text(f"Welcome:{settings.get('welcome')}")
    elif d=="tl": settings["anti_link"]=not settings.get("anti_link",False); save_data(); await q.edit_message_text(f"AntiLink:{settings.get('anti_link')}")
    elif d=="keys":
        t="\n".join([f"{k} -> {v[:30]}" for k,v in keywords.items()]) or "Nta keyword\nKoresha /addkey hello | Muraho"
        await q.edit_message_text(t,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back",callback_data="back")]]))
    elif d=="back": await q.edit_message_text(f"👑 RZ PANEL 👑\n\nRwanda online business zizewe 🇷🇼\nG:{len(groups)} | P:{len(pending)} | J:{len(jobs)}\nLIVE 🟢" + OWNER_TABLE,reply_markup=panel_kb())

async def post_init(app): asyncio.create_task(loop_job(app))
def main():
    app=Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("broadcast",start))
    app.add_handler(CommandHandler("groups",groups_cmd))
    app.add_handler(CommandHandler("addkey",addkey))
    app.add_handler(CommandHandler("delkey",delkey))
    app.add_handler(CommandHandler("schedule",schedule))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS,new_mem))
    app.add_handler(CallbackQueryHandler(btn))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND,handle_msg))
    print("RZ BOT V7 STARTED"); app.run_polling()
if __name__=="__main__": main()
