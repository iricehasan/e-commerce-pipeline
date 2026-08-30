from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

from data_generator.providers import EventTypeProvider


def generate_events(
    n: int,
    counter: int,
    customers_df: pd.DataFrame,
    event_date: str,
    fake: Faker,
    rng: np.random.Generator,
) -> pd.DataFrame:
    fake.add_provider(EventTypeProvider)

    customer_ids = customers_df["customer_id"].to_numpy()
    chosen_customers = rng.choice(customer_ids, size=n, replace=True)

    day_start = datetime.strptime(event_date, "%Y-%m-%d")
    day_end = day_start + timedelta(days=1) - timedelta(seconds=1)

    rows = []
    for i in range(n):
        rows.append(
            {
                "event_id": f"evt_{counter + i:08d}",
                "customer_id": chosen_customers[i],
                "event_type": fake.event_type(),
                "event_timestamp": fake.date_time_between(start_date=day_start, end_date=day_end),
            }
        )
    return pd.DataFrame(rows)
