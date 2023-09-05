import csv
import time
import logging
from moralis import evm_api  # Assuming you have imported Moralis

# Initialize logging
logging.basicConfig(filename='wallet_profit.log', level=logging.INFO)

# Your API key
api_key = ""

# Initialize variables
chain = "eth"
uniswap_router = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'

# Function to fetch transactions from Moralis
def get_wallet_transactions(wallet_address):
    params = {
        "chain": chain,
        "address": wallet_address
    }
    return evm_api.transaction.get_wallet_transactions(api_key=api_key, params=params)

# Read wallet addresses from CSV
wallet_addresses = []
try:
    with open('CashWallets.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            wallet_addresses.append(row[0])
except FileNotFoundError:
    logging.error("CSV file not found.")
    exit()

# Prepare CSV output
try:
    with open('profitability_results.csv', 'w', newline='') as csvfile:
        fieldnames = ['Wallet Address', 'Total Realized Profit', 'Total Unrealized Profit']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Initialize a dictionary to hold buy and sell transactions for each token
        transactions = {}

        # Loop through each wallet address
        for wallet_address in wallet_addresses:
            total_realized_profit = 0.0

            # Fetch ERC20 transfers for the wallet
            try:
                result = get_wallet_transactions(wallet_address)
            except Exception as e:
                logging.error(f"Error fetching ERC20 transfers for {wallet_address}: {e}")
                continue

            # Loop through transactions
            for tx in result['result']:
                token_symbol = tx.get('token_symbol', 'Unknown')
                value_decimal = float(tx.get('value_decimal', 0.0))
                
                if tx['to_address'] == uniswap_router:
                    # This is a buy transaction
                    transactions.setdefault(token_symbol, []).append(('buy', value_decimal))

                elif tx['from_address'] == uniswap_router:
                    # This is a sell transaction
                    if any(action == 'buy' and value == value_decimal for action, value in transactions.get(token_symbol, [])):
                        transactions.setdefault(token_symbol, []).append(('sell', value_decimal))

            # Calculate profit for each token
            for token_symbol, txs in transactions.items():
                buy_value = 0.0
                sell_value = 0.0
                for action, value in txs:
                    if action == 'buy':
                        buy_value += value
                    elif action == 'sell':
                        sell_value += value

                profit = sell_value - buy_value
                total_realized_profit += profit

            # Write to CSV
            writer.writerow({
                'Wallet Address': wallet_address,
                'Total Realized Profit': total_realized_profit,
                'Total Unrealized Profit': 0.0  # Placeholder
            })

            logging.info(f"Processed wallet address {wallet_address}")

            # Pause to avoid rate-limiting
            time.sleep(2)

except Exception as e:
    logging.error(f"Error writing to CSV: {e}")
