from datamodel import OrderDepth, TradingState, Order
from typing import List, Dict
import json
from collections import deque


class Trader:
    def __init__(self):
        self.price_history: Dict[str, deque] = {}
        self.max_history_length = 1000  # Use last 5 mid-prices for averaging

    def run(self, state: TradingState):
        result = {}
        conversions = 1

        if state.traderData:
            try:
                self.price_history = {
                    k: deque(v, maxlen=self.max_history_length)
                    for k, v in json.loads(state.traderData).items()
                }
            except Exception as e:
                print("Failed to load traderData:", e)

        for product, order_depth in state.order_depths.items():
            orders: List[Order] = []

            best_bid = max(order_depth.buy_orders.keys()) if order_depth.buy_orders else None
            best_ask = min(order_depth.sell_orders.keys()) if order_depth.sell_orders else None

            if best_bid is not None and best_ask is not None:
                mid_price = (best_bid + best_ask) / 2

                if product not in self.price_history:
                    self.price_history[product] = deque(maxlen=self.max_history_length)
                self.price_history[product].append(mid_price)

                fair_value = sum(self.price_history[product]) / len(self.price_history[product])

                for ask_price, ask_volume in sorted(order_depth.sell_orders.items()):
                    if ask_price < fair_value:
                        buy_volume = min(-ask_volume, 20)  # Limit order size
                        print(f"[{product}] BUY {buy_volume} @ {ask_price}")
                        orders.append(Order(product, ask_price, buy_volume))

                for bid_price, bid_volume in sorted(order_depth.buy_orders.items(), reverse=True):
                    if bid_price > fair_value:
                        sell_volume = min(bid_volume, 20)  # Limit order size
                        print(f"[{product}] SELL {sell_volume} @ {bid_price}")
                        orders.append(Order(product, bid_price, -sell_volume))

            result[product] = orders

        serialized_data = json.dumps({
            k: list(v) for k, v in self.price_history.items()
        })

        return result, conversions, serialized_data
