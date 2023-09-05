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
uniswap_routers = ['0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D', '0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD']
weth_contract = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'

# Function to fetch transactions from Moralis
def get_wallet_transactions(wallet_address):
    params = {
        "chain": chain,
        "address": wallet_address
    }
    return evm_api.transaction.get_wallet_transactions_verbose(api_key=api_key, params=params)

# Read wallet addresses from CSV
wallet_addresses = []
with open('CashWallets.csv', 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        wallet_addresses.append(row[0])

# Prepare CSV output
with open('profitability_results.csv', 'w', newline='') as csvfile:
    fieldnames = ['Wallet Address', 'Total Realized Profit']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # Loop through each wallet address
    for wallet_address in wallet_addresses:
        transactions = {}

        # Fetch transactions for the wallet
        result = get_wallet_transactions(wallet_address)
        print(f"Transactions for {wallet_address}: {result}")
        # Loop through transactions
        for tx in result['result']:
            if 'decoded_call' in tx and tx['decoded_call'] is not None:  # Added check here
                if tx['decoded_call']['signature'] == 'transfer(address,uint256)':
                    token_symbol = tx['decoded_call']['params'][0]['value']
                    amount = tx['decoded_call']['params'][1]['value']

                    if tx['to_address'] in uniswap_routers:
                        transactions.setdefault(token_symbol, {}).setdefault('bought', 0)
                        transactions[token_symbol]['bought'] += amount

                        if tx['from_address'] == wallet_address:
                            transactions[token_symbol]['spent_weth'] = float(tx['value']) / 1e18

                    elif tx['from_address'] in uniswap_routers:
                        transactions.setdefault(token_symbol, {}).setdefault('sold', 0)
                        transactions[token_symbol]['sold'] += amount

                        if tx['to_address'] == wallet_addresses:
                            transactions[token_symbol]['received_weth'] = float(tx['value']) / 1e18

        # Calculate profit
        total_realized_profit = 0.0
        for token_symbol, tx_data in transactions.items():
            if tx_data.get('bought', 0) == tx_data.get('sold', 0):
                profit = tx_data.get('received_weth', 0) - tx_data.get('spent_weth', 0)
                total_realized_profit += profit

        # Write to CSV
        writer.writerow({
            'Wallet Address': wallet_address,
            'Total Realized Profit': total_realized_profit
        })

        logging.info(f"Processed wallet address {wallet_address}")

        # Pause to avoid rate-limiting
        time.sleep(2)
