import pandas as pd
from faker import Faker

from data_generator.providers import PaymentMethodProvider


def generate_payments(orders_df: pd.DataFrame, counter: int, fake: Faker) -> pd.DataFrame:
    fake.add_provider(PaymentMethodProvider)
    rows = []
    for i, row in enumerate(orders_df.itertuples(index=False)):
        rows.append(
            {
                "payment_id": f"pay_{counter + i:07d}",
                "order_id": row.order_id,
                "amount": row.total_amount,
                "method": fake.payment_method(),
                "status": "completed",
                "payment_date": row.order_date,
            }
        )
    return pd.DataFrame(rows)
