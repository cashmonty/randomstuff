import logging
import csv
import asyncio
from web3 import Web3

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Web3
w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/'))

# Read wallet addresses from CSV file
wallet_addresses = []
with open('ChainEdge_Wallets.csv', 'r') as f:
    csv_reader = csv.reader(f)
    for row in csv_reader:
        wallet_addresses.append(row[0].lower())  # Convert to lowercase for easier comparison

async def monitor_transactions(context: ContextTypes.DEFAULT_TYPE) -> None:
    latest_block = w3.eth.get_block('latest')
    for tx_hash in latest_block['transactions']:
        tx = w3.eth.get_transaction(tx_hash)
        if tx['from'].lower() in wallet_addresses:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            for log in receipt['logs']:
                if len(log['topics']) >= 1:
                    from_address = w3.toChecksumAddress(log['topics'][1][-40:])
                    to_address = w3.toChecksumAddress(log['topics'][2][-40:])
                    value = int(log['data'], 16)
                    message = f"Token Swap Detected!\nFrom: {from_address}\nTo: {to_address}\nAmount: {value}"
                    await context.bot.send_message(chat_id='', text=message)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Monitoring started.")
    while True:
        await monitor_transactions(context)
        await asyncio.sleep(10)  # Check every 10 seconds

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Use /start to start monitoring.")

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = (
        Application.builder()
        .token("")
        .build()
    )

    application.add_handler(CommandHandler("start", start))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
