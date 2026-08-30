import numpy as np
import pandas as pd
from faker import Faker


def generate_order_items(
    orders_df: pd.DataFrame,
    products_df: pd.DataFrame,
    start_id: int,
    fake: Faker,
    rng: np.random.Generator,
) -> pd.DataFrame:
    rows = []
    item_counter = start_id
    for order_id in orders_df["order_id"]:
        n_items = int(rng.integers(1, 5))
        chosen = products_df.sample(n=n_items, random_state=int(rng.integers(0, 2**31 - 1)))
        for _, product in chosen.iterrows():
            rows.append(
                {
                    "order_item_id": f"item_{item_counter:08d}",
                    "order_id": order_id,
                    "product_id": product["product_id"],
                    "quantity": int(rng.integers(1, 5)),
                    "unit_price_at_purchase": product["price"],
                }
            )
            item_counter += 1
    return pd.DataFrame(rows)


def compute_order_totals(orders_df: pd.DataFrame, order_items_df: pd.DataFrame) -> pd.DataFrame:
    """Derives orders.total_amount from its own line items."""
    line_totals = order_items_df["quantity"] * order_items_df["unit_price_at_purchase"]
    totals = line_totals.groupby(order_items_df["order_id"]).sum().rename("total_amount")
    return orders_df.merge(totals, on="order_id", how="left")
