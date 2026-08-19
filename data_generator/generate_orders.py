import pandas as pd
from faker import Faker
import numpy as np

from data_generator.providers import OrderStatusProvider

def generate_orders(
        n: int, 
        counter: int, 
        customers_df: pd.DataFrame,
        order_date: str,
        fake: Faker,
        rng: np.random.Generator
    ) -> pd.DataFrame:

    """
    Using Pareto Distribution to simulate disproportionate share of orders, i.e.,
    small set of customers order more.

    Weights recomputed per day against whichever customers exist as of this day.
    """
    customer_ids = customers_df["customer_id"].to_numpy()
    raw_weights = rng.pareto(a=2.0, size=len(customer_ids)) + 0.1
    weights = raw_weights / raw_weights.sum()
    chosen_customers = rng.choice(customer_ids, size=n, replace=True, p=weights)

    rows = []
    for i in range(n):
        rows.append(
            {
                "order_id": f"ord_{counter + i:07d}",
                "customer_id": chosen_customers[i],
                "order_date": order_date,
                "status": fake.order_status(),
            }
        )
    return pd.DataFrame(rows)