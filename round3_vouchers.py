from datamodel import OrderDepth, TradingState, Order
from typing import List, Dict
import json


class Trader:
    def __init__(self):
        self.price_history: Dict[str, List[float]] = {}
        self.max_history_length = 7  # Use last 7 mid-prices for averaging

    def run(self, state: TradingState):
        result = {}
        conversions = 1

        tradable_products = {"KELP", "RAINFOREST_RESIN"}
        tradable_prefix = "VOLCANIC_ROCK_VOUCHER"

        # Restore saved price history
        if state.traderData:
            try:
                loaded_data = json.loads(state.traderData)
                self.price_history = {
                    k: v[-self.max_history_length:] for k, v in loaded_data.items()
                }
            except Exception as e:
                print("Failed to load traderData:", e)

        for product, order_depth in state.order_depths.items():
            if product not in tradable_products and not product.startswith(tradable_prefix):
                continue  # Ignore unpredictable products

            orders: List[Order] = []

            best_bid = max(order_depth.buy_orders.keys()) if order_depth.buy_orders else None
            best_ask = min(order_depth.sell_orders.keys()) if order_depth.sell_orders else None

            if best_bid is not None and best_ask is not None:
                mid_price = (best_bid + best_ask) / 2

                if product not in self.price_history:
                    self.price_history[product] = []

                self.price_history[product].append(mid_price)
                if len(self.price_history[product]) > self.max_history_length:
                    self.price_history[product].pop(0)

                fair_value = sum(self.price_history[product]) / len(self.price_history[product])

                # Special logic for VOLCANIC_ROCK_VOUCHER_x
                if product.startswith(tradable_prefix):
                    try:
                        strike = int(product.split("_")[-1])
                        rock_prices = self.price_history.get("VOLCANIC_ROCK", [])

                        if rock_prices:
                            rock_avg = sum(rock_prices) / len(rock_prices)
                            intrinsic_value = max(rock_avg - strike, 0)

                            voucher_mid = (best_bid + best_ask) / 2

                            # Buy undervalued vouchers
                            if voucher_mid < intrinsic_value - 10:
                                for ask_price, ask_volume in sorted(order_depth.sell_orders.items()):
                                    if ask_price < intrinsic_value - 10:
                                        buy_volume = min(-ask_volume, 20)
                                        print(f"[{product}] BUY undervalued VOUCHER {buy_volume} @ {ask_price}")
                                        orders.append(Order(product, ask_price, buy_volume))

                            # Sell overvalued vouchers
                            if voucher_mid > intrinsic_value + 10:
                                for bid_price, bid_volume in sorted(order_depth.buy_orders.items(), reverse=True):
                                    if bid_price > intrinsic_value + 10:
                                        sell_volume = min(bid_volume, 20)
                                        print(f"[{product}] SELL overvalued VOUCHER {sell_volume} @ {bid_price}")
                                        orders.append(Order(product, bid_price, -sell_volume))
                    except Exception as e:
                        print(f"Failed to process {product} as voucher:", e)

                    result[product] = orders
                    continue  # Skip general logic for vouchers

                # General trading logic for KELP and RESIN
                for ask_price, ask_volume in sorted(order_depth.sell_orders.items()):
                    if ask_price < fair_value - 0.2:
                        buy_volume = min(-ask_volume, 50)
                        print(f"[{product}] BUY {buy_volume} @ {ask_price}")
                        orders.append(Order(product, ask_price, buy_volume))

                for bid_price, bid_volume in sorted(order_depth.buy_orders.items(), reverse=True):
                    if bid_price > fair_value + 0.2:
                        sell_volume = min(bid_volume, 50)
                        print(f"[{product}] SELL {sell_volume} @ {bid_price}")
                        orders.append(Order(product, bid_price, -sell_volume))

                # Conservative layer
                for ask_price, ask_volume in sorted(order_depth.sell_orders.items()):
                    if ask_price < fair_value - 0.01:
                        buy_volume = min(-ask_volume, 20)
                        print(f"[{product}] BUY {buy_volume} @ {ask_price}")
                        orders.append(Order(product, ask_price, buy_volume))

                for bid_price, bid_volume in sorted(order_depth.buy_orders.items(), reverse=True):
                    if bid_price > fair_value + 0.01:
                        sell_volume = min(bid_volume, 20)
                        print(f"[{product}] SELL {sell_volume} @ {bid_price}")
                        orders.append(Order(product, bid_price, -sell_volume))

            result[product] = orders

        # Save price history for next round
        serialized_data = json.dumps({
            k: v for k, v in self.price_history.items()
        })

        return result, conversions, serialized_data
