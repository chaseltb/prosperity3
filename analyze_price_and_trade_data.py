import pandas as pd
import matplotlib.pyplot as plt
import glob
import os

folder = "./data/round1/"

# === 1. Load and merge pricing data with timestamp shifting ===
price_files = sorted(glob.glob(os.path.join(folder, "prices_round_1_day_*.csv")))
price_df_list = []

time_offset = 0
for file in price_files:
    df = pd.read_csv(file, sep=';')
    df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
    df['timestamp'] += time_offset
    time_offset = df['timestamp'].max() + 1  # Shift next day after this one's max timestamp
    price_df_list.append(df)

price_df = pd.concat(price_df_list, ignore_index=True)

# === 2. Load and merge trade data with timestamp shifting ===
trade_files = sorted(glob.glob(os.path.join(folder, "trades_round_1_day_*.csv")))
trade_df_list = []

time_offset = 0
for file in trade_files:
    df = pd.read_csv(file, sep=';')
    df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
    df['timestamp'] += time_offset
    time_offset = df['timestamp'].max() + 1
    trade_df_list.append(df)

trade_df = pd.concat(trade_df_list, ignore_index=True)

# === 3. Plotting Mid Prices (excluding Resin) ===
plt.figure(figsize=(10, 5))
for product in price_df['product'].unique():
    if product == "RAINFOREST_RESIN":
        continue
    subset = price_df[price_df['product'] == product]
    plt.plot(subset['timestamp'], subset['mid_price'], label=product)

plt.title("Mid Prices Over Time")
plt.xlabel("Timestamp")
plt.ylabel("Mid Price")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# === 4. Plotting Trade Prices (excluding Resin) ===
plt.figure(figsize=(10, 5))
for symbol in trade_df['symbol'].unique():
    if symbol == "RAINFOREST_RESIN":
        continue
    subset = trade_df[trade_df['symbol'] == symbol]
    plt.plot(subset['timestamp'], subset['price'], marker='o', linestyle='-', label=symbol)

plt.title("Trade Prices Over Time")
plt.xlabel("Timestamp")
plt.ylabel("Trade Price")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()


volume_by_symbol = trade_df.groupby('symbol')['quantity'].sum().sort_values(ascending=False)
print("Total Volume Traded per Symbol:")
print(volume_by_symbol)

import seaborn as sns

plt.figure(figsize=(10, 5))
sns.barplot(x=volume_by_symbol.index, y=volume_by_symbol.values, palette='viridis')
plt.title("Total Volume Traded per Symbol")
plt.xlabel("Symbol")
plt.ylabel("Total Quantity Traded")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
