import os
import time
import json
from dotenv import load_dotenv
from web3 import Web3
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Wczytanie zmiennych środowiskowych
load_dotenv()

# Token bota Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))

bot = Bot(token=TELEGRAM_TOKEN)

# Połączenie z blockchainem INK
INK_RPC_URL = "wss://ink.drpc.org"
web3 = Web3(Web3.HTTPProvider(INK_RPC_URL))

# Plik do przechowywania adresów portfeli
WALLETS_FILE = "wallets.json"

# Sprawdzenie połączenia
if web3.is_connected():
    print("✅ Połączono z siecią INK!")
else:
    print("❌ Błąd połączenia!")
    exit()

# Funkcja zapisywania adresów do pliku
def save_wallets(wallets):
    with open(WALLETS_FILE, "w") as f:
        json.dump(wallets, f)

# Funkcja ładowania adresów
def load_wallets():
    if not os.path.exists(WALLETS_FILE):
        return []
    with open(WALLETS_FILE, "r") as f:
        return json.load(f)

# Funkcja obsługująca komendę /add
def add_wallet(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        update.message.reply_text("❌ Użycie: /add 0xADRES_PORTFELA")
        return
    address = context.args[0]
    wallets = load_wallets()
    if address in wallets:
        update.message.reply_text("⚠️ Ten portfel jest już śledzony!")
    else:
        wallets.append(address)
        save_wallets(wallets)
        update.message.reply_text(f"✅ Dodano portfel {address} do monitorowania!")

# Funkcja obsługująca komendę /remove
def remove_wallet(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        update.message.reply_text("❌ Użycie: /remove 0xADRES_PORTFELA")
        return
    address = context.args[0]
    wallets = load_wallets()
    if address in wallets:
        wallets.remove(address)
        save_wallets(wallets)
        update.message.reply_text(f"✅ Usunięto portfel {address} z monitorowania!")
    else:
        update.message.reply_text("⚠️ Ten portfel nie jest śledzony!")

# Funkcja obsługująca komendę /list
def list_wallets(update: Update, context: CallbackContext):
    wallets = load_wallets()
    if wallets:
        update.message.reply_text("📜 Śledzone portfele:\n" + "\n".join(wallets))
    else:
        update.message.reply_text("🚫 Nie śledzisz żadnych portfeli!")

# Funkcja sprawdzająca nowe transakcje
def check_transactions():
    latest_block = web3.eth.block_number
    while True:
        new_block = web3.eth.block_number
        if new_block > latest_block:
            block = web3.eth.get_block(new_block, full_transactions=True)
            wallets = load_wallets()
            for tx in block.transactions:
                if tx["from"] in wallets or tx["to"] in wallets:
                    message = f"📢 Nowa transakcja!\n\n🔹 Od: {tx['from']}\n🔹 Do: {tx['to']}\n🔹 Wartość: {web3.from_wei(tx['value'], 'ether')} INK\n🔹 Hash: {tx['hash'].hex()}"
                    bot.send_message(chat_id=CHAT_ID, text=message)
                    print(message)
            latest_block = new_block
        time.sleep(10)  # Sprawdza co 10 sekund

# Uruchomienie bota Telegram
def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("add", add_wallet))
    dp.add_handler(CommandHandler("remove", remove_wallet))
    dp.add_handler(CommandHandler("list", list_wallets))
    updater.start_polling()
    check_transactions()

if __name__ == "__main__":
    main()
