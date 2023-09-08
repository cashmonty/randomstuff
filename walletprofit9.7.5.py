import csv
import time
import logging
import os
from moralis import evm_api  # Assuming you have imported Moralis
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='moralisapi.env')

# Initialize logging
logging.basicConfig(filename='wallet_profit.log', level=logging.DEBUG)

# Get API key from environment variables
api_key = os.getenv("API_KEY")
if not api_key:
    logging.error("API key not found in environment variables.")
    exit(1)

# Initialize variables
chain = "eth"

# Function to fetch transactions from Moralis
def get_wallet_transactions(wallet_address):
    params = {
        "chain": chain,
        "address": wallet_address
    }
    result = evm_api.transaction.get_wallet_transactions_verbose(api_key=api_key, params=params)
    logging.debug(f"API result for {wallet_address}: {result}")
    return result

# Function to check if two amounts are approximately equal
def approximately_equal(amount_spent, amount_received, tolerance=0.1):
    return (1 - tolerance) * amount_spent <= amount_received <= (1 + tolerance) * amount_spent

# Read wallet addresses from CSV
wallet_addresses = []
with open('CEWallets.csv', 'r') as f:
    reader = csv.reader(f)
    next(reader, None)  # Skip the header
    for row in reader:
        wallet_addresses.append(row[0])

# Prepare CSV output
with open('ProfitabilityCEWallets.csv', 'w', newline='') as csvfile:
    fieldnames = ['Wallet Address', 'Total Realized Profit', 'Total Trades', 'Profitable %']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # Loop through each wallet address
    for wallet_address in wallet_addresses:
        transactions = {}
        total_trades = 0
        profitable_trades = 0
        total_realized_profit = 0  # Reset for each wallet

        # Fetch transactions for the wallet
        result = get_wallet_transactions(wallet_address)
        if result is None:
            continue

        logging.debug(f"Transactions for {wallet_address}: {result.get('result', [])}")

        # Loop through transactions
        for tx in result.get('result', []):
            decoded_event = tx.get('decoded_event', {})
            params = decoded_event.get('params', [])
            input_data = tx.get('input', '')

            # Extract token address from input data
            if len(input_data) >= 138:
                token_address = "0x" + input_data[-40:]
                transactions.setdefault(token_address, {'spent_weth': 0, 'received_tokens': 0, 'sold_tokens': 0, 'received_weth': 0})

                if decoded_event and decoded_event.get('signature') == 'Swap(address,uint256,uint256,uint256,uint256,address)':
                    if len(params) >= 5:
                        amount0In = int(params[1]['value'])  # Tokens sold
                        amount1In = int(params[2]['value'])  # WETH spent
                        amount0Out = int(params[3]['value'])  # Tokens received
                        amount1Out = int(params[4]['value'])  # WETH received

                        # Sum up the values for multiple Swap events
                        if amount1In != 0:  # This is a buy
                            transactions[token_address]['spent_weth'] += amount1In
                            transactions[token_address]['received_tokens'] += amount0Out
                            total_trades += 1
                        elif amount1Out != 0:  # This is a sell
                            transactions[token_address]['sold_tokens'] += amount0In
                            transactions[token_address]['received_weth'] += amount1Out

        # Calculate total profit and profitability
        for token_address, token_data in transactions.items():
            logging.debug(f"Token data for {token_address}: {token_data}")
            if approximately_equal(token_data['received_tokens'], token_data['sold_tokens']):
                profit = (token_data['received_weth'] - token_data['spent_weth']) / 1e18  # Convert to ETH
                total_realized_profit += profit
                if profit > 0:
                    profitable_trades += 1

        profitable_percent = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0

        # Write to CSV
        writer.writerow({
            'Wallet Address': wallet_address,
            'Total Realized Profit': total_realized_profit,
            'Total Trades': total_trades,
            'Profitable %': profitable_percent
        })

        logging.info(f"Processed wallet address {wallet_address}")

        # Pause to avoid rate-limiting
        logging.debug("Sleeping for 2 seconds to avoid rate-limiting.")
        time.sleep(2)
