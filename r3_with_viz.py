import json
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any, List, Dict

class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]], conversions: int, trader_data: str) -> None:
        base_length = len(self.to_json([
            self.compress_state(state, ""),
            self.compress_orders(orders),
            conversions,
            "",
            "",
        ]))

        max_item_length = (self.max_log_length - base_length) // 3

        print(self.to_json([
            self.compress_state(state, self.truncate(state.traderData, max_item_length)),
            self.compress_orders(orders),
            conversions,
            self.truncate(trader_data, max_item_length),
            self.truncate(self.logs, max_item_length),
        ]))

        self.logs = ""

    def compress_state(self, state: TradingState, trader_data: str) -> list[Any]:
        return [
            state.timestamp,
            trader_data,
            self.compress_listings(state.listings),
            self.compress_order_depths(state.order_depths),
            self.compress_trades(state.own_trades),
            self.compress_trades(state.market_trades),
            state.position,
            self.compress_observations(state.observations),
        ]

    def compress_listings(self, listings: dict[Symbol, Listing]) -> list[list[Any]]:
        return [[listing["symbol"], listing["product"], listing["denomination"]] for listing in listings.values()]

    def compress_order_depths(self, order_depths: dict[Symbol, OrderDepth]) -> dict[Symbol, list[Any]]:
        return {symbol: [order_depth.buy_orders, order_depth.sell_orders] for symbol, order_depth in order_depths.items()}

    def compress_trades(self, trades: dict[Symbol, list[Trade]]) -> list[list[Any]]:
        return [
            [trade.symbol, trade.price, trade.quantity, trade.buyer, trade.seller, trade.timestamp]
            for arr in trades.values() for trade in arr
        ]

    def compress_observations(self, observations: Observation) -> list[Any]:
        conversion_observations = {
            product: [
                observation.bidPrice,
                observation.askPrice,
                observation.transportFees,
                observation.exportTariff,
                observation.importTariff,
                observation.sunlight,
                observation.humidity,
            ]
            for product, observation in observations.conversionObservations.items()
        }
        return [observations.plainValueObservations, conversion_observations]

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[Any]]:
        return [[order.symbol, order.price, order.quantity] for arr in orders.values() for order in arr]

    def to_json(self, value: Any) -> str:
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))

    def truncate(self, value: str, max_length: int) -> str:
        return value if len(value) <= max_length else value[:max_length - 3] + "..."

logger = Logger()

class Trader:
    def __init__(self):
        self.price_history: Dict[str, List[float]] = {}
        self.max_history_length = 7

    def run(self, state: TradingState) -> tuple[dict[Symbol, list[Order]], int, str]:
        result: Dict[Symbol, List[Order]] = {}
        conversions = 1

        tradable_products = {"KELP", "RAINFOREST_RESIN"}
        tradable_prefix = "VOLCANIC_ROCK_VOUCHER"

        if state.traderData:
            try:
                loaded_data = json.loads(state.traderData)
                self.price_history = {
                    k: v[-self.max_history_length:] for k, v in loaded_data.items()
                }
            except Exception as e:
                logger.print("Failed to load traderData:", e)

        for product, order_depth in state.order_depths.items():
            if product not in tradable_products and not product.startswith(tradable_prefix):
                continue

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

                if product.startswith(tradable_prefix):
                    try:
                        strike = int(product.split("_")[-1])
                        rock_prices = self.price_history.get("VOLCANIC_ROCK", [])

                        if rock_prices:
                            rock_avg = sum(rock_prices) / len(rock_prices)
                            intrinsic_value = max(rock_avg - strike, 0)

                            voucher_mid = mid_price

                            if voucher_mid < intrinsic_value - 10:
                                for ask_price, ask_volume in sorted(order_depth.sell_orders.items()):
                                    if ask_price < intrinsic_value - 10:
                                        buy_volume = min(-ask_volume, 20)
                                        logger.print(f"[{product}] BUY undervalued VOUCHER {buy_volume} @ {ask_price}")
                                        orders.append(Order(product, ask_price, buy_volume))

                            if voucher_mid > intrinsic_value + 10:
                                for bid_price, bid_volume in sorted(order_depth.buy_orders.items(), reverse=True):
                                    if bid_price > intrinsic_value + 10:
                                        sell_volume = min(bid_volume, 20)
                                        logger.print(f"[{product}] SELL overvalued VOUCHER {sell_volume} @ {bid_price}")
                                        orders.append(Order(product, bid_price, -sell_volume))
                    except Exception as e:
                        logger.print(f"Failed to process {product} as voucher:", e)

                    result[product] = orders
                    continue

                for ask_price, ask_volume in sorted(order_depth.sell_orders.items()):
                    if ask_price < fair_value - 0.2:
                        buy_volume = min(-ask_volume, 50)
                        logger.print(f"[{product}] BUY {buy_volume} @ {ask_price}")
                        orders.append(Order(product, ask_price, buy_volume))

                for bid_price, bid_volume in sorted(order_depth.buy_orders.items(), reverse=True):
                    if bid_price > fair_value + 0.2:
                        sell_volume = min(bid_volume, 50)
                        logger.print(f"[{product}] SELL {sell_volume} @ {bid_price}")
                        orders.append(Order(product, bid_price, -sell_volume))

                for ask_price, ask_volume in sorted(order_depth.sell_orders.items()):
                    if ask_price < fair_value - 0.01:
                        buy_volume = min(-ask_volume, 20)
                        logger.print(f"[{product}] BUY {buy_volume} @ {ask_price}")
                        orders.append(Order(product, ask_price, buy_volume))

                for bid_price, bid_volume in sorted(order_depth.buy_orders.items(), reverse=True):
                    if bid_price > fair_value + 0.01:
                        sell_volume = min(bid_volume, 20)
                        logger.print(f"[{product}] SELL {sell_volume} @ {bid_price}")
                        orders.append(Order(product, bid_price, -sell_volume))

            result[product] = orders

        serialized_data = json.dumps({
            k: v for k, v in self.price_history.items()
        })

        logger.flush(state, result, conversions, serialized_data)
        return result, conversions, serialized_data
