from moralis import evm_api
import csv
import time
import logging
import os
from dotenv import load_dotenv

# Initialize logging and environment variables
logging.basicConfig(filename='wallet_profit.log', level=logging.INFO)
load_dotenv(dotenv_path='moralisapi.env')
api_key = os.getenv("API_KEY")
chain = "eth"

# Function to fetch token transfers by block range
def get_token_transfers(address):
    params = {"chain": chain, "address": address}
    return evm_api.token.get_wallet_token_transfers(api_key=api_key, params=params)

# Function to fetch transactions from Moralis
def transfer_tx_hash(transaction_hash):
    params = {"chain": chain, "transaction_hash": transaction_hash}
    return evm_api.transaction.get_transaction_verbose(api_key=api_key, params=params)

# Read wallet addresses from CSV
wallet_addresses = []
with open('CEWallets.csv', 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        wallet_addresses.append(row[0])

# Open CSV file for writing
with open('ProfitabilityReport.csv', 'w', newline='') as csvfile:
    fieldnames = ['Wallet Address', 'Total Realized Profit', 'Total Trades', 'Profitable %']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # Loop through each wallet address
    for wallet_address in wallet_addresses:
        transactions = {}
        total_trades = 0
        profitable_trades = 0

        # Fetch token transfers for the wallet
        token_transfers = get_token_transfers(wallet_address)

        # Match transaction hashes to token addresses
        for transfer in token_transfers.get('result', []):
            transaction_hash = transfer.get('transaction_hash')
            token_address = transfer.get('address')
            transactions[transaction_hash] = {'token_address': token_address, 'spent_weth': 0, 'received_tokens': 0, 'sold_tokens': 0, 'received_weth': 0}
    

        # Fetch transactions for the wallet
        for transaction_hash in transactions.keys():
            result = transfer_tx_hash(transaction_hash)

            # Loop through transactions to find 'Swap' events
            for tx in result.get('result', []):
                for log in tx.get('logs', []):
                    transaction_value = int(log.get('transaction_value', '0'))
                    is_buy = transaction_value > 0  # Determine if it's a buy or sell
                    transactions[transaction_hash]['is_buy'] = is_buy

                    decoded_event = log.get('decoded_event', {})
                    if decoded_event and decoded_event.get('signature') == 'Swap(address,uint256,uint256,uint256,uint256,address)':
                        params = decoded_event.get('params', [])
                        if len(params) >= 5:
                            amount0In = int(params[1]['value'])
                            amount1In = int(params[2]['value'])
                            amount0Out = int(params[3]['value'])
                            amount1Out = int(params[4]['value'])

                            if is_buy:  # This is a buy
                                transactions[transaction_hash]['spent_weth'] += amount1In
                                transactions[transaction_hash]['received_tokens'] += amount0Out
                                total_trades += 1
                            else:  # This is a sell
                                transactions[transaction_hash]['sold_tokens'] += amount0In
                                transactions[transaction_hash]['received_weth'] += amount1Out

        # Calculate total profit and profitability
        total_realized_profit = 0.0
        for tx_data in transactions.values():
            profit = (tx_data['received_weth'] - tx_data['spent_weth']) / 1e18  # Convert to ETH
            profit += (tx_data['sold_tokens'] - tx_data['received_tokens']) / 1e18  # Convert to ETH
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
