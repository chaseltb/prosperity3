
from datamodel import OrderDepth, TradingState, Order
from typing import List, Dict
import json


class Trader:
    def __init__(self):
        self.price_history: Dict[str, List[float]] = {}
        self.max_history_length = 7  # Use last 8 mid-prices for averaging

    def run(self, state: TradingState):
        result = {}
        conversions = 1

        if state.traderData:
            try:
                loaded_data = json.loads(state.traderData)
                self.price_history = {
                    k: v[-self.max_history_length:] for k, v in loaded_data.items()
                }
            except Exception as e:
                print("Failed to load traderData:", e)

        for product, order_depth in state.order_depths.items():
            if product == "SQUID_INK":
                continue

            orders: List[Order] = []

            best_bid = max(order_depth.buy_orders.keys()) if order_depth.buy_orders else None
            best_ask = min(order_depth.sell_orders.keys()) if order_depth.sell_orders else None

            if best_bid is not None and best_ask is not None:
                mid_price = (best_bid + best_ask) / 2

                if product not in self.price_history:
                    self.price_history[product] = []

                # Add the new price and maintain history length manually
                self.price_history[product].append(mid_price)
                if len(self.price_history[product]) > self.max_history_length:
                    self.price_history[product].pop(0)  # Remove the oldest price

                fair_value = sum(self.price_history[product]) / len(self.price_history[product])

                # Handle buy orders
                for ask_price, ask_volume in sorted(order_depth.sell_orders.items()):
                    if ask_price < fair_value - .25:
                        buy_volume = min(-ask_volume, 50)
                        print(f"[{product}] BUY {buy_volume} @ {ask_price}")
                        orders.append(Order(product, ask_price, buy_volume))

                # Handle sell orders
                for bid_price, bid_volume in sorted(order_depth.buy_orders.items(), reverse=True):
                    if bid_price > fair_value + .25:
                        sell_volume = min(bid_volume, 50)
                        print(f"[{product}] SELL {sell_volume} @ {bid_price}")
                        orders.append(Order(product, bid_price, -sell_volume))

                for ask_price, ask_volume in sorted(order_depth.sell_orders.items()):
                    if ask_price < fair_value - .05:
                        buy_volume = min(-ask_volume, 20)  # Limit order size
                        print(f"[{product}] BUY {buy_volume} @ {ask_price}")
                        orders.append(Order(product, ask_price, buy_volume))

                # Handle sell orders
                for bid_price, bid_volume in sorted(order_depth.buy_orders.items(), reverse=True):
                    if bid_price > fair_value + .05:
                        sell_volume = min(bid_volume, 20)  # Limit order size
                        print(f"[{product}] SELL {sell_volume} @ {bid_price}")
                        orders.append(Order(product, bid_price, -sell_volume))

            # Store the orders for each product
            result[product] = orders

        # Save price history for next round
        serialized_data = json.dumps({
            k: v for k, v in self.price_history.items()
        })

        return result, conversions, serialized_data
