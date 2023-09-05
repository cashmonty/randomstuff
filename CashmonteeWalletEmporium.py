from web3 import Web3
from telegram.ext import Updater, CommandHandler, ContextTypes
import logging
import csv

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Web3
w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/'))

wallet_addresses = []
with open('ChainEdge_Wallets.csv', 'r') as f:
    csv_reader = csv.reader(f)
    for row in csv_reader:
        wallet_addresses.append(row[0].lower())  # Convert to lowercase for easier comparison

def monitor_transactions(context: ContextTypes.DEFAULT_TYPE):
    # Get the latest block
    latest_block = w3.eth.getBlock('latest')
    
    # Loop through all transactions in the latest block
    for tx_hash in latest_block['transactions']:
        tx = w3.eth.getTransaction(tx_hash)
        
        # Check if the 'from' address is in the list of wallet addresses
        if tx['from'].lower() in wallet_addresses:
            # Get the transaction receipt to access its logs
            receipt = w3.eth.getTransactionReceipt(tx_hash)
            
            for log in receipt['logs']:
                # Extract the 'from', 'to', and 'value' from the logs
                # Note: This assumes a standard ERC-20 Transfer event; actual topics may vary
                if len(log['topics']) >= 3:
                    from_address = w3.toChecksumAddress(log['topics'][1][-40:])
                    to_address = w3.toChecksumAddress(log['topics'][2][-40:])
                    value = int(log['data'], 16)
                    
                    # Send a Telegram message
                    message = f"Token Swap Detected!\nFrom: {from_address}\nTo: {to_address}\nAmount: {value}"
                    context.bot.send_message(chat_id='', text=message)

if __name__ == '__main__':
    try:
        updater = Updater(token=':', use_context=True)
        job_queue = updater.job_queue
        job_queue.run_repeating(monitor_transactions, interval=10)  # Check every 10 seconds
        updater.start_polling()
    except Exception as e:
        logger.error(f"Error in main: {e}")
