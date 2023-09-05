from moralis import evm_api
from decimal import Decimal
import csv
import time

# Your API key
api_key = ""

# Initialize variables
chain = "eth"
WETH_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"  # WETH address on Ethereum mainnet

# Read wallet addresses from CSV
wallet_addresses = []
try:
    with open('CashWallets.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            wallet_addresses.append(row[0])
except FileNotFoundError:
    print("CSV file not found.")
    exit()

# Prepare CSV output
try:
    with open('profitability_results.csv', 'w', newline='') as csvfile:
        fieldnames = ['Wallet Address', 'Total Profit', 'Profitability %']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Loop through each wallet address
        for wallet_address in wallet_addresses:
            params = {
                "address": wallet_address,
                "chain": chain,
            }

            # Initialize counters and storage
            total_profit = 0.0
            total_trades = 0
            profitable_trades = 0
            buy_info = {}  # To store the original buy information

            # Fetch all transactions for the wallet
            try:
                result = evm_api.transaction.get_wallet_transactions(
                    api_key=api_key,
                    params=params,
                )
            except Exception as e:
                print(f"Error fetching transactions for {wallet_address}: {e}")
                continue

            # Loop through transactions
            for tx in result['result']:
                token_address = tx['to_address'] if tx['to_address'] != wallet_address else tx['from_address']
                if token_address == WETH_address:
                    total_trades += 1
                    value_in_ether = float(tx['value']) / 1e18  # Convert value from Wei to Ether

                    # If it's a buy, store the value of WETH
                    if tx['to_address'] == wallet_address:
                        buy_info[token_address] = value_in_ether

                    # If it's a sale, calculate the profit or loss
                    elif tx['from_address'] == wallet_address:
                        original_value = buy_info.get(token_address, 0)
                        if original_value:
                            profit = value_in_ether - original_value
                            total_profit += profit
                            if profit > 0:
                                profitable_trades += 1

            # Calculate profitability percentage
            profitability_percent = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0

            # Write results to CSV
            writer.writerow({
                'Wallet Address': wallet_address,
                'Total Profit': total_profit,
                'Profitability %': profitability_percent
            })

            # Pause to avoid rate-limiting
            time.sleep(60)

except Exception as e:
    print(f"Error writing to CSV: {e}")
