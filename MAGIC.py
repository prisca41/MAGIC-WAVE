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

TOKEN = "8479817666:AAEnoq833aARTCf5L-awiQGeiNYJp3lsSH8"  # À remplacer par votre token
WELCOME_IMAGE_URL = "https://i.postimg.cc/g0cyddpt/IMG-1929.jpg"

WAITING_SOLDE = 1
WAITING_PRENOM = 2
WAITING_HISTORY = 3
WAITING_IMAGE_URL = 4

# État global
app_status = {
    "solde": 0,
    "nom": "",
    "image_selected": "Aucune",
    "banknote": "Aucun",
    "vibration": True,
    "icons_blocked": False,
    "vibration_intensity": 50,  # Valeur par défaut à 50%
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
            InlineKeyboardButton("🔊+ Vib +", callback_data="cmd_vibration_intensity_plus"),
            InlineKeyboardButton("🔊- Vib -", callback_data="cmd_vibration_intensity_minus"),
        ],
        [
            InlineKeyboardButton("🔒 Bloquer icônes", callback_data="cmd_blockicons_on"),
            InlineKeyboardButton("🔓 Débloquer icônes", callback_data="cmd_blockicons_off"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption_text = (
        "🪄 *KiM Magic Bot - Télécommande Globale*\n\n"
        "Bienvenue dans votre interface de contrôle. "
        "Cliquez sur un bouton ci-dessous pour interagir avec l'application."
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
            f"{caption_text}\n\n_(Note: Impossible de charger l'image : {e})_",
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )

async def button_click_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Gestion spécifique pour l'augmentation de la vibration
    if data == "cmd_vibration_intensity_plus":
        if app_status["vibration_intensity"] < 100:
            app_status["vibration_intensity"] = min(100, app_status["vibration_intensity"] + 5)
        
        val = app_status["vibration_intensity"]
        cmd_text = f"/vibration_intensity {val}"
        command_queue.put(cmd_text)
        await query.message.reply_text(f"🔊 Intensité vibration augmentée : *{val}%*", parse_mode="Markdown")
        return ConversationHandler.END

    # Gestion spécifique pour la diminution de la vibration
    elif data == "cmd_vibration_intensity_minus":
        if app_status["vibration_intensity"] > 0:
            app_status["vibration_intensity"] = max(0, app_status["vibration_intensity"] - 5)
        
        val = app_status["vibration_intensity"]
        cmd_text = f"/vibration_intensity {val}"
        command_queue.put(cmd_text)
        await query.message.reply_text(f"🔉 Intensité vibration diminuée : *{val}%*", parse_mode="Markdown")
        return ConversationHandler.END

    command_map = {
        "cmd_voir": "/voir",
        "cmd_cacher": "/cacher",
        "cmd_reveler": "/reveler",
        "cmd_effacer": "/effacer",
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
            f"• Image sélectionnée : {app_status['image_selected']}\n"
            f"• Billet actif : {app_status['banknote']}\n"
            f"• Vibration : {'Activée' if app_status['vibration'] else 'Désactivée'}\n"
            f"• Intensité vibration : {app_status['vibration_intensity']}%\n"
            f"• Icônes bloquées : {'Oui' if app_status['icons_blocked'] else 'Non'}"
        )
        await query.message.reply_text(status_msg, parse_mode="Markdown")
    else:
        await query.message.reply_text("⚠️ Commande non reconnue.")
    return ConversationHandler.END

# ------------------ CONVERSATIONS ------------------
async def prompt_solde(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "💰 *Saisie du Solde*\n"
        "Veuillez entrer le montant (ex: `15000` ou `25000 Wave 0700000000`) :",
        parse_mode="Markdown"
    )
    return WAITING_SOLDE

async def process_solde_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    command_text = f"/solde {user_input}"
    parts = user_input.split()
    try:
        app_status["solde"] = int(parts[0])
    except:
        pass
    command_queue.put(command_text)
    await update.message.reply_text(f"✅ Montant enregistré. Le téléphone va vibrer pour confirmer la réception.", parse_mode="Markdown")
    return ConversationHandler.END

async def prompt_prenom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "👤 *Définition du Prénom*\n"
        "Entrez le prénom à enregistrer (ex: `David`) :",
        parse_mode="Markdown"
    )
    return WAITING_PRENOM

async def process_prenom_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    command_text = f"/prenom {user_input}"
    app_status["nom"] = user_input
    command_queue.put(command_text)
    await update.message.reply_text(f"✅ Prénom enregistré. Utilisez « Révéler (10s) » pour l'afficher.", parse_mode="Markdown")
    return ConversationHandler.END

async def prompt_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "📜 *Ajout d'historique*\n"
        "Entrez le nombre de transactions à générer (1 à 5) :",
        parse_mode="Markdown"
    )
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
    await query.message.reply_text(
        "🔗 *Saisie d'URL d'image*\n"
        "Veuillez entrer l'URL complète de l'image (ex: `https://exemple.com/image.png`) :",
        parse_mode="Markdown"
    )
    return WAITING_IMAGE_URL

async def process_image_url_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    if user_input.startswith("http"):
        command_text = f"/image {user_input}"
        app_status["image_selected"] = "URL personnalisée"
        command_queue.put(command_text)
        await update.message.reply_text(f"✅ Commande envoyée : `{command_text}`", parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ URL invalide. Veuillez entrer une URL commençant par http.")
        return WAITING_IMAGE_URL
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Action annulée.")
    return ConversationHandler.END

# ------------------ MAIN ------------------
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

    print("🤖 KiM Magic Bot en cours d'exécution... (Flask sur port 5000)")
    app.run_polling()

if __name__ == "__main__":
    main()
