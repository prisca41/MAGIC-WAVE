import logging
import threading
import queue
from flask import Flask, jsonify, request
from flask_cors import CORS
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

TOKEN = "8479817666:AAEnoq833aARTCf5L-awiQGeiNYJp3lsSH8"
WELCOME_IMAGE_URL = "https://i.postimg.cc/g0cyddpt/IMG-1929.jpg"

WAITING_SOLDE = 1
WAITING_PRENOM = 2
WAITING_HISTORY = 3
WAITING_IMAGE_URL = 4

# État global de l'application
app_status = {
    "solde": 0,
    "nom": "",
    "image_selected": "Aucune",
    "banknote": "Aucun",
    "vibration": True,
    "vibration_level": 3,
    "icons_blocked": False,
}

# ------------------ SERVEUR FLASK ------------------
app_flask = Flask(__name__)
CORS(app_flask)
command_queue = queue.Queue()

@app_flask.route('/get_command', methods=['GET'])
def get_command():
    try:
        cmd = command_queue.get_nowait()
        return jsonify({'command': cmd})
    except queue.Empty:
        return jsonify({'command': None})

@app_flask.route('/clear_command', methods=['POST'])
def clear_command():
    while not command_queue.empty():
        command_queue.get_nowait()
    return jsonify({'status': 'cleared'})

def run_flask():
    app_flask.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# ------------------ BOT TELEGRAM ------------------
def build_main_menu():
    keyboard = [
        [
            InlineKeyboardButton("💰 Solde", callback_data="btn_solde"),
            InlineKeyboardButton("▶️ Voir (10s)", callback_data="cmd_voir"),
            InlineKeyboardButton("⏹ Cacher (10s)", callback_data="cmd_cacher"),
        ],
        [
            InlineKeyboardButton("👤 Définir Prénom", callback_data="btn_prenom"),
            InlineKeyboardButton("✨ Révéler (10s)", callback_data="cmd_reveler"),
            InlineKeyboardButton("❌ Effacer (10s)", callback_data="cmd_effacer"),
        ],
        [
            InlineKeyboardButton("📳 Vib High (5)", callback_data="cmd_vib_5"),
            InlineKeyboardButton("📳 Vib Mid (3)", callback_data="cmd_vib_3"),
            InlineKeyboardButton("📳 Vib Low (1)", callback_data="cmd_vib_1"),
        ],
        [
            InlineKeyboardButton("🪙 Pièce 100F", callback_data="cmd_img_100f"),
            InlineKeyboardButton("🪙 Pièce 200F", callback_data="cmd_img_200f"),
        ],
        [
            InlineKeyboardButton("🎯 Afficher Pièce (10s)", callback_data="cmd_piece"),
            InlineKeyboardButton("🙈 Masquer Pièce (10s)", callback_data="cmd_depiece"),
        ],
        [
            InlineKeyboardButton("💵 Billet 500F", callback_data="cmd_banknote_500"),
            InlineKeyboardButton("💵 Billet 1000F", callback_data="cmd_banknote_1000"),
            InlineKeyboardButton("💵 Billet 2000F", callback_data="cmd_banknote_2000"),
        ],
        [
            InlineKeyboardButton("🎯 Afficher Billet (10s)", callback_data="cmd_afficher_billet"),
            InlineKeyboardButton("🙈 Masquer Billet (10s)", callback_data="cmd_masquer_billet"),
        ],
        [
            InlineKeyboardButton("📜 History", callback_data="btn_history"),
            InlineKeyboardButton("📊 Status", callback_data="cmd_status"),
            InlineKeyboardButton("🔗 URL Image", callback_data="btn_image_url"),
        ],
        [
            InlineKeyboardButton("🔇 Vibration off", callback_data="cmd_vibration_off"),
            InlineKeyboardButton("🔊 Vibration on", callback_data="cmd_vibration_on"),
            InlineKeyboardButton("🔒 Bloquer icônes", callback_data="cmd_blockicons_on"),
            InlineKeyboardButton("🔓 Débloquer icônes", callback_data="cmd_blockicons_off"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption_text = (
        "🪄 *KiM Magic Bot - Télécommande Globale*\n\n"
        "Interface de contrôle synchronisée avec le serveur."
    )
    reply_markup = build_main_menu()
    try:
        await update.message.reply_photo(
            photo=WELCOME_IMAGE_URL,
            caption=caption_text,
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )
    except Exception as e:
        await update.message.reply_text(
            f"{caption_text}\n\n_(Erreur chargement photo: {e})_",
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )

async def button_click_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    command_map = {
        "cmd_voir": "/voir",
        "cmd_cacher": "/cacher",
        "cmd_reveler": "/reveler",
        "cmd_effacer": "/effacer",
        "cmd_vib_1": "/vibration_level 1",
        "cmd_vib_3": "/vibration_level 3",
        "cmd_vib_5": "/vibration_level 5",
        "cmd_img_100f": "/image 100F",
        "cmd_img_200f": "/image 200F",
        "cmd_piece": "/piece",
        "cmd_depiece": "/depiece",
        "cmd_banknote_500": "/banknote 500",
        "cmd_banknote_1000": "/banknote 1000",
        "cmd_banknote_2000": "/banknote 2000",
        "cmd_afficher_billet": "/afficher_billet",
        "cmd_masquer_billet": "/masquer_billet",
        "cmd_vibration_on": "/vibration on",
        "cmd_vibration_off": "/vibration off",
        "cmd_blockicons_on": "/blockicons on",
        "cmd_blockicons_off": "/blockicons off",
    }

    if data in command_map:
        cmd_text = command_map[data]
        command_queue.put(cmd_text)
        await query.message.reply_text(f"✅ Commande envoyée : `{cmd_text}`", parse_mode="Markdown")
    elif data == "cmd_status":
        status_msg = (
            f"📊 *État de l'application :*\n"
            f"• Solde configuré : {app_status['solde']} F\n"
            f"• Prénom enregistré : {app_status['nom'] or 'Aucun'}\n"
            f"• Niveau Vibration : {app_status['vibration_level']}\n"
            f"• Vibration : {'Activée' if app_status['vibration'] else 'Désactivée'}\n"
            f"• Icônes bloquées : {'Oui' if app_status['icons_blocked'] else 'Non'}"
        )
        await query.message.reply_text(status_msg, parse_mode="Markdown")
    return ConversationHandler.END

# ------------------ CONVERSATIONS ------------------
async def prompt_solde(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("💰 Entrez le montant du solde (ex: `15000`) :", parse_mode="Markdown")
    return WAITING_SOLDE

async def process_solde_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    command_text = f"/solde {user_input}"
    command_queue.put(command_text)
    await update.message.reply_text(f"✅ Solde sélectionné (En attente du clic Suivant) : `{command_text}`", parse_mode="Markdown")
    return ConversationHandler.END

async def prompt_prenom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("👤 Entrez le prénom (ex: `David`) :", parse_mode="Markdown")
    return WAITING_PRENOM

async def process_prenom_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    command_text = f"/prenom {user_input}"
    app_status["nom"] = user_input
    command_queue.put(command_text)
    await update.message.reply_text(f"✅ Prénom enregistré : `{command_text}`", parse_mode="Markdown")
    return ConversationHandler.END

async def prompt_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📜 Nombre de transactions (1 à 5) :", parse_mode="Markdown")
    return WAITING_HISTORY

async def process_history_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    command_text = f"/history {user_input}"
    command_queue.put(command_text)
    await update.message.reply_text(f"✅ Commande envoyée : `{command_text}`", parse_mode="Markdown")
    return ConversationHandler.END

async def prompt_image_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🔗 Entrez l'URL de l'image :", parse_mode="Markdown")
    return WAITING_IMAGE_URL

async def process_image_url_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    if user_input.startswith("http"):
        command_text = f"/image {user_input}"
        command_queue.put(command_text)
        await update.message.reply_text(f"✅ URL image mise à jour", parse_mode="Markdown")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Action annulée.")
    return ConversationHandler.END

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(TOKEN).build()

    solde_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(prompt_solde, pattern="^btn_solde$")],
        states={WAITING_SOLDE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_solde_input)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    prenom_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(prompt_prenom, pattern="^btn_prenom$")],
        states={WAITING_PRENOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_prenom_input)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    history_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(prompt_history, pattern="^btn_history$")],
        states={WAITING_HISTORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_history_input)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    image_url_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(prompt_image_url, pattern="^btn_image_url$")],
        states={WAITING_IMAGE_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_image_url_input)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(solde_conv)
    app.add_handler(prenom_conv)
    app.add_handler(history_conv)
    app.add_handler(image_url_conv)
    app.add_handler(CallbackQueryHandler(button_click_handler))

    print("🤖 Bot démarré...")
    app.run_polling()

if __name__ == "__main__":
    main()
