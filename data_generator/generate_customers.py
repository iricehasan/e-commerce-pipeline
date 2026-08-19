from collections import OrderedDict

import pandas as pd
from faker import Faker

_COUNTRY_WEIGHTS = OrderedDict(
    [
        ("US", 0.40),
        ("GB", 0.15),
        ("DE", 0.15),
        ("FR", 0.10),
        ("CA", 0.10),
        ("JP", 0.10),
    ]
)


def generate_customers(n: int, counter: int, fake: Faker, signup_date: str) -> pd.DataFrame:
    """n new customers who signed up on signup_date. 

    email uniqueness is guaranteed with customer_id instead of 
    fake.unique.email() to have uniqueness across all dates not just a single day
    """
    countries = fake.random_elements(elements=_COUNTRY_WEIGHTS, length=n, use_weighting=True)

    rows = []
    for i in range(n):
        customer_id = f"cust_{counter + i:06d}"
        rows.append(
            {
                "customer_id": customer_id,
                "name": fake.name(),
                "email": f"{fake.user_name()}.{customer_id}@example.com",
                "country_code": countries[i],
                "signup_date": signup_date,
            }
        )
    return pd.DataFrame(rows)
